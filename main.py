from api.oanda_api import OandaApi
from instruments.instruments import instrument_collection
from simulation.ma_cross import run_ma_sim
from data.collect_data import run_collection
if __name__ == '__main__':
    api = OandaApi()
    # instrument_collection.create_file(api.get_account_instruments(), "./data")
    # instrument_collection.print_instruments()
    instrument_collection.load_instruments("./data")
    run_collection(instrument_collection, api)

    #run_ma_sim(curr_list=["EUR", "USD", "GBP", "JPY", "AUD", "CAD"])