"""
Created on Mon Jun 25 09:54:10 2018

@author: Osama Iqbal

Code uses Python 2.7, packaged with Anaconda 4.4.0
Code developed on Windows 10 OS

Project 3:
-- Steps:
1.	download/access data of relevant stocks or broad market indices for the same period
2.	A simple approach to measure the effect of an event is to identify the size of its reaction. This can be done by comparing the volatility of the current day with the average volatility of the recent past, using the true range calculation
3.	Determine the optimal values of Volatility Ratio that has greatest predictive power in back-tests
4.	Device a simple trading strategy that trades any of the broad market indices based on buy-sell signals generated from Volatility as an event driven indicator
5.  Estimate historic performance for such a system and calculate all the relevant KPIs as marked below
"""
# Some Metadata about the script
__author__ = 'Osama Iqbal (iqbal.osama@icloud.com)'
__license__ = 'MIT'
__vcs_id__ = '$Id$'
__version__ = '1.0.0'  # Versioning: http://www.python.org/dev/peps/pep-0386/

import logging  # Logging class for logging in the case of an error, makes debugging easier
import sys  # For gracefully notifying whether the script has ended or not
import warnings  # For removing Deprecation Warning w.r.t. Yahoo Finance Fix
from pandas_datareader import data as pdr  # The pandas Data Module used for fetching data from a Data Source
import numpy as np
import datetime
import matplotlib.pyplot as plt  # For plotting charts
import matplotlib.dates as mdates
import matplotlib.cbook as cbook

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fix_yahoo_finance import pdr_override  # For overriding Pandas DataFrame Reader not connecting to YF


def yahoo_finance_bridge():
    """
    This function fixes problems w.r.t. fetching data from Yahoo Finance
    :return: None
    """
    pdr_override()


def get_data_from_yahoo_finance(stock_ticker):
    """
    This function fetches data from Yahoo Finance in the form of a Pandas DataFrame
    :param stock_ticker: The Ticker symbol for which data needs to be fetched
    :return: pd.DataFrame - Returns a DataFrame containing the data fetched from Yahoo Finance
    """
    start = datetime.datetime(2007, 6, 1)
    end = datetime.datetime(2018, 1, 1)
    data = pdr.get_data_yahoo(stock_ticker, start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'), auto_adjust=True)
    if data.empty:
        logging.info('No Data found for Ticker %s. The ticker does not exist' % stock_ticker)
        raise ValueError('No Data found for Ticker %s. The ticker does not exist' % stock_ticker)
    else:
        return data


def compute_vol_ratio_and_aty(stock_data):
    """
    Computes the Vol Ratio and ATR5 for the given data
    :param stock_data: The stock data dataframe for computing, and for storing the result
    :return:
    """
    # Compute the logarithmic returns using the Closing price
    stock_data['Log_Ret'] = np.log(stock_data['Close'] / stock_data['Close'].shift(1))

    # Compute Volatility using the pandas rolling standard deviation function
    stock_data['Volatility'] = stock_data['Log_Ret'].rolling(window=252, center=False).std() * np.sqrt(252)
    stock_data['ATR'] = abs(stock_data['High'] - stock_data['Low'])

    # Plot the close, volatility and ATR to get a rough idea of what's happening
    stock_data[['Close', 'Volatility', 'ATR']].plot(subplots=True, color='blue', figsize=(8, 6))
    plt.show()
    plt.close()

    # Calculate ATR for a window of 5 days
    stock_data['ATR5'] = (stock_data['ATR'].rolling(min_periods=1, window=5).sum()) / 4
    # Calculate the Volatility Ratio
    stock_data['VolRatio'] = (stock_data['ATR'] / stock_data['ATR5'])

    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    yearsFmt = mdates.DateFormatter('%Y')
    fig, ax = plt.subplots()
    ax.plot(stock_data['VolRatio'])
    # format the ticks
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)

    # round to nearest years...
    datemin = np.datetime64(stock_data.index[0], 'Y')
    datemax = np.datetime64(stock_data.index[-1], 'Y') + np.timedelta64(1, 'Y')
    ax.set_xlim(datemin, datemax)

    # format the coords message box
    def price(x):
        return '$%1.2f' % x

    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.format_ydata = price
    ax.grid(True)

    # rotates and right aligns the x labels, and moves the bottom of the
    # axes up to make room for them
    fig.autofmt_xdate()

    plt.show()
    plt.close()

    # Plot the Vol Ratip
    stock_data[['Close', 'VolRatio']].plot(subplots=True, color='blue', figsize=(16, 10))
    plt.show()
    plt.close()

    return stock_data


def compute_buy_sell_on_vol(stock_data):
    """
    Compute Buy-Sell Signal based on volatility
    :param stock_data: The stock data
    :return:
    """
    # Create an "empty" column as placeholder for our /position signals
    stock_data['Position'] = None

    # Fill our newly created position column - set to sell (-1) when the price hits the upper band, and set to buy (1) when it hits the lower band
    for row in range(len(stock_data)):

        if (stock_data['VolRatio'].iloc[row] > 1.4) and (stock_data['VolRatio'].iloc[row - 1] < 1.4):
            stock_data['Position'].iloc[row] = 1

        if (stock_data['VolRatio'].iloc[row] < 0.4) and (stock_data['VolRatio'].iloc[row - 1] > 0.4):
            stock_data['Position'].iloc[row] = 0  # -1

    # Forward fill our position column to replace the "None" values with the correct long/short positions to represent the "holding" of our position
    # forward through time
    stock_data['Position'].fillna(method='ffill', inplace=True)

    # Calculate the daily market return and multiply that by the position to determine strategy returns
    stock_data['Market Return'] = np.log(stock_data['Close'] / stock_data['Close'].shift(1))
    stock_data['Strategy Return'] = stock_data['Market Return'] * stock_data['Position']

    # Plot the strategy returns
    stock_data['Strategy Return'].cumsum().plot(subplots=True, color='blue', figsize=(16, 10))
    plt.show()
    plt.close()

    return stock_data


def calculate_kpis(stock_data):
    """
    Calculates KPIs and prints it
    :param stock_data: The data used to calculate KPIs
    :return:
    """
    import ffn
    # %pylab inline
    df2_portfolio_value = stock_data['Strategy Return'].cumsum()
    perf2 = df2_portfolio_value.calc_stats()
    perf = stock_data['Strategy Return']
    print(perf2.display())

    ax = perf.to_drawdown_series().plot(subplots=True, color='blue', figsize=(16, 10))
    plt.show()
    plt.close()


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

        # ===== Step 1: Download the data for the Ticker =====
        # Get the data fetched from Yahoo Finance
        stock_data = get_data_from_yahoo_finance('AAPL')

        # ===== Step 3: Compute Volatility and Average True Range =====
        stock_data = compute_vol_ratio_and_aty(stock_data)

        # ===== Step 4: Generate Buy-Sell signals based on Volatility =====
        stock_data = compute_buy_sell_on_vol(stock_data)

        # ===== Step 5: Calculate KPIs =====
        calculate_kpis(stock_data)

    except BaseException, e:
        # Casting a wide net to catch all exceptions
        print('\n%s' % str(e))
        return 1


if __name__ == '__main__':
    # Initialize Logger
    logging.basicConfig(format='%(asctime)s %(message)s: ')
    logging.info('Application Started')
    exit_code = main()
    logging.info('Application Ended')
    sys.exit(exit_code)
