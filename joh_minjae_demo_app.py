"""Minjae Joh's Demo Streamlit App"""

import pandas as pd
import streamlit as st


@st.cache_data
def get_data():
    """Get data for the app"""
    data_stopevents = pd.read_csv("data/ClinicDump-StopEvents.csv")
    mean_durations = data_stopevents.groupby("routeName")["stopDurationSeconds"].mean()
    result = mean_durations.to_frame().T
    return result


@st.fragment
def show_mean_durations(data):
    """Fragment showing the mean durations"""
    st.header("Mean Stop Duration Seconds by Route")
    st.write("Below is a table showing mean stop duration for each route.")
    st.dataframe(data)


def main():
    """Main Streamlit Function"""
    data = get_data()
    show_mean_durations(data)


if __name__ == "__main__":
    main()
