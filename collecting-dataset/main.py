import pandas as pd
import time

from utils import extract_all_data, transform_all_data, store_to_csv

def main():
    urls = {
        'somethinc' : "https://www.tokopedia.com/somethinc/product",
        'scarlett' : "https://www.tokopedia.com/scarlettwhite/product",
        'ms glow' : "https://www.tokopedia.com/msglowdistributorjkt/product",
        'avoskin' : "https://www.tokopedia.com/avoskinbandung/product",
        'whitelab' : "https://www.tokopedia.com/whitelab/product",
        'azarine' : "https://www.tokopedia.com/azarinecosmetics/product",
        'wardah' : "https://www.tokopedia.com/wardah-official/product",
        'erha'  : "https://www.tokopedia.com/erhaultimateofficial/product",
        'emina' : "https://www.tokopedia.com/emina-official/product",
        'bio beauty lab' : "https://www.tokopedia.com/biobeautylab/product",
        'theoriginote': "https://www.tokopedia.com/theoriginote/product",
    }
    
    print("[1] Mulai proses ekstraksi...")
    # extract_all_data('data', urls)

    print("[2] Transformasi data...")
    data = transform_all_data()

    print("[3] Load data ke dalam file CSV...")
    store_to_csv(data, 'processed_data.csv')

if __name__ == "__main__":
    main()
