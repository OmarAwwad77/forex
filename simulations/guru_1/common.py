BUY = 1
SELL = -1
NONE = 0
RSI_LIMIT = 50.0


def apply_signal(row):
    if row.ENGULFING == True:
        if row.direction == BUY and row.mid_l > row.EMA_200:
            if row.RSI_14 > RSI_LIMIT:
                return BUY
        if row.direction == SELL and row.mid_h < row.EMA_200:
            if row.RSI_14 < RSI_LIMIT:
                return SELL
    return NONE


def apply_take_profit(row, PROFIT_FACTOR):
    if row.SIGNAL != NONE:
        if row.SIGNAL == BUY:
            if row.direction == BUY:
                return (row.ask_c - row.ask_o) * PROFIT_FACTOR + row.ask_c
            else:
                return (row.ask_o - row.ask_c) * PROFIT_FACTOR + row.ask_o
        else:
            if row.direction == SELL:
                return (row.bid_c - row.bid_o) * PROFIT_FACTOR + row.bid_c
            else:
                return (row.bid_o - row.bid_c) * PROFIT_FACTOR + row.bid_o
    else:
        return 0.0


def apply_stop_loss(row):
    if row.SIGNAL != NONE:
        if row.SIGNAL == BUY:
            if row.direction == BUY:
                return row.ask_o
            else:
                return row.ask_c
        else:
            if row.direction == SELL:
                return row.bid_o
            else:
                return row.bid_c
    else:
        return 0.0

def apply_signals(df, PROFIT_FACTOR, sig):
    df["SIGNAL"] = df.apply(sig, axis=1)
    df["TP"] = df.apply(apply_take_profit, axis=1, PROFIT_FACTOR=PROFIT_FACTOR)
    df["SL"] = df.apply(apply_stop_loss, axis=1)