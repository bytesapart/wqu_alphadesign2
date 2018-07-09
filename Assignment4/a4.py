"""
Created on Mon Jun 25 09:54:10 2018

@author: Osama Iqbal

Code uses Python 2.7, packaged with Anaconda 4.4.0
Code developed on Windows 10 OS

Project 4:
-- Steps:
1.	Choose a sectoral index and all of its constituent stocks
2.	Download/access 1 min stock data from an appropriate financial website such as Google Finance, Yahoo Finance, Quandl, CityFALCON, or another similar source.
3.	Using historical data check the stocks for correlation w.r.t its Index and identify the one with the strongest relationship
4. Device a pairs trading strategy on the 1 minute timeframe when the index and its constituent stock moves out of sync with each other (Short one and go long the other). Focus should be the simplicity of code and fast execution.
5.	Exit trade when relationship mean revert
6.  Consider Equal amount invested for every trade
7. Estimate KPI

"""

# Some Metadata about the script
__author__ = 'Osama Iqbal (iqbal.osama@icloud.com)'
__license__ = 'MIT'
__vcs_id__ = '$Id$'
__version__ = '1.0.0'  # Versioning: http://www.python.org/dev/peps/pep-0386/

import logging  # Logging class for logging in the case of an error, makes debugging easier
import sys  # For gracefully notifying whether the script has ended or not
import warnings  # For removing Deprecation Warning w.r.t. Yahoo Finance Fix
import csv
import re
import codecs
import requests
import pandas as pd
import logging
import numpy as np
import datetime
import matplotlib.pyplot as plt
import seaborn as sns


def get_google_finance_intraday(ticker, period=60, days=1, exchange='NASD', index=False):
    """
    Retrieve intraday stock data from Google Finance.

    Parameters
    ----------------
    ticker : str
        Company ticker symbol.
    period : int
        Interval between stock values in seconds.
        i = 60 corresponds to one minute tick data
        i = 86400 corresponds to daily data
    days : int
        Number of days of data to retrieve.
    exchange : str
        Exchange from which the quotes should be fetched

    Returns
    ---------------
    df : pandas.DataFrame
        DataFrame containing the opening price, high price, low price,
        closing price, and volume. The index contains the times associated with
        the retrieved price values.
    """

    # build url
    if index is not True:
        url = 'https://finance.google.com/finance/getprices' + \
          '?p={days}d&f=d,o,h,l,c,v&q={ticker}&i={period}&x={exchange}'.format(ticker=ticker,
                                                                               period=period,
                                                                               days=days,
                                                                               exchange=exchange)
    else:
        url = 'https://finance.google.com/finance/getprices' + \
              '?p={days}d&f=d,o,h,l,c,v&q={ticker}&i={period}'.format(ticker=ticker,
                                                                                   period=period,
                                                                                   days=days,
                                                                                   exchange=exchange)

    page = requests.get(url)
    reader = csv.reader(codecs.iterdecode(page.content.splitlines(), "utf-8"))
    columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    rows = []
    times = []
    for row in reader:
        if re.match('^[a\d]', row[0]):
            if row[0].startswith('a'):
                start = datetime.datetime.fromtimestamp(int(row[0][1:]))
                times.append(start)
            else:
                times.append(start + datetime.timedelta(seconds=period * int(row[0])))
            rows.append(map(float, row[1:]))
    if len(rows):
        return pd.DataFrame(rows, index=pd.DatetimeIndex(times, name='Date'), columns=columns)
    else:
        return pd.DataFrame(rows, index=pd.DatetimeIndex(times, name='Date'))


def main():
    """
    This function is called from the main block. The purpose of this function is to contain all the calls to
    business logic functions
    :return: int - Return 0 or 1, which is used as the exist code, depending on successful or erroneous flow
    """
    # Wrap in a try block so that we catch any exceptions thrown by other functions and return a 1 for graceful exit
    try:
        # ===== Step 1: Get Intraday data =====
        # input data
        tickers = pd.read_csv('20151117-master.csv', header=None)
        main_data = pd.DataFrame()
        period = 60
        days = 1
        dju_data = get_google_finance_intraday('DJU', period=period, days=days, index=True)
        main_data = main_data.append(dju_data['Open']).T
        main_data.columns = ['DJU']
        for index, ticker in tickers.iterrows():
            print('Downloading data for: %s' % ticker.values.tolist()[0])
            the_data = get_google_finance_intraday(ticker.values.tolist()[0], period=period, days=days, index=True)
            main_data = main_data.join(the_data['Open'])
            main_data.columns = main_data.columns.values.tolist()[:-1] + ticker.values.tolist()
        data = main_data
        data = data.sort_index(axis=0, ascending=True)

        # ===== Step 2: Get the highly co-related stock =====
        stock = data.corr().abs()['DJU'].sort_values(ascending=False).index[1]
        # ===== Step 3: Get Pairs =====
        data['pair'] = data['DJU'] - data[stock]

        data = data['pair']
        data = pd.DataFrame(data)

        data['returns'] = np.log(data / data.shift(1))
        data['SMA'] = data['pair'].rolling(window=50, center=False).mean()
        threshold = 0.0
        data['distance'] = data['pair'] - data['SMA']
        data = data.dropna()
        data = pd.DataFrame(data)
        data.head()

        sns.tsplot(data=data['distance'],
                   condition="Deviation", value="Spread")
        plt.show()
        plt.close()

        data['position'] = np.where(data['distance'] > threshold, -1, np.nan)
        data['position'] = np.where(data['distance'] < -threshold, 1, data['position'])
        data['position'] = np.where(data['distance'] * data['distance'].shift(1) < 0, 0, data['position'])
        data['position'] = data['position'].ffill().fillna(0)
        data['position'].plot(figsize=(10, 6))
        plt.show()
        plt.close()

        data['strategy'] = data['position'].shift(1) * data['returns']
        data[['returns', 'strategy']].dropna().cumsum().apply(np.exp).plot(figsize=(10, 6))
        plt.show()
        plt.close()

        import ffn
        df_portfolio_value = data['strategy']
        perf = df_portfolio_value.calc_stats()
        perf.plot()
        plt.show()
        plt.close()

        print perf.display()

        ax = perf.prices.to_drawdown_series().plot()
        plt.show()
        plt.close()

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
