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


### CHANGES OVER TIME ###
def create_COT_report(cxy_api_key:str, collection_id:int, StartDate:str, EndDate:str, IncludeChangeLog:bool=True,\
                    IncludeCountByOpenStatus:bool=True, IncludeCountByCountry:bool=True, IncludeCountByState:bool=False,\
                    IncludeCountByStoreType:bool=False):
    """
    Generates a report based on the provided input parameters. Returns a URL to the report.
    cxy_api_key:str - ChainXY API Key,
    collection_id:int - ID of the collection for which a report will be generated,
    StartDate:str -  Starting point of the report (YYYY-MM-DD),
    EndDate:str - End point of the report (YYYY-MM-DD),
    IncludeChangeLog:bool - Choose whether to include a Change Log. A Change Log (the third sheet on
        the report) will create a list of all the chain locations that have been added
        and removed within the selected time frame.
    IncludeCountByOpenStatus:bool - Do you want a break down by chain status? Summary Stats will break out 
        the changes by chains by open status of open, coming soon, or closed, 
    IncludeCountByCountry:bool - Do you want a count of stores for each country?, 
    IncludeCountByState:bool - Do you want a count of stores for each state?, 
    IncludeCountByStoreType:bool - Do you want a count of stores for each store type? 
        Summary Stats are represented by the changes in each individual type of store 
        available. For example, an apparel chain may have store types which include Seasonal, popup, outlet, etc.
    """

    check_api_key(cxy_api_key)
    headers = {'x-apikey': cxy_api_key,
            'x-Application': 'Python API Call',
            'content-type': 'application/json'}

    apiUrl = "https://location.chainxy.com/api/ChainLists/UpdatesDiffReport/{}?format=XLSX"
    params = {
        "StartDate": StartDate, 
        "EndDate": EndDate, 
        "IncludeChangeLog": IncludeChangeLog, 
        "IncludeCountByOpenStatus": IncludeCountByOpenStatus,
        "IncludeCountByCountry": IncludeCountByCountry, 
        "IncludeCountByState": IncludeCountByState, 
        "IncludeCountByStoreType": IncludeCountByStoreType
        }
   
    r = requests.post(url=apiUrl.format(collection_id), data=json.dumps(params), headers=headers)
    r_body = json.loads(r.text)
    downloadId = r_body['Id']
    downloadLink = False
    generatedReportLink = None

    while downloadLink == False:
        print(f"Checking for status of generated report {downloadId}...")
        apiUrl = 'https://location.chainxy.com/api/ChainListDownloads/{}'.format(downloadId)
        r = requests.get(url=apiUrl, headers=headers)
        r_body = json.loads(r.text)['Record']

        if r_body['Status'] == 0:
            print(f"Download URL for {collection_id} is still generating")
            time.sleep(30)

        elif r_body['Status'] == 2:
            print(r_body)
            print(f"Report URL generation failed. Speak to ChainXY for assistance")
            downloadLink = True

        elif r_body['Status'] == 1:
            print(f"Report URL generation completed!")
            downloadLink = True
            generatedReportLink = r_body['Link']
        
    print('----------------------------------------------------------------')
    print('REPORT URL:')
    print(generatedReportLink)
    print('----------------------------------------------------------------')
    return generatedReportLink

### NEAREST REPORT ###
def create_Nearest_report(cxy_api_key:str, targetCollectionId:int, sourceChainIds:list, n:int, aggregate:bool=True):
    """
    Generates a report based on the provided input parameters. Returns a URL to the report.
    cxy_api_key:str - ChainXY API Key,
    targetCollectionId:int - ID of the collection you would like to perform the Nearest Report on,
    sourceChainIds:list - list of chainids to be used as the source
    n:int - Specifies the number of nearest locations you are interested in
        measuring to.
        Note: For chains with higher geographic density, selecting 2nd or 3rd
        closest locations may provide a more thorough analysis.
    aggregate:bool When turned on, all locations from the Target Collection are treated as
        equal. In other words, the report will find the number of nearest
        locations of everything within the target collection.
    """

    check_api_key(cxy_api_key)
    headers = {'x-apikey': cxy_api_key,
            'x-Application': 'Python API Call',
            'content-type': 'application/json'}

    apiUrl = 'https://location.chainxy.com/api/ChainLists/NearestReport/{}?format=CSV' ## target
    if len(sourceChainIds) == 1:
        sources = sourceChainIds[-1]
    else:
        raise Exception("More than 1 source ChainId for the Nearest Neighbor report is not advisable.")
        
    params = {
        "Aggregate": aggregate, 
        "InputChainId": sources,
        "N": n
        }
   
    r = requests.post(url=apiUrl.format(targetCollectionId), data=json.dumps(params), headers=headers)
    r_body = json.loads(r.text)
    downloadId = r_body['Id']
    downloadLink = False
    generatedReportLink = None

    while downloadLink == False:
        print(f"Checking for status of generated report {downloadId}...")
        apiUrl = 'https://location.chainxy.com/api/ChainListDownloads/{}'.format(downloadId)
        r = requests.get(url=apiUrl, headers=headers)
        r_body = json.loads(r.text)['Record']

        if r_body['Status'] == 0:
            print(f"Download URL for {targetCollectionId} is still generating")
            time.sleep(30)

        elif r_body['Status'] == 2:
            print(r_body)
            print(f"Report URL generation failed. Speak to ChainXY for assistance")
            downloadLink = True

        elif r_body['Status'] == 1:
            print(f"Report URL generation completed!")
            downloadLink = True
            generatedReportLink = r_body['Link']
        
    print('----------------------------------------------------------------')
    print('REPORT URL:')
    print(generatedReportLink)
    print('----------------------------------------------------------------')
    return generatedReportLink
    
### VOID ANALYSIS ###
def create_VA_report(cxy_api_key:str, targetCollectionId:int, rad:int, AdminLevel:int, lat:float, lng:float, Categorization:str, Label:str):
    """
    Generates a report based on the provided input parameters. Returns a URL to the report.
    cxy_api_key:str - ChainXY API Key,
    targetCollectionId:int - Collection ID that includes chains to look for which are closest to the source(s),
    rad:int - This radius will determine the distance in miles from the centroid of the
        trade area to the extent of the circular boundary. The trade area radius
        should represent the necessary area for chains within your collection to
        operate.
    AdminLevel:int - The compare to geography, or benchmark, is the geography or
        geographies which are being used to compare the trade area to. This
        geography will be larger than the trade area and should approximate a
        homogenous potential market for the chains in this report. 
        1: Country, 2: State/Province/Region, 3: CBSA/CMA, 4: County (USA), 5: DMA (USA)
    Lat/Lng:float - center of search radius
    Categorization:str - Choose one from: Category, NAICS, or SIC
    Label - file name of report
    """

    check_api_key(cxy_api_key)
    headers = {'x-apikey': cxy_api_key,
            'x-Application': 'Python API Call',
            'content-type': 'application/json'}

    apiUrl = 'https://location.chainxy.com/api/ChainLists/VoidAnalysisReport/{}?format=CSV' ## target
        
    params = {
    "SearchRadius": rad, # Radiu s (in miles) around the provided Lat/Long to search - Trade Area. 
    "AdminLevel": str(AdminLevel), #which admin level to compare the Trade Area to. 1: Country, 2: State/Province, 3: CBSA/CMA, 4: County (USA), 5: DMA (USA)
    "TargetLocation": {
        "Latitude": lat,
        "Longitude": lng
    },
    "Label": Label,  #Title of the report
    "Categorization": Categorization #Category, SIC, or NAICS
    }
   
    r = requests.post(url=apiUrl.format(targetCollectionId), data=json.dumps(params), headers=headers)
    r_body = json.loads(r.text)
    downloadId = r_body['Id']
    downloadLink = False
    generatedReportLink = None

    while downloadLink == False:
        print(f"Checking for status of generated report {downloadId}...")
        apiUrl = 'https://location.chainxy.com/api/ChainListDownloads/{}'.format(downloadId)
        r = requests.get(url=apiUrl, headers=headers)
        r_body = json.loads(r.text)['Record']

        if r_body['Status'] == 0:
            print(f"Download URL for {targetCollectionId} is still generating")
            time.sleep(30)

        elif r_body['Status'] == 2:
            print(r_body)
            print(f"Report URL generation failed. Speak to ChainXY for assistance")
            downloadLink = True

        elif r_body['Status'] == 1:
            print(f"Report URL generation completed!")
            downloadLink = True
            generatedReportLink = r_body['Link']
        
    print('----------------------------------------------------------------')
    print('REPORT URL:')
    print(generatedReportLink)
    print('----------------------------------------------------------------')
    return generatedReportLink

def main():
    # FILL THESE
    # your chainxy api key
    cxy_api_key = ''
    
    ## Type of Report (COT - Changes Over Time, NN - Nearest Neighbor, VA - Void Analysis)
    report = 'VA'

    if report == 'COT': ## Changes-Over-Time
        collection_id = 0
        StartDate = '2022-09-01'  #YYYY-MM-DD
        EndDate = '2022-09-30' 
        create_COT_report(cxy_api_key, collection_id, StartDate, EndDate)

    elif report == 'NN': ## Nearest Neighbor
        targetCollectionId = 0
        sourceChainId = [0] # target chain 
        n = 1
        create_Nearest_report(cxy_api_key, targetCollectionId, sourceChainId, n)

    elif report == 'VA': ## Void Analysis
        targetCollectionId = 0
        SearchRadius = 10 #miles 
        AdminLevel = 1
        Latitude = 0
        Longitude = 0
        Label = ""
        Categorization = ""
        create_VA_report(cxy_api_key, targetCollectionId, rad=SearchRadius, AdminLevel=AdminLevel, lat=Latitude,\
                        lng=Longitude, Label=Label, Categorization=Categorization)

if __name__ == '__main__':
    main()