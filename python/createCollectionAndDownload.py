# this script sample allows you to create a collection given a list of ChainId's
import requests
import json
import time


def check_api_key(cxy_api_key):
    url = "https://location.chainxy.com/api/Users/Me"
    headers = {
        "x-apikey": cxy_api_key,
        "x-Application": "Python API Call",
        "content-type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 401:
        raise ValueError(
            "Bad ChainXY API key provided, double-check the provided value!"
        )


def generate_collection(cxy_api_key: str, collection_params: dict = {}):
    """
    Generates a ChainXY collection based on the provided input parameters. This function does not download a generated collection.
    cxy_api_key:str - ChainXY API Key
    collection_params: dict - definition of the collection, including chain and geographic filters.
    """
    check_api_key(cxy_api_key)

    headers = {
        "x-apikey": cxy_api_key,
        "x-Application": "Python API Call",
        "content-type": "application/json",
    }

    apiUrl = "https://location.chainxy.com/api/ChainLists"
    chains = collection_params.get("Chains")
    chains_query = collection_params.get("ChainsQuery")
    admin_levels = collection_params.get("AdminLevels")

    if admin_levels:
        collection_params["AdminLevels"] = []
        for id in admin_levels:
            if isinstance(id, int):
                collection_params["AdminLevels"].append({"Id": id})
            else:
                raise ValueError("Admin Level ids must be integers.")
    if chains_query:
        collection_params["ChainsQuery"] = json.dumps(
            chains_query, separators=(",", ":")
        )
    if chains and chains_query:
        raise ValueError(
            f"The list of chains and a chains query can't be both specified at once. Current values: {chains=}, {chains_query=}"
        )

    # i.e. include all chains
    if not chains and not chains_query:
        collection_params["ChainsQuery"] = "{}"

    print("generatng a colleciton...")
    response = requests.post(url=apiUrl, json=collection_params, headers=headers)
    r_body = response.json()

    created_collection_id = r_body["Id"]

    print(f"Generated Collection ID: {created_collection_id}")
    return created_collection_id


def download_collection(
    cxy_api_key: str,
    collection_id: int,
    data_date: str = None,
    check_frequency: float = 1,
):
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
    headers = {
        "x-apikey": cxy_api_key,
        "x-Application": "Python API Call",
        "content-type": "application/json",
    }

    url_params = {
        "format": "CSV",
        "splitLayers": "false",
    }
    if data_date:
        url_params["dataDate"] = data_date
    api_download_url = "https://location.chainxy.com/api/ChainLists/Download/"

    response = requests.post(
        url=api_download_url + str(collection_id), params=url_params, headers=headers
    )
    r_body = response.json()

    collection_download_id = r_body["Id"]
    # BECAUSE THE DOWNLOADED FILES MAY TAKE A FEW MINUTES TO GENERATE, WE DO A CHECK EVERY FEW SECONDS TO SEE IF IT HAS FINISHED GENERATING.
    # ONCE YOU HAVE A URL FROM THE CHAINLISTDOWNLOADS ENDPOINT, THEN YOU'RE GOOD TO GO AND CAN DO WHATEVER YOU NEED WITH THAT FILE

    fileGenerated = False
    createdCollectionFileURL = False

    while fileGenerated == False:
        print(
            f"Checking for status of generated file for Download Id: {str(collection_download_id)}"
        )
        response = requests.get(
            url=f"https://location.chainxy.com/api/Downloads/{collection_download_id}",
            headers=headers,
        )
        r_body = response.json()["Record"]

        if r_body["Status"] == 0:
            print("Download " + str(collection_id) + " is still generating")
            time.sleep(check_frequency)

        elif r_body["Status"] == 2:
            print("File generation failed. Speak to ChainXY for assistance")
            fileGenerated = True

        elif r_body["Status"] == 1:
            print("File generation completed!")
            fileGenerated = True
            createdCollectionFileURL = r_body["Link"]
    print("----------------------------------------------------------------")
    print("COLLECTION DOWNLOAD URL:")
    print(createdCollectionFileURL)
    print("----------------------------------------------------------------")
    return createdCollectionFileURL


def download_file(url: str, output_file: str):
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(output_file, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)

    print(f"Saved {url}\nto\n{output_file}")
    return output_file


def main():
    # FILL THESE
    # your chainxy api key
    cxy_api_key = ""

    # name of the collection
    collection_label = ""
    # optional comments included in the collection description
    comments = ""
    # uncomment params to override default preferences of your account. You can update the defaults on your user page.
    collection_params = {
        "Label": collection_label,
        "AdminLevels": [],  # list of geographic entity ids e.g., [20982, 20803] to include US, Canada -- see https://location.chainxy.com/AdminLevel for ids of individual countries/states etc.
        "Comments": comments,
        # "IncludeComingSoon": True,
        # "IncludeClosed": True,
        # "IncludePast": False,
        # "IncludeDistributors": True,
        # "IncludeSubChains": True,
        # "IncludeDeprecatedChains": True,
        # "IncludeClosedChains": True,
        # "IncludePOI": False
    }
    # Specify the chains that will be included in the collection:
    # either a list of chain_ids
    # OR a ChainsQuery object. Refer to https://github.com/ChainXY/ChainXY_API?tab=readme-ov-file#query-parameters for information about the consruction of a valid Query object.
    # chain_ids = []
    # collection_params["Chains"] = [{"Id": id} for id in chain_ids]
    collection_params["ChainsQuery"] = (
        {}
    )  # a valid ChainsQuery object, containing a filter for selection of chains, e.g., to select Groceries & QSRs: {"Categories":{"Id":[154,180]}}; to select all chains leave blank {}

    data_date = ""  # date formated as YYYY-MM-DD for vintage of the data
    check_frequency = 1  # how often the download status is checked, lower the value for smaller collections. smallest collections generate in <0.5 seconds.
    collection_id = generate_collection(cxy_api_key, collection_params)
    collection_download_url = download_collection(
        cxy_api_key, collection_id, data_date, check_frequency
    )  # can pass the URL directly to pandas to read the csv

    # output_file = r""
    # download_file(collection_download_url, output_file)


if __name__ == "__main__":
    main()
