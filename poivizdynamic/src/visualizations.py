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

def get_animated_bubble_map(
    df,
    title_text="My animated bubble map with value/ colored with spot or group",
    title_size=20,
    color_group_lab="spot_name",
    color_value_discrete=True,
    bubble_size="interest_value",
    radius=20,
    zoom=2.5,
    fig_name="my_animated_bubble_plot",
):