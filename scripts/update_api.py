import os
import sys
import numpy as np
import pandas as pd
sys.path.append('hyperdrive')
from DataSource import MarketData  # noqa autopep8
from History import Historian  # noqa autopep8
import Constants as C  # noqa autopep8
from Exchange import Kraken  # noqa autopep8


def transform_stats(stats, metrics):
    return {
        k: (
            None if pd.isna(v) else round(v, 2)
        ) for k, v in dict(stats[metrics]).items()
    }


md = MarketData()
md.provider = 'polygon'
hist = Historian()
kr = Kraken(test=True)
symbol = os.environ['SYMBOL']
signals_path = md.finder.get_signals_path()
signals = md.reader.load_csv(signals_path)
signals[C.TIME] = pd.to_datetime(signals[C.TIME])
df = md.get_ohlc(symbol).merge(signals, on=C.TIME)

# 1 week delay
df = df.head(len(df) - 5)


def create_portfolio_preview(close, signals, invert):
    metrics = [
        'Total Return [%]',
        'Max Drawdown [%]',
        'Win Rate [%]',
        'Profit Factor',
    ]
    if invert:
        close = 1 / close
        init_cash = 1 + C.ABS_TOL
        metrics.append('Total Fees Paid')
    else:
        init_cash = close.iloc[0]
        metrics.append('Sharpe Ratio')
        metrics.append('Sortino Ratio')

    holding_signals = np.full(len(signals), not invert)

    holding_pf = hist.create_portfolio(close, holding_signals, init_cash)
    if C.PREF_EXCHANGE == C.BINANCE:
        fee = C.BINANCE_FEE
    else:
        base = C.KRAKEN_SYMBOLS['BTC']
        quote = C.KRAKEN_SYMBOLS['USD']
        pair = kr.create_pair(base, quote)
        pair_info = kr.get_asset_pair(pair)
        fee = pair_info['fees'][0][1] / 100
    hyper_pf = hist.create_portfolio(
        close, ~signals if invert else signals, init_cash, fee)

    holding_values = holding_pf.value()
    hyper_values = hyper_pf.value()
    holding_balances = [round(bal, 2) for bal in list(holding_values)]
    hyper_balances = [round(bal, 2) for bal in list(hyper_values)]

    holding_stats = transform_stats(holding_pf.stats(), metrics)
    hyper_stats = transform_stats(hyper_pf.stats(), metrics)

    if invert:
        holding_stats['Max Drawdown [%]'] = 0.0
        profitable_time = sum(
            (hyper_values - holding_values) > 0) / len(hyper_values)
        new_metric = 'Profitable Time [%]'
        hyper_stats[new_metric] = round(profitable_time * 100, 2)
        holding_stats[new_metric] = round(100 -
                                          hyper_stats[new_metric], 2)
        metrics.append(new_metric)

    dates = list(df[C.TIME].dt.strftime('%m/%d/%Y'))
    signals = hist.unfill(list(df[C.SIG]))
    records = []

    for idx, date in enumerate(dates):
        records.append({
            'Name': 'HODL',
            C.TIME: date,
            C.BAL: holding_balances[idx],
        })

        records.append({
            'Name': 'hyperdrive',
            C.TIME: date,
            C.BAL: hyper_balances[idx],
            C.SIG: signals[idx]
        })

    stats = []
    for idx, metric in enumerate(metrics):

        stats.append({
            'key': idx,
            'metric': metric,
            'HODL': holding_stats[metric],
            'hyperdrive': hyper_stats[metric]
        })

    preview = {
        'data': records,
        'stats': stats
    }
    return preview


usd_preview = create_portfolio_preview(df[C.CLOSE], df[C.SIG], False)
btc_preview = create_portfolio_preview(df[C.CLOSE], df[C.SIG], True)

preview = {
    'BTC': btc_preview,
    'USD': usd_preview
}

preview_path = md.finder.get_api_path('preview')
md.writer.save_json(preview_path, preview)
