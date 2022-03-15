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

def clean_dataset(df):
    """
    This function gets ready the data type in the dataset for animated map ploting usage.
    It ensures the "date" is date format; "longitude" and "latitude" are numeric format.

    Parameters
    ---
    dataframe : pandans.DataFrame
        This is the input dataframe.

    Returns
    ---
    Output dataframe has dypes as follows:

    unique_id                    int64
    spot_name                   object
    street                      object
    city                        object
    state                       object
    country                     object
    interest_value               int64
    date                datetime64[ns]
    symbol                      object
    latitude                   float64
    longitude                  float64
    formattedAddress            object
    dtype: object

    """
    df["date"] = pd.to_datetime(df["date"])
    df["longitude"] = pd.to_numeric(df["longitude"])  # ,errors = 'coerce'
    df["latitude"] = pd.to_numeric(df["latitude"])
    df = df.sort_values(by="date")
    return df

def get_footprint_map(
    TOKEN_MAPBOX,
    df_in,
    fig_name="my_animate_map",
    title_text="My animated map",
    title_size=20,
    zoom=2.5,
):
    """
    This function returns a dynamic footprint plotly map plot saved as "html" file in the "demo_output" directory.

    Parameters
    ---
    TOKEN_MAPBOX: an access token is required by Mapbox in order to get the dynamic plot look nicer.
        Free access for the token: https://docs.mapbox.com/help/getting-started/access-tokens/.
    df_in:  pd.DataFrame
        The dataframe contains the information would be animated and mapped.
    fig_name: str, default "my_animate_map"
        Customize name of saving html file.
    title_text: str, default "My animated map"
        Customize name of the map title.
    title_size: int, default 20
        Customize the font size of the map title.
    zoom: float/ int, default 2.5
        Customize the zoom level of the map plot. 2.5 for country level, 10~20 for city/ street level.

    Returns
    ---
    Output plotly dynamic map plot of the POIs' geometric information change with the date information. Trace line of the activity is shown.

    Example
    ---
    get_footprint_map(TOKEN_MAPBOX, travel, fig_name = "my foot print", title_text = "My Animated Footprint Map")

    """

    # TOKEN_MAPBOX = os.getenv("TOKEN_MAPBOX")

    lon = [df_in["longitude"][0]]
    lat = [df_in["latitude"][0]]

    mid_lat = df_in["latitude"].mean()
    mid_lon = df_in["longitude"].mean()
    lon_ls = df_in["longitude"].values.tolist()
    lat_ls = df_in["latitude"].values.tolist()

    frames = []

    for i in range(1, len(df_in)):

        lon.append(lon_ls[i])

        lat.append(lat_ls[i])

        framei = go.Frame(
            data=[
                go.Scattermapbox(
                    lon=lon,
                    lat=lat,
                )
            ],
        )
        frames.append(framei)

    fig = go.Figure(
        data=[
            go.Scattermapbox(
                mode="markers+text+lines",
                lon=lon_ls,
                lat=lat_ls,
                marker={"size": 20, "symbol": df_in["symbol"].tolist()},
                text=df_in["spot_name"].tolist(),
                textposition="bottom right"
                # symbols: https://labs.mapbox.com/maki-icons/
            )
        ],
        layout=go.Layout(
            updatemenus=[
                dict(
                    type="buttons",
                    buttons=[dict(label="Play", method="animate", args=[None])],
                )
            ],
            mapbox={"accesstoken": TOKEN_MAPBOX, "style": "light", "zoom": zoom},
        ),
        frames=frames,
    )

    fig.update_layout(
        mapbox_center={"lat": mid_lat, "lon": mid_lon},
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title_text=title_text,
        title_font_size=title_size,
    )

    fig.show()

    # save the html dynamic file
    if not os.path.exists("demo_output"):
        os.makedirs("demo_output")

    html_path = f"demo_output/{fig_name}.html"
    # html_path = f'{fig_name}.html'
    fig.write_html(html_path)
    # return fig


    """
    This function returns a dynamic bubble plotly map plot saved as "html" file in the "demo_output" directory. The bubble size and color could be controlled.
    More customized parameters are still under exploration due to the time limitation...

    Parameters
    ---
    df: pd.DataFrame
        The dataframe contains the information would be animated and mapped.
    title_text: str, default "My animated map"
        Customize name of the map title.
    title_size: int, default 20
        Customize the font size of the map title.
    color_group_lab: str, default "spot_name"
        This control the color group, which means the color will be group by color_group_lab.
    color_value_discrete: bool, default True
        True: the color value is continuous, so the color bar will be set in a continous form.
        False: the color value is discrete, so the color will be categorical set.
    bubble_size: str -> name of column, or int -> constant bubble_size; default "interest_value"
        Can be the name of column with dynamic values, and the bubble size will change along with the change of the dynamic values given.
        If the bubble_size input is an instant, the bubble size will remain the same during the whole time-series process shown on the plot.
    radius: int, default 20
        Customize the radius of the bubble.
    zoom: float/ int, default 2.5
        Customize the zoom level of the map plot. 2.5 for country level, 10~20 for city/ street level.
    fig_name: str, default "my_animate_map"
        Customize name of saving html file.

    Returns
    ---
    Output plotly dynamic bubble map plot of the POIs' geometric information change with the date information.

    Example
    ---
    get_animated_bubble_map(TOKEN_MAPBOX, starb2, zoom = 10, color_value_discrete = False, bubble_size = "interest_value", color_group_lab = "interest_value", fig_name = "starbuck2")

    """
    df = df.dropna(subset=["longitude", "latitude"], axis=0)

    lat_lab = "latitude"
    lon_lab = "longitude"

    date = df["date"].apply(lambda x: x.strftime("%Y-%m-%d"))

    mid_lat = median(df[lat_lab])

    mid_lon = median(df[lon_lab])

    if type(bubble_size) == str:

        df[bubble_size] = df[bubble_size].apply(lambda x: pd.to_numeric(x))
        print("bubble_size will change along with the true value")
    else:
        const_num = bubble_size
        bubble_size = [const_num] * len(df)
        print("bubble_size is a constant number")

    if color_value_discrete == True:
        print("the value is discrete")
        fig = px.scatter_mapbox(
            df,
            lat=lat_lab,
            lon=lon_lab,
            size=bubble_size,
            color=color_group_lab,
            animation_frame=date,
            color_discrete_sequence=px.colors.qualitative.D3,
            # https://plotly.com/python/discrete-color/
            size_max=radius,
            # labels = {value_lab:'income'} # only for continuous data
        )
    else:
        print("the value is continuous")
        fig = px.scatter_mapbox(
            df,
            lat=lat_lab,
            lon=lon_lab,
            size=bubble_size,
            color=color_group_lab,
            animation_frame=date,
            color_continuous_scale=px.colors.sequential.Mint,
            # color_continuous_scale=px.colors.cyclical.IceFire,
            # color_continuous_scale=px.colors.sequential.Viridis,
            # color_discrete_sequence = px.colors.qualitative.D3,
            # https://plotly.com/python/discrete-color/
            size_max=radius,
            # labels = {value_lab:'income'} # only for continuous data
        )
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=zoom,
        mapbox_center={"lat": mid_lat, "lon": mid_lon},
    )
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
    fig.update_layout(title_text=title_text, title_font_size=title_size)

    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 600
    fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 600
    fig.layout.coloraxis.showscale = True
    fig.layout.sliders[0].pad.t = 10
    fig.layout.updatemenus[0].pad.t = 10

    fig.show()

    # save the html dynamic file
    if not os.path.exists("demo_output"):
        os.makedirs("demo_output")

    html_path = f"demo_output/{fig_name}.html"
    # html_path = f'{fig_name}.html'
    fig.write_html(html_path)

    # return fig
