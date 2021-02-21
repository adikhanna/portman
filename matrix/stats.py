import statistics
import pandas as pd

from yahooquery import Ticker


def get_history(symbol: str, interval: str, period: str) -> pd.DataFrame:
    ticker = Ticker(symbol, adj_ohlc=True)
    row = ticker.history(interval=interval, period=period)
    return row

def compute_returns(history: pd.DataFrame) -> list:
    returns = []
    adj_close = history['adjclose']
    oldest_close = adj_close.pop(0)
    for _, curr_close in adj_close.items():
        returns.append((curr_close - oldest_close)/oldest_close)
    return returns

def compute_stats(ticker: str, returns: list) -> dict:
    if returns:
        return {ticker: {
            'mean': statistics.mean(returns),
            'median': statistics.median(returns),
            'stdev': statistics.stdev(returns),
            'var': statistics.variance(returns)
        }}
    return None

def compute_returns_stats(ticker: str, interval: str, period: str) -> dict:
    ticks = get_history(ticker, interval, period).reset_index()
    df = ticks[['date', 'adjclose']]
    return compute_stats(ticker, compute_returns(df.to_dict()))

if __name__ == "__main__":
    print(compute_returns_stats('aapl', '1d', '7d'))