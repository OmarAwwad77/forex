class Instrument:

    def __init__(self, name, ins_type, display_name,
                 pip_location, trade_units_precision, margin_rate):
        self.name = name
        self.ins_type = ins_type
        self.displayName = display_name
        self.pipLocation = pow(10, pip_location)
        self.tradeUnitsPrecision = trade_units_precision
        self.marginRate = float(margin_rate)

    def __repr__(self):
        return str(vars(self))

    @classmethod
    def from_api_object(cls, ob):
        return Instrument(
            ob['name'],
            ob['type'],
            ob['displayName'],
            ob['pipLocation'],
            ob['tradeUnitsPrecision'],
            ob['marginRate']
        )