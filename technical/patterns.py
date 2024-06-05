import pandas as pd
from exploration.plotting import CandlePlot
import plotly.graph_objects as go


def is_bearish_pattern(row: pd.Series, df: pd.DataFrame):
    return is_shooting_star(row) or is_bearish_engulfing(row, df) or is_dark_cloud(row, df) or is_evening_star(row, df)


def is_bullish_pattern(row: pd.Series, df: pd.DataFrame):
    return is_hammer(row) or is_piercing(row, df) or is_morning_star(row, df) or is_bullish_engulfing(row, pd)


def is_star_candle(row: pd.Series, prev: pd.Series, next_c: pd.Series):
    prev_body_height = abs(prev['mid_o'] - prev['mid_c'])
    next_body_height = abs(next_c['mid_o'] - next_c['mid_c'])
    star_body_height = abs(row['mid_o'] - row['mid_c'])
    min_height = min(prev_body_height, next_body_height)

    if min_height and round(star_body_height / min_height) <= 0.25:
        return True
    return False


def is_small_candle(row: pd.Series):
    s = 0.00015
    if row['mid_c'] > row['mid_o']:  # green
        if row['mid_c'] <= row['mid_o'] + (row['mid_o'] * s):
            return True
    else:  # red
        if row['mid_c'] >= row['mid_o'] - (row['mid_o'] * s):
            return True


def is_big_candle(row: pd.Series):
    b = 0.00035
    if row['mid_c'] > row['mid_o']:  # green
        # print(row['mid_c'],  row['mid_o'] + (row['mid_o'] * b))
        if row['mid_c'] >= row['mid_o'] + (row['mid_o'] * b):
            return True
    else:  # red
        if row['mid_c'] <= row['mid_o'] - (row['mid_o'] * b):
            return True


def highlight_candles(df: pd.DataFrame, indexes, color='#0066FF'):
    cp = CandlePlot(df, candles=True)
    df_temp = cp.df_plot[cp.df_plot.index.isin(indexes)]
    cp.fig.add_trace(go.Candlestick(
        x=df_temp.sTime,
        open=df_temp.mid_o,
        high=df_temp.mid_h,
        low=df_temp.mid_l,
        close=df_temp.mid_c,
        line=dict(width=1), opacity=1,
        increasing_fillcolor=color,
        decreasing_fillcolor=color,
        increasing_line_color=color,
        decreasing_line_color=color
    ))

    cp.show_plot(width=1100, height=500)


def get_body_perc(row: pd.Series):
    full_height = row['mid_h'] - row['mid_l']
    body_height = abs(row['mid_o'] - row['mid_c'])
    return body_height / full_height * 100


def is_hammer(row: pd.Series, head_perc_limit: float = 25, high_to_head_perc_limit: float = 5, debug=False):
    full_height = row['mid_h'] - row['mid_l']

    max_body_price = max(row['mid_o'], row['mid_c'])
    min_body_price = min(row['mid_o'], row['mid_c'])

    head_perc = (row['mid_h'] - min_body_price) / full_height * 100
    high_to_head_perc = (row['mid_h'] - max_body_price) / full_height * 100

    if debug:
        print(f'{head_perc} <= {head_perc_limit} -> {head_perc <= head_perc_limit}')
        print(f'{high_to_head_perc} <= {high_to_head_perc_limit} -> {high_to_head_perc <= high_to_head_perc_limit}')

    if head_perc <= head_perc_limit and high_to_head_perc <= high_to_head_perc_limit:
        return True

    return False


def is_bullish_engulfing(row: pd.Series, df: pd.DataFrame):
    curr_idx = row.name
    prev_idx = curr_idx - 1
    if prev_idx not in df.index:
        return False

    prev_row = df.iloc[prev_idx]
    # prev is red
    if prev_row['mid_c'] - prev_row['mid_o'] < 0:
        # curr is green
        if row['mid_c'] - row['mid_o'] > 0:
            # curr is bigger than prev
            curr_body_height = row['mid_c'] - row['mid_o']
            prev_body_height = prev_row['mid_o'] - prev_row['mid_c']
            if curr_body_height > prev_body_height:
                return True
    return False


def is_piercing(row: pd.Series, df: pd.DataFrame):
    curr_idx = row.name
    prev_idx = curr_idx - 1
    if prev_idx not in df.index:
        return False

    prev_row = df.iloc[prev_idx]
    # prev is red
    if prev_row['mid_c'] - prev_row['mid_o'] < 0:
        # curr is green
        if row['mid_c'] - row['mid_o'] > 0:
            # body mid point of red
            prev_body_distance = prev_row['mid_o'] - prev_row['mid_c']
            prev_body_mid_point = (prev_body_distance / 2) + prev_row['mid_c']
            if row['mid_c'] >= prev_body_mid_point:
                return True
    return False


def is_morning_star(row: pd.Series, df: pd.DataFrame):
    curr_idx = row.name
    prev_idx = curr_idx - 1
    before_prev_idx = prev_idx - 1

    if before_prev_idx not in df.index:
        return False

    prev_row = df.iloc[prev_idx]
    before_prev_row = df.iloc[before_prev_idx]

    # before_prev is red and big
    if before_prev_row['mid_c'] - before_prev_row['mid_o'] < 0:
        # prev is small
        if is_star_candle(prev_row, before_prev_row, row):
            # curr is green and big
            if row['mid_c'] - row['mid_o'] > 0:
                before_prev_body_distance = before_prev_row['mid_o'] - before_prev_row['mid_c']
                before_prev_body_mid_point = (before_prev_body_distance / 2) + before_prev_row['mid_c']
                if row['mid_c'] >= before_prev_body_mid_point:
                    return True
    return False


def is_shooting_star(row: pd.Series, head_perc_limit: float = 25, low_to_head_perc_limit: float = 5, debug=False):
    full_height = row['mid_h'] - row['mid_l']

    max_body_price = max(row['mid_o'], row['mid_c'])
    min_body_price = min(row['mid_o'], row['mid_c'])
    head_perc = abs(row['mid_l'] - max_body_price) / full_height * 100
    low_to_head_perc = abs(row['mid_l'] - min_body_price) / full_height * 100

    if debug:
        print(f'{head_perc} <= {head_perc_limit} -> {head_perc <= head_perc_limit}')
        print(f'{low_to_head_perc} <= {low_to_head_perc_limit} -> {low_to_head_perc <= low_to_head_perc_limit}')

    if head_perc <= head_perc_limit and low_to_head_perc <= low_to_head_perc_limit:
        return True

    return False


def is_bearish_engulfing(row: pd.Series, df: pd.DataFrame):
    curr_idx = row.name
    prev_idx = curr_idx - 1
    if prev_idx not in df.index:
        return False

    prev_row = df.iloc[prev_idx]
    # prev is green
    if prev_row['mid_c'] - prev_row['mid_o'] > 0:
        # curr is red
        if row['mid_c'] - row['mid_o'] < 0:
            # curr is bigger than prev
            curr_body_height = row['mid_o'] - row['mid_c']
            prev_body_height = prev_row['mid_c'] - prev_row['mid_o']
            if curr_body_height > prev_body_height:
                return True
    return False


def is_dark_cloud(row: pd.Series, df: pd.DataFrame):
    curr_idx = row.name
    prev_idx = curr_idx - 1
    if prev_idx not in df.index:
        return False

    prev_row = df.iloc[prev_idx]
    # prev is green
    if prev_row['mid_c'] - prev_row['mid_o'] > 0:
        # curr is red
        if row['mid_c'] - row['mid_o'] < 0:
            # body mid point of green
            prev_body_distance = prev_row['mid_c'] - prev_row['mid_o']
            prev_body_mid_point = (prev_body_distance / 2) + prev_row['mid_o']
            if row['mid_c'] <= prev_body_mid_point:
                return True
    return False


def is_evening_star(row: pd.Series, df: pd.DataFrame):
    curr_idx = row.name
    prev_idx = curr_idx - 1
    before_prev_idx = prev_idx - 1

    if before_prev_idx not in df.index:
        return False

    prev_row = df.iloc[prev_idx]
    before_prev_row = df.iloc[before_prev_idx]

    # before_prev is green
    if before_prev_row['mid_c'] - before_prev_row['mid_o'] > 0:
        # prev is small
        if is_star_candle(prev_row, before_prev_row, row):
            # curr is red
            if row['mid_c'] - row['mid_o'] < 0:
                before_prev_body_height = before_prev_row['mid_c'] - before_prev_row['mid_o']
                before_prev_body_mid_point = (before_prev_body_height / 2) + before_prev_row['mid_o']
                if row['mid_c'] <= before_prev_body_mid_point:
                    return True
    return False