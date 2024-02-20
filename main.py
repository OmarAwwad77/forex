from api.oanda_api import OandaApi
from instruments.instruments import instrument_collection
from simulation.ma_cross import run_ma_sim

if __name__ == '__main__':
    api = OandaApi()
    # instrument_collection.create_file(api.get_account_instruments(), "./data")
    # instrument_collection.load_instruments("./data")
    # instrument_collection.print_instruments()
    run_ma_sim(curr_list=["EUR", "USD", "GBP", "JPY", "AUD", "CAD"])