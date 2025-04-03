"""This module provides a Streamlit dashboard for analyzing UGo shuttle rider waiting patterns.

The dashboard allows filtering by stop and time of day, and displays average stop durations.

"""

import pandas as pd
import streamlit as st

# Set page configuration for Streamlit
st.set_page_config(page_title="UGo Shuttle Rider Analysis", layout="wide")
st.title("🚍 UGo Shuttle Rider Waiting Patterns")
st.markdown(
    "Analyze stop wait times by time of day and location to support better route and scheduling decisions."
)

# Load data from a relative path (data file is not tracked by Git)
stop_events_df = pd.read_csv("data/ClinicDump-StopEvents.csv")

# Convert relevant columns to appropriate data types
stop_events_df["arrivalTime"] = pd.to_datetime(stop_events_df["arrivalTime"])
stop_events_df["departureTime"] = pd.to_datetime(stop_events_df["departureTime"])
stop_events_df["stopDurationSeconds"] = pd.to_numeric(
    stop_events_df["stopDurationSeconds"], errors="coerce"
)
stop_events_df["hour"] = stop_events_df["arrivalTime"].dt.hour

# Define constants for time block thresholds
MORNING_START = 5
MORNING_END = 12
AFTERNOON_END = 17
EVENING_END = 21


def get_time_block(hour):
    """Returns a time block label based on the given hour.

    Args:
        hour (int): The hour of the day (0-23).

    Returns:
        str: A string indicating the time block.

    """
    if MORNING_START <= hour < MORNING_END:
        return "Morning (5AM–12PM)"
    elif MORNING_END <= hour < AFTERNOON_END:
        return "Afternoon (12PM–5PM)"
    elif AFTERNOON_END <= hour < EVENING_END:
        return "Evening (5PM–9PM)"
    else:
        return "Night (9PM–5AM)"


stop_events_df["timeBlock"] = stop_events_df["hour"].apply(get_time_block)

# Sidebar filters for stop names and time blocks
st.sidebar.header("Filter Options")
selected_stops = st.sidebar.multiselect(
    "Select Stop(s):",
    options=sorted(stop_events_df["stopName"].dropna().unique()),
    default=[],
)
selected_time_blocks = st.sidebar.multiselect(
    "Select Time of Day:",
    options=stop_events_df["timeBlock"].unique(),
    default=stop_events_df["timeBlock"].unique(),
)

# Filter data based on selected options
filtered_df = stop_events_df[
    (stop_events_df["timeBlock"].isin(selected_time_blocks))
    & (stop_events_df["stopName"].isin(selected_stops) if selected_stops else True)
]

st.markdown(f"### Showing data for {len(filtered_df)} stop events")

# Visualization: Average Stop Duration by Stop
st.write("#### ⏱️ Average Stop Duration by Stop")
avg_duration_by_stop = (
    filtered_df.groupby("stopName")["stopDurationSeconds"]
    .mean()
    .sort_values(ascending=False)
)
st.bar_chart(avg_duration_by_stop)

# Visualization: Average Stop Duration by Time of Day
st.write("#### ⏰ Average Stop Duration by Time of Day")
avg_duration_by_time = filtered_df.groupby("timeBlock")["stopDurationSeconds"].mean()
st.bar_chart(avg_duration_by_time)

# Optionally show raw filtered data
if st.checkbox("Show filtered raw data"):
    st.dataframe(filtered_df)
