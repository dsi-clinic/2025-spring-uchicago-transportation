"""Multipage Streamlit app for UGo Transportation analysis."""

import altair as alt
import pandas as pd
import streamlit as st

from src.utils.load import (
    add_time_blocks,
    add_traffic_flag,
    aggregate_by_time,
    assign_expected_frequencies,
    get_route_level_ridership_vs_variance,
    load_stop_events,
    process_arrival_times,
    time_extraction,
)

# Set page configuration for Streamlit
st.set_page_config(page_title="UGo Shuttle Analysis Dashboard", layout="wide")

# Create a sidebar for navigation
st.sidebar.title("UGo Shuttle Analysis")

# Navigation options
page = st.sidebar.radio(
    "Select Analysis Page:",
    [
        "Rider Waiting Patterns",
        "Bus Stop Variance Explorer",
        "Route Duration Summary",
        "Time Series Analysis",
    ],
)

# Load data based on selected page to avoid duplicate loading
if page == "Rider Waiting Patterns":
    stop_events_df = load_stop_events()
    stop_events_df = add_time_blocks(stop_events_df)
    stop_events_df = add_traffic_flag(stop_events_df)

    # Sidebar filters
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
    show_traffic = st.sidebar.checkbox("Show Traffic Flag Analysis")

    # Filter data
    filtered_df = stop_events_df[
        (stop_events_df["timeBlock"].isin(selected_time_blocks))
        & (stop_events_df["stopName"].isin(selected_stops) if selected_stops else True)
    ]

    st.title("🚍 UGo Shuttle Rider Waiting Patterns")
    st.markdown(
        "Analyze stop wait times by time of day and location to support better route and scheduling decisions."
    )
    st.markdown(f"### Showing data for {len(filtered_df)} stop events")

    # ⏱️ Average Stop Duration by Stop
    st.subheader("⏱️ Average Stop Duration by Stop")
    avg_duration_by_stop = (
        filtered_df.groupby("stopName")["stopDurationSeconds"]
        .mean()
        .reset_index()
        .sort_values("stopDurationSeconds", ascending=False)
    )
    bar_stop = (
        alt.Chart(avg_duration_by_stop)
        .mark_bar()
        .encode(
            x=alt.X(
                "stopDurationSeconds:Q",
                title="Avg Stop Duration (sec)",
                scale=alt.Scale(zero=True),
            ),
            y=alt.Y("stopName:N", sort="-x", title="Stop Name"),
            tooltip=["stopName", "stopDurationSeconds"],
        )
        .properties(width=600, height=400)
    )
    st.altair_chart(bar_stop, use_container_width=True)

    # ⏰ Average Stop Duration by Time of Day
    st.subheader("⏰ Average Stop Duration by Time of Day")
    avg_duration_by_time = (
        filtered_df.groupby("timeBlock")["stopDurationSeconds"].mean().reset_index()
    )
    bar_time = (
        alt.Chart(avg_duration_by_time)
        .mark_bar()
        .encode(
            x=alt.X("timeBlock:N", title="Time of Day"),
            y=alt.Y(
                "stopDurationSeconds:Q",
                title="Avg Stop Duration (sec)",
                scale=alt.Scale(zero=True),
            ),
            tooltip=["timeBlock", "stopDurationSeconds"],
        )
        .properties(width=600, height=400)
    )
    st.altair_chart(bar_time, use_container_width=True)

    # 📊 Optional raw data
    if st.checkbox("Show filtered raw data"):
        st.dataframe(filtered_df)

    # 🚦 Optional traffic flag analysis
    if show_traffic:
        st.subheader("🚦 Number of Stops by Traffic Level")

        bar_chart = (
            alt.Chart(stop_events_df)
            .mark_bar()
            .encode(
                x=alt.X("trafficFlag:N", sort=["low", "mid", "high"]),
                y=alt.Y("count()", title="Number of Stops"),
                tooltip=["trafficFlag", "count()"],
            )
            .properties(title="Stops by Traffic Level", width=400, height=300)
        )
        st.altair_chart(bar_chart, use_container_width=True)

        st.subheader("📈 Stop Duration by Traffic Level")

        scatter_chart = (
            alt.Chart(filtered_df)
            .mark_point(filled=True, size=60, opacity=0.6)
            .encode(
                x=alt.X(
                    "trafficFlag:N", title="Traffic Level", sort=["low", "mid", "high"]
                ),
                y=alt.Y(
                    "stopDurationSeconds:Q",
                    title="Stop Duration (sec)",
                    scale=alt.Scale(zero=True),
                ),
                color=alt.Color("trafficFlag:N", title="Traffic Level"),
                tooltip=["stopName", "stopDurationSeconds", "trafficFlag", "timeBlock"],
            )
            .properties(title="Scatter of Stop Durations", width=600, height=300)
        )
        st.altair_chart(scatter_chart, use_container_width=True)

elif page == "Bus Stop Variance Explorer":
    # Load and process data for the Bus Stop Variance Explorer page
    stop_events_df = load_stop_events()
    _, variances, medians = process_arrival_times(stop_events_df)
    stop_events_df = assign_expected_frequencies(stop_events_df)

    st.sidebar.header("Frequency (in minutes)")
    available_frequencies = (
        stop_events_df["expectedFreq"].dropna().astype(int).sort_values().unique()
    )
    selected_freq = st.sidebar.selectbox(
        "Select Expected Frequency:",
        options=available_frequencies,
        format_func=lambda x: f"{int(x)} min",
    )

    stop_events_df = stop_events_df[stop_events_df["expectedFreq"] == selected_freq]
    variances = variances[
        variances["routeName"].isin(stop_events_df["routeName"].unique())
    ]
    medians = medians[medians["routeName"].isin(stop_events_df["routeName"].unique())]

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
    data = get_route_level_ridership_vs_variance()

    st.title("UGo Shuttle Route Summary")

    st.write("### Route-Level Scatter: Variance vs. Daily Ridership")
    st.markdown(
        "Each point represents a route. The X-axis shows how variable the arrival times are, "
        "while the Y-axis reflects average daily boardings."
    )

    chart = (
        alt.Chart(data)
        .mark_circle(size=120)
        .encode(
            x=alt.X("arrival_stdev:Q", title="Avg Arrival Time Std Dev (mins)"),
            y=alt.Y("avg_daily_boardings:Q", title="Avg Daily Boardings"),
            color=alt.Color("routeName:N", title="Route"),
            tooltip=["routeName", "arrival_stdev", "avg_daily_boardings"],
        )
        .properties(width=700, height=500)
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)

    if st.checkbox("Show route-level data"):
        st.dataframe(data)


elif page == "Time Series Analysis":
    st.title("🚍 Visualizing Intra-Month Variability in Passenger Load")
    st.markdown(
        "This visualization displays weekly ridership trends for a selected transit route and month."
    )
    # Convert arrivalTime to datetime and extract the day of the week and week number.
    data = time_extraction()
    # Group by week and day, and sum passengerLoad.
    agg_df = aggregate_by_time(data)

    month_order = ["January", "February", "March"]
    month_options = [m for m in month_order if m in agg_df["month"].unique()]

    # Streamlit Visualization
    selected_route = st.selectbox("Select Route", agg_df["routeName"].unique())
    selected_month = st.selectbox("Select Month", month_options)

    # Filter data
    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    filtered = agg_df[
        (agg_df["routeName"] == selected_route) & (agg_df["month"] == selected_month)
    ].copy()

    # 🛠️ Make 'week_day' an ordered categorical
    filtered["week_day"] = pd.Categorical(
        filtered["week_day"], categories=day_order, ordered=True
    )

    # Pivot and sort index
    pivot = filtered.pivot_table(
        index="week_day", columns="month_week", values="passengerLoad"
    )
    pivot = pivot.sort_index()
    pivot.columns = [f"Week {int(w)}" for w in pivot.columns]

    st.write("#### ⏱️ Sum of Riders Given Route and Date")
    st.line_chart(pivot)
