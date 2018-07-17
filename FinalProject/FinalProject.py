# Some Metadata about the script
__author__ = 'Osama Iqbal (iqbal.osama@icloud.com)'
__license__ = 'MIT'
__vcs_id__ = '$Id$'
__version__ = '1.0.0'  # Versioning: http://www.python.org/dev/peps/pep-0386/

from pandas_datareader import data as pdr  # The pandas Data Module used for fetching data from a Data Source
import ffn
import pandas as pd
import warnings  # For removing Deprication Warning w.r.t. Yahoo Finance Fix
import numpy as np  # For numerical operations


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


def portfolio_calculations(port, prices_panel, period_policy, stages):
    """
    This function generates ema and atr and decisions to buy or sell based on those parameters
    """

    # period_policy 1 => ema of 21
    if period_policy == 1:
        ema = prices_panel['Close'].ewm(21).mean()

    # period_policy 2 or all other imply ema of 45 days
    else:
        ema = prices_panel['Close'].ewm(45).mean()

    port['ema'] = ema

    # calcualte each cell direction and progress in stage of pyramid strategy
    for ticker in prices_panel.minor_axis:
        prev_date = prices_panel.major_axis[0]
        for date in prices_panel.major_axis:
            port.loc['atr', date, ticker] = \
                max(prices_panel['High', date, ticker] - prices_panel['Low', date, ticker],
                    abs(prices_panel['High', date, ticker] - prices_panel['Close', prev_date, ticker]),
                    abs(prices_panel['Low', date, ticker] - prices_panel['Close', prev_date, ticker]))

            yest_close = prices_panel['Close', prev_date, ticker]
            avg = port['ema', date, ticker]
            band = 0.5 * port['atr', date, ticker]

            direction = 0
            progress = 0
            old_direction = port.loc['direction', prev_date, ticker]
            old_progress = port.loc['progress', prev_date, ticker]

            # if we are in lowest zone, we need to start selling
            # if we are already selling, progress in stage
            if yest_close < avg - band:
                direction = 'sell'
                if old_direction == 'sell':
                    if old_progress < 4:
                        progress = old_progress + 1
                    else:
                        progress = old_progress


            # case where we should should stop buying
            elif avg - band < yest_close < avg:
                direction = 'sell'
                if old_direction == 'buy':
                    progress = 0  # by default but making it explicit

                # if we were selling, increment progress
                elif old_progress < 4:
                    progress = old_progress + 1
                else:
                    progress = old_progress

            # case when we should stop selling
            elif avg < yest_close < avg + band:
                direction = 'buy'
                if old_direction == 'sell':
                    progress = 0
                elif old_progress < 4:
                    progress = old_progress + 1
                else:
                    progress = old_progress

            # case where we should start buying
            else:
                direction = 'buy'
                if old_direction == 'buy':
                    if old_progress < 4:
                        progress = old_progress + 1
                    else:
                        progress = old_progress

            port.loc['direction', date, ticker] = direction
            port.loc['progress', date, ticker] = progress
            port.loc['progress_percent', date, ticker] = stages[progress] / 100
            prev_date = date

    return port


def generate_pyramid(pyramid):
    # case 1 => upright pyramid
    # In this we keep adding position in 5 stages
    # after trade moves in our direction
    if pyramid == 1:
        stages = [50, 75, 88, 95, 100]

    # case 2 => inverted pyramid
    # In this case, we constantly add same size
    elif pyramid == 2:
        stages = [20, 40, 60, 80, 100]

    # case 3 => reflective pyramid
    # we achieve final target after 2 affirmation
    # but liquidate the position by 5 affirmations
    else:
        stages = [60, 90, 100, 60, 0]
    return stages


def generate_portfolio():

    stock_list = ['3M', 'AXP', 'AAPL', 'BA', 'CAT',
                  'CVX', 'CSCO', 'CCE', 'DIS', 'DFT',
                  'XOM', 'GE', 'GS', 'HD', 'IBM',
                  'INTC', 'JNJ', 'JPM', 'MCD', 'MRK',
                  'MSFT', 'NKE', 'PFE', 'PG', 'TRV',
                  'UTX', 'UNH', 'VZA', 'V', 'WMT']
    stock_list = ['MSFT', 'AAPL', 'WMT']
    # start_date = '19910101'
    start_date = '2014-01-01'
    end_date = '2016-01-01'

    # Fix Pandas Datareader's Issues with Yahoo Finance (Since yahoo abandoned it's API)
    yahoo_finance_bridge()
    prices_panel = pdr.get_data_yahoo(stock_list, start_date, end_date, as_panel=True, auto_adjust=False).fillna(0)
    position = pd.DataFrame(data=0, index=prices_panel.major_axis, columns=prices_panel.minor_axis)
    atr = pd.DataFrame(data=0, index=prices_panel.major_axis, columns=prices_panel.minor_axis)
    direction = pd.DataFrame(data=0, index=prices_panel.major_axis, columns=prices_panel.minor_axis)
    progress = pd.DataFrame(data=0, index=prices_panel.major_axis, columns=prices_panel.minor_axis)
    progress_percent = pd.DataFrame(data=0, index=prices_panel.major_axis, columns=prices_panel.minor_axis)
    target = pd.DataFrame(data=0, index=prices_panel.major_axis, columns=prices_panel.minor_axis)

    port = pd.Panel({'price': prices_panel['Adj Close'],
                     'pos': position,
                     'atr': atr,
                     'direction': direction,
                     'progress': progress,
                     'progress_percent': progress_percent,
                     'target': target,
                     })
    return [port, prices_panel]


def position_sizing(port, policy):
    # policy 1 => constant risk sizing, seems to be no cap on AUM
    if policy == 1:
        AUM = 1000000
        aum_risk_factor = 0.20
        account_risk = AUM * aum_risk_factor
        num_instruments = 10
        risk_per_instrument = account_risk / num_instruments
        port['target'] = risk_per_instrument / port['atr']
        port['pos'] = port['target'] * port['progress_percent']

    # policy 2 => constant risk sizing
    # with different weight to PNL
    elif policy == 2:
        AUM = 1000000
        aum_risk_factor = 0.20
        pnl_risk_factor = 0.50

        for ticker in port.minor_axis:
            prev_date = port.major_axis[0]
            cum_pnl = 0
            for date in port.major_axis:
                account_risk = AUM * aum_risk_factor + cum_pnl * pnl_risk_factor
                num_instruments = 10
                risk_per_instrument = account_risk / num_instruments
                port['target', date, ticker] = risk_per_instrument / port['atr', date, ticker]
                port['pos', date, ticker] = port['target', date, ticker] * port['progress_percent', date, ticker]
                cum_pnl += port['pos', date, ticker] * \
                           (port['price', date, ticker] - port['price', prev_date, ticker])

    # policy 3 => combination of constant risk and fixed weight
    else:
        AUM = 1000000
        aum_risk_factor = 0.20
        account_risk = AUM * aum_risk_factor
        num_instruments = 10
        risk_per_instrument = account_risk / num_instruments
        atr_target = risk_per_instrument / port['atr']
        price_target = risk_per_instrument / port['price']
        port['target'] = atr_target.where(price_target < atr_target, price_target).fillna(atr_target)
        port['pos'] = port['target'] * port['progress_percent']

    return port


def find_kpi(port_new):
    """ Find KPIs of the portfolio"""
    p = port_new['pos']
    for col in p.columns:
        print('Calculating for %s' % col)
        print(p[col].replace(0, np.nan).dropna(how='all').calc_stats().display())
        print('Max Drawdown: %s' % str(p[col].replace(0, np.nan).dropna(how='all').calc_max_drawdown()))


def main():
    """
    generate portfolio
    calculate trend lines
        21 and 45 day ema and calculate 0.5ATR for each ( 2 cases)
        determine sizes by % vol model, market money model, multiple tier model ( 3 cases)
        determinze size changes by upright/inverted/reflecting pyramid ( 3 cases)
        assume slippage / brokerage fee for trading
        60% insample to determine above cases, 20% out of sample for KPIs
    :return: nothing
    """
    [port, prices_panel] = generate_portfolio()
    pyramid_dict = {
        1: 'Upright Pyramid',
        2: 'Inverted Pyramid',
        3: 'Reflective Pyramid'
    }
    period_policy_dict = {
        1: 'EMA of 21',
        2: 'EMA of 45'
    }
    position_sizing_dict = {
        1: 'Constant Risk Sizing, No cap to AUM',
        2: 'Constant Risk Sizing, Different Weight to PNL',
        3: 'Combination of Constant Risk and Fixed Weight'
    }
    for pyramid_policy in range(1, 4):
        stages = generate_pyramid(pyramid_policy)
        for period_policy in range(1, 3):
            port_new = portfolio_calculations(port, prices_panel, period_policy, stages)
            for positions_policy in range(1, 4):
                port_new = position_sizing(port_new, positions_policy)
                print('\n')
                print("Pyramid type = %s, Period type = %s, Position sizing type = %s" %
                      (pyramid_dict[pyramid_policy], period_policy_dict[period_policy], position_sizing_dict[positions_policy]))
                find_kpi(port_new)


if __name__ == '__main__':
    main()
