from typing import Optional

import pandas as pd
import datetime as dt

from simulator.trade import Trade, SignalType
from strategies.strategy import Strategy
from technical.peaks import get_peak, PeakType


class SwingStrategy(Strategy):
    def apply_signal(self, row: pd.Series, df: pd.DataFrame, df_lower: pd.DataFrame, delta_in_mins: int) -> Optional[Trade]:
        perc = 0.00800
        idx = df.index.get_loc(row.name)
        self.iteration_data['peaks'] = self.update_peaks_list(df.iloc[:idx + 1], self.iteration_data['peaks'])

        if len(self.iteration_data['peaks']) >= 2:
            first_peak = self.iteration_data['peaks'][-2]
            second_peak = self.iteration_data['peaks'][-1]

            if first_peak.type != second_peak.type:
                if first_peak.type == PeakType.UP:
                    upper_bound = df.iloc[first_peak.high_low_idx]['mid_h']
                    lower_bound = df.iloc[second_peak.high_low_idx]['mid_l']
                    swing_start_price = upper_bound
                    swing_end_price = lower_bound

                else:
                    upper_bound = df.iloc[second_peak.high_low_idx]['mid_h']
                    lower_bound = df.iloc[first_peak.high_low_idx]['mid_l']
                    swing_start_price = lower_bound
                    swing_end_price = upper_bound

                if (upper_bound - (upper_bound * perc)) >= lower_bound:
                    candles_between = df.iloc[second_peak.high_low_idx + 1: idx + 1][['mid_h', 'mid_l']]
                    min_in_between = min(candles_between.min())
                    max_in_between = max(candles_between.max())
                    if max_in_between > upper_bound or min_in_between < lower_bound:
                        return

                    # if there is a trade
                    start_date = row.time
                    end_date = start_date + dt.timedelta(minutes=delta_in_mins)
                    df_for_row = df_lower[(df_lower.time >= start_date) & (df_lower.time <= end_date)]
                    distance = upper_bound - lower_bound
                    candles_between = df.iloc[second_peak.idx + 1: idx + 1][['mid_c']]

                    if swing_end_price > swing_start_price:
                        min_max_price = min(candles_between.min())
                    else:
                        min_max_price = max(candles_between.max())

                    if min_max_price != row['mid_c']:
                        return


                    for lower_idx in range(len(df_for_row)):
                        lower_row = df_for_row.iloc[lower_idx]

                        if swing_end_price > swing_start_price:
                            tp = swing_end_price - distance * 0.75
                            sl = swing_end_price + distance * 0.25
                            if lower_row['mid_c'] > swing_end_price - abs(swing_start_price - swing_end_price) * 0.25 or lower_row[
                                'mid_c'] < swing_end_price - abs(swing_start_price - swing_end_price) * 0.30:
                                continue
                        else:
                            tp = swing_end_price + distance * 0.75
                            sl = swing_end_price - distance * 0.25
                            if lower_row['mid_c'] < swing_end_price + abs(swing_start_price - swing_end_price) * 0.25 or lower_row[
                                'mid_c'] > swing_end_price + abs(swing_start_price - swing_end_price) * 0.30:
                                continue

                        return Trade(tp=tp, sl=sl,
                                     entry_price=lower_row['ask_c'] if swing_end_price < swing_start_price else lower_row['bid_c'],
                                     data={'swing': (first_peak.high_low_idx, second_peak.high_low_idx)}, entry_idx=idx,
                                     entry_time=row.time,
                                     signal=SignalType.BUY if swing_end_price < swing_start_price else SignalType.SELL)



    def update_peaks_list(self, df, peaks_list):
        peaks_copy = list(peaks_list)
        if peaks_copy:
            last_peak = peaks_copy[-1]
            iter_start_idx = last_peak.idx + 1
        else:
            iter_start_idx = 0
        for idx in range(iter_start_idx, len(df)):
            if peak := get_peak(df, idx):
                if peaks_copy:
                    last_peak = peaks_copy[-1]
                    if last_peak.high_low_idx == peak.high_low_idx:
                        continue
                peaks_copy.append(peak)

        return peaks_copy
