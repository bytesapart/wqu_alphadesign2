import warnings
import pandas as pd
import numpy as np
from pandas_datareader import data as pdr  # The pandas Data Module used for fetching data from a Data Source
import numpy as np
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fix_yahoo_finance import pdr_override  # For overriding Pandas DataFrame Reader not connecting to YF


def yahoo_finance_bridge():
    """
    This function fixes problems w.r.t. fetching data from Yahoo Finance
    :return: None
    """
    pdr_override()


def RSI(series, period):
    delta = series.diff().dropna()
    u = delta * 0
    d = u.copy()
    u[delta > 0] = delta[delta > 0]
    d[delta < 0] = -delta[delta < 0]
    u[u.index[period-1]] = np.mean( u[:period] ) #first value is sum of avg gains
    u = u.drop(u.index[:(period-1)])
    d[d.index[period-1]] = np.mean( d[:period] ) #first value is sum of avg losses
    d = d.drop(d.index[:(period-1)])
    rs = pd.stats.moments.ewma(u, com=period-1, adjust=False) / \
         pd.stats.moments.ewma(d, com=period-1, adjust=False)
    return 100 - 100 / (1 + rs)


def main():
    """
    Main entry function of the script
    :return:
    """
    # ===== Get Data =====
    yahoo_finance_bridge()
    start = datetime.datetime(2007, 6, 1)
    end = datetime.datetime(2018, 1, 1)
    ticker = raw_input('Please Enter a Valid (single) Ticker to fetch the data for. Example \'AAPL\'')
    data = pdr.get_data_yahoo(ticker, start=start, end=end, auto_adjust=True)
    if data.empty:
        print('Please enter valid ticker')
        return 1
    data = pd.DataFrame(data['Open'])
    data.columns = [str(ticker)]
    data = data.sort_index(axis=0, ascending=True)

    # ====== Step 2: Calc. SMA =====
    data['SMA1'] = data.rolling(50).mean()
    data['SMA2'] = data[ticker].rolling(200).mean()
    data.plot(title=ticker + ' stock price | 50 & 200 days SMAs', figsize=(10, 6))
    plt.show()
    plt.close()

    # ===== Construct Portfolio =====
    data['position'] = np.where(data['SMA1'] > data['SMA2'], 1, -1)
    data.dropna(inplace=True)
    data['position'].plot(ylim=[-1.1, 1.1], title='Market Positioning')
    data['returns'] = np.log(data['AAPL'] / data['AAPL'].shift(1))
    data['returns'].hist(bins=35)
    data['strategy'] = data['position'].shift(1) * data['returns']
    data[['returns', 'strategy']].sum()
    data[['returns', 'strategy']].cumsum().apply(np.exp).plot(figsize=(10, 6))
    plt.show()
    plt.close()

    data['cumreturns'] = 1 + (data['strategy'].cumsum())

    import ffn
    # %pylab inline
    df_portfolio_value = data['cumreturns']
    perf = df_portfolio_value.calc_stats()
    perf.plot()
    plt.show()
    plt.close()
    ax = perf.prices.to_drawdown_series().plot()
    plt.show()
    plt.close()
    print perf.display()

    data['RSI'] = RSI(data[ticker], 14)

    # Let's see a historical view of the closing price
    data.plot(legend=True, figsize=(15, 8))
    plt.show()
    plt.close()

    # Create an "empty" column as placeholder for our /position signals
    data['Position'] = None

    # Fill our newly created position column - set to sell (-1) when the price hits the upper band, and set to buy (1) when it hits the lower band
    for row in range(len(data)):

        if (data['RSI'].iloc[row] > 69) and (data['RSI'].iloc[row - 1] < 69):
            data['Position'].iloc[row] = 1

        if (data['RSI'].iloc[row] < 30) and (data['RSI'].iloc[row - 1] > 30):
            data['Position'].iloc[row] = -1

            # Forward fill our position column to replace the "None" values with the correct long/short positions to represent the "holding" of our position
    # forward through time
    data['Position'].fillna(method='ffill', inplace=True)

    # Calculate the daily market return and multiply that by the position to determine strategy returns
    data['Market Return'] = np.log(data['AAPL'] / data['AAPL'].shift(1))
    data['Strategy Return'] = data['Market Return'] * data['Position']

    # Plot the strategy returns
    data['Strategy Return'].cumsum().plot()
    plt.show()
    plt.close()

    df2_portfolio_value = data['Strategy Return'].cumsum()
    perf2 = df2_portfolio_value.calc_stats()
    print perf2.display()

    ax = perf2.prices.to_drawdown_series().plot()
    plt.show()
    plt.close()


if __name__ == '__main__':
    main()