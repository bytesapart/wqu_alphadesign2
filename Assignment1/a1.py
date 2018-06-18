import warnings
import pandas as pd
from yahoofinancials import YahooFinancials
import pickle
from pandas_datareader import data as pdr  # The pandas Data Module used for fetching data from a Data Source
import numpy as np
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import ffn
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fix_yahoo_finance import pdr_override  # For overriding Pandas DataFrame Reader not connecting to YF


def yahoo_finance_bridge():
    """
    This function fixes problems w.r.t. fetching data from Yahoo Finance
    :return: None
    """
    pdr_override()


def get_balance_sheets(tickers):
    """
    Get yearly balance sheets
    :param tickers: List of tickers
    :return:
    """
    print('Fetching Yearly Balance Data from Yahoo for 100 Tickers...')
    total_data = {}
    for index, ticker in enumerate(tickers):
        if index % 1 == 0:
            print('Fetching Yearly Balance Data for %d out of %d' % (index, len(tickers)))
        yahoo_financials = YahooFinancials(ticker)
        total_data[ticker] = \
        yahoo_financials.get_financial_stmts('quaterly', 'balance')['balanceSheetHistoryQuarterly'][ticker]
    return total_data


def get_combined_yearly_data(tickers, yearly_balance_sheets):
    """
    COmbine quartery data to yearly data
    :param tickers:
    :return:
    """
    yearly_combination = {}
    for ticker in tickers:
        yearly_combination[ticker] = {}
        flag = True
        for items in yearly_balance_sheets[ticker]:
            for key, quarter in items.items():
                if flag is True:
                    yearly_combination[ticker].update(quarter)
                    flag = False
                else:
                    yearly_combination[ticker] = dict(yearly_combination[ticker].items() + quarter.items())
    return yearly_combination


def get_combined_yearly_data2(tickers, yearly_balance_sheets):
    """
    COmbine quartery data to yearly data
    :param tickers:
    :return:
    """
    yearly_combination = {}
    for ticker in tickers:
        yearly_combination[ticker] = {}
        flag = True
        for items in yearly_balance_sheets[ticker]['cashflowStatementHistoryQuarterly'][ticker]:
            for key, quarter in items.items():
                if flag is True:
                    yearly_combination[ticker].update(quarter)
                    flag = False
                else:
                    yearly_combination[ticker] = dict(yearly_combination[ticker].items() + quarter.items())
    return yearly_combination


def calc_earnings_yield(tickers):
    """
    calc earnings to yield ratio
    :param tickers:
    :return:
    """
    print('Fetching Earnings to Yield Data from Yahoo for 100 Tickers...')
    total_data = {}
    for index, ticker in enumerate(tickers):
        if index % 1 == 0:
            print('Fetching Earnings to Yield Data for %d out of %d' % (index, len(tickers)))
        try:
            yahoo_financials = YahooFinancials(ticker)
            total_data[ticker] = 1 / yahoo_financials.get_pe_ratio()
        except KeyError:
            print('Could not calc. PE for %s' % ticker)
            total_data[ticker] = None
            continue

    return total_data


def calc_ebita(tickers):
    print('Fetching EBITA Data from Yahoo for 100 Tickers...')
    total_data = {}
    for index, ticker in enumerate(tickers):
        if index % 1 == 0:
            print('Fetching EBITA for %d out of %d' % (index, len(tickers)))
        try:
            yahoo_financials = YahooFinancials(ticker)
            total_data[ticker] = yahoo_financials.get_ebit()
        except KeyError:
            print('Could not calc. PE for %s' % ticker)
            total_data[ticker] = None
            continue

    return total_data


def calc_fcf(tickers):
    print('Fetching Free Cash Flow Yield Data from Yahoo for 100 Tickers...')
    total_data = {}
    for index, ticker in enumerate(tickers):
        if index % 1 == 0:
            print('Fetching Free Cash Flow Yield Data for %d out of %d' % (index, len(tickers)))
        try:
            yahoo_financials = YahooFinancials(ticker)
            total_data[ticker] = yahoo_financials.get_financial_stmts('quarterly', 'balance')
        except KeyError:
            print('Could not fetch Free Cash Flow Yield for %s' % ticker)
            total_data[ticker] = None
            continue

    return total_data


def calc_roce(fcf_raw, earnings_yield):
    fcf_dict = {}
    for ticker, data in fcf_raw.items():
        tcl = fcf_raw[ticker].get('totalCurrentLiabilities')
        if tcl is None:
            tcl = 0
        fcf_dict[ticker] = earnings_yield[ticker] / (fcf_raw[ticker]['totalAssets'] - tcl)
    return fcf_dict


def get_fcf(fcf_raw_yearly):
    total = {}
    for ticker, data in fcf_raw_yearly.items():
        cap_ex = fcf_raw_yearly[ticker].get('capitalExpenditures')
        if cap_ex is None:
            cap_ex = 0
        total[ticker] = fcf_raw_yearly[ticker]['totalCashFromOperatingActivities'] - cap_ex
    return total


def calc_b2m(tickers):
    total = {}
    for index, ticker in enumerate(tickers):
        if index % 1 == 0:
            print('Fetching B2M Data for %d out of %d' % (index, len(tickers)))
        yahoo_financials = YahooFinancials(ticker)
        total[ticker] = yahoo_financials.get_book_value() / yahoo_financials.get_market_cap()
    return total


def main():
    """
    Main function of the program
    :return:
    """
    # ===== Step 1: Read CSV and get 100 Random companies across all sectors =====
    constituents = pd.read_csv('constituents.csv', sep=',')
    # Get 100 random companies
    tickers = \
        constituents[constituents['Sector'].isin(constituents['Sector'].drop_duplicates().sample(10))].sample(100)[
            'Symbol'].reset_index(drop=True)

    # ===== Step 2: Get Financials of the 100 companies =====
    # yearly_balance_sheets = get_balance_sheets(tickers.values.tolist())

    # ===== Step 2.1 Read from pickle if above code is taking too much time =====
    with open('balance.p', 'rb') as handle:
        yearly_balance_sheets = pickle.load(handle)
    tickers = pd.read_pickle('tickers.p')

    # remove all blanks from tickers and balance sheet
    blank = [tick[0] for tick in yearly_balance_sheets.items() if len(tick[1]) == 0]
    for item in blank:
        del yearly_balance_sheets[item]
    tickers.drop(tickers[tickers.isin(blank)].index, inplace=True)

    # combine all the data to yearly data
    yearly_combination = get_combined_yearly_data(tickers.values.tolist(), yearly_balance_sheets)

    # ===== Step 3: Calculate fundamentals =====
    # earnings_yield = calc_earnings_yield(tickers.values.tolist())
    with open('balance.p', 'rb') as handle:
        earnings_yield = pickle.load(handle)
    # remove all blanks from tickers and balance sheet
    blank = [tick[0] for tick in yearly_balance_sheets.items() if tick[1] is None]
    for item in blank:
        del yearly_balance_sheets[item]
        del yearly_combination[item]
    tickers.drop(tickers[tickers.isin(blank)].index, inplace=True)
    # ebita = calc_ebita(tickers.values.tolist())
    with open('earnings_yield.p', 'rb') as handle:
        earnings_yield = pickle.load(handle)
    with open('ebita.p', 'rb') as handle:
        ebita = pickle.load(handle)
    # remove all blanks from tickers and balance sheet
    blank = [tick[0] for tick in yearly_balance_sheets.items() if tick[1] == 0]
    for item in blank:
        del yearly_balance_sheets[item]
        del yearly_combination[item]
    tickers.drop(tickers[tickers.isin(blank)].index, inplace=True)
    with open('fcf_raw.p', 'rb') as handle:
        fcf_raw = pickle.load(handle)
    fcf_raw_yearly = get_combined_yearly_data2(tickers.values.tolist(), fcf_raw)
    fcf = get_fcf(fcf_raw_yearly)
    return_on_cap_emp = calc_roce(yearly_combination, ebita)
    book_to_market = calc_b2m(tickers.values.tolist()[:10])

    print('===== Yearly Balance Sheet =====')
    print(yearly_combination)

    print('===== Earnings Yield =====')
    print(earnings_yield)

    print('===== EBITA =====')
    print(ebita)

    print('===== Free Cash Flow =====')
    print(fcf)

    print('===== Return on Cap Employee =====')
    print(return_on_cap_emp)

    print('===== Book to Market =====')
    print(book_to_market)


    data_df = pd.DataFrame.from_dict(ebita, orient='index').reset_index().sort_values(0)
    data_df = data_df.loc[data_df[0] != 0]
    ticks = data_df['index'][:10].values.tolist()
    yahoo_finance_bridge()

    start = datetime.datetime(2014, 6, 1)
    end = datetime.datetime(2018, 1, 1)

    tickers = ticks
    print('===== Bottom Decile =====')
    print(tickers)
    data = pdr.get_data_yahoo(tickers, start=start, end=end, auto_adjust=True)
    data = data['Open']
    data = data.sort_index(axis=0, ascending=True)
    df_normalized = data / data.iloc[0]
    returns = np.log(data / data.shift(1))
    allocation = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    df_allocated = df_normalized * allocation
    initial_investment = 10000
    df_position = df_allocated * initial_investment
    df_portfolio_value = pd.DataFrame(df_position.sum(axis=1))
    df_portfolio_value.columns = ['Portfolio_Valuation']
    perf = df_portfolio_value.calc_stats()
    perf.plot()
    plt.show()
    plt.close()
    print perf.display()

    # Define a trailing 252 trading day window
    window = 252

    # Calculate the max drawdown in the past window days for each day
    rolling_max = df_portfolio_value.rolling(window, min_periods=1).max()
    daily_drawdown = df_portfolio_value / rolling_max - 1.0

    # Calculate the minimum (negative) daily drawdown
    max_daily_drawdown = daily_drawdown.rolling(window, min_periods=1).min()

    # Plot the results
    daily_drawdown.plot(legend=True, figsize=(15, 8))
    max_daily_drawdown.plot(legend=True, figsize=(15, 8))

    # Show the plot
    plt.show()
    plt.close()


if __name__ == '__main__':
    main()
