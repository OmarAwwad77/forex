from api.oanda_api import OandaApi
from instruments.instruments import instruments

if __name__ == '__main__':

    api = OandaApi()

    instruments.create_file(api.get_account_instruments(), "./data")
    instruments.load_instruments("./data")
    instruments.print_instruments()
