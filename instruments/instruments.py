import json
from .instrument import Instrument


class Instruments:
    _filename = "instruments.json"
    _keys = ['name', 'type', 'displayName', 'pipLocation',
                'displayPrecision', 'tradeUnitsPrecision', 'marginRate']

    def __init__(self):
        self.instruments_dict = {}

    def load_instruments(self, path):
        self.instruments_dict = {}
        filename = f"{path}/{Instruments._filename}"
        with open(filename, "r") as f:
            data = json.loads(f.read())
            for k, v in data.items():
                self.instruments_dict[k] = Instrument.from_api_object(v)

    def create_file(self, data, path):
        if data is None:
            print("Instrument file creation failed")
            return

        instruments_dict = {}
        for i in data:
            key = i['name']
            instruments_dict[key] = {k: i[k] for k in Instruments._keys}

        filename = f"{path}/{Instruments._filename}"
        with open(filename, "w") as f:
            f.write(json.dumps(instruments_dict, indent=2))

    def print_instruments(self):
        [print(k, v) for k, v in self.instruments_dict.items()]
        print(len(self.instruments_dict.keys()), "instruments")


instrument_collection = Instruments() # singleton
