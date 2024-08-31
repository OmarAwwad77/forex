from typing import List, Callable, Dict, Union, Tuple

import pandas as pd
import plotly.graph_objects as go

from exploration.plotting import CandlePlot
from strategies.Trade import Trade, TradeStatus, TradeOutcome
from strategies.strategy import Strategy

class Simulation:
    def __init__(self, strategy: Strategy, df: pd.DataFrame, df_smaller: pd.DataFrame, delta_in_mins: int):
        self.strategy = strategy
        self.df = df
        self.df_smaller = df_smaller
        self.delta_in_mins = delta_in_mins

    def plot_trades(self, trades: List[Trade], hover_txt_callback: Callable[[Dict], str]):
        cp = CandlePlot(self.df, candles=True)
        prices = []
        times = []
        indexes = []
        hover_text: List[str] = []
        for t in trades:
            indexes.append(t.entry_idx)
            prices.extend([t.tp, t.sl])
            times.extend([cp.df_plot.iloc[t.entry_idx]['sTime'], cp.df_plot.iloc[t.entry_idx]['sTime']])
            hover_text.append(hover_txt_callback(t.data))

        # stop loss and take profit markers
        cp.fig.add_trace(go.Scatter(
            x=times,
            y=prices,
            mode='markers',
            marker=dict(color='#FFFFFF', size=3)
        ))

        # highlight trade candles and add hover text
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

    def run(self) -> Tuple[List, List]:
        open_trades = []
        closed_trades = []

        for i in range(len(self.df)):
            indices_to_close = []
            row = self.df.iloc[i]

            for open_trade_idx, open_trade in enumerate(open_trades):
                row_idx = self.df.index.get_loc(row.name)
                open_trade.update(row_idx, row, self.df_smaller, self.delta_in_mins)
                if open_trade.status == TradeStatus.CLOSED:
                    indices_to_close.append(open_trade_idx)
                    closed_trades.append(open_trade)

            for j in range(len(indices_to_close) - 1, -1, -1):
                idx_to_remove = indices_to_close[j]
                open_trades.remove(open_trades[idx_to_remove])

            trade = self.strategy.apply_signal(row, self.df)
            if trade:
                open_trades.append(trade)

        bad_trades = [t for t in closed_trades if t.outcome == TradeOutcome.LOSS]
        bad_trades_len = len(bad_trades)
        closed_trades_len = len(closed_trades)

        print(
            f'{bad_trades_len} ({bad_trades_len / closed_trades_len * 100:.2f}%) wrong trades taken out of: {closed_trades_len} trades in total')
        return open_trades, closed_trades