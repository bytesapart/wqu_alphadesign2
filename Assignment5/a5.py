"""
Created on Mon Aug 14 09:54:10 2017

@author: Osama Iqbal

Code uses Python 2.7, packaged with Anaconda 4.4.0
Code developed on Windows 10 OS.

Project 5:
-- Steps:
1.	Write a python program that prompts the user to enter any valid stock symbol available in Google Finance, Yahoo Finance, Quandl, CityFALCON, or another similar source for NYSE & NASDAQ. Ensure proper error handling for wrong user inputs..
2.	Download data for last 1 month for user entered ticker from Google Finance, Yahoo Finance, Quandl, CityFALCON, or another similar source
3.	Using Interpolation techniques, fit a quadratic line through the data points and plot the same
4.	Choose a quadratic equation of your choice and using SciPy leastsq() optimization method calculate the best fit line with respect to the downloaded data
5.  Plot the best fit line and the actual data points together with error bars.
"""
# Some Metadata about the script
__author__ = 'Osama Iqbal (iqbal.osama@icloud.com)'
__license__ = 'MIT'
__vcs_id__ = '$Id$'
__version__ = '1.0.0'  # Versioning: http://www.python.org/dev/peps/pep-0386/

import logging  # Logging class for logging in the case of an error, makes debugging easier
import sys  # For gracefully notifying whether the script has ended or not
from pandas_datareader import data as pdr  # The pandas Data Module used for fetching data from a Data Source
import pandas as pd
import warnings  # For removing Deprication Warning w.r.t. Yahoo Finance Fix
import datetime  # For setting correct dates from today up to a year in the past to get data from YF
import numpy as np  # For numerical operations
import matplotlib.pyplot as plt

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fix_yahoo_finance import pdr_override  # For overriding Pandas DataFrame Reader not connecting to YF


def yahoo_finance_bridge():
    """
    This function fixes problems w.r.t. fetching data from Yahoo Finance
    :return: None
    """
    print('Correcting Yahoo Finance')
    pdr_override()


def get_ticker_from_user():
    """
    This function prompts a user for an input, and returns it as the ticker
    :return:
    """
    logging.info('Prompting user to enter a ticker symbol')
    print('Note: Data up to 1 month from today will be fetched from Yahoo Finance')
    return raw_input('Enter a Symbol Ticker (case insensitive): ')


def get_data_from_yahoo_finance(stock_ticker):
    """
    This function fetches data from Yahoo Finance in the form of a Pandas DataFrame
    :param stock_ticker: The Ticker symbol for which data needs to be fetched
    :return: pd.DataFrame - Returns a DataFrame containing the data fetched from Yahoo Finance
    """
    today = datetime.datetime.now().date() - datetime.timedelta(1)
    previous_years = today.replace(year=today.year - 5)
    data = pdr.get_data_yahoo(stock_ticker, start=str(previous_years), end=str(today), auto_adjust=True)
    if data.empty:
        print('No Data found for Ticker %s. The ticker does not exist' % stock_ticker)
        raise ValueError('No Data found for Ticker %s. The ticker does not exist' % stock_ticker)
    else:
        return data


def main():
    """
    This function is called from the main block. The purpose of this function is to contain all the calls to
    business logic functions
    :return: int - Return 0 or 1, which is used as the exist code, depending on successful or erroneous flow
    """
    # Wrap in a try block so that we catch any exceptions thrown by other functions and return a 1 for graceful exit
    try:
        # ===== Step 0: Sanitation =====
        # Fix Pandas Datareader's Issues with Yahoo Finance (Since yahoo abandoned it's API)
        yahoo_finance_bridge()

        # ===== Step 1: Get the Ticker From user =====
        # Prompt the user to input the data that needs to be downloaded
        stock_ticker = get_ticker_from_user()
        logging.debug('Stock Ticker is: %s' % str(stock_ticker))

        # ===== Step 2: Download the data for the Ticker =====
        # Get the data fetched from Yahoo Finance
        data = get_data_from_yahoo_finance(str(stock_ticker))
        data = pd.DataFrame(data['Open'])
        data = data.sort_index(axis=0, ascending=True)

        # Calculate daily differences
        data['diff'] = data.diff(periods=1)
        ## Calcultate the cumulative returns
        data['cum'] = data['diff'].cumsum()

        #Meanreversion
        # Setting position long = 1 and short = -1 based on previous day move
        delta = 0.005
        # If previous day price difference was less than or equal then delta, we go long
        # If previous day price difference was more than or equal then delta, we go short
        data['position_mr'] = np.where(data['diff'].shift(1) <= -delta,1, np.where(data['diff'].shift(1) >= delta, -1, 0))
        data['result_mr'] = (data['diff'] * data['position_mr']).cumsum()

        # We will filter execution of our strategy by only executing if our result are above it's 200 day moving average
        win = 200
        data['ma_mr'] = pd.rolling_mean(data['result_mr'], window=win)
        filtering_mr = data['result_mr'].shift(1) > data['ma_mr'].shift(1)
        data['filteredresult_mr'] = np.where(filtering_mr, data['diff'] * data['position_mr'], 0).cumsum()
        # if we do not want to filter we use below line of code
        # df['filteredresult_mr'] = (df['diff'] * df['position_mr']).cumsum()
        data[['ma_mr', 'result_mr', 'filteredresult_mr']].plot(figsize=(10, 8))
        plt.show()
        plt.close()

        # Breakout
        # Setting position long = 1 and short = -1 based on previous day move
        # By setting the delta to negative we are switching the strategy to Breakout
        delta = -0.01
        # If previous day price difference was less than or equal then delta, we go long
        # If previous day price difference was more than or equal then delta, we go short
        data['position_bo'] = np.where(data['diff'].shift(1) <= -delta, 1,
                                       np.where(data['diff'].shift(1) >= delta, -1, 0))
        data['result_bo'] = (data['diff'] * data['position_bo']).cumsum()

        # We will filter execution of our strategy by only executing if our result are above it's 200 day moving average
        win = 200
        data['ma_bo'] = pd.rolling_mean(data['result_bo'], window=win)
        filtering_bo = data['result_bo'].shift(1) > data['ma_bo'].shift(1)
        data['filteredresult_bo'] = np.where(filtering_bo, data['diff'] * data['position_bo'], 0).cumsum()
        # df['filteredresult_bo'] = (df['diff'] * df['position_bo']).cumsum()
        data[['ma_bo', 'result_bo', 'filteredresult_bo']].plot(figsize=(10, 8))
        plt.show()
        plt.close()
        # Here we combine the Meanreversion and the Breakout strategy results
        data['combi'] = data['filteredresult_mr'] + data['filteredresult_bo']
        data[['combi', 'filteredresult_mr', 'filteredresult_bo']].plot(figsize=(10, 8))

        # get 80% data
        data['sel'] = range(int(len(data)))
        eighty_data = data.loc[:data.index[data['sel'] == int(0.8 * len(data))].strftime('%Y%m%d').tolist()[0]]
        # Calculate Optimal F for 80% data FOR MOVING AVERAGE
        p_mr = float(len(eighty_data[eighty_data['result_mr'] > 0])) / float(len(data))
        plr_mr = eighty_data[eighty_data['result_mr'] > 0]['result_mr'].mean() / eighty_data[eighty_data['result_mr'] < 0]['result_mr'].mean()
        op_f_mr = p_mr * (plr_mr + 1) - 1 / plr_mr
        print('Optimal F for MR is: %s' % str(op_f_mr))

        # Calculate Optimal F for 80% data FOR BREAKOUT
        p_bo = float(len(eighty_data[eighty_data['result_bo'] > 0])) / float(len(data))
        plr_bo = eighty_data[eighty_data['result_bo'] > 0]['result_bo'].mean() / \
                 eighty_data[eighty_data['result_bo'] < 0]['result_bo'].mean()
        op_f_bo = p_bo * (plr_bo + 1) - 1 / plr_bo
        print('Optimal F for BO is: %s' % str(op_f_bo))

        # Calculate KPIs on 20% data
        twenty_data = data.loc[:data.index[data['sel'] == int(0.2 * len(data))].strftime('%Y%m%d').tolist()[0]]
        import ffn
        # FOR Moving Average
        df_portfolio_value_mr = twenty_data['result_mr']
        perf = df_portfolio_value_mr.calc_stats()
        perf.plot()
        plt.show()
        plt.close()
        print perf.display()

        # FOR Breakout
        df_portfolio_value_bo = twenty_data['result_bo']
        perf_bo = df_portfolio_value_bo.calc_stats()
        perf_bo.plot()
        plt.show()
        plt.close()
        print perf_bo.display()

    except BaseException, e:
        # Casting a wide net to catch all exceptions
        print('\n%s' % str(e))
        return 1


# Main block of the program. The program begins execution from this block when called from a cmd
if __name__ == '__main__':
    # Initialize Logger
    logging.basicConfig(format='%(asctime)s %(message)s: ')
    logging.info('Application Started')
    exit_code = main()
    logging.info('Application Ended')
    sys.exit(exit_code)