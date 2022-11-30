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
    

def generate_collection(cxy_api_key:str, chain_ids:list, collection_label:str, comments:str = '', IncludeComingSoon:bool = True,\
    IncludeClosed:bool = True, IncludeDistributors:bool = True, IncludeSubChains:bool = True, IncludeDeprecatedChains:bool = True,\
    IncludeClosedChains:bool = True, IncludePOI:bool = True):
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

    formatted_chain_ids = []
    for id in chain_ids:
        formatted_chain_ids.append({"Id":id})

    apiUrl = "https://location.chainxy.com/api/ChainLists"
    params = {
        "Label": collection_label,
        "Chains": formatted_chain_ids,
        "AdminLevels": [],
        "Comments": comments,
        "IncludeComingSoon": IncludeComingSoon,
        "IncludeClosed": IncludeClosed,
        "IncludeDistributors": IncludeDistributors,
        "IncludeSubChains": IncludeSubChains,
        "IncludeDeprecatedChains": IncludeDeprecatedChains,
        "IncludeClosedChains": IncludeClosedChains,
        "IncludePOI": IncludePOI
    }
    #i.e. include all chains
    if not formatted_chain_ids:
        params["ChainsQuery"] = "{}"
    
    print('STARTING...')
    response = requests.post(url=apiUrl, data=json.dumps(params), headers=headers)
    r_body = json.loads(response.text)

    created_collection_id = r_body['Id']

    print(f'Generated Collection ID: {created_collection_id}')
    return created_collection_id

def download_collection(cxy_api_key:str, collection_id:int):
    """
    Downloads a chainxy collection based on the provided collection ID.
    Params:
    cxy_api_key:str - ChainXY API Key
    collection_id:str - ID of the collection for which a new download will be initiated.
    """
    
    check_api_key(cxy_api_key)
    
    # THIS SECTION CREATES THE DOWNLOAD REQUEST
    headers = {'x-apikey': cxy_api_key,
            'x-Application': 'Python API Call',
            'content-type': 'application/json'}

    url_params = {
        "format": "CSV",  # ZIP_CSV Also works
        "splitLayers": "false",
        # "dataDate": "2019-10-03" # OPTIONAL
    }
    data = {}
    api_download_url = "https://location.chainxy.com/api/ChainLists/Download/"

    response = requests.post(url=api_download_url + str(collection_id), data=json.dumps(data), params=url_params, headers=headers)
    r_body = json.loads(response.text)

    collection_download_id = r_body['Id']
    # BECAUSE THE DOWNLOADED FILES MAY TAKE A FEW MINUTES TO GENERATE, WE DO A CHECK EVERY FEW SECONDS TO SEE IF IT HAS FINISHED GENERATING.
    # ONCE YOU HAVE A URL FROM THE CHAINLISTDOWNLOADS ENDPOINT, THEN YOU'RE GOOD TO GO AND CAN DO WHATEVER YOU NEED WITH THAT FILE

    fileGenerated = False
    createdCollectionFileURL = False
    
    while(fileGenerated == False):
        print("Checking for status of generated file " + str(collection_download_id) + "...")
        response = requests.get(url='https://location.chainxy.com/api/ChainListDownloads/{}'.format(collection_download_id), headers=headers)
        r_body = json.loads(response.text)['Record']

        if r_body['Status'] == 0:
            print("Download " + str(collection_id) + " is still generating")
            time.sleep(5)

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
    
    # proposed name of the collection
    collection_label = ''
    # integers (comma separated), list of chain ids to create the collection from, leave empty for all chains
    chain_ids = []
    # not mandatory: comments
    comments = ''
    collection_id = generate_collection(cxy_api_key, chain_ids, collection_label)
    collection_download_url = download_collection(cxy_api_key, collection_id)
    
    output_file = r""
    download_file(collection_download_url, output_file)


if __name__ == '__main__':
    main()