# AUTHOR: Andy Nguyen
# FIXED BY: Andy Nguyen 09/21/22
# FIX: Add main controller, new functions
# This script sample allows you to download all scrape updates for individual chains and prints out a url in console
import requests
import json
import time

# This is used for api calls with headers set in each function along with the api key being passed from main
def check_api_key(cxy_api_key):
    
    url = 'https://location.chainxy.com/api/Users/Me'
    headers = {'x-apikey': cxy_api_key,
            'x-Application': 'Python API Call',
            'content-type': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 401:
        raise ValueError("Bad ChainXY API key provided, double-check the provided value!")

def generate_updates_list(cxy_api_key:str, chain_id:int):
    """
    Returns a record list of chainxy scrape updates based on the provided chain_id from the main controller
    Params: Used to query out chain_id from api-caller
    cxy_api_key:str - ChainXY API Key
    chains_id:int - ID of the chain for which all the update ids will be returned.
    """
    
    check_api_key(cxy_api_key)
    
    headers = {'x-apikey': cxy_api_key,
        'x-Application': 'Python API Call',
        'content-type': 'application/json'}
    
    apiUrl = "https://location.chainxy.com/api/ChainScrapes"
    
    params = {
            "fields": "Id,RunDate",
            "Query": str({"ChainId":chain_id}),
            "Limit": "100"
    }

    # Gets the data from the page and loads params and headers
    r = requests.get(url=apiUrl, params=params, headers=headers)
    r_body = json.loads(r.text)

    return r_body['Records']

def generate_downloads(cxy_api_key:str, scrape_update_list:list):
    """
    Posts downloads on the CXY platform and prints out in console the list of scrapeids and the urls 
    Params:
    cxy_api_key:str - ChainXY API Key
    scrape_update_list:list - Calls the returned list of Scapes from generate_updates_list
    """
    
    check_api_key(cxy_api_key)
    
    headers = {'x-apikey': cxy_api_key,
            'x-Application': 'Python API Call',
            'content-type': 'application/json'}

    url_params = {
        "format": "CSV",  # ZIP_CSV Also works
        "splitLayers": "false",
        # "dataDate": "2019-10-03" # OPTIONAL
    }

    data = {}
    createdScrapeFileURLs = []
    api_download_url = "https://location.chainxy.com/api/ChainScrapes/Download/"
    

    # Loops untill the end of the scape ids list and executes the post and get api calls as well as printing/returning the url to the console.
    for item in scrape_update_list:

        # Posts and creates the links on the platform here
        response = requests.post(url=api_download_url + str(item['Id']), data=json.dumps(data), params=url_params, headers=headers)
        r_body = json.loads(response.text)

        #Uses the "Id" in r_body for get request for the url link in order to print onto the console
        scrape_download_id = r_body['Id']
        print("Run Date: " + str(item['RunDate']))
        fileGenerated = False
        createdScrapeFileURL = False
        
        # While Loop checks for status downloads for each step of the way and will pause for 5 seconds while it is downloading.
        while(fileGenerated == False):
            print("Checking for status of generated file, Download Id: " + str(scrape_download_id) + "...")
            response = requests.get(url='https://location.chainxy.com/api/ChainListDownloads/{}'.format(scrape_download_id), headers=headers)
            r_body = json.loads(response.text)['Record']

            if r_body['Status'] == 0:
                print("Download Scrape ID: " + str(item['Id']) + " is still being generated")
                time.sleep(5)

            elif r_body['Status'] == 2:
                print("File generation failed. Speak to ChainXY for assistance")
                fileGenerated = True

            elif r_body['Status'] == 1:
                print("File generation completed!")
                fileGenerated = True
                createdScrapeFileURL = r_body['Link']
                createdScrapeFileURLs.append(r_body['Link']) 
                print('Download Link Here: {}'.format(createdScrapeFileURL))
                print('----------------------------------------------------------------') 
    
    return createdScrapeFileURLs

def main():
    """
    this function is used as a controller to pass the variables through the other functions and executes them
    cxy_api_key:str - Insert the generate ChainXY API Key to allow for api calls to the platform.
    chain_id:list - Choose which chain_id to pull scraping updates from.
    """

    cxy_api_key = ''
    chain_id = 0 
    
    # Calls variables and Executes Functions here
    updates_record_list = generate_updates_list(cxy_api_key, chain_id)
    scrape_download_urls = generate_downloads(cxy_api_key, updates_record_list)


if __name__ == '__main__':
    main()