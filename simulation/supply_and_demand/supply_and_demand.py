from typing import List

import pandas as pd
from exploration.plotting import CandlePlot
from technical.patterns import is_bullish_pattern, is_bearish_pattern
from technical.peaks import get_peak, PeakType
import plotly.graph_objects as go


class Trade:
    def __init__(self, tp, sl, entry_price, peaks, entry_idx, entry_time, exit_time=None, exit_idx=None):
        self.tp = tp
        self.sl = sl
        self.entry_price = entry_price
        self.peaks = peaks
        self.entry_idx = entry_idx
        self.entry_time = entry_time
        self.exit_idx = exit_idx
        self.exit_time = exit_time

    def __repr__(self):
        return str(vars(self))


def plot_trades(trades: List[Trade], df):
    cp = CandlePlot(df, candles=True)
    prices = []
    times = []
    indexes = []
    hover_text = []
    for t in trades:
        indexes.append(t.entry_idx)
        prices.extend([t.tp, t.sl])
        times.extend([cp.df_plot.iloc[t.entry_idx]['sTime'], cp.df_plot.iloc[t.entry_idx]['sTime']])
        hover_text.append(f'peak_1: {t.peaks[0].idx}\n peak_2: {t.peaks[1].idx}')

    cp.fig.add_trace(go.Scatter(
        x=times,
        y=prices,
        mode='markers',
        marker=dict(color='#FFFFFF', size=3)
    ))

    df_temp = cp.df_plot[cp.df_plot.index.isin(indexes)]
    cp.fig.add_trace(go.Candlestick(
        x=df_temp.sTime,
        open=df_temp.mid_o,
        high=df_temp.mid_h,
        low=df_temp.mid_l,
        close=df_temp.mid_c,
        hovertext=hover_text,
        line=dict(width=1), opacity=1,
        increasing_fillcolor='#0066FF',
        decreasing_fillcolor='#0066FF',
        increasing_line_color='#0066FF',
        decreasing_line_color='#0066FF'
    ))
    cp.show_plot(width=1100, height=500)


def apply_signal(row: pd.Series, df: pd.DataFrame, risk_to_reward=1.5):
    peaks = []
    window_start = max(0, row.name - 100)
    window_end = row.name + 1

    for i in range(window_start, window_end):
        peak = get_peak(df.iloc[:window_end], i)
        if peak:
            if any(p.type == peak.type and p.idx == peak.idx - 1 for p in peaks):
                continue
            peaks.append(peak)

    if len(peaks) >= 3:
        peak_one = peaks[-1]
        peak_two = peaks[-2]
        peak_three = peaks[-3]
        peak_four = peaks[-4] if len(peaks) >= 4 else None
        curr_close = row['mid_c']

        if peak_one.type == PeakType.UP and peak_two.type == PeakType.DOWN and is_bullish_pattern(row, df):
            peak_one_price = max(df.iloc[peak_one.idx]['mid_o'], df.iloc[peak_one.idx]['mid_c'])
            peak_two_price = min(df.iloc[peak_two.idx]['mid_o'], df.iloc[peak_two.idx]['mid_c'])

            if peak_two_price < curr_close < peak_one_price:
                if peak_three.type == PeakType.DOWN:
                    prev_up_peak = peak_three
                elif peak_four and peak_four.type == PeakType.DOWN:
                    prev_up_peak = peak_four
                else:
                    return None

                prev_up_peak_price = min(df.iloc[prev_up_peak.idx]['mid_o'], df.iloc[prev_up_peak.idx]['mid_c'])

                if peak_two_price > prev_up_peak_price:
                    tp_price = df.iloc[peak_one.high_low_idx]['mid_h']

                    if curr_close + curr_close * 0.00125 <= tp_price:
                        tp_distance = abs(curr_close - tp_price)
                        sl_distance = tp_distance / risk_to_reward
                        sl_price = max(curr_close - sl_distance, df.iloc[peak_two.high_low_idx]['mid_l'])
                        trade_peaks = [peak_one, peak_two, peak_three]
                        if peak_four: trade_peaks.append(peak_four)
                        return Trade(tp=tp_price, sl=sl_price, entry_price=curr_close, peaks=trade_peaks,
                                     entry_idx=row.name, entry_time=row.time)

        if peak_one.type == PeakType.DOWN and peak_two.type == PeakType.UP and is_bearish_pattern(row, df):
            peak_one_price = min(df.iloc[peak_one.idx]['mid_o'], df.iloc[peak_one.idx]['mid_c'])
            peak_two_price = max(df.iloc[peak_two.idx]['mid_o'], df.iloc[peak_two.idx]['mid_c'])

            if peak_one_price < curr_close < peak_two_price:
                if peak_three.type == PeakType.UP:
                    prev_up_peak = peak_three
                elif peak_four and peak_four.type == PeakType.UP:
                    prev_up_peak = peak_four
                else:
                    return None

                prev_up_peak_price = max(df.iloc[prev_up_peak.idx]['mid_o'], df.iloc[prev_up_peak.idx]['mid_c'])

                if peak_two_price < prev_up_peak_price:
                    tp_price = df.iloc[peak_one.high_low_idx]['mid_l']
                    if curr_close - curr_close * 0.00125 >= tp_price:
                        tp_distance = abs(curr_close - tp_price)
                        sl_distance = tp_distance / risk_to_reward
                        sl_price = min(curr_close + sl_distance, df.iloc[peak_two.high_low_idx]['mid_h'])
                        trade_peaks = [peak_one, peak_two, peak_three]
                        if peak_four: trade_peaks.append(peak_four)
                        return Trade(tp=tp_price, sl=sl_price, entry_price=curr_close, peaks=trade_peaks,
                                     entry_idx=row.name, entry_time=row.time)

