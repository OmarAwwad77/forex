from dataclasses import dataclass
from enum import Enum
from typing import List

import pandas as pd
import plotly.graph_objects as go

from exploration.plotting import CandlePlot

PeakType = Enum('PeakType', ['NOPEAK', 'UP', 'DOWN'])


@dataclass
class Peak:
    type: PeakType
    idx: int


def get_peak(df: pd.DataFrame, idx: int, width=10, trend_len=3, perc=0.0008, debug=False) -> Peak:
    def find_price_in_range(start, end, reverse, cond):
        loop_range = range(end, start - 1, -1) if reverse else range(start, end + 1)
        for i in loop_range:
            curr_close = df.iloc[i]['mid_c']
            if cond(curr_close):
                return curr_close, i
        return None, None

    df = df.filter(['mid_c', 'mid_o'])
    last_idx = len(df) - 1
    start_idx = max(idx - width, 0)
    end_idx = min(idx + width, last_idx)

    if start_idx > idx - trend_len or end_idx < idx + trend_len:
        return Peak(type=PeakType.NOPEAK, idx=idx)

    lowest_prev_price, lowest_prev_idx = find_price_in_range(start_idx, idx - trend_len, True,
                                                             lambda price: df.iloc[idx].max() >= price + (price * perc))
    lowest_next_price, lowest_next_idx = find_price_in_range(idx + trend_len, end_idx, False,
                                                             lambda price: df.iloc[idx].max() >= price + (price * perc))

    if lowest_prev_price and lowest_next_price:
        highest = max(df.iloc[lowest_prev_idx + 1: lowest_next_idx].max())
        if highest == df.iloc[idx].max():
            return Peak(type=PeakType.UP, idx=idx)

    heighest_prev_price, heighest_prev_idx = find_price_in_range(start_idx, idx - trend_len, True,
                                                                 lambda price: df.iloc[idx].min() <= price - (
                                                                             price * perc))
    heighest_next_price, heighest_next_idx = find_price_in_range(idx + trend_len, end_idx, False,
                                                                 lambda price: df.iloc[idx].min() <= price - (
                                                                             price * perc))

    if heighest_prev_price and heighest_next_price:
        lowest = min(df.iloc[heighest_prev_idx + 1: heighest_next_idx].min())
        if lowest == df.iloc[idx].min():
            return Peak(type=PeakType.DOWN, idx=idx)

    return Peak(type=PeakType.NOPEAK, idx=idx)


def plot_peaks(df: pd.DataFrame, peak_list: List[Peak]):
    cp = CandlePlot(df, candles=True)
    y = [cp.df_plot.iloc[p.idx]['mid_h'] if p.type == PeakType.UP else cp.df_plot.iloc[p.idx]['mid_l'] for p in peak_list]
    x = [cp.df_plot.iloc[p.idx]['sTime'] for p in peak_list]
    cp.fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=dict(color='#FFFFFF', size=3)
    ))
    cp.show_plot(width=1100, height=500)
