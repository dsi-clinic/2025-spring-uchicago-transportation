"""Multipage Streamlit app for UGo Transportation analysis."""

import altair as alt
import streamlit as st

from src.utils.load import (
    add_time_blocks,
    calculate_route_mean_durations,
    load_stop_events,
    process_arrival_times,
)

# Set page configuration for Streamlit
st.set_page_config(page_title="UGo Shuttle Analysis Dashboard", layout="wide")

# Create a sidebar for navigation
st.sidebar.title("UGo Shuttle Analysis")
st.sidebar.image(
    "https://transportation.uchicago.edu/wp-content/uploads/2021/09/UchiShuttle-Logo-New.jpg",
    width=200,
)

# Navigation options
page = st.sidebar.radio(
    "Select Analysis Page:",
    ["Rider Waiting Patterns", "Bus Stop Variance Explorer", "Route Duration Summary"],
)

# Load data based on selected page to avoid duplicate loading
if page == "Rider Waiting Patterns":
    stop_events_df = load_stop_events()
    stop_events_df = add_time_blocks(stop_events_df)

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

    # Main content for Rider Waiting Patterns page
    st.title("🚍 UGo Shuttle Rider Waiting Patterns")
    st.markdown(
        "Analyze stop wait times by time of day and location to support better route and scheduling decisions."
    )

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
    avg_duration_by_time = filtered_df.groupby("timeBlock")[
        "stopDurationSeconds"
    ].mean()
    st.bar_chart(avg_duration_by_time)

    # Optionally show raw filtered data
    if st.checkbox("Show filtered raw data"):
        st.dataframe(filtered_df)

elif page == "Bus Stop Variance Explorer":
    # Load and process data for the Bus Stop Variance Explorer page
    stop_events_df = load_stop_events()
    _, variances, medians = process_arrival_times(stop_events_df)

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

elif page == "Route Duration Summary":
    # Load data for the Route Duration Summary page
    data = calculate_route_mean_durations()

    st.title("UGo Shuttle Route Summary")

    # Display mean durations
    st.header("Mean Stop Duration Seconds by Route")
    st.write("Below is a table showing mean stop duration for each route.")
    st.dataframe(data)
