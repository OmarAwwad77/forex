import pandas as pd
from typing_extensions import override, Optional
import datetime as dt
from simulator.trade import Trade, SignalType
from strategies.strategy import Strategy
from technical.peaks import get_peak, PeakType
from technical.patterns import is_bullish_pattern, is_bearish_pattern


def get_peaks_list(df,**kwargs):
    peaks_list = []
    for idx in range(len(df)):
        if peak := get_peak(df, idx, **kwargs):
            if peaks_list and peak.idx in range(peaks_list[-1].start_idx, peaks_list[-1].end_idx) and peaks_list[-1].type == peak.type:
                # which is better
                if (peak.type == PeakType.UP and df.iloc[peak.idx]['mid_c'] <= df.iloc[peaks_list[-1].idx]['mid_c']) or (peak.type == PeakType.DOWN and df.iloc[peak.idx]['mid_c'] >= df.iloc[peaks_list[-1].idx]['mid_c']):
                    continue
                peaks_list.remove(peaks_list[-1])
            peaks_list.append(peak)
    return peaks_list


class SupplyDemandStrategy(Strategy):
    @override
    def apply_signal(self, row: pd.Series, df: pd.DataFrame, df_lower: pd.DataFrame, delta_in_mins: int) -> Optional[Trade]:
        row_idx = df.index.get_loc(row.name)
        if not self.iteration_data['peaks']:
            self.iteration_data['peaks'] = get_peaks_list(df, width=300, perc=0.012, trend_len=50)

        peaks_list = [p for p in self.iteration_data['peaks'] if p.end_idx <= row_idx]

        if len(peaks_list) >= 4:
            peak_one = peaks_list[-1]
            peak_two = peaks_list[-2]
            peak_three = peaks_list[-3]
            peak_four = peaks_list[-4]

            curr_close = row['mid_c']
            max_between_peak_one_and_row = max(df.iloc[peak_one.idx + 1: row_idx + 1][['mid_c', 'mid_o']].max())
            min_between_peak_one_and_row = min(df.iloc[peak_one.idx + 1: row_idx + 1][['mid_c', 'mid_o']].min())

            if (
                    peak_one.type == PeakType.UP and
                    peak_two.type == PeakType.DOWN and
                    peak_three.type == PeakType.UP and
                    peak_four.type == PeakType.DOWN
            ):
                peak_one_price = max(df.iloc[peak_one.idx]['mid_o'], df.iloc[peak_one.idx]['mid_c'])
                peak_two_price = min(df.iloc[peak_two.idx]['mid_o'], df.iloc[peak_two.idx]['mid_c'])
                peak_three_price = max(df.iloc[peak_three.idx]['mid_o'], df.iloc[peak_three.idx]['mid_c'])
                peak_four_price = min(df.iloc[peak_four.idx]['mid_o'], df.iloc[peak_four.idx]['mid_c'])

                if (
                        peak_one_price >= peak_three_price and
                        peak_two_price >= peak_four_price and
                        peak_two_price <= min_between_peak_one_and_row and
                        peak_one_price >= max_between_peak_one_and_row
                        # peak_two_price >= (peak_four_price + (peak_four_price * 0.007)) and
                        # peak_one_price >= (peak_three_price + (peak_three_price * 0.007))
                ):
                    # if (peak_one_price - ((peak_one_price - peak_two_price) * 0.25)) >= lower_row['mid_c']:
                    sl_price = df.iloc[peak_four.idx]['mid_c']
                    sl_distance = curr_close - sl_price
                    tp_price = curr_close + sl_distance
                    trade_peaks = [peak_one, peak_two, peak_three, peak_four]
                    return Trade(tp=tp_price, sl=sl_price, entry_price=row['ask_c'], data={'peaks': trade_peaks},
                                 entry_idx=row_idx, entry_time=row.time, signal=SignalType.BUY)

            if (
                    peak_one.type == PeakType.DOWN and
                    peak_two.type == PeakType.UP and
                    peak_three.type == PeakType.DOWN and
                    peak_four.type == PeakType.UP
            ):
                peak_one_price = min(df.iloc[peak_one.idx]['mid_o'], df.iloc[peak_one.idx]['mid_c'])
                peak_two_price = max(df.iloc[peak_two.idx]['mid_o'], df.iloc[peak_two.idx]['mid_c'])
                peak_three_price = min(df.iloc[peak_three.idx]['mid_o'], df.iloc[peak_three.idx]['mid_c'])
                peak_four_price = max(df.iloc[peak_four.idx]['mid_o'], df.iloc[peak_four.idx]['mid_c'])

                if (
                        peak_one_price <= peak_three_price and
                        peak_two_price <= peak_four_price and
                        peak_one_price <= min_between_peak_one_and_row and
                        peak_two_price >= max_between_peak_one_and_row
                        # peak_three_price >= (peak_one_price + (peak_one_price * 0.007)) and
                        # peak_four_price >= (peak_two_price + (peak_two_price * 0.007))
                ):

                    sl_price = df.iloc[peak_four.idx]['mid_c']
                    sl_distance = sl_price - curr_close
                    tp_price = curr_close - sl_distance
                    trade_peaks = [peak_one, peak_two, peak_three, peak_four]
                    return Trade(tp=tp_price, sl=sl_price, entry_price=row['bid_c'], data={'peaks': trade_peaks},
                                 entry_idx=row_idx, entry_time=row.time, signal=SignalType.SELL)
