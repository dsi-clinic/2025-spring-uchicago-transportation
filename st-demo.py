"""Streamlit app for visualizing CTA bus arrival variability by stop and route."""

import altair as alt
import pandas as pd
import streamlit as st


def load_data():
    """This function loads the UGo Transportation data with a relative path and cleans it for analysis.

    The data is grouped by route, stop, and arrival times, and outliers are removed to unskew the
    summary statistics. The standard deviation and median are then taken.
    """
    bus_df = pd.read_csv("data/ClinicDump-StopEvents.csv")
    bus_df["arrivalTime"] = pd.to_datetime(bus_df["arrivalTime"])
    df_sorted = bus_df.sort_values(by=["routeName", "stopName", "arrivalTime"])
    df_sorted["arrival_diff"] = (
        df_sorted.groupby(["routeName", "stopName"])["arrivalTime"]
        .diff()
        .dt.total_seconds()
    ) / 60
    df_valid = df_sorted.dropna(subset=["arrival_diff"])
    lower = df_valid["arrival_diff"].quantile(0.05)
    upper = df_valid["arrival_diff"].quantile(0.95)
    df_filtered = df_valid[
        (df_valid["arrival_diff"] >= lower) & (df_valid["arrival_diff"] <= upper)
    ]
    variances = (
        df_filtered.groupby(["routeName", "stopName"])["arrival_diff"]
        .std()
        .reset_index()
    )
    variances = variances.rename(columns={"arrival_diff": "arrival_stdev"})
    medians = (
        df_filtered.groupby(["routeName", "stopName"])["arrival_diff"]
        .median()
        .reset_index()
    )
    medians = medians.rename(columns={"arrival_diff": "arrival_median"})
    return variances, medians


variances, medians = load_data()

st.title("Chicago Bus Stop Variance Explorer")

routes = variances["routeName"].unique()
selected_route = st.selectbox("Select a route:", sorted(routes))

view_choice = st.radio(
    "View by:", ["Standard Deviation of Wait Time", "Median Wait Time"]
)

if view_choice == "Standard Deviation of Wait Time":
    data = variances[variances["routeName"] == selected_route].sort_values(
        by="arrival_stdev", ascending=False
    )
    value_column = "arrival_stdev"
    chart_title = f"Standard Deviation of Arrival Time (mins) - {selected_route}"
else:
    data = medians[medians["routeName"] == selected_route].sort_values(
        by="arrival_median", ascending=False
    )
    value_column = "arrival_median"
    chart_title = f"Median Time Between Arrivals (mins) - {selected_route}"

chart = (
    alt.Chart(data)
    .mark_bar()
    .encode(
        x=alt.X(f"{value_column}:Q", title="Minutes"),
        y=alt.Y("stopName:N", title="Stop Name", sort="-x"),
        tooltip=["stopName", value_column],
    )
    .properties(width=700, height=500, title=chart_title)
)

st.altair_chart(chart, use_container_width=True)
