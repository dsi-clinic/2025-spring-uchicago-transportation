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
        "Bunching Exploration",
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

    st.markdown("""
    This page investigates the consistency of arrivals of a given stop on a given bus route.

    Calculated based on time between consecutive stop events at each stop for every route.

    - Use the dropdown selectbox to select a specific route, and view all the stops on that route.
    - Use the sidebar to filter by expected frequency of arrivals.
        - Ex. the South Loop Shuttle is expected every 60 minutes, you would find it under the 60 min view.
        - Some routes have different expected frequencies during different times of day, so they appear under multiple filters.
    - Explore patterns in standard deviation and median wait times across UGo shuttles.

    """)

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

    # Make 'week_day' an ordered categorical
    filtered["week_day"] = pd.Categorical(
        filtered["week_day"], categories=day_order, ordered=True
    )

    # Pivot and sort index
    pivot = filtered.pivot_table(
        index="week_day", columns="month_week", values="passengerLoad"
    )
    pivot = pivot.sort_index()
    pivot.columns = [f"Week {int(w)}" for w in pivot.columns]

    # Melt pivoted data back into long format for Altair
    long_df = pivot.reset_index().melt(
        id_vars="week_day", var_name="week", value_name="passengerLoad"
    )

    # Merge to get actual dates back
    date_map = filtered[["week_day", "month_week", "date"]].drop_duplicates()
    date_map["week"] = "Week " + date_map["month_week"].astype(int).astype(str)

    # Merge with long_df to get date for tooltip
    merged = long_df.merge(date_map, on=["week_day", "week"], how="left")

    # Altair chart with hover tooltip
    chart = (
        alt.Chart(merged)
        .mark_line(point=True)
        .encode(
            x=alt.X("week_day:N", sort=day_order, title="Day of the Week"),
            y=alt.Y("passengerLoad:Q", title="Passenger Load"),
            color="week:N",
            tooltip=[
                alt.Tooltip("week_day:N", title="Weekday"),
                alt.Tooltip("week:N", title="Week"),
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("passengerLoad:Q", title="Passenger Load"),
            ],
        )
        .properties(title="⏱️ Sum of Riders Given Route and Date")
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)

    if st.checkbox("Show route-level data"):
        st.dataframe(agg_df)

elif page == "Bunching Exploration":
    # Load the data
    stop_events_df = load_stop_events()
    stop_events_df = assign_expected_frequencies(stop_events_df)

    # Compute back-looking headway
    headways_df = (
        stop_events_df.assign(date=stop_events_df["arrivalTime"].dt.date)
        .sort_values(["routeName", "stopName", "date", "arrivalTime"])
        .assign(
            prev_arrival=lambda d: d.groupby(["routeName", "stopName", "date"])[
                "arrivalTime"
            ].shift(1)
        )
        .assign(
            headway_min=lambda d: (
                d["arrivalTime"] - d["prev_arrival"]
            ).dt.total_seconds()
            / 60
        )
        .dropna(subset=["headway_min", "expectedFreq"])
    )

    # Trim outliers using IQR
    def iqr_trim(
        df: pd.DataFrame,
        grp_col: str = "expectedFreq",
        val_col: str = "headway_min",
        k: float = 1.5,
    ) -> pd.DataFrame:
        """Drop rows lying outside [Q1 − k·IQR, Q3 + k·IQR] within each group."""
        quartiles = df.pivot_table(
            index=grp_col,
            values=val_col,
            aggfunc=[lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)],
        )
        quartiles.columns = ["q1", "q3"]
        quartiles["iqr"] = quartiles["q3"] - quartiles["q1"]
        quartiles["lower"] = quartiles["q1"] - k * quartiles["iqr"]
        quartiles["upper"] = quartiles["q3"] + k * quartiles["iqr"]
        out = df.merge(
            quartiles[["lower", "upper"]],
            left_on=grp_col,
            right_index=True,
            how="left",
        )
        mask = (out[val_col] >= out["lower"]) & (out[val_col] <= out["upper"])
        return out.loc[mask].drop(columns=["lower", "upper"])

    trimmed_df = iqr_trim(headways_df, k=1.5)
    # Box and Whisker plot
    trimmed_df["expectedFreq"] = trimmed_df["expectedFreq"].astype(int)
    freq_order = sorted(trimmed_df["expectedFreq"].unique())  # [10,15,20,30,60]

    box = (
        alt.Chart(trimmed_df)
        .mark_boxplot(extent="min-max")
        .encode(
            x=alt.X(
                "expectedFreq:O", title="Scheduled Frequency (min)", sort=freq_order
            ),
            y=alt.Y("headway_min:Q", title="Observed Gap Since Previous Bus (min)"),
            color=alt.Color("expectedFreq:O", legend=None),
        )
        .properties(
            width=750,
            height=450,
            title="Observed Gaps vs. Scheduled Frequency (IQR-trimmed)",
        )
    )

    st.altair_chart(box, use_container_width=True)

    with st.expander("Show headway table (IQR-trimmed)"):
        st.dataframe(trimmed_df)
