"""This module runs a Streamlit dashboard visualizing transportation data. Code source: Steamlit Tutorial"""

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Transportation Dashboard", layout="wide")

st.title("🚇 New York Transportation Dashboard")


DATE_COLUMN = "date/time"
DATA_URL = (
    "https://s3-us-west-2.amazonaws.com/"
    "streamlit-demo-data/uber-raw-data-sep14.csv.gz"
)


def lowercase(x):
    """Lower case the column name"""
    return str(x).lower()


@st.cache_data
def load_data(nrows):
    """Load and clean transportation data from NY transportation API"""
    data = pd.read_csv(DATA_URL, nrows=nrows)
    data = data.rename(lowercase, axis="columns")
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    return data


# Create a text element and let the reader know the data is loading.
data_load_state = st.text("Loading data...")
# Load 10,000 rows of data into the dataframe.
data = load_data(10000)
# Notify the reader that the data was successfully loaded.
data_load_state.text("Done! (using st.cache_data)")

st.subheader("Raw data")
st.write(data)

st.subheader("Number of pickups by hour")
hist_values = np.histogram(data[DATE_COLUMN].dt.hour, bins=24, range=(0, 24))[0]
st.bar_chart(hist_values)
