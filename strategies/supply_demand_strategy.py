import pandas as pd
from typing_extensions import override, Optional

from simulator.trade import Trade, SignalType
from strategies.strategy import Strategy
from technical.peaks import get_peak, PeakType
from technical.patterns import is_bullish_pattern, is_bearish_pattern

class SupplyDemandStrategy(Strategy):
    @override
    def apply_signal(self, row: pd.Series, df: pd.DataFrame, df_lower: pd.DataFrame, delta_in_mins: int) -> Optional[Trade]:
        peaks = []
        row_idx = df.index.get_loc(row.name)
        window_start = max(0, row_idx - 100)

        for i in range(row_idx, window_start - 1, -1):
            if len(peaks) >= 4:
                break

            if peak:= get_peak(df.iloc[:row_idx + 1], i):
                if any(p.type == peak.type and p.idx == peak.idx + 1 for p in peaks):
                    continue
                peaks.append(peak)

        if len(peaks) >= 4:
            peak_one = peaks[0]
            peak_two = peaks[1]
            peak_three = peaks[2]
            peak_four = peaks[3]
            curr_close = row['mid_c']
            max_between_peak_one_and_row = max(df.iloc[peak_one.idx + 1: row_idx + 1][['mid_c', 'mid_o']].max())
            min_between_peak_one_and_row = min(df.iloc[peak_one.idx + 1: row_idx + 1][['mid_c', 'mid_o']].min())

            if (
                    peak_one.type == PeakType.UP and
                    peak_two.type == PeakType.DOWN and
                    peak_three.type == PeakType.UP and
                    peak_four.type == PeakType.DOWN and
                    is_bullish_pattern(row, df)
            ):
                peak_one_price = max(df.iloc[peak_one.idx]['mid_o'], df.iloc[peak_one.idx]['mid_c'])
                peak_two_price = min(df.iloc[peak_two.idx]['mid_o'], df.iloc[peak_two.idx]['mid_c'])
                peak_three_price = max(df.iloc[peak_three.idx]['mid_o'], df.iloc[peak_three.idx]['mid_c'])
                peak_four_price = min(df.iloc[peak_four.idx]['mid_o'], df.iloc[peak_four.idx]['mid_c'])

                before_peak_four = df.iloc[max(0, peak_four.idx - 24): peak_four.idx]
                max_price_before_peak_four = max(before_peak_four[['mid_c', 'mid_o']].max())
                up_trend_before_beak_four = (peak_three_price - peak_three_price * 0.001) >= max_price_before_peak_four

                if (
                        peak_one_price >= peak_three_price and
                        peak_two_price >= peak_four_price and
                        peak_two_price <= min_between_peak_one_and_row and
                        peak_one_price >= max_between_peak_one_and_row and
                        # up_trend_before_beak_four and
                        peak_four_price - (peak_four_price * 0.002) >= df.iloc[max(peak_four.idx - 48, 0)]['mid_c']
                ):
                    sl_price = df.iloc[peak_four.high_low_idx]['mid_l']
                    sl_distance = curr_close - sl_price
                    tp_price = curr_close + sl_distance
                    # tp_price = df.iloc[peak_one.high_low_idx]['mid_h']
                    trade_peaks = [peak_one, peak_two, peak_three, peak_four]
                    if curr_close + curr_close * 0.00125 <= tp_price and ((peak_one_price - peak_two_price) * 0.25 + peak_two_price) >= curr_close:
                        return Trade(tp=tp_price, sl=sl_price, entry_price=row['ask_c'], data={'peaks': trade_peaks},
                                     entry_idx=row_idx, entry_time=row.time, signal=SignalType.BUY)

            if (
                    peak_one.type == PeakType.DOWN and
                    peak_two.type == PeakType.UP and
                    peak_three.type == PeakType.DOWN and
                    peak_four.type == PeakType.UP and
                    is_bearish_pattern(row, df)
            ):
                peak_one_price = min(df.iloc[peak_one.idx]['mid_o'], df.iloc[peak_one.idx]['mid_c'])
                peak_two_price = max(df.iloc[peak_two.idx]['mid_o'], df.iloc[peak_two.idx]['mid_c'])
                peak_three_price = min(df.iloc[peak_three.idx]['mid_o'], df.iloc[peak_three.idx]['mid_c'])
                peak_four_price = max(df.iloc[peak_four.idx]['mid_o'], df.iloc[peak_four.idx]['mid_c'])

                before_peak_four = df.iloc[max(0, peak_four.idx - 24): peak_four.idx]
                min_price_before_peak_four = min(before_peak_four[['mid_c', 'mid_o']].min())
                down_trend_before_beak_four = (peak_three_price + peak_three_price * 0.001) <= min_price_before_peak_four

                if (
                        peak_one_price <= peak_three_price and
                        peak_two_price <= peak_four_price and
                        peak_one_price <= min_between_peak_one_and_row and
                        peak_two_price >= max_between_peak_one_and_row and
                        # down_trend_before_beak_four and
                        peak_four_price + (peak_four_price * 0.002) <= df.iloc[max(peak_four.idx - 48, 0)]['mid_c']
                ):
                    sl_price = df.iloc[peak_four.high_low_idx]['mid_h']
                    sl_distance = sl_price - curr_close
                    tp_price = curr_close - sl_distance
                    # tp_price = df.iloc[peak_one.high_low_idx]['mid_l']
                    trade_peaks = [peak_one, peak_two, peak_three, peak_four]
                    if curr_close - curr_close * 0.00125 >= tp_price and ((peak_two_price - peak_one_price) * 0.25 + peak_one_price) <= curr_close:
                        return Trade(tp=tp_price, sl=sl_price, entry_price=row['bid_c'], data={'peaks': trade_peaks},
                                     entry_idx=row_idx, entry_time=row.time, signal=SignalType.SELL)