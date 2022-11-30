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
    # id of the collection to download
    collection_id = 0
    collection_download_url = download_collection(cxy_api_key, collection_id)
    
    # optional - if you want to download the file
    output_file = r""
    download_file(collection_download_url, output_file)


if __name__ == '__main__':
    main()