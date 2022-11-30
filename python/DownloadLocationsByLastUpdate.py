### This script lets you list and download locations chains that were updated after a certain update data
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

def list_locations_by_last_scrape_date(cxy_api_key:str, ChainIds:list, LastUpdateDate:str, north:float=90, east:float=180, south:float=-90, west:float=-180, limit:int=100):
    '''
    Generates a file based on the provided input parameters. Returns a URL to the report.
    cxy_api_key:str - ChainXY API Key,
    ChainIds:list - list of Chain ids in int form (e.g. [5111, 1])
    LastUpdateDate:str -  Starting point of the updates in YYYY-MM-DD
    north, east, south, west:float - points of polygon search area
    limit:int - Max number of results returned. We recommend requesting 5000 records max at a time. 
        You can bypass this record limit by passing limit=-1. 
        We ask that you be reasonable with your records requests. 
        We reserve the right to suspend your API access if your usage is deemed unreasonable.
    '''

    check_api_key(cxy_api_key)
    headers = {'x-apikey': cxy_api_key,
            'x-Application': 'Python API Call',
            'content-type': 'application/json'}

    pageUrl = f"https://location.chainxy.com/api/Locations?chainIds={ChainIds}&Limit={limit}&Page={i}&OrderBy=Id&North={north}&East={east}&South={south}&West={west}&LastUpdate=>{LastUpdateDate}"
    records = []
    pages = getPageNum(pageUrl, headers)
    

    for i in range(1, pages+1):
        apiUrl = f"https://location.chainxy.com/api/Locations?chainIds={ChainIds}&Limit={limit}&Page={i}&OrderBy=Id&North={north}&East={east}&South={south}&West={west}&LastUpdate=>{LastUpdateDate}"
        r = requests.get(url=apiUrl, headers=headers)
    
        generated_file = False
        while generated_file == False:
            print(f"Requesting records for page {i}/{pages}...")
            r_body = json.loads(r.text)
            if r_body:
                print('Request complete!')
                generated_file = True
                records.extend(r_body['Records'])
            else:
                print('There are no records for your request. Speak to ChainXY for assistance.')

    return records

def getPageNum(url, headers):
    '''Returns the total number pages of the request'''
    r = requests.get(url=url, headers=headers)
    r_body = json.loads(r.text)
    return r_body['Pages']

def download_file(input:dict, filename:str):
    """
    Downloads a file in the specified format based on the provided 
    input from list_locations_by_last_scrape_date(). Returns a csv (default) or json.
    input:dict - output of list_locations_by_last_scrape_date(),
    filename:str -  name/path of the file to be downloaded. Including the file extension (e.g. filename.csv)
    """
    import pandas as pd
    if '.json' in filename.lower():
        with open(filename, 'w', encoding='utf-8') as w:
                json.dump(input, w, ensure_ascii=False)
    else:
        df = pd.DataFrame.from_dict(input)
        df.to_csv(filename, index=False)
    
    print('File generation complete!')

def main():
    # FILL THESE
    # your chainxy api key
    cxy_api_key = ''
    # Chain Ids in str format separated by commas (e.g. "1, 2, 3")
    ChainIds = ''
    # In the format of YYYY-MM-DD (e.g. '2022-01-22')
    LastUpdateDate = ''
    # Max number of results
    limit = 100
    # Boundaries of search
    north = 90
    east = 180
    south = -90
    west = -180
    
    raw = list_locations_by_last_scrape_date(cxy_api_key=cxy_api_key, ChainIds=ChainIds, LastUpdateDate=LastUpdateDate, limit=limit)
    download_file(raw, 'filename.csv')

if __name__ == '__main__':
    main()