import pandas as pd
import datetime as dt
from technical.indicators import rsi
from technical.udemy_patterns import apply_patterns
from simulation.guru_1.common import BUY, SELL, NONE, apply_signal, apply_signals

def create_signals(df, time_d=1):
    df_signals = df[df.SIGNAL != NONE].copy()
    df_signals['m5_start'] = [x + dt.timedelta(hours=time_d) for x in df_signals.time]
    df_signals.drop(['time', 'mid_o', 'mid_h', 'mid_l', 'bid_o', 'bid_h', 'bid_l',
                     'ask_o', 'ask_h', 'ask_l', 'direction'], axis=1, inplace=True)
    df_signals.rename(columns={
        'bid_c': 'start_price_BUY',  # for tracking the trade
        'ask_c': 'start_price_SELL',
        'm5_start': 'time'
    }, inplace=True)
    return df_signals

class Trade:
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

    def update(self, row):
        if self.SIGNAL == BUY:
            if row.bid_h >= self.TP:
                self.close_trade(row, self.profit_factor, row.bid_h)
            elif row.bid_l <= self.SL:
                self.close_trade(row, self.loss_factor, row.bid_l)
        if self.SIGNAL == SELL:
            if row.ask_l <= self.TP:
                self.close_trade(row, self.profit_factor, row.ask_l)
            elif row.ask_h >= self.SL:
                self.close_trade(row, self.loss_factor, row.ask_h)

class GuruTester:
    def __init__(self, df_big,
                 apply_signal,
                 df_m5,
                 LOSS_FACTOR=-1.0,
                 PROFIT_FACTOR=1.5,
                 time_d=1):
        self.df_big = df_big.copy()
        self.apply_signal = apply_signal
        self.df_m5 = df_m5.copy()
        self.LOSS_FACTOR = LOSS_FACTOR
        self.PROFIT_FACTOR = PROFIT_FACTOR
        self.time_d = time_d

        self.prepare_data()

    def prepare_data(self):

        print("prepare_data...")

        apply_signals(self.df_big,
                      self.PROFIT_FACTOR,
                      self.apply_signal)

        df_m5_slim = self.df_m5[['time', 'bid_h', 'bid_l', 'ask_h', 'ask_l']].copy()
        df_signals = create_signals(self.df_big, time_d=self.time_d)
        print(f'Number of trades: {df_signals.shape[0]}')
        self.merged = pd.merge(left=df_m5_slim, right=df_signals, on='time', how='left')
        self.merged.fillna(0, inplace=True)
        self.merged.SIGNAL = self.merged.SIGNAL.astype(int)


    def run_test(self):
        print("run_test...")
        open_trades_m5 = []
        closed_trades_m5 = []

        for index, row in self.merged.iterrows():

            if row.SIGNAL != NONE:
                open_trades_m5.append(Trade(row, self.PROFIT_FACTOR, self.LOSS_FACTOR))

            for ot in open_trades_m5:
                ot.update(row)
                if ot.running == False:
                    closed_trades_m5.append(ot)
            open_trades_m5 = [x for x in open_trades_m5 if x.running == True]

        self.df_results = pd.DataFrame.from_dict([vars(x) for x in closed_trades_m5])
        print("Result:", self.df_results.result.sum())


def run_pair(pair):
    df_an = pd.read_pickle(f"data/candles/{pair}_H1.pkl")
    df_m5 = pd.read_pickle(f"data/candles/{pair}_M5.pkl")
    df_an.reset_index(drop=True, inplace=True)
    df_m5.reset_index(drop=True, inplace=True)
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
        apply_signal,
        df_m5,
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
