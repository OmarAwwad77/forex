from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import pandas as pd
import plotly.graph_objects as go

from exploration.plotting import CandlePlot

class PeakType(Enum):
    UP = 1
    DOWN = 2
# PeakType = Enum('PeakType', ['UP', 'DOWN'])


@dataclass
class Peak:
    type: PeakType
    idx: int
    start_idx: int
    end_idx: int
    high_low_idx: int

    def __hash__(self):
        return hash(self.type) ^ hash(self.idx) ^ hash(self.start_idx) ^ hash(self.end_idx)

    def __eq__(self, other):
        if (self.type == other.type and self.start_idx == other.start_idx
                and self.idx == other.idx and self.end_idx == other.end_idx):
            return True
        return False


def get_peak(df: pd.DataFrame, idx: int, width=10, trend_len=3, perc=0.0008, debug=False) -> Optional[Peak]:
    def find_price_in_range(start, end, reverse, cond):
        loop_range = range(end, start - 1, -1) if reverse else range(start, end + 1)
        for i in loop_range:
            curr_close = df.iloc[i]['mid_c']
            if cond(curr_close):
                return curr_close, i
        return None, None

    df = df.filter(['mid_c', 'mid_o', 'mid_h', 'mid_l'])
    last_idx = len(df) - 1
    start_idx = max(idx - width, 0)
    end_idx = min(idx + width, last_idx)

    if start_idx > idx - trend_len or end_idx < idx + trend_len:
        return None

    lowest_prev_price, lowest_prev_idx = find_price_in_range(start_idx, idx - trend_len, True,
                                                             lambda price: df.iloc[idx][['mid_o', 'mid_c']].max() >= price + (price * perc))
    lowest_next_price, lowest_next_idx = find_price_in_range(idx + trend_len, end_idx, False,
                                                             lambda price: df.iloc[idx][['mid_o', 'mid_c']].max() >= price + (price * perc))

    if lowest_prev_price and lowest_next_price:
        highest = max(df.iloc[lowest_prev_idx + 1: lowest_next_idx][['mid_o', 'mid_c']].max())
        high_idx = df.iloc[lowest_prev_idx + 1: lowest_next_idx]['mid_h'].idxmax()
        if highest == df.iloc[idx][['mid_o', 'mid_c']].max():
            return Peak(type=PeakType.UP, idx=idx, start_idx=lowest_prev_idx, end_idx=lowest_next_idx, high_low_idx=high_idx)

    highest_prev_price, highest_prev_idx = find_price_in_range(start_idx, idx - trend_len, True,
                                                                 lambda price: df.iloc[idx][['mid_o', 'mid_c']].min() <= price - (
                                                                             price * perc))
    highest_next_price, highest_next_idx = find_price_in_range(idx + trend_len, end_idx, False,
                                                                 lambda price: df.iloc[idx][['mid_o', 'mid_c']].min() <= price - (
                                                                             price * perc))

    if highest_prev_price and highest_next_price:
        lowest = min(df.iloc[highest_prev_idx + 1: highest_next_idx][['mid_o', 'mid_c']].min())
        low_idx = df.iloc[highest_prev_idx + 1: highest_next_idx]['mid_l'].idxmin()
        if lowest == df.iloc[idx][['mid_o', 'mid_c']].min():
            return Peak(type=PeakType.DOWN, idx=idx, start_idx=highest_prev_idx, end_idx=highest_next_idx, high_low_idx=low_idx)

    return None


def get_peak_highest_high(df: pd.DataFrame, peak: Peak):
    return df.iloc[peak.start_idx + 1: peak.end_idx]['mid_h'].max()


def get_peak_lowest_low(df: pd.DataFrame, peak: Peak):
    return df.iloc[peak.start_idx + 1: peak.end_idx]['mid_l'].min()


def get_peaks(df: pd.DataFrame) -> List[Peak]:
    peaks = []
    for i in range(len(df)):
        peak = get_peak(df, i)
        if peak:
            peaks.append(peak)
    return peaks


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
