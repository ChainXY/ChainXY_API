#this script sample allows you to create a collection given a list of ChainId's
import requests
import json
import time
from datetime import datetime

def request_api(url:str, headers:str, method='GET', params=None, data={}):
    """
    Handles making requests to the ChainXY API and returns the response.
    """
    r = requests.request(url=url, method=method, headers=headers, params=params, data=data)
    if r.status_code == 401:
        raise ValueError("Bad ChainXY API key provided, please double-check the input value!")
    elif r.status_code != 200 and 'does not correspond to a collection' in r.text.lower():
        print("The collection does not exist in the database.")
        r = None
    else:
        return r

def validate_inputs(headers:str, cxy_api_key:str, collection_type:str, cache_time:int):
    """
    Verifies that a given API key is valid for making requests to the API and checks that the collection download
    inputs are valid for processing.
    """
    url = 'https://location.chainxy.com/api/Users/Me'
    r = request_api(url=url, headers=headers)
    if not isinstance(collection_type, str) or collection_type.lower() not in ['chain', 'center']:
        raise ValueError(f"Collection type '{collection_type}' must be one of ['chain', 'center'].")
    
    if cache_time < 0:
        raise ValueError("Please enter a valid duration for cache_time that is an int > 0.")

def get_collection_urls(collection_id:str, collection_type:str):
    """
    Returns URLs and url params for requesting the ChainXY API for collection records based on collection_type.
    """
    records_url = check_url = new_download_url = ''

    if collection_type == 'chain':
        
        records_url = f'https://location.chainxy.com/api/Downloads?fields=Id,ChainList,Label,User,ReportType,CreateDate,DataDate,Status,Format,Count,Link,DisplayValue,&Query=%7B%22ChainListId%22:{collection_id}%7D&OrderBy=-CreateDate'
        check_url = f'https://location.chainxy.com/api/ChainLists/{collection_id}'
        new_download_url = f"https://location.chainxy.com/api/ChainLists/Download/{collection_id}"

        url_params = {
            "format": "CSV",  # ZIP_CSV also works
            "splitLayers": "false",
            # "dataDate": "2019-10-03" # OPTIONAL
        }

    elif collection_type == 'center':
        
        records_url = f'https://location.chainxy.com/api/Downloads?fields=Id,SiteList,Label,User,ReportType,CreateDate,DataDate,Status,Format,Count,Link,DisplayValue,&Query=%7B%22SiteListId%22:{collection_id}%7D&OrderBy=-CreateDate'
        check_url = f'https://location.chainxy.com/api/SiteLists/{collection_id}'
        new_download_url =  f'https://location.chainxy.com/api/SiteLists/Download/{collection_id}'

        url_params = {
            "format": "ZIP_CSV"
        }
    
    return records_url, check_url, new_download_url, url_params

def retrieve_new_download(create_date, cache_time:int):
    """
    Returns true if a new download should be created. 
    """
    dt = datetime.strptime(create_date, '%Y-%m-%dT%H:%M:%S.%f')
    now = datetime.utcnow()
    td = (abs(dt - now)).total_seconds()/3600
    return td > cache_time
    
def check_record_exists(url:str, headers:str):
    """
    Returns true if a record of the collection exists in the database.
    """
    r = request_api(url=url, headers=headers)
    result = json.loads(r.text)
    if 'Message' in result:
        if 'record does not exist' in result['Message'].lower():
            print("No collection found. Please ensure you have the correct collection ID and collection Type.")
            return False
    
    if r.status_code == 200:
        return True

def create_new_download(new_download_url:str, headers:str, params:str):
    """
    Begins a new download of a collection and returns the download Id.
    """
    r = request_api(url=new_download_url, headers=headers, method='POST', params=params)
    r_body = json.loads(r.text)
    return r_body['Id']

def generate_download(collection_download_id:int, headers:str):
    """
    Checks and waits for a download to finish before returning the URL of the collection file.
    """
    file_generated = False
    collection_download_link = False
    
    print(f"Checking for status of downloaded file...")
    
    while(file_generated == False):
        
        r = request_api(url=f'https://location.chainxy.com/api/Downloads/{collection_download_id}', headers=headers)
        r_body = json.loads(r.text)['Record']

        if r_body['Status'] == 0:
            print(f"Download {str(collection_download_id)} is still generating...")
            time.sleep(5)

        elif r_body['Status'] == 2:
            print("File generation failed. Please reach out to ChainXY support for assistance.")
            file_generated = True

        elif r_body['Status'] == 1:
            print("File generation completed!")
            file_generated = True
            collection_download_link = r_body['Link']
    
    return collection_download_link

def download_collection(cxy_api_key:str, collection_id:int, collection_type:str, cache_time:int = 24):
    """
    Downloads a collection based on the provided collection ID and collection type. An optional input cache_time determines if a new download should be made.
    Params:
        cxy_api_key:str - ChainXY API Key
        collection_id:str - ID of the collection for which a new download will be initiated.
        collectiontype:str - 'chain' or 'center' collection
        cache_time:int - max. time in hours since the latest download before a new one is requested
    Returns:
        collection_download_link:str - link to S3 URL of the downloaded collection
    """

    # FOR MAKING REQUESTS TO THE API
    headers = {
        'x-apikey': cxy_api_key,
        'x-Application': 'Python API Call',
        'content-type': 'application/json'
        }

    validate_inputs(headers, cxy_api_key, collection_type, cache_time)    

    records_url, check_url, new_download_url, url_params = get_collection_urls(collection_id, collection_type)
    
    records = json.loads(request_api(records_url, headers).text)['Records']

    # IF A RECORD DOES NOT EXIST, CHECK IF THE COLLECTION EXISTS WITH 0 DOWNLOADS AND CREATE A NEW ONE;
    # OTHERWISE, THERE IS NO DOWNLOAD TO BE MADE
    if not records:
        if check_record_exists(check_url, headers): 
            print(f"A record of collection {collection_id} exists with 0 downloads. Starting a new download...")
            collection_download_id = create_new_download(new_download_url, headers, url_params)
            collection_download_link = generate_download(collection_download_id, headers)
        else:
            print(f"Collection Id: {collection_id}, Collection Type: {collection_type}")
            return ''
    else:
        create_date = records[0]['CreateDate']
        if retrieve_new_download(create_date, cache_time):
            print(f"It has been longer than {cache_time} hour(s) since the latest download of this collection. Starting a new download...")
            collection_download_id = create_new_download(new_download_url, headers, url_params)
            collection_download_link = generate_download(collection_download_id, headers)
        else:
            print(f"A download created within the last {cache_time} hour(s) exists. Retrieving record...")
            if records[0]['Status'] == 1: ## records are ordered by -CreateDate, so the first should be the latest
                collection_download_link = records[0]['Link']
            else: ## if the existing record is still pending, wait for it to finish
                print(f"The latest download (Id: {records[0]['Id']}) is still pending...") 
                collection_download_link = generate_download(records[0]['Id'], headers)
    
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

    print(f"Saved to: {output_file}")
    return output_file
    
def main():
    # FILL THESE
    # your chainxy api key
    cxy_api_key = ''
    # id of the collection to download
    collection_id = 234166
    # type of the collection to download ('chain' or 'center')
    collection_type = 'chain'
    # optional - the oldest a download can be (in hours) before creating a new download
    cache_time = 1
    collection_download_url = download_collection(cxy_api_key, collection_id, collection_type, cache_time)
    
    # optional - if you want to download the file
    output_file = r""
    if output_file:
        output_file += ".csv" if collection_type == 'chain' else ".zip"
        download_file(collection_download_url, output_file)

    print(f"Finished {collection_type.title()} Collection {collection_id}.")

if __name__ == '__main__':
    main()