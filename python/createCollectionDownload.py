#this script sample allows you to download a collection
import requests
import json
import time
from datetime import datetime

def request_api(url:str, cxy_api_key:str, method='GET', params=None, data={}):
    """
    Handles making requests to the ChainXY API and returns the response.
    """
    headers = {
        'x-apikey': cxy_api_key,
        'x-Application': 'Python API Call',
        'content-type': 'application/json'
        }
    r = requests.request(url=url, method=method, headers=headers, params=params, data=data)
    if r.status_code == 401:
        raise ValueError("Bad ChainXY API key provided, please double-check the input value!")
    elif r.status_code != 200 and 'does not correspond to a collection' in r.text.lower():
        print("The collection does not exist in the database.")
        r = None
    else:
        return r

def validate_inputs(cxy_api_key:str, collection_type:str, cache_time:int):
    """
    Verifies that a given API key is valid for making requests to the API and checks that the collection download
    inputs are valid for processing.
    """
    url = 'https://location.chainxy.com/api/Users/Me'
    r = request_api(url, cxy_api_key)
    if not isinstance(collection_type, str) or collection_type.lower() not in ['chain', 'center']:
        raise ValueError(f"Collection type '{collection_type}' must be one of ['chain', 'center'].")
    
    if cache_time < 0:
        raise ValueError("Please enter a valid duration for cache_time that is an int > 0.")

def is_download_stale(create_date, cache_time:int):
    """
    Returns true if a new download should be created. 
    """
    dt = datetime.strptime(create_date, '%Y-%m-%dT%H:%M:%S.%f')
    now = datetime.utcnow()
    td = (abs(dt - now)).total_seconds()/3600
    return td > cache_time
    
def check_record_exists(url:str, cxy_api_key:str):
    """
    Returns true if a record of the collection exists in the database.
    """
    r = request_api(url, cxy_api_key)
    result = json.loads(r.text)
    if 'Message' in result:
        if 'record does not exist' in result['Message'].lower():
            raise ValueError(f"No collection found. Please ensure you have the correct collection ID and collection Type.")
            
    if r.status_code == 200:
        return True

def create_new_download(new_download_url:str, cxy_api_key:str, params:str):
    """
    Begins a new download of a collection and returns the download Id.
    """
    r = request_api(new_download_url, cxy_api_key, method='POST', params=params)
    r_body = json.loads(r.text)
    if isinstance(r_body, list):
        return r_body[0]['Id'] # center collections return a list
    else:
        return r_body['Id']

def get_download_link(collection_download_id:int, cxy_api_key:str, check_frequency:float=1):
    """
    Checks and waits for a download to finish before returning the URL of the collection file.
    """
    file_generated = False
    collection_download_link = False
    
    print(f"Checking for status of downloaded file...")
    
    while(file_generated == False):
        
        r = request_api(url=f'https://location.chainxy.com/api/Downloads/{collection_download_id}', cxy_api_key=cxy_api_key)
        r_body = json.loads(r.text)['Record']

        if r_body['Status'] == 0:
            print(f"Download {str(collection_download_id)} is still generating...")
            time.sleep(check_frequency)

        elif r_body['Status'] == 2:
            print("File generation failed. Please reach out to ChainXY support for assistance.")
            file_generated = True

        elif r_body['Status'] == 1:
            print("File generation completed!")
            file_generated = True
            collection_download_link = r_body['Link']
    
    return collection_download_link

def download_collection(cxy_api_key:str, collection_id:int, collection_type:str, cache_time:int = 24, url_params:dict = {}, data_date:str="", check_frequency:float=1):
    """
    Downloads a collection based on the provided collection ID and collection type. An optional input cache_time determines if a new download should be made.
    Params:
        cxy_api_key:str - ChainXY API Key
        collection_id:str - ID of the collection for which a new download will be initiated.
        collectiontype:str - 'chain' or 'center' collection
        cache_time:int - max. time in hours since the latest download before a new one is requested
        data_date:str - vintage of the data to be downloaded, e.g., if you want data corresponding to March 1, 2020 you would use "2020-03-01"
        check_frequency:float - delay (in seconds) between successive checks of the status of the download, can be lowered for faster responses for small collections.
    Returns:
        collection_download_link:str - link to S3 URL of the downloaded collection
    """

    validate_inputs(cxy_api_key, collection_type, cache_time)    
    print(f"""Preparing collection download with inputs:
        {collection_id=}
        {collection_type=}
        {cache_time=}
        """)

    ## GET THE APPROPRIATE API REQUEST URLS FOR COLLECTION TYPE
    records_url = check_url = new_download_url = ''
    if collection_type == 'chain':
        records_url = f'https://location.chainxy.com/api/Downloads?Query=%7B%22ChainListId%22:{collection_id},%22ReportType%22:[0],%22Status%22:[0,1]%7D&OrderBy=-CreateDate'
        check_url = f'https://location.chainxy.com/api/ChainLists/{collection_id}'
        new_download_url = f"https://location.chainxy.com/api/ChainLists/Download/{collection_id}"
        default_url_params = {
            "format": "CSV",
            "splitLayers": False,
        }

    elif collection_type == 'center':
        records_url = f'https://location.chainxy.com/api/Downloads?Query=%7B%22SiteListId%22:{collection_id},%22ReportType%22:[4]%7D&OrderBy=-CreateDate'
        check_url = f'https://location.chainxy.com/api/SiteLists/{collection_id}'
        new_download_url =  f'https://location.chainxy.com/api/SiteLists/Download/{collection_id}'
        default_url_params = {
            "format": "ZIP_CSV"
        }
    url_params = url_params if url_params else default_url_params

    if data_date:
        url_params['dataDate'] = data_date
    records = json.loads(request_api(records_url, cxy_api_key).text)['Records']

    # IF A DOWNLOAD RECORD DOES NOT EXIST, CHECK IF THE COLLECTION EXISTS WITH 0 DOWNLOADS AND CREATE ITS FIRST DOWNLOAD;
    # OTHERWISE, IF THE COLLECTION DOESN'T EXIST THE PROGRAM WILL RAISE A ValueError
    if not records:
        if check_record_exists(check_url, cxy_api_key): 
            print(f"A record of collection {collection_id} exists with 0 downloads. Starting a new download...")
            collection_download_id = create_new_download(new_download_url, cxy_api_key, url_params)
            collection_download_link = get_download_link(collection_download_id, cxy_api_key, check_frequency)
    else:
        create_date = records[0]['CreateDate']
        if is_download_stale(create_date, cache_time):
            print(f"It has been longer than {cache_time} hour(s) since the latest download of this collection. Starting new download...")
            collection_download_id = create_new_download(new_download_url, cxy_api_key, url_params)
            collection_download_link = get_download_link(collection_download_id, cxy_api_key, check_frequency)
        else:
            print(f"A download created within the last {cache_time} hour(s) exists. Retrieving record...")
            if records[0]['Status'] == 1: ## records are ordered by -CreateDate, so the first should be the latest
                collection_download_link = records[0]['Link']
            else: ## if the existing record is still pending, wait for it to finish
                print(f"The latest download (Id: {records[0]['Id']}) is still pending...") 
                collection_download_link = get_download_link(records[0]['Id'], cxy_api_key, check_frequency)
    
    print('----------------------------------------------------------------')
    print('COLLECTION DOWNLOAD URL:')
    print(collection_download_link)
    print('----------------------------------------------------------------')
    return collection_download_link

def download_file(url:str, output_file:str):
    """
    Downloads the collection file to path output_file.
    """
    if not url:
        return 

    # NOTE the stream=True parameter below
    print(f"Saving file...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(output_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)

    print(f"Saved file downloaded from:\n{url}\nto: {output_file}")
    return output_file
    
def main():
    # FILL THESE
    # your chainxy api key
    cxy_api_key = ''
    # id of the collection to download
    collection_id = 0
    # type of the collection to download ('chain' or 'center')
    collection_type = 'chain'
    # optional - the oldest a download to reuse (in hours) before creating a new download
    cache_time = 24
    #optional - overwrite default file output/export behavior; e.g., set "splitLayer":True if you want each chain to be in a separate CSV; set "DataDate":"2022-01-01" if you want to see the records as of Jan 1, 2022 (use YYYY-MM-DD format)
    url_params = {} 

    collection_download_url = download_collection(cxy_api_key, collection_id, collection_type, cache_time, url_params, check_frequency=1)
    
    # FILL THIS optional - if you want to download the file
    output_file = r""
    
    if output_file:
        output_file += ".csv" if collection_type == 'chain' else ".zip"
        download_file(collection_download_url, output_file)

    print(f"Finished request for {collection_type.title()} Collection {collection_id}.")

if __name__ == '__main__':
    main()