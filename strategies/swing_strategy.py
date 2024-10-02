from typing import Optional

import pandas as pd

from simulator.trade import Trade, SignalType
from strategies.strategy import Strategy
from technical.peaks import get_peak, PeakType


class SwingStrategy(Strategy):
    def apply_signal(self, row: pd.Series, df: pd.DataFrame) -> Optional[Trade]:
        perc = 0.01250
        idx = df.index.get_loc(row.name)

        self.iteration_data['peaks'] = self.update_peaks_list(df.iloc[:idx + 1], self.iteration_data['peaks'])
        row = df.iloc[idx]
        if self.iteration_data['curr_swing']:
            # if row breaks swing
            if self.iteration_data['peaks'][self.iteration_data['curr_swing']['start_peak_idx']].type == PeakType.UP:
                upper_bound = df.iloc[self.iteration_data['peaks'][self.iteration_data['curr_swing']['start_peak_idx']].high_low_idx]['mid_h']
                lower_bound = df.iloc[self.iteration_data['peaks'][self.iteration_data['curr_swing']['end_peak_idx']].high_low_idx]['mid_l']
                swing_start_price = upper_bound
                swing_end_price = lower_bound
            else:
                upper_bound = df.iloc[self.iteration_data['peaks'][self.iteration_data['curr_swing']['end_peak_idx']].high_low_idx]['mid_h']
                lower_bound = df.iloc[self.iteration_data['peaks'][self.iteration_data['curr_swing']['start_peak_idx']].high_low_idx]['mid_l']
                swing_start_price = lower_bound
                swing_end_price = upper_bound
            if row['mid_l'] < lower_bound or row['mid_h'] > upper_bound:
                # print(f"Swing: ({peaks[curr_swing['start_peak_idx']].idx},{peaks[curr_swing['end_peak_idx']].idx}) broke at {idx}")
                self.iteration_data['broken_swings'][self.iteration_data['curr_swing']['start_peak_idx'], self.iteration_data['curr_swing']['end_peak_idx']] = idx
                self.iteration_data['prev_swing'] = self.iteration_data['curr_swing']
                self.iteration_data['curr_swing'] = {}
                return

            # if there is a trade
            if abs(row['mid_c'] - swing_start_price) < abs(row['mid_c'] - swing_end_price):
                self.iteration_data['trade_swings'].append(dict(self.iteration_data['curr_swing']))
                # check if the current swing confirm with prev trend (analyze last x candles or check prev swing?)
                if self.iteration_data['prev_swing'] and \
                    self.iteration_data['peaks'][self.iteration_data['prev_swing']['end_peak_idx']].type == self.iteration_data['peaks'][self.iteration_data['curr_swing']['end_peak_idx']].type:
                    return Trade(tp=swing_end_price, sl=swing_start_price,
                                 entry_price=row['ask_c'] if swing_end_price > swing_start_price else row['bid_c'],
                                 data={'swing': dict(self.iteration_data['curr_swing'])}, entry_idx=idx, entry_time=row.time,
                                 signal=SignalType.BUY if swing_end_price > swing_start_price else SignalType.SELL)

        else:
            iter_start_idx = self.iteration_data['prev_swing']['start_peak_idx'] if self.iteration_data['prev_swing'] else 0
            for i in range(iter_start_idx, len(self.iteration_data['peaks'])):
                peak = self.iteration_data['peaks'][i]
                for j in range(i + 1, len(self.iteration_data['peaks'])):
                    if (i, j) in self.iteration_data['broken_swings']:
                        continue
                    following_peak = self.iteration_data['peaks'][j]
                    if peak.type != following_peak.type:
                        if peak.type == PeakType.UP:
                            upper_bound = df.iloc[peak.high_low_idx]['mid_h']
                            lower_bound = df.iloc[following_peak.high_low_idx]['mid_l']
                        else:
                            upper_bound = df.iloc[following_peak.high_low_idx]['mid_h']
                            lower_bound = df.iloc[peak.high_low_idx]['mid_l']

                        if (upper_bound - (upper_bound * perc)) >= lower_bound:
                            candles_between = df.iloc[following_peak.high_low_idx + 1: idx + 1][
                                ['mid_h', 'mid_l']]
                            min_in_between = min(candles_between.min())
                            max_in_between = max(candles_between.max())
                            if max_in_between > upper_bound or min_in_between < lower_bound:
                                self.iteration_data['broken_swings'][i, j] = idx
                                continue

                            self.iteration_data['curr_swing']['start_peak_idx'] = i
                            self.iteration_data['curr_swing']['end_peak_idx'] = j
                            self.iteration_data['swings'].append(self.iteration_data['curr_swing'])
                            # print(f'({peaks[i].idx},{peaks[j].idx}) added at {idx}')

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
