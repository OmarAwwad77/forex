from simulation.guru_1.original import guru_1_original
from simulation.guru_1.improved import guru_1_improved

if __name__ == '__main__':
    guru_1_original.run()
    # guru_1_improved.run()
    # api = OandaApi()
    # instrument_collection.create_file(api.get_account_instruments(), "./data")
    # instrument_collection.print_instruments()
    # instrument_collection.load_instruments("./data")
    # run_collection(instrument_collection, api)

    #run_ma_sim(curr_list=["EUR", "USD", "GBP", "JPY", "AUD", "CAD"])