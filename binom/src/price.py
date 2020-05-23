import arch
import numpy as np
import pandas as pd
import yfinance as yf
from tabulate import tabulate
import pandas_datareader.data as pdr

yf.pdr_override()


class stock_vol:
    def __init__(self, tk, start, end):
          self.tk = tk
          self.start = start
          self.end = end
          all_data = pdr.get_data_yahoo(self.tk, start=self.start, end=self.end)
          self.stock_data = pd.DataFrame(all_data['Adj Close'], columns=["Adj Close"])
          self.stock_data["log"] = np.log(self.stock_data)-np.log(self.stock_data.shift(1))

    def garch_sigma(self):
          model = arch.arch_model(self.stock_data["log"].dropna(), mean='Zero', vol='GARCH', p=1, q=1)
          model_fit = model.fit()
          forecast = model_fit.forecast(horizon=1)
          var = forecast.variance.iloc[-1]
          sigma = float(np.sqrt(var))
          return sigma


def binomialCoeff(n, k):
    res = 1
    if (k > n - k):
        k = n - k
    for i in range(0, k):
        res = res * (n - i)
        res = res // (i + 1)
    return res


def binomial(n, S, r, v, t):
    At = t / n
    u = np.exp(v * np.sqrt(At))
    d = 1. / u
    p = (np.exp(r * At) - d) / (u - d)
    stockvalue = np.zeros((n + 1, n + 1), dtype=tuple)
    stockvalue[0, 0] = (S, 1)

    for i in range(1, n + 1):
        prob = binomialCoeff(i, 0) * (p ** i)
        stockvalue[i, 0] = (stockvalue[i - 1, 0][0] * u, prob)
        for j in range(1, i + 1):
            prob = binomialCoeff(i, j) * (p ** (i - j)) * ((1 - p) ** j)
            stockvalue[i, j] = (stockvalue[i - 1, j - 1][0] * d, prob)

    print(tabulate(pd.DataFrame(stockvalue), headers='keys'))
    return stockvalue


sv = stock_vol("AAPL", "2019-05-23",  "2020-05-23")

n = 3
S = 318
r = 0.12
v = sv.garch_sigma()
t = 1.

binomial(n, S, r, v, t)