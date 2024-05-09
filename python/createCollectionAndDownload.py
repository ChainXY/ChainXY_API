#this script sample allows you to create a collection given a list of ChainId's
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
    

def generate_collection(cxy_api_key:str, collection_params:dict = {}):
    """
    Generates a ChainXY collection based on the provided input parameters. This function does not download a generated collection.
    cxy_api_key:str - ChainXY API Key
    chain_ids:list - comma-separated list of chain ids to be included in the download, leave empty for all chains
    collection_label:str - name of the generated collection
    comments:str - additional comments that will be added to a collection
    IncludeComingSoon:bool - do you want to include Coming Soon locations?
    IncludeClosed:bool - do you want to include locations labelled as Closed?
    IncludeDistributors:bool - - do you want to include Distributor locations?
    IncludeSubChains:bool - do you want to include SubChains? e.g. for Walmart, do you want to include Walmart Gas Stations?
    IncludeDeprecatedChains:bool - do you want to include Chains that are no longer updated?
    IncludeClosedChains:bool - do you want to include Chains that are closed?
    IncludePOI:bool - do you want to include Points of Interest datasets?
    """

    check_api_key(cxy_api_key)
    
    headers = {'x-apikey': cxy_api_key,
            'x-Application': 'Python API Call',
            'content-type': 'application/json'}


    apiUrl = "https://location.chainxy.com/api/ChainLists"
    #i.e. include all chains
    if not collection_params['Chains'] and not collection_params["ChainsQuery"]:
        collection_params["ChainsQuery"] = "{}"
    
    print('STARTING...')
    response = requests.post(url=apiUrl, data=json.dumps(collection_params), headers=headers)
    r_body = json.loads(response.text)

    created_collection_id = r_body['Id']

    print(f'Generated Collection ID: {created_collection_id}')
    return created_collection_id

def download_collection(cxy_api_key:str, collection_id:int, data_date:str = None, check_frequency:float=1):
    """
    Downloads a chainxy collection based on the provided collection ID.
    Params:
    cxy_api_key:str - ChainXY API Key
    collection_id:str - ID of the collection for which a new download will be initiated.
    data_date:str - vintage of the data to be downloaded, e.g., if you want data corresponding to March 1, 2020 you would use "2020-03-01"
    check_frequency:float - delay (in seconds) between successive checks of the status of the download, can be lowered for faster responses for small collections.
    """
    
    check_api_key(cxy_api_key)
    
    # THIS SECTION CREATES THE DOWNLOAD REQUEST
    headers = {'x-apikey': cxy_api_key,
            'x-Application': 'Python API Call',
            'content-type': 'application/json'}

    url_params = {
        "format": "CSV",
        "splitLayers": "false",
    }
    if data_date:
        url_params['dataDate'] = data_date
    api_download_url = "https://location.chainxy.com/api/ChainLists/Download/"

    response = requests.post(url=api_download_url + str(collection_id), params=url_params, headers=headers)
    r_body = json.loads(response.text)

    collection_download_id = r_body['Id']
    # BECAUSE THE DOWNLOADED FILES MAY TAKE A FEW MINUTES TO GENERATE, WE DO A CHECK EVERY FEW SECONDS TO SEE IF IT HAS FINISHED GENERATING.
    # ONCE YOU HAVE A URL FROM THE CHAINLISTDOWNLOADS ENDPOINT, THEN YOU'RE GOOD TO GO AND CAN DO WHATEVER YOU NEED WITH THAT FILE

    fileGenerated = False
    createdCollectionFileURL = False
    
    while(fileGenerated == False):
        print("Checking for status of generated file " + str(collection_download_id) + "...")
        response = requests.get(url='https://location.chainxy.com/api/Downloads/{}'.format(collection_download_id), headers=headers)
        r_body = json.loads(response.text)['Record']

        if r_body['Status'] == 0:
            print("Download " + str(collection_id) + " is still generating")
            time.sleep(check_frequency)

        elif r_body['Status'] == 2:
            print("File generation failed. Speak to ChainXY for assistance")
            fileGenerated = True

        elif r_body['Status'] == 1:
            print("File generation completed!")
            fileGenerated = True
            createdCollectionFileURL = r_body['Link']
    print('----------------------------------------------------------------')
    print('COLLECTION DOWNLOAD URL:')
    print(createdCollectionFileURL)
    print('----------------------------------------------------------------')
    return createdCollectionFileURL

def download_file(url:str, output_file:str):
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(output_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)

    print(f"Saved {url}\nto\n{output_file}")
    return output_file
    
def main():
    # FILL THESE
    # your chainxy api key
    cxy_api_key = ''
    
    # name of the collection
    collection_label = ''
    # integers (comma separated), list of chain ids to create the collection from, leave empty for all chains
    chain_ids = []
    # optional comments included in the collection description
    comments = ''
    #uncomment params to override default preferences of your account. You can update the defaults on your user page.
    collection_params = {
        "Label": collection_label,
        "AdminLevels": [], #list of geographic filters formatted as [{"Id":20982}] -- see https://location.chainxy.com/AdminLevel for ids of individual countries/states etc.
        "Comments": comments,
        "Chains": [{"Id":id} for id in chain_ids], #comment out the key if you want to include all chains; alternatively use ChainsQuery key to define a filter. See usage based on API calls made through the UI.
        #"IncludeComingSoon": True,
        #"IncludeClosed": True,
        #"IncludePast": False,
        #"IncludeDistributors": True,
        #"IncludeSubChains": True,
        #"IncludeDeprecatedChains": True,
        #"IncludeClosedChains": True,
        #"IncludePOI": False
    }
    data_date = "" #date formated as YYYY-MM-DD for vintage of the data
    check_frequency = 1 #how often the download status is checked, lower the value for smaller collections. smallest collections generate in <0.5 seconds.
    collection_id = generate_collection(cxy_api_key, collection_params)
    collection_download_url = download_collection(cxy_api_key, collection_id, data_date, check_frequency) # can pass the URL directly to pandas to read the csv
    
    #output_file = r""
    #download_file(collection_download_url, output_file)


if __name__ == '__main__':
    main()