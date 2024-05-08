import pandas as pd
import datetime as dt
from technical.indicators import rsi
from technical.udemy_patterns import apply_patterns
from simulation.guru_1.common import BUY, SELL, NONE, apply_signal, apply_signals

class Trade:
    DF_M5 = pd.read_pickle(f"data/candles/EUR_USD_M5.pkl")
    def __init__(self, row, profit_factor, loss_factor):
        self.running = True
        self.start_index_m5 = row.name
        self.profit_factor = profit_factor
        self.loss_factor = loss_factor

        if row.SIGNAL == BUY:
            self.start_price = row.start_price_BUY
            self.trigger_price = row.start_price_BUY

        if row.SIGNAL == SELL:
            self.start_price = row.start_price_SELL
            self.trigger_price = row.start_price_SELL

        self.SIGNAL = row.SIGNAL
        self.TP = row.TP
        self.SL = row.SL
        self.result = 0.0
        self.end_time = row.time
        self.start_time = row.time

    def close_trade(self, row, result, trigger_price):
        self.running = False
        self.result = result
        self.end_time = row.time
        self.trigger_price = trigger_price

    def break_down_candle(self, row, buy=True):
        start_date = row.time
        end_date = start_date + dt.timedelta(minutes=55)
        df = Trade.DF_M5[(Trade.DF_M5.time >= start_date) & (Trade.DF_M5.time <= end_date)]
        for index, row in df.iterrows():
            if buy:
                if row.bid_h >= self.TP:
                    return 1, row.bid_h
                elif row.bid_l <= self.SL:
                    return 0, row.bid_l
            else:
                if row.ask_l <= self.TP:
                    return 1, row.ask_l
                elif row.ask_h >= self.SL:
                    return 0, row.ask_h

    def update(self, row):
        if self.SIGNAL == BUY:
            if row.bid_h >= self.TP and row.bid_l <= self.SL:
                res, trigger_price = self.break_down_candle(row)
                if res:
                    self.close_trade(row, self.profit_factor, trigger_price)
                else:
                    self.close_trade(row, self.loss_factor, trigger_price)
            elif row.bid_h >= self.TP:
                self.close_trade(row, self.profit_factor, row.bid_h)
            elif row.bid_l <= self.SL:
                self.close_trade(row, self.loss_factor, row.bid_l)
        if self.SIGNAL == SELL:
            if row.ask_l <= self.TP and row.ask_h >= self.SL:
                res, trigger_price = self.break_down_candle(row, buy=False)
                if res:
                    self.close_trade(row, self.profit_factor, trigger_price)
                else:
                    self.close_trade(row, self.loss_factor, trigger_price)
            elif row.ask_l <= self.TP:
                self.close_trade(row, self.profit_factor, row.ask_l)
            elif row.ask_h >= self.SL:
                self.close_trade(row, self.loss_factor, row.ask_h)


class GuruTester:
    def __init__(self, df_big,
                 apply_signal,
                 LOSS_FACTOR=-1.0,
                 PROFIT_FACTOR=1.5):
        self.df_big = df_big.copy()
        self.apply_signal = apply_signal
        self.LOSS_FACTOR = LOSS_FACTOR
        self.PROFIT_FACTOR = PROFIT_FACTOR

        self.prepare_data()

    def prepare_data(self):

        print("prepare_data...")

        apply_signals(self.df_big,
                      self.PROFIT_FACTOR,
                      self.apply_signal)

        self.df_big.rename(columns={
            'bid_c': 'start_price_BUY',  # for tracking the trade
            'ask_c': 'start_price_SELL',
            'm5_start': 'time'
        }, inplace=True)
        print(f'Number of trades: {self.df_big[self.df_big.SIGNAL != NONE].shape[0]}')

    def run_test(self):
        print("run_test...")
        open_trades_m5 = []
        closed_trades_m5 = []

        for index, row in self.df_big.iterrows():
            for ot in open_trades_m5:
                ot.update(row)
                if ot.running == False:
                    closed_trades_m5.append(ot)
            open_trades_m5 = [x for x in open_trades_m5 if x.running == True]
            if row.SIGNAL != NONE:
                open_trades_m5.append(Trade(row, self.PROFIT_FACTOR, self.LOSS_FACTOR))

        self.df_results = pd.DataFrame.from_dict([vars(x) for x in closed_trades_m5])
        print("Result:", self.df_results.result.sum())


def run_pair(pair):
    df_an = pd.read_pickle(f"data/candles/{pair}_H1.pkl")
    df_an.reset_index(drop=True, inplace=True)
    df_an = rsi(df_an)
    df_an = apply_patterns(df_an)
    df_an['EMA_200'] = df_an.mid_c.ewm(span=200, min_periods=200).mean()
    our_cols = ['time', 'mid_o', 'mid_h', 'mid_l', 'mid_c',
                'bid_o', 'bid_h', 'bid_l', 'bid_c',
                'ask_o', 'ask_h', 'ask_l', 'ask_c',
                'ENGULFING', 'direction', 'EMA_200', 'RSI_14']
    df_slim = df_an[our_cols].copy()
    df_slim.dropna(inplace=True)

    df_slim.reset_index(drop=True, inplace=True)
    gt = GuruTester(
        df_slim,
        apply_signal
    )

    gt.run_test()
    return gt.df_results


def run():
    pairs = ["EUR_USD", "GBP_JPY"]
    pairs.remove('GBP_JPY')
    res = []
    for p in pairs:
        res.append(dict(pair=p, res=run_pair(p)))
    closed_trades_df = res[0]['res']
    print(f'Number of trades taken: {closed_trades_df.shape[0]}')