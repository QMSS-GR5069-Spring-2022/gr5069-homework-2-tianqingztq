import requests
import pandas as pd
from statistics import median
import os

# from requests_oauthlib import OAuth1Session
import time
from datetime import datetime, timedelta

# from dateutil import rrule
import warnings

import plotly.graph_objects as go
import plotly.express as px



def get_coordinate_api(api_key, dataframe, maptype="world"):
    """
    This function returns a one-line pandans.DataFrame showing coordination information of a POI.

    Parameters
    ---
    api_key: a private api key
        if maptype = "US":
            pass in the private api key GEO_CENSUS_API_KEY provided by the U.S. Census Bureau. https://www.census.gov/data/developers/data-sets/popest-popproj/popest.html
        if maptype = "wold":
            pass in the private api key GEO_RADAR_API_KEY provided by Radar (Radar is the leading geofencing and location tracking platform). Instruction on how to get the code at Authentication session: https://radar.com/documentation/api

    dataframe : pandans.DataFrame
        This is the input one-line dataframe, which used as the query text for the geo-APIs.
        It should contain the address information for only one POI.

    maptype : {"world", "US"}, default "world", optional
        Geo-API to use. The "US" API returns more accurate result than "world" when specifically looking at places in the US.
        Details provided in the links attached below the api_key description.

    Returns
    ---
    Output one-line pandans.DataFrame showing coordination information of a POI with latitude, longitude, and formattedAddress.
    latitude            float64
    longitude           float64
    formattedAddress     object

    Example
    ---
    get_coordinate_api(api_key = GEO_CENSUS_API_KEY, dataframe, maptype = "US")
    get_coordinate_api(api_key = GEO_RADAR_API_KEY, dataframe, maptype = "world")

    """

    start = time.time()  # time in seconds

    addr = dataframe[["street", "city", "state", "country"]].values.tolist()[0]

    if maptype == "world":

        # GEO_RADAR_API_KEY = os.getenv("GEO_RADAR_API_KEY")
        # api_key = GEO_RADAR_API_KEY
        api_url = f"https://api.radar.io/v1/geocode/forward?query={addr}"
        try:
            r = requests.get(api_url, headers={"Authorization": api_key})
            # If the response was successful, no Exception will be raised
            r.raise_for_status()
        except requests.exceptions.RequestException as http_err:
            print(f"Error occurred:{http_err}")
        else:
            # json_output = json.loads(r.content)
            print("Successful! Status Code:{}".format(r.status_code))
            out_df = pd.DataFrame(r.json()["addresses"])[
                ["latitude", "longitude", "formattedAddress"]
            ]
            if out_df.empty == True:
                warnings.warn(
                    "Sorry! This address cannot be searched through the api and returned an empty result"
                )
                return None
            else:
                end = time.time()
                print(f"Requested the api in {end - start:0.4f} seconds")
            # return out_df
    elif maptype == "US":
        # GEO_CENSUS_API_KEY = os.getenv("GEO_CENSUS_API_KEY")
        # api_key = GEO_CENSUS_API_KEY

        street, city, state, _ = addr

        benchmark = "Public_AR_Census2020"
        vintage = "Census2020_Census2020"
        layers = "10"
        api_url = f"https://geocoding.geo.census.gov/geocoder/geographies/address?street={street}&city={city}&state={state}&benchmark={benchmark}&vintage={vintage}&layers={layers}&format=json&key={api_key}"
        try:
            r = requests.get(api_url)
            # If the response was successful, no Exception will be raised
            r.raise_for_status()
        except requests.exceptions.RequestException as http_err:
            print(f"Error occurred:{http_err}")
        else:
            # json_output = json.loads(r.content)
            print("Successful! Status Code:{}".format(r.status_code))
            df = pd.DataFrame(r.json()["result"]["addressMatches"])
            if df.empty == True:
                warnings.warn(
                    "Sorry! This address cannot be searched through census_geocoding api and returned an empty result"
                )
                return None
            else:
                cord = df["coordinates"].values.tolist()
                cord_split = pd.DataFrame(cord, columns=["x", "y"])
                # adds = df["addressComponents"].values.tolist()
                # adds_split = pd.DataFrame(adds, columns = ['city', 'state', 'zip'])
                # out_df = pd.concat([df, cord_split, adds_split],axis=1)
                out_df = pd.concat([df, cord_split], axis=1)[
                    ["y", "x", "matchedAddress"]
                ]
                out_df.columns = ["latitude", "longitude", "formattedAddress"]
                end = time.time()
                print(
                    f"Requested the api and transformed into dataframe in {end - start:0.4f} seconds"
                )

    return out_df

def get_geo_dataset(api_key, df, maptype="world"):
    """
    This function returns a whole dataset with geo-information, a pandans.DataFrame combined original information with matched geographical information.

    Parameters
    ---
    api_key: a private api key (pass the api key to the inner function get_coordinate_api(); same help doc of that one).
        if maptype = "US":
            pass in the private api key GEO_CENSUS_API_KEY provided by the U.S. Census Bureau. https://www.census.gov/data/developers/data-sets/popest-popproj/popest.html
        if maptype = "wold":
            pass in the private api key GEO_RADAR_API_KEY provided by Radar (Radar is the leading geofencing and location tracking platform). Instruction on how to get the code at Authentication session: https://radar.com/documentation/api

    dataframe : pandans.DataFrame
        This is the input dataframe, which contains a list of POI's address information.

    maptype : {"world", "US"}, default "world", optional
        Geo-API to use. The "US" API returns more accurate result than "world" when specifically looking at places in the US.
        Details provided in the links attached below the api_key description.

    Returns
    ---
    Output the whole dataset with geo-information, a pandans.DataFrame combined original information with matched geographical information.
    The column number should be 12.

    unique_id             int64
    spot_name            object
    street               object
    city                 object
    state                object
    country              object
    interest_value        int64
    date                 object
    symbol               object
    latitude            float64
    longitude           float64
    formattedAddress     object
    dtype: object

    Example
    ---
    get_coordinate_api(api_key = GEO_RADAR_API_KEY, travel, maptype = "world")
    get_coordinate_api(api_key = GEO_CENSUS_API_KEY, starbuck, maptype = "US")

    """

    # apply api only on unique address in oreder to save time and even money.
    # get non-duplication dataset
    temp_nodup = df.drop_duplicates(subset=["street", "city"])

    for i in range(len(temp_nodup)):
        temp = temp_nodup.iloc[i, :]
        temp = pd.DataFrame([temp.values], columns=temp.index)

        temp2 = get_coordinate_api(api_key, temp, maptype=maptype)
        if i == 0:
            df_out = pd.concat([temp, temp2], axis=1)
        else:
            if temp2 is None:
                continue
            else:

                mid = pd.concat([temp, temp2], axis=1)
                df_out = df_out.append(mid, ignore_index=True)

        i += 1

    # left join the list of outcome to the original dataset (with duplicates)
    df_out_final = df.merge(
        df_out[
            ["street", "city", "state", "latitude", "longitude", "formattedAddress"]
        ],
        on=["street", "city", "state"],
        how="left",
    )

    return df_out_final


def get_demo_data(df, demo_data="my travel map"):
    """
    This function gets the three demo datasets.

    Parameters
    ---
    dataframe : pandans.DataFrame
        This is the input dataframe named "demo_fake_data".

    demo_data: {"my travel map", "life log", "starbuck"}, default "my travel map".
        my travel map: This is the fake dataset for a travel foot print log including 4 cities in NY: New York -> Seattle -> Los Angela -> Miami.
        life log: This is the fake dataset contains the daily active routine of a Columbia nerd.
        starbuck: This is the fake dataset contains the starbucks income changed by date around New Haven city and neighorhoods.

    Returns
    ---
    Relative dataframes.

    Example
    ---
    travel = pv.get_demo_data(df, "my travel map")
    life = pv.get_demo_data(df, "life log")
    starb = pv.get_demo_data(df, "starbuck")

    >> travel.columns
    Index(['unique_id', 'spot_name', 'street', 'city', 'state', 'country',
       'interest_value', 'date', 'symbol'],
      dtype='object')

    """
    if demo_data == "my travel map":
        df = df.iloc[
            0:4,
        ]
    elif demo_data == "life log":
        df = df.iloc[
            4:7,
        ]
    elif demo_data == "starbuck":
        df = df.iloc[
            7:,
        ]
    return df
