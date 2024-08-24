import pandas as pd


class Trade:
    OPEN = 0
    CLOSED = 1
    BUY = 2
    SELL = 3
    WIN = 4
    LOSS = 5

    def __init__(self, tp, sl, entry_price, entry_idx, entry_time, data,
                 signal, exit_price=None, exit_time=None, exit_idx=None,
                 status=OPEN, outcome=None, duration=None):
        self.tp = tp
        self.sl = sl
        self.entry_idx = entry_idx
        self.entry_price = entry_price
        self.exit_idx = exit_idx
        self.exit_price = exit_price
        self.status = status
        self.outcome = outcome
        self.signal = signal
        self.data = data
        self.duration = duration
        self.entry_time = entry_time
        self.exit_time = exit_time

    def _close(self, idx: int, row: pd.Series, outcome: int, exit_price: float):
        self.outcome = outcome
        self.status = Trade.CLOSED
        self.exit_price = exit_price
        self.exit_idx = idx
        self.exit_time = row['time']
        self.duration = (self.exit_time - row['time']) / 60 / 60  # hours

    def update(self, idx: int, row: pd.Series):
        if self.signal == Trade.BUY:
            if row['bid_c'] <= self.sl:
                self._close(idx, row, Trade.LOSS, row['bid_c'])
            elif row['bid_c'] >= self.tp:
                self._close(idx, row, Trade.WIN, row['bid_c'])
        else:  # SELL
            if row['ask_c'] >= self.sl:
                self._close(idx, row, Trade.LOSS, row['ask_c'])
            elif row['ask_c'] <= self.tp:
                self._close(idx, row, Trade.WIN, row['ask_c'])

    def __repr__(self):
        return str(vars(self))