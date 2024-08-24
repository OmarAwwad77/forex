from enum import Enum
from typing import List, Optional

import pandas as pd
from exploration.plotting import CandlePlot
from technical.patterns import is_bullish_pattern, is_bearish_pattern
from technical.peaks import get_peak, PeakType
import plotly.graph_objects as go


# class Trade:
#     OPEN = 0
#     CLOSED = 1
#     BUY = 2
#     SELL = 3
#     WIN = 4
#     LOSS = 5
#
#     def __init__(self, tp, sl, entry_price, entry_idx, entry_time, data,
#                  signal, exit_price=None, exit_time=None, exit_idx=None,
#                  status=OPEN, outcome=None, duration=None):
#         self.tp = tp
#         self.sl = sl
#         self.entry_idx = entry_idx
#         self.entry_price = entry_price
#         self.exit_idx = exit_idx
#         self.exit_price = exit_price
#         self.status = status
#         self.outcome = outcome
#         self.signal = signal
#         self.data = data
#         self.duration = duration
#         self.entry_time = entry_time
#         self.exit_time = exit_time
#
#     def _close(self, idx: int, row: pd.Series, outcome: int, exit_price: float):
#         self.outcome = outcome
#         self.status = Trade.CLOSED
#         self.exit_price = exit_price
#         self.exit_idx = idx
#         self.exit_time = row['time']
#         self.duration = (self.exit_time - row['time']) / 60 / 60  # hours
#
#     def update(self, idx: int, row: pd.Series):
#         if self.signal == Trade.BUY:
#             if row['bid_c'] <= self.sl:
#                 self._close(idx, row, Trade.LOSS, row['bid_c'])
#             elif row['bid_c'] >= self.tp:
#                 self._close(idx, row, Trade.WIN, row['bid_c'])
#         else: # SELL
#             if row['ask_c'] >= self.sl:
#                 self._close(idx, row, Trade.LOSS, row['ask_c'])
#             elif row['ask_c'] <= self.tp:
#                 self._close(idx, row, Trade.WIN, row['ask_c'])
#
#
#
#     def __repr__(self):
#         return str(vars(self))
#
#
# def plot_trades(trades: List[Trade], df):
#     cp = CandlePlot(df, candles=True)
#     prices = []
#     times = []
#     indexes = []
#     hover_text = []
#     for t in trades:
#         indexes.append(t.entry_idx)
#         prices.extend([t.tp, t.sl])
#         times.extend([cp.df_plot.iloc[t.entry_idx]['sTime'], cp.df_plot.iloc[t.entry_idx]['sTime']])
#         hover_text.append(f'peak_1: {t.data["peaks"][0].idx}\n peak_2: {t.data["peaks"][1].idx}')
#
#     cp.fig.add_trace(go.Scatter(
#         x=times,
#         y=prices,
#         mode='markers',
#         marker=dict(color='#FFFFFF', size=3)
#     ))
#
#     df_temp = cp.df_plot[cp.df_plot.index.isin(indexes)]
#     cp.fig.add_trace(go.Candlestick(
#         x=df_temp.sTime,
#         open=df_temp.mid_o,
#         high=df_temp.mid_h,
#         low=df_temp.mid_l,
#         close=df_temp.mid_c,
#         hovertext=hover_text,
#         line=dict(width=1), opacity=1,
#         increasing_fillcolor='#0066FF',
#         decreasing_fillcolor='#0066FF',
#         increasing_line_color='#0066FF',
#         decreasing_line_color='#0066FF'
#     ))
#     cp.show_plot(width=1100, height=500)
#
#
# def apply_signal(row: pd.Series, df: pd.DataFrame, risk_to_reward=1.5) -> Optional[Trade]:
#     peaks = []
#     row_idx = df.index.get_loc(row.name)
#     window_start = max(0, row_idx - 100)
#
#     for i in range(row_idx, window_start - 1, -1):
#         if len(peaks) >= 4:
#             break
#         peak = get_peak(df.iloc[:row_idx + 1], i)
#         if peak:
#             if any(p.type == peak.type and p.idx == peak.idx + 1 for p in peaks):
#                 continue
#             peaks.append(peak)
#
#     if len(peaks) >= 4:
#         peak_one = peaks[0]
#         peak_two = peaks[1]
#         peak_three = peaks[2]
#         peak_four = peaks[3]
#         curr_close = row['mid_c']
#         max_between_peak_one_and_row = max(df.iloc[peak_one.idx + 1: row_idx + 1][['mid_c', 'mid_o']].max())
#         min_between_peak_one_and_row = min(df.iloc[peak_one.idx + 1: row_idx + 1][['mid_c', 'mid_o']].min())
#
#         if (
#             peak_one.type == PeakType.UP and
#             peak_two.type == PeakType.DOWN and
#             peak_three.type == PeakType.UP and
#             peak_four.type == PeakType.DOWN and
#             is_bullish_pattern(row, df)
#         ):
#             peak_one_price = max(df.iloc[peak_one.idx]['mid_o'], df.iloc[peak_one.idx]['mid_c'])
#             peak_two_price = min(df.iloc[peak_two.idx]['mid_o'], df.iloc[peak_two.idx]['mid_c'])
#             peak_three_price = max(df.iloc[peak_three.idx]['mid_o'], df.iloc[peak_three.idx]['mid_c'])
#             peak_four_price = min(df.iloc[peak_four.idx]['mid_o'], df.iloc[peak_four.idx]['mid_c'])
#
#             if (
#                 peak_one_price >= peak_three_price and
#                 peak_two_price >= peak_four_price and
#                 peak_two_price <= min_between_peak_one_and_row and
#                 peak_one_price >= max_between_peak_one_and_row
#             ):
#                 tp_price = df.iloc[peak_one.high_low_idx]['mid_h']
#
#                 if curr_close + curr_close * 0.00125 <= tp_price:
#                     tp_distance = abs(curr_close - tp_price)
#                     sl_distance = tp_distance / risk_to_reward
#                     sl_price = max(curr_close - sl_distance, df.iloc[peak_two.high_low_idx]['mid_l'])
#                     trade_peaks = [peak_one, peak_two, peak_three, peak_four]
#                     return Trade(tp=tp_price, sl=sl_price, entry_price=row['ask_c'], data={'peaks': trade_peaks},
#                                  entry_idx=row_idx, entry_time=row.time, signal=Trade.BUY)
#
#         if (
#             peak_one.type == PeakType.DOWN and
#             peak_two.type == PeakType.UP and
#             peak_three.type == PeakType.DOWN and
#             peak_four.type == PeakType.UP and
#             is_bearish_pattern(row, df)
#         ):
#             peak_one_price = min(df.iloc[peak_one.idx]['mid_o'], df.iloc[peak_one.idx]['mid_c'])
#             peak_two_price = max(df.iloc[peak_two.idx]['mid_o'], df.iloc[peak_two.idx]['mid_c'])
#             peak_three_price = min(df.iloc[peak_three.idx]['mid_o'], df.iloc[peak_three.idx]['mid_c'])
#             peak_four_price = max(df.iloc[peak_four.idx]['mid_o'], df.iloc[peak_four.idx]['mid_c'])
#
#             if (
#                 peak_one_price <= peak_three_price and
#                 peak_two_price <= peak_four_price and
#                 peak_one_price <= min_between_peak_one_and_row and
#                 peak_two_price >= max_between_peak_one_and_row
#             ):
#                 tp_price = df.iloc[peak_one.high_low_idx]['mid_l']
#                 if curr_close - curr_close * 0.00125 >= tp_price:
#                     tp_distance = abs(curr_close - tp_price)
#                     sl_distance = tp_distance / risk_to_reward
#                     sl_price = min(curr_close + sl_distance, df.iloc[peak_two.high_low_idx]['mid_h'])
#                     trade_peaks = [peak_one, peak_two, peak_three, peak_four]
#                     return Trade(tp=tp_price, sl=sl_price, entry_price=row['bid_c'], data={'peaks': trade_peaks},
#                                  entry_idx=row_idx, entry_time=row.time, signal=Trade.SELL)
#
