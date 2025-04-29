"""Multipage Streamlit app for UGo Transportation analysis."""

import altair as alt
import pandas as pd
import streamlit as st

from src.utils.data_cleaning import load_data
from src.utils.load import (
    add_time_blocks,
    add_traffic_flag,
    aggregate_by_time,
    assign_expected_frequencies,
    load_stop_events,
    process_arrival_times,
    time_extraction,
)

# Set page configuration for Streamlit
st.set_page_config(page_title="UGo Shuttle Analysis Dashboard", layout="wide")

# Create a sidebar for navigation
st.sidebar.title("UGo Shuttle Analysis")

@st.cache_resource()
def startup():
    load_data()

startup()

# Navigation options
page = st.sidebar.radio(
    "Select Analysis Page:",
    [
        "Rider Waiting Patterns by Stop",
        "Rider Waiting Patterns by Traffic Level",
        "Bus Stop Variance Explorer",
        # "Route Duration Summary",
        "Time Series Analysis",
        "Bunching Exploration",
    ],
)


if page == "Rider Waiting Patterns by Stop":
    stop_events_df = load_stop_events()
    stop_events_df = add_time_blocks(stop_events_df)
    stop_events_df = add_traffic_flag(stop_events_df)

    # In-page filters
    selected_time_block = st.selectbox(
        "Select Time Period for Analysis:",
        options=stop_events_df["timeBlock"].unique(),
        index=0,
        help="Choose morning, afternoon, etc.",
    )
    selected_stops = st.multiselect(
        "Filter Stops Based on Location:",
        options=sorted(stop_events_df["stopName"].dropna().unique()),
        default=sorted(stop_events_df["stopName"].dropna().unique()),
        help="Pick one or more stops.",
    )

    # Apply filters
    filtered_df = stop_events_df[
        (stop_events_df["timeBlock"] == selected_time_block)
        & (stop_events_df["stopName"].isin(selected_stops) if selected_stops else True)
    ]

    # Convert to minutes
    filtered_df["stopDurationMinutes"] = filtered_df["stopDurationSeconds"] / 60

    # ── Outlier detection ──
    threshold = filtered_df["stopDurationMinutes"].quantile(0.95)
    core_df = filtered_df[filtered_df["stopDurationMinutes"] <= threshold]
    outliers_df = filtered_df[filtered_df["stopDurationMinutes"] > threshold]

    # Display
    st.title("🚍 UGo Shuttle Rider Waiting Patterns (By Stop)")
    st.markdown(f"### Showing data for {len(filtered_df)} stop events")
    st.markdown("This chart shows the average time buses spend at each stop.")

    # ⏱️ Average Stop Duration by Stop (excluding outliers)
    avg_by_stop = (
        core_df.groupby("stopName")["stopDurationMinutes"]
        .mean()
        .reset_index()
        .sort_values("stopDurationMinutes", ascending=False)
    )
    bar_stop = (
        alt.Chart(avg_by_stop)
        .mark_bar()
        .encode(
            x=alt.X("stopDurationMinutes:Q", title="Avg Duration (min)"),
            y=alt.Y("stopName:N", sort="-x", title="Stop Name"),
            tooltip=["stopName", "stopDurationMinutes"],
        )
        .properties(width=800, height=500)
    )
    st.altair_chart(bar_stop, use_container_width=True)

    # Average Stop Duration by Time of Day (excluding outliers)
    avg_by_time = (
        core_df.groupby("timeBlock")["stopDurationMinutes"].mean().reset_index()
    )
    bar_time = (
        alt.Chart(avg_by_time)
        .mark_bar()
        .encode(
            x=alt.X("timeBlock:N", title="Time of Day"),
            y=alt.Y("stopDurationMinutes:Q", title="Avg Duration (min)"),
            tooltip=["timeBlock", "stopDurationMinutes"],
        )
        .properties(width=800, height=500)
    )
    st.altair_chart(bar_time, use_container_width=True)

    # Show the outliers in an expander
    if not outliers_df.empty:
        with st.expander(
            f"🔍 Show {len(outliers_df)} outlier events (> {threshold:.1f} min)"
        ):
            st.dataframe(
                outliers_df[
                    ["stopName", "timeBlock", "stopDurationMinutes"]
                ].sort_values("stopDurationMinutes", ascending=False)
            )


elif page == "Rider Waiting Patterns by Traffic Level":
    stop_events_df = load_stop_events()
    stop_events_df = add_time_blocks(stop_events_df)
    stop_events_df = add_traffic_flag(stop_events_df)

    # In-page time filter
    selected_time_block = st.selectbox(
        "Select Time Period for Analysis:",
        options=stop_events_df["timeBlock"].unique(),
        index=0,
        help="Choose morning, afternoon, etc.",
    )

    # Filter by selected time block
    filtered_df = stop_events_df[stop_events_df["timeBlock"] == selected_time_block]

    # Convert to minutes
    filtered_df["stopDurationMinutes"] = filtered_df["stopDurationSeconds"] / 60

    # ── Flag 95th‐pct outliers ──
    thr = filtered_df["stopDurationMinutes"].quantile(0.95)
    filtered_df["isOutlier"] = filtered_df["stopDurationMinutes"] > thr

    # Show count of outliers
    st.markdown(
        f"> **Note:** {filtered_df['isOutlier'].sum()} events exceed "
        f"{thr:.1f} min and are flagged as outliers."
    )

    st.title("🚍 UGo Shuttle Rider Waiting Patterns (By Traffic Level)")
    st.markdown(f"### Showing data for {len(filtered_df)} stop events")
    st.markdown("Number of stops and stop durations by traffic level.")

    # 🚦 Number of Stops by Traffic Level
    st.subheader("🚦 Number of Stops by Traffic Level")
    bar_chart = (
        alt.Chart(filtered_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "trafficFlag:N", sort=["low", "mid", "high"], title="Traffic Level"
            ),
            y=alt.Y("count():Q", title="Number of Stops"),
            tooltip=["trafficFlag", "count()"],
        )
        .properties(width=900, height=500)
    )
    st.altair_chart(bar_chart, use_container_width=True)

    # 📈 Stop Duration by Traffic Level (outliers in red)
    st.subheader("📈 Stop Duration by Traffic Level")
    scatter_chart = (
        alt.Chart(filtered_df)
        .mark_point(filled=True, size=60, opacity=0.6)
        .encode(
            x=alt.X(
                "trafficFlag:N", sort=["low", "mid", "high"], title="Traffic Level"
            ),
            y=alt.Y("stopDurationMinutes:Q", title="Stop Duration (min)"),
            color=alt.Color(
                "isOutlier:N",
                scale=alt.Scale(domain=[False, True], range=["steelblue", "firebrick"]),
                legend=alt.Legend(title="Outlier"),
            ),
            tooltip=[
                "stopName",
                "stopDurationMinutes",
                "trafficFlag",
                "timeBlock",
                "isOutlier",
            ],
        )
        .properties(
            title="Stop Durations by Traffic Level (outliers in red)",
            width=900,
            height=500,
        )
    )
    st.altair_chart(scatter_chart, use_container_width=True)


elif page == "Bus Stop Variance Explorer":
    stop_events_df = load_stop_events()
    _, variances, medians = process_arrival_times(stop_events_df)
    stop_events_df = assign_expected_frequencies(stop_events_df)

    st.sidebar.header("Frequency (in minutes)")
    frequencies = (
        stop_events_df["expectedFreq"].dropna().astype(int).sort_values().unique()
    )
    selected_freq = st.sidebar.selectbox(
        "Select Expected Frequency:",
        options=frequencies,
        format_func=lambda x: f"{x} min",
    )

    stop_events_df = stop_events_df[stop_events_df["expectedFreq"] == selected_freq]
    variances = variances[variances["routeName"].isin(stop_events_df["routeName"])]
    medians = medians[medians["routeName"].isin(stop_events_df["routeName"])]

    st.title("Chicago Bus Stop Variance Explorer")
    st.markdown(
        """
        This page investigates consistency of arrivals by route and stop.
        """
    )
    routes = variances["routeName"].unique()
    selected_route = st.selectbox("Select a route:", sorted(routes))
    view = st.radio("View by:", ["Standard Deviation of Wait Time", "Median Wait Time"])
    if view == "Standard Deviation of Wait Time":
        data = variances[variances["routeName"] == selected_route].sort_values(
            by="arrival_stdev", ascending=False
        )
        col, title = (
            "arrival_stdev",
            f"Std Dev of Arrival Time (min) - {selected_route}",
        )
    else:
        data = medians[medians["routeName"] == selected_route].sort_values(
            by="arrival_median", ascending=False
        )
        col, title = (
            "arrival_median",
            f"Median Time Between Arrivals (min) - {selected_route}",
        )

    st.altair_chart(
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(f"{col}:Q", title="Minutes"),
            y=alt.Y("stopName:N", sort="-x", title="Stop Name"),
            tooltip=["stopName", col],
        )
        .properties(width=700, height=500, title=title),
        use_container_width=True,
    )


elif page == "Time Series Analysis":
    st.title("🚍 Intra-Month Passenger Load Variability")
    st.markdown("Weekly ridership trends for a selected route and month.")
    data = time_extraction()
    agg = aggregate_by_time(data)

    month_order = ["January", "February", "March"]
    months = [m for m in month_order if m in agg["month"].unique()]

    route_sel = st.selectbox("Select Route", agg["routeName"].unique())
    month_sel = st.selectbox("Select Month", months)

    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    filt = agg[(agg["routeName"] == route_sel) & (agg["month"] == month_sel)].copy()
    filt["week_day"] = pd.Categorical(filt["week_day"], categories=days, ordered=True)

    pivot = filt.pivot_table(
        index="week_day", columns="month_week", values="passengerLoad"
    ).sort_index()
    pivot.columns = [f"Week {int(w)}" for w in pivot.columns]
    long = pivot.reset_index().melt(
        id_vars="week_day", var_name="week", value_name="passengerLoad"
    )

    dm = filt[["week_day", "month_week", "date"]].drop_duplicates()
    dm["week"] = "Week " + dm["month_week"].astype(int).astype(str)
    merged = long.merge(dm, on=["week_day", "week"], how="left")

    st.altair_chart(
        alt.Chart(merged)
        .mark_line(point=True)
        .encode(
            x=alt.X("week_day:N", sort=days, title="Day of Week"),
            y=alt.Y("passengerLoad:Q", title="Passenger Load"),
            color="week:N",
            tooltip=[
                alt.Tooltip("week_day:N", title="Weekday"),
                alt.Tooltip("week:N", title="Week"),
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("passengerLoad:Q", title="Load"),
            ],
        )
        .properties(title="Riders by Weekday & Week")
        .interactive(),
        use_container_width=True,
    )


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
