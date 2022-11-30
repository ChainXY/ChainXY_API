### This script lets you list and download information on chains that were updated after a certain update data
### download of a .csv requires an installation of the pandas package for your python environment
import requests
import json
import time

def check_api_key(cxy_api_key):
    url = 'https://location.chainxy.com/api/Users/Me'
    headers = {'x-apikey': cxy_api_key,
            'x-Application': 'Python API Call',
            'content-type': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 401:
        raise ValueError("Bad ChainXY API key provided, double-check the provided value!")

def list_chains_by_last_scrape_date(cxy_api_key:str, ChainIds:list, LastScrapeDate:str):
    """
    Generates a file based on the provided input parameters. Returns a URL to the report.
    cxy_api_key:str - ChainXY API Key,
    ChainIds:list - list of Chain ids:int
    LastScrapeDate:str -  Starting point of the updates in YYYY-MM-DD
    """

    check_api_key(cxy_api_key)
    headers = {'x-apikey': cxy_api_key,
            'x-Application': 'Python API Call',
            'content-type': 'application/json'}

    apiUrl = "https://location.chainxy.com/api/Chains?query={}"
    url_params = {
        "LastScrapeDate": f">{LastScrapeDate}",
        "Id": ChainIds
        }
    r = requests.get(url=apiUrl.format(json.dumps(url_params)), headers=headers)
    
    generated_file = False
    while generated_file == False:
        print(f"Requesting records...")
        r_body = json.loads(r.text)['Records']
        if r_body:
            print('Request complete!')
            generated_file = True
            return r_body
        else:
            print('There are no records for your request. Speak to ChainXY for assistance.')

def download_file(input:dict, filename:str):
    """
    Downloads a file in the specified format based on the provided 
    input from list_chains_by_last_scrape_date(). Returns a csv (default) or json.
    input:dict - output of list_chains_by_last_scrape_date(),
    filename:str -  name/path of the file to be downloaded. Including the file extension (e.g. filename.csv)
    """
    import pandas as pd
    if '.json' in filename.lower():
        with open(filename, 'w', encoding='utf-8') as w:
                json.dump(input, w, ensure_ascii=False)
    else:
        df = pd.DataFrame.from_dict(input)
        df[['Name', 'Id', 'LastScrapeDate']].to_csv(filename, index=False)
    
    print('File generation complete!')

def main():
    # FILL THESE
    # your chainxy api key
    cxy_api_key = ''
    # Chain Ids as list of int
    ChainIds = []
    # In the format of YYYY-MM-DD
    LastScrapeDate = '2022-09-01'
    chains = list_chains_by_last_scrape_date(cxy_api_key, ChainIds, LastScrapeDate)
    download_file(chains, 'test.csv')

if __name__ == '__main__':
    main()