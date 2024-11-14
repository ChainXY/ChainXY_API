import requests
import re
import json
import time
from datetime import datetime, timedelta


def check_api_key(cxy_api_key):
    """
    Validate the ChainXY API key.
    """
    url = "https://location.chainxy.com/api/Users/Me"
    headers = {
        "x-apikey": cxy_api_key,
        "x-application": "Python API Call",
        "content-type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 401:
        raise ValueError(
            "Bad ChainXY API key provided, double-check the provided value!"
        )


def format_as_date(dt):
    return dt.strftime("%Y-%m-%d")


def download_changes_over_time_report(cxy_api_key, collection_id, report_params):
    """
    Download the Changes Over Time (COT) report based on the provided parameters.
    """
    check_api_key(cxy_api_key)
    headers = {
        "x-apikey": cxy_api_key,
        "x-application": "Python API Call",
        "content-type": "application/json",
    }

    api_url = f"https://location.chainxy.com/api/ChainLists/ChangesOverTimeReport/{collection_id}?format=XLSX"
    response = requests.post(
        url=api_url, data=json.dumps(report_params), headers=headers
    )
    response.raise_for_status()
    response_body = json.loads(response.text)
    download_id = response_body["Id"]
    return check_report_status(cxy_api_key, download_id)


def download_nearest_report(cxy_api_key, report_params):
    """
    Download the Nearest Neighbor (NN) report based on the provided parameters.
    """
    check_api_key(cxy_api_key)
    headers = {
        "x-apikey": cxy_api_key,
        "x-application": "Python API Call",
        "content-type": "application/json",
    }

    api_url = f"https://location.chainxy.com/api/ChainLists/NearestReport?format=CSV"
    response = requests.post(
        url=api_url, data=json.dumps(report_params), headers=headers
    )
    response.raise_for_status()
    download_id = response.json()["Id"]
    return check_report_status(cxy_api_key, download_id)


def download_void_analysis_report(cxy_api_key, report_params):
    """
    Download the Void Analysis (VA) report based on the provided parameters.
    """
    check_api_key(cxy_api_key)
    headers = {
        "x-apikey": cxy_api_key,
        "x-application": "Python API Call",
        "content-type": "application/json",
    }

    api_url = f"https://location.chainxy.com/api/ChainLists/VoidAnalysisReport/{target_collection_id}?format=CSV"
    response = requests.post(
        url=api_url, data=json.dumps(report_params), headers=headers
    )
    response.raise_for_status()
    download_id = response.json()["Id"]
    return check_report_status(cxy_api_key, download_id)


def check_report_status(cxy_api_key, download_id, check_interval_seconds=5):
    """
    Check the status of a report generation and return the report download URL.
    """
    headers = {
        "x-apikey": cxy_api_key,
        "x-application": "Python API Call",
        "content-type": "application/json",
    }

    download_link = False
    generated_report_link = None

    while not download_link:
        status_url = f"https://location.chainxy.com/api/Downloads/{download_id}"
        response = requests.get(url=status_url, headers=headers)
        record = json.loads(response.text)["Record"]

        if record["Status"] == 0:
            print(f"Download for report {download_id} is still generating.")
            time.sleep(check_interval_seconds)
        elif record["Status"] == 2:
            print(record)
            print("Report generation failed. Contact ChainXY for assistance.")
            download_link = True
        elif record["Status"] == 1:
            print("Report generation completed!")
            download_link = True
            generated_report_link = record["Link"]

    return generated_report_link


def get_filename_from_content_disposition(content_disposition: str) -> str:
    """
    Extracts the file name from the Content-Disposition header.
    """
    if content_disposition:
        match = re.search(r'filename="(.+)"', content_disposition)
        if match:
            return match.group(1)
    return None


def download_file(url: str, output_file: str = None):
    """
    Downloads the file from the given URL.
    If output_file is not specified, attempts to derive the file name from the Content-Disposition header.
    """
    if not url:
        return

    print(f"Saving file...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        if not output_file:
            content_disposition = r.headers.get("Content-Disposition")
            output_file = (
                get_filename_from_content_disposition(content_disposition)
                or f"Report_{format_as_date(datetime.now())}"
            )

        with open(output_file, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"Saved file downloaded from:\n{url}\nto: {output_file}")
    return output_file


def main():
    cxy_api_key = ""  # ChainXY API Key
    # Options: ("changes_over_time", "nearest_neighbor", "void_analysis")
    report_type = ""
    collection_id = 0
    target_collection_id = 0  # used for nearest_neighbor and void_analysis reports

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=365)
    # Parameters for Changes Over Time Report
    cnanges_over_time_report_params = {
        "IncludeSummaryStats": True,
        "StartDate": format_as_date(start_time),
        "EndDate": format_as_date(end_time),
        "IncludeChangeLog": False,
        "IncludeCountByOpenStatus": False,
        "IncludeCountByCountry": False,
        "IncludeCountByState": False,
        "IncludeCountByStoreType": False,
        "IncludeCountByDMA": False,
        "IncludeCountByCounty": False,
    }

    # Parameters for Nearest Report
    nearest_neighbor_report_params = {
        "NearestN": 1,  # number of nearest neighbors
        "SeedChainListId": collection_id,  # starting locations
        "TargetChainListId": target_collection_id,  # neighbor locations to find
        # or, to run against a specific chain without creating a collection: "TargetChainId": target_chain_id,
    }

    # Parameters for Void Analysis Report
    void_analysis_report_params = {
        "SearchRadius": 10,
        "AdminLevel": "1",  # Admin level (1: Country, 2: State, etc.)
        "TargetLocation": {"Latitude": 0.0, "Longitude": 0.0},
        "Label": "Void Analysis Report",
        "Categorization": "Category",  # Choose from Category, NAICS, or SIC
    }

    valid_report_types = ("changes_over_time", "nearest_neighbor", "void_analysis")
    if report_type not in valid_report_types:
        raise ValueError(
            f"Invalid report type specified. Choose from {valid_report_types}"
        )
    else:
        print(f"Generating {report_type} report for collection {collection_id}.")

    if report_type == "changes_over_time":
        report_url = download_changes_over_time_report(
            cxy_api_key, collection_id, cnanges_over_time_report_params
        )
    elif report_type == "nearest_neighbor":
        report_url = download_nearest_report(
            cxy_api_key, nearest_neighbor_report_params
        )
    elif report_type == "void_analysis":
        report_url = download_void_analysis_report(
            cxy_api_key, void_analysis_report_params
        )

    print(f"Download URL: {report_url}")
    # download_file(report_url)


if __name__ == "__main__":
    main()
