from enum import Enum
from typing import Union, Dict, Optional

import pandas as pd
import datetime as dt

from pandas import Timestamp, Timedelta


class TradeStatus(Enum):
    OPEN = 0
    CLOSED = 1

class TradeOutcome(Enum):
    LOSS = 0
    WIN = 1

class SignalType(Enum):
    BUY = 0
    SELL = 1

class Trade:

    def __init__(self, tp: float, sl: float, entry_price: float, entry_idx: int, entry_time: Timestamp, data: Dict,
                 signal: SignalType, exit_price: Optional[float]=None, exit_time: Optional[Timestamp]=None, exit_idx: Optional[int]=None,
                 status: TradeStatus=TradeStatus.OPEN, outcome: Optional[TradeOutcome]=None, duration: Optional[Timedelta]=None):
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

    def _close(self, idx: int, row: pd.Series, outcome: TradeOutcome, exit_price: float):
        self.outcome = outcome
        self.status = TradeStatus.CLOSED
        self.exit_price = exit_price
        self.exit_idx = idx
        self.exit_time = row['time']
        self.duration = (self.exit_time - row['time']) / 60 / 60  # hours

    def _break_down_candle(self, big_candle_idx: int, big_candle: pd.Series, tp: float, sl: float, df_smaller: pd.DataFrame, delta_in_mins: int, signal: SignalType):
        print(f"""
        **************
        Breaking row: {big_candle_idx}
        bid_h: {big_candle["bid_h"]}
        bid_l: {big_candle["bid_l"]}
        ask_h: {big_candle["ask_h"]}
        ask_l: {big_candle["ask_l"]}
        take profit: {tp}
        stop_loss: {sl}
        **************
        """)
        start_date = big_candle.time
        end_date = start_date + dt.timedelta(minutes=delta_in_mins)
        df = df_smaller[(df_smaller.time >= start_date) & (df_smaller.time <= end_date)]

        for idx in range(len(df)):
            row = df.iloc[idx]
            if signal == SignalType.BUY:
                if row.bid_h >= tp:
                    self._close(big_candle_idx, big_candle, TradeOutcome.WIN, big_candle['bid_h'])
                elif row.bid_l <= sl:
                    self._close(big_candle_idx, big_candle, TradeOutcome.LOSS, big_candle['bid_l'])
            else:
                if row.ask_l <= tp:
                    self._close(big_candle_idx, big_candle, TradeOutcome.WIN, big_candle['ask_l'])
                elif row.ask_h >= sl:
                    self._close(big_candle_idx, big_candle, TradeOutcome.LOSS, big_candle['ask_h'])

    def update(self, idx: int, row: pd.Series, df_smaller: pd.DataFrame, delta_in_mins: int):
        if self.signal == SignalType.BUY:
            if row['bid_l'] <= self.sl and row['bid_h'] >= self.tp:
                self._break_down_candle(
                    big_candle_idx=idx,
                    big_candle=row,
                    tp=self.tp,
                    sl=self.sl,
                    df_smaller=df_smaller,
                    delta_in_mins=delta_in_mins,
                    signal=SignalType.BUY
                )
                return
            if row['bid_l'] <= self.sl:
                self._close(idx, row, TradeOutcome.LOSS, row['bid_l'])
            elif row['bid_h'] >= self.tp:
                self._close(idx, row, TradeOutcome.WIN, row['bid_h'])

        else:  # SELL
            if row['ask_h'] >= self.sl and row['ask_l'] <= self.tp:
                self._break_down_candle(
                    big_candle_idx=idx,
                    big_candle=row,
                    tp=self.tp,
                    sl=self.sl,
                    df_smaller=df_smaller,
                    delta_in_mins=delta_in_mins,
                    signal=SignalType.SELL
                )
                return
            if row['ask_h'] >= self.sl:
                self._close(idx, row, TradeOutcome.LOSS, row['ask_h'])
            elif row['ask_l'] <= self.tp:
                self._close(idx, row, TradeOutcome.WIN, row['ask_l'])


    def __repr__(self):
        return str(vars(self))

