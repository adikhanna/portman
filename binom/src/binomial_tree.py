import arch
import json
import imgkit
import warnings
import argparse

warnings.simplefilter(action="ignore",
                      category=FutureWarning)

import numpy as np
import pandas as pd
import yfinance as yf
import pandas_datareader.data as pdr

from datetime import datetime, timedelta

yf.pdr_override()


class StockVol:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.end = datetime.now()
        self.start = self.end - timedelta(days=365)
        self.stock_data = pd.DataFrame(pdr.get_data_yahoo(self.ticker,
                                                          start=self.start.strftime("%Y-%m-%d"),
                                                          end=self.end.strftime("%Y-%m-%d"))
                                                          ["Adj Close"], columns=["Adj Close"])
        self.stock_data["log"] = np.log(self.stock_data)\
                                - np.log(self.stock_data.shift(1))

    def get_garch_sigma(self) -> float:
        model = arch.arch_model(self.stock_data["log"].dropna(),
                                  mean="Zero",
                                  vol="GARCH",
                                  p=1,
                                  q=1).fit()
        forecast = model.forecast(horizon=1)
        return float(np.sqrt(forecast.variance.iloc[-1]))

    def get_mean_sigma(self) -> float:
        return self.stock_data["log"].dropna().ewm(span=252).std().iloc[-1]


class BinomialTree:
    def __init__(self, config: dict):
        self.time_period = config["time_period_in_years"]
        self.steps = config["number_of_binomial_steps"]
        self.risk_free_rate = config["risk_free_rate"]
        self.init_stock_price = config["initial_stock_price"]
        self.auto_vol = config["auto_volatility"]
        self.input_vol = config["volatility_estimate"]
        self.ticker = config["ticker"]
        self.decis = config["round_up_decimals"]
        self.vol = self._get_vol()

    @staticmethod
    def _get_coefficient(n: int, k: int) -> int:
        coefficient = 1
        k = n-k if k > n-k else k
        for i in range(0, k):
            coefficient = coefficient*(n-i)
            coefficient = coefficient//(i+1)
        return coefficient

    def _get_vol(self) -> float:
        if self.auto_vol:
            return StockVol(self.ticker).get_mean_sigma()*np.sqrt(12)
        else:
            return self.input_vol

    def export(self) -> None:
        print(f"Using volatility of: {self.vol}")
        at = self.time_period/self.steps
        up = np.exp(self.vol*np.sqrt(at))
        down = 1./up
        rn_prob = (np.exp(self.risk_free_rate*at)-down)/(up-down)

        stock_tree = np.zeros((self.steps + 1,
                               self.steps + 1),
                               dtype=tuple)
        stock_tree[0, 0] = (self.init_stock_price, 1)

        for i in range(1, self.steps + 1):
            implicit_prob = round(self._get_coefficient(i, 0) * (rn_prob ** i) * 100, self.decis)
            stock_tree[i, 0] = (round(stock_tree[i - 1, 0][0] * up, self.decis), implicit_prob)
            for j in range(1, i + 1):
                implicit_prob = round(self._get_coefficient(i, j) * (rn_prob ** (i - j)) * ((1 - rn_prob) ** j) * 100,
                                      self.decis)
                stock_tree[i, j] = (round(stock_tree[i - 1, j - 1][0] * down, self.decis), implicit_prob)

        styled_table = pd.DataFrame(stock_tree).style.background_gradient().render()
        imgkit.from_string(styled_table, f"{self.ticker}_stock_tree_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.png")


def parse_args() -> str:
    parser = argparse.ArgumentParser(description="binomial_stock_stree")
    parser.add_argument("-config",
                        type=str,
                        required=True,
                        help="Config file")
    args = parser.parse_args()
    return args.config


def main():
    config = parse_args()

    with open(config) as conf:
        params = json.load(conf)

    binom_tree = BinomialTree(params)
    binom_tree.export()


if __name__ == "__main__":
    main()
