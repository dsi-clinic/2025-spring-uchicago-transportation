"""Multipage Streamlit app for UGo Transportation analysis."""

import json
import math
import os
import re

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from src.utils.data_cleaning import load_data
from src.utils.load import (
    add_time_blocks,
    add_traffic_flag,
    aggregate_by_time,
    assign_expected_frequencies,
    load_holdover_data,
    load_stop_events,
    process_arrival_times,
    time_extraction,
)

load_dotenv()

# ── Page config & startup ───────────────────────────────────────────────────
st.set_page_config(page_title="UGo Shuttle Analysis Dashboard", layout="wide")
st.sidebar.title("UGo Shuttle Analysis")


@st.cache_resource()
def startup():
    """Initialize and cache the raw data for the dashboard."""
    load_data()


startup()

page = st.sidebar.radio(
    "Select Analysis Page:",
    [
        "Welcome",
        "About",
        "Stop Wait Patterns",
        "Frequency vs. Wait",
        "Bus Stop Variance Explorer",
        "Time Series Analysis",
        "Bunching Exploration",
        "Connector Bunching Map",
        "NightRide Explorer",
    ],
)


# ── Normalization helpers ────────────────────────────────────────────────────
def normalize_route(r: str) -> str:
    """Turn a raw route string into a lowercase key without prefixes/suffixes."""
    if not isinstance(r, str):
        return ""
    r = re.sub(r"\[.*?\]\s*", "", r)
    r = re.sub(r"\(version.*?\)", "", r, flags=re.IGNORECASE)
    return r.strip().lower()


def normalize_stop(s: str) -> str:
    """Turn a raw stop string into a normalized lowercase key."""
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"\(.*?\)", "", s)
    s = s.replace("&", " and ").replace("/", " and ")
    s = re.sub(r"[^a-z0-9\.\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


# ──────────────────────────────────────────────────────────────────────────────
if page == "Welcome":
    st.title("Welcome to the Spring DSI Clinic's UGo Shuttle Analysis")

    st.markdown("""

    Use the menu on the left to learn more this project on the **About Page** or to navigate to each analysis page.

    ### Table of Contents

    - **Stop Wait Patterns**
      - Select a route, time block, and stops to compare their average dwell times, highlighting holdovers.
    - **Frequency vs Wait**
      - Plot each stop’s average daily service frequency against its average wait time, with a trend line to reveal their relationship.
    - **Bus Stop Variance Explorer**
      - Investigate the consistency of arrivals of a given stop on a given route, calculated based on time between consecutive stop events.
    - **Time Series Analysis**
      - Track weekly ridership changes across days and weeks.
    - **Bunching Exploration**
      - Examine which buses are arriving closer together than scheduled.
    - **Connector Bunching Map**
      - Visualize bunching hotspots in the Downtown Connector route.
    - **NightRide Explorer**
      - Analyze ridership by hour for NightRide shuttles.

    """)

elif page == "About":
    st.title("About Us")

    st.markdown("""

    This dashboard was created to better understand UGo shuttle rider waiting patterns with respect to time-of-day and location-specific effects.

    You can find the full code repository here: [Github](https://github.com/dsi-clinic/2025-spring-uchicago-transportation)

    ### Project Goals
    - Use shuttle data to answer key questions related to patterns in rider wait times and service reliability.
    - Help UChicago Transportation make informed, data-driven decisions about the UGo shuttles.

    ### Meet the Team
    - **Kristen Wallace** — 4th year undergraduate student, Data Science & Business Economics. [LinkedIn](https://www.linkedin.com/in/kristen-wallace-8094a01a3/)
    - **Minjae Joh** — 3rd year undergradate student, Data Science & Linguistics. [LinkedIn](https://www.linkedin.com/in/minjae-joh-73b840210/)
    - **Leah Dimsu** — 3rd year undergradate student, Data Science & Business Economics [LinkedIn](https://www.linkedin.com/in/leah-dimsu/)
    - **Luna Jian** — 2nd year graduate student, Computer Science & Public Policy

    ### Data
    The requisite files can be fetched from the uchicago Box, in file '2025-Spring-UChicago-Transportation'. If without access, please consult DSI for access to the data. Below is the link to the Box.

    https://uchicago.app.box.com/folder/313087826266?s=8soop37anr53ivgllbiy6tp690syd5tz&tc=collab-folder-invite-treatment-b

    The following files should be contained in this directory:

    - ClinicDump-25-23-24-NumShuttlesRunning.csv
    - ClinicDump-25-23-24-StopEvents.csv
    - ClinicDump-NumShuttlesRunning.csv
    - ClinicDump-StopEvents.csv

    ### Tools Used
    - Streamlit
    - Python
    - Google Maps API

    """)

elif page == "Stop Wait Patterns":
    # ── Page header ─────────────────────────────────────────────────────────
    st.title("🚍 UGo Shuttle Rider Waiting Patterns (By Stop)")
    st.markdown("""
    **How to use this page:**
    1. Choose your **Route**, one or more **Stops**, and a **Time block** from the **sidebar**.
    2. The **top chart** shows average stop duration per stop (95th-pct outliers removed).
       - Holdover stops are highlighted in **yellow**.
    3. The **bottom chart** shows average stop duration _across all_ time blocks.
    """)

    # ── Key Takeaways ───────────────────────────────────────────────────────
    st.markdown("### Key Takeaways")
    st.markdown("""
    - Some **non-holdover** stops actually have **longer** average stop durations than known holdover stops.
      - On the **South** route, **Cottage Grove & 60th** and **Woodlawn Ave & 63rd** both exceed the average dwell time at **60th St & Ellis** (a holdover).
      - On the **Red Line/Arts Block** route, **Garfield Redline Station(WB), Midway Plaisance and Cottage Grove, Ellis/57th, and Institute for Study of Ancient Cultures** exceeds the duration at **Garfield Red Line/Logan Center** (holdover).
    """)

    # ── Data load ─────────────────────────────────────────────────────────────
    df_events = load_stop_events()
    df_events = add_time_blocks(df_events)
    df_events = add_traffic_flag(df_events)

    # ── Sidebar filters ───────────────────────────────────────────────────────
    st.sidebar.header("Filter Options")
    routes = sorted(df_events["routeName"].dropna().unique())
    selected_route = st.sidebar.selectbox("Select Route:", routes)

    stops = (
        df_events.query("routeName == @selected_route")["stopName"].dropna().unique()
    )
    selected_stops = st.sidebar.multiselect("Select Stops:", sorted(stops))

    tblocks = sorted(df_events["timeBlock"].dropna().unique())
    selected_time_block = st.sidebar.selectbox("Select Time Period:", tblocks)

    # ── Guard: must pick at least one stop ──────────────────────────────────
    if not selected_stops:
        st.info("Please select at least one stop to see the charts.")
        st.stop()

    # ── Filter & convert durations ─────────────────────────────────────────
    filtered_events = df_events.query(
        "routeName == @selected_route "
        "and stopName in @selected_stops "
        "and timeBlock == @selected_time_block"
    ).copy()
    filtered_events["stopDurationMinutes"] = filtered_events["stopDurationSeconds"] / 60

    # ── Outlier split ───────────────────────────────────────────────────────
    thr = filtered_events["stopDurationMinutes"].quantile(0.95)
    core = filtered_events[filtered_events["stopDurationMinutes"] <= thr].copy()
    outliers = filtered_events[filtered_events["stopDurationMinutes"] > thr].copy()

    # ── Holdover merge ──────────────────────────────────────────────────────
    # 1) normalize both sides
    core["route_key"] = core["routeName"].apply(normalize_route)
    core["stop_key"] = core["stopName"].apply(normalize_stop)
    core["stop_key"] = core["stop_key"].replace(
        {
            "logan cneter": "logan center for arts",
            "logan center": "logan center for arts",
            "drexel garage": "drexel garage",
        }
    )

    hold = load_holdover_data()
    hold["route_key"] = hold["route"].apply(normalize_route)
    hold["stop_key"] = hold["holdover_stop"].apply(normalize_stop)

    # 2) patch special cases twice (typo + proper name)
    special = {
        "law": "law school",
        "goldblatt pavillion": "goldblatt pavilion",
        "60th and ellis": "60th st. and ellis",
        "logan cneter": "logan center for arts",
        "logan center": "logan center for arts",
    }
    hold["stop_key"] = hold["stop_key"].replace(special)
    hold["stop_key"] = hold["stop_key"].replace(special)

    # 3) merge & flag
    merged = core.merge(hold, how="left", on=["route_key", "stop_key"])
    merged["isHoldover"] = merged["durationMinutes"].fillna(0) > 0

    # ── Chart 1: Avg by Stop ────────────────────────────────────────────────
    avg_stop = (
        merged.groupby(["stopName", "isHoldover"])["stopDurationMinutes"]
        .mean()
        .reset_index()
        .sort_values("stopDurationMinutes", ascending=False)
    )
    chart1 = (
        alt.Chart(avg_stop)
        .mark_bar()
        .encode(
            x=alt.X("stopDurationMinutes:Q", title="Avg Duration (min)"),
            y=alt.Y("stopName:N", sort="-x", title="Stop Name"),
            color=alt.Color(
                "isHoldover:N",
                scale=alt.Scale(domain=[True, False], range=["yellow", "steelblue"]),
                legend=alt.Legend(title="Holdover Stop"),
            ),
            tooltip=[
                alt.Tooltip("stopName:N", title="Stop Name"),
                alt.Tooltip("stopDurationMinutes:Q", title="Avg Duration"),
            ],
        )
        .properties(title="Avg Stop Duration (Holdovers in Yellow)", height=400)
    )
    st.altair_chart(chart1, use_container_width=True)

    # ── Chart 2: Avg by Time Block ─────────────────────────────────────────
    avg_time = (
        filtered_events.groupby("timeBlock")["stopDurationMinutes"].mean().reset_index()
    )
    mx = avg_time["stopDurationMinutes"].max()
    y_scale = alt.Scale(domain=[0, mx * 1.1]) if not math.isnan(mx) else alt.Scale()

    chart2 = (
        alt.Chart(avg_time)
        .mark_bar()
        .encode(
            x=alt.X(
                "timeBlock:N",
                title="Time of Day",
                axis=alt.Axis(labelAngle=-45, labelPadding=10),
            ),
            y=alt.Y("stopDurationMinutes:Q", title="Avg Duration (min)", scale=y_scale),
            tooltip=["timeBlock", "stopDurationMinutes"],
        )
        .properties(
            title="Avg Stop Duration Across Time Blocks",
            height=500,
            padding={"left": 50, "right": 10, "top": 20, "bottom": 80},
        )
    )
    st.write("")  # spacing
    st.altair_chart(chart2, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
elif page == "Frequency vs. Wait":
    events_df = load_stop_events()
    events_df = add_time_blocks(events_df)

    # ── Page header ─────────────────────────────────────────────────────
    st.title("🚍 UGo Shuttle: Stop Frequency vs. Wait Time")
    st.markdown("""
    **How to use this page:**
    1. Pick a **Time block** in the sidebar.
    2. Chart 1 shows how many stops fall into each service-frequency band.
    3. Chart 2 shows each stop’s average daily frequency vs. its average wait time.
    """)

    # ── Sidebar filter ───────────────────────────────────────────────────
    st.sidebar.header("Filter Options")
    time_blocks = sorted(events_df["timeBlock"].dropna().unique())
    selected_time_block = st.sidebar.selectbox("Select Time Period:", time_blocks)

    # ── Filter & convert wait to minutes ────────────────────────────────
    block_df = events_df[events_df["timeBlock"] == selected_time_block].assign(
        waitMin=lambda d: d["stopDurationSeconds"] / 60
    )
    clip_val = block_df["waitMin"].quantile(0.95)
    core_df = block_df[block_df["waitMin"] <= clip_val].copy()

    # ── Compute per-stop avg daily visits & avg wait ────────────────────
    daily_counts = (
        core_df.groupby(["stopName", core_df["arrivalTime"].dt.date])
        .size()
        .reset_index(name="daily_count")
    )
    stats = (
        daily_counts.groupby("stopName")["daily_count"]
        .mean()
        .reset_index(name="avg_daily_count")
        .merge(
            core_df.groupby("stopName")["waitMin"].mean().reset_index(name="avg_wait"),
            on="stopName",
        )
    )

    # ── Bucket into frequency bands ──────────────────────
    RARE_THRESHOLD = 2
    OCCASIONAL_THRESHOLD = 6
    FREQUENT_THRESHOLD = 12

    # ── Bucket into human-readable frequency bands ──────────────────────────
    def bucket(freq: float) -> str:
        """Return a service-frequency band name based on average daily visit count."""
        if freq < RARE_THRESHOLD:
            return "Rare (<2/day)"
        elif freq < OCCASIONAL_THRESHOLD:
            return "Occasional (2–5/day)"
        elif freq < FREQUENT_THRESHOLD:
            return "Frequent (6–11/day)"
        else:
            return "Very Frequent (12+/day)"

    stats["freqBucket"] = stats["avg_daily_count"].apply(bucket)
    band_order = [
        "Rare (<2/day)",
        "Occasional (2–5/day)",
        "Frequent (6–11/day)",
        "Very Frequent (12+/day)",
    ]
    band_counts = (
        stats.groupby("freqBucket")
        .size()
        .reindex(band_order, fill_value=0)
        .rename_axis("Frequency Band")
        .reset_index(name="Num Stops")
    )

    # ── Chart 1: Bar chart with full labels ──────────────────────────────
    chart1 = (
        alt.Chart(band_counts)
        .mark_bar()
        .encode(
            x=alt.X(
                "Frequency Band:N",
                sort=band_order,
                title="Service Frequency Band",
                axis=alt.Axis(
                    labelAngle=0,
                    labelAlign="center",
                    labelFontSize=12,
                    titleFontSize=14,
                    labelLimit=200,
                ),
            ),
            y=alt.Y(
                "Num Stops:Q",
                title="Number of Stops",
                axis=alt.Axis(labelFontSize=12, titleFontSize=14),
            ),
            tooltip=["Frequency Band", "Num Stops"],
        )
        .properties(
            title={"text": "Stops by Service Frequency Band", "fontSize": 16},
            width=700,
            height=300,
        )
    )
    st.altair_chart(chart1, use_container_width=True)

    # ── Chart 2: Scatter of frequency vs. wait with trend line ──────────
    base = alt.Chart(stats).encode(
        x=alt.X("avg_daily_count:Q", title="Avg Daily Stop Visits"),
        y=alt.Y("avg_wait:Q", title="Avg Wait (min)"),
        tooltip=["stopName", "avg_daily_count", "avg_wait"],
    )
    points = base.mark_point(size=60, opacity=0.6)
    trend = base.transform_regression("avg_daily_count", "avg_wait").mark_line(
        color="red"
    )
    scatter = (points + trend).properties(
        title="Stop Frequency vs. Average Wait", width=700, height=400
    )
    st.altair_chart(scatter, use_container_width=True)

    # ── Key Takeaways ────────────────────────────────────────────────────
    st.markdown("### Key Takeaways")
    st.markdown("""
    - The **Frequent (6–11/day)** band contains the largest share of stops.
    - The **downward trend** confirms that stops served more often generally have shorter waits.
    - **Rare (<2/day)** stops suffer the longest waits, indicating potential service gaps.
    """)


elif page == "Bus Stop Variance Explorer":
    stop_events_df = load_stop_events()
    stop_events_df = assign_expected_frequencies(stop_events_df)

    st.sidebar.header("Filter Options")
    frequencies = (
        stop_events_df["expectedFreq"].dropna().astype(int).sort_values().unique()
    )
    selected_freq = st.sidebar.selectbox(
        "Expected Frequency (min):",
        options=frequencies,
        format_func=lambda x: f"{x} min",
    )

    stop_events_df = stop_events_df[stop_events_df["expectedFreq"] == selected_freq]
    stop_events_df = stop_events_df[stop_events_df["expectedFreq"].notna()]
    _, variances, medians = process_arrival_times(stop_events_df)

    routes = variances["routeName"].unique()
    selected_route = st.sidebar.selectbox("Route:", sorted(routes))

    view = st.sidebar.radio(
        "Metric:", ["Standard Deviation of Wait Time", "Median Wait Time"]
    )

    st.title("UGo Shuttle Variance Explorer")

    st.markdown("""

    This page investigates the consistency of arrivals of a given stop on a given bus route, calculated based on time between consecutive stop events at each stop for every route.

    The sidebar has three filters:
    - Expected frequency of arrivals, or how often a given shuttle is supposed to run
    - The metric being calculated, either the standard deviation of wait times or the median
    - The route being displayed, which will show all stops along that route
        - Some routes have different expected frequencies during different times of day; their stop events are split under multiple filters.

    Use this page to explore patterns in wait times across UGo shuttles. For example, the **Downtown Campus Connector** has an advertised median wait time of 20 minutes, but every stop has an observed wait time between 22 minutes (Goldblatt) and 41 minutes (Gleacher), making it rather unreliable.

    """)

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
        .properties(width=700, height=500, title={"text": title, "anchor": "middle"}),
        use_container_width=True,
    )


elif page == "Time Series Analysis":
    st.title("🚍 Intra-Month Passenger Load Variability")
    st.markdown("Weekly ridership trends for a selected route and month.")
    st.markdown("### 🔍 Data Exploration")
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
        index="week_day", columns="month_week", values="passengerLoad", observed=True
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

    st.markdown("### 🔍 Key Takeaways")
    st.markdown(
        """
        - Midweek ridership is higher than on Mondays or Fridays, suggesting peak usage happens Tuesday to Thursday.
        - Final week shows lower traffic, possibly because fewer students are arriving on or leaving campus.
        """
    )

elif page == "Bunching Exploration":
    # Load the data
    stop_events_df = load_stop_events()
    stop_events_df = assign_expected_frequencies(stop_events_df)
    st.title("Heaway by Scheduled Frequency")
    st.markdown("""
    This page investigates experienced headway for each 'scheduled headway' groups.
    Calculated by calculating actual gap between buses at the stops.
    - Click 'Show headway table' to see the data in table format.

    """)
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

elif page == "Connector Bunching Map":
    st.title("Downtown Connector – Stop-level Bunching")
    st.markdown("""
    This page investigates the rate of bunching in the downtown connector shuttle route in the user-selected timeframe.
    Calculated based on time between consecutive stop events at each stop for every route.
    - Use the sidebar to select the timeframe which you are interested in.
    - Click each stop for detailed information.
        - The color of the stop represents the bunching rate
        - The name and bunching rate at the stop is displayed when clicked.
    - Click 'Show underlying numbers' to see the data in table format.

    """)

    # ── Google Maps API key ──────────────────────────────────────────────
    api_key = os.environ["GOOGLE_MAP_KEY"]  # make sure this is loaded

    # ── Stop coordinates ────────────────────────────────────────────────
    STOP_COORDS = {
        "Gleacher Center": (41.88964, -87.62196),
        "Rockefeller Chapel": (41.78779, -87.59664),
        "E Randolph St & S Michigan Ave": (41.88430, -87.62383),
        "S Michigan Ave/Roosevelt": (41.86795, -87.62397),
        "S (Upper) Wacker Dr & W Adams St": (41.87950, -87.63701),
        "S Lake Park Ave & E Hyde Park Blvd": (41.80279, -87.58782),
        "N (Upper) Wacker Dr & W Madison St": (41.88205, -87.63712),
        "S Lake Park & E 53rd St": (41.79952, -87.58716),
        "55th Street & University": (41.79497, -87.59787),
        "UCHICAGO Medicine - River East": (41.89192, -87.61817),
        "Goldblatt Pavilion": (41.78778, -87.60380),
        "UCHICAGO Medicine - South Loop": (41.86968, -87.63950),
        "Roosevelt Station": (41.86729, -87.62686),
    }
    coord_df = (
        pd.DataFrame.from_dict(STOP_COORDS, orient="index", columns=["lat", "lon"])
        .reset_index()
        .rename(columns={"index": "stopName"})
    )

    # ── Load + preprocess ALL events once (no hour filter yet) ─────────
    ROUTE_KEY = "Downtown Campus Connector"
    base_df = assign_expected_frequencies(load_stop_events())
    base_df = base_df[base_df["routeName"].str.contains(ROUTE_KEY, na=False)]
    base_df = (
        base_df.assign(date=base_df["arrivalTime"].dt.date)
        .sort_values(["stopName", "date", "arrivalTime"])
        .assign(
            prev_arrival=lambda d: d.groupby(["stopName", "date"])["arrivalTime"].shift(
                1
            )
        )
        .assign(
            headway_min=lambda d: (
                d["arrivalTime"] - d["prev_arrival"]
            ).dt.total_seconds()
            / 60
        )
        .dropna(subset=["headway_min", "expectedFreq"])
    )

    # ── Hour-range slider → subset for the map ─────────────────────────
    hr_start, hr_end = st.slider(
        "Select hour range",
        0,
        23,
        (7, 10),
        1,
        format="%0dh",
        help="Arrivals whose *hour* falls in this range are counted.",
    )
    sub_df = base_df[base_df["arrivalTime"].dt.hour.between(hr_start, hr_end)]
    bunch_sub = (
        sub_df.assign(is_bunched=sub_df["headway_min"] < 0.5 * sub_df["expectedFreq"])
        .groupby("stopName")["is_bunched"]
        .mean()
        .reset_index(name="bunching_rate")
    )

    # ── Merge coords & JSON serialise ─────────────────────────────────
    plot_df = (
        bunch_sub.merge(coord_df, on="stopName", how="left")
        .dropna(subset=["lat", "lon"])
        .assign(pct=lambda d: (d["bunching_rate"] * 100).round(1))
    )
    points_json = json.dumps(
        plot_df[["stopName", "lat", "lon", "pct"]].to_dict("records")
    )

    # ── Build the embedded HTML/JS page ───────────────────────────────
    color_js = """
      // -------- Viridis palette (light ➟ dark, 7 steps) ---------------
      const VIRIDIS = ['#FDE725','#B4DE2C','#6DCD59',
                       '#35B779','#1F9E89','#31688E','#440154'];

      // -------- Fixed boundaries (0,10,20,…,70) -----------------------
      const BREAKS = [0,10,20,30,40,50,60,70];

      // -------- Map a value → colour, using fixed buckets -------------
      function pctToColor(val){
        for(let i=0;i < BREAKS.length-1; i++){
          if(val < BREAKS[i+1]) return VIRIDIS[i];
        }
        return VIRIDIS[VIRIDIS.length-1];            // ≥ 70 %
      }

      // -------- Produce legend rows -----------------------------------
      function buildLegendRows(){
        const rows = [];
        for(let i=0; i<VIRIDIS.length; i++){
          const lower = BREAKS[i];
          const upper = (i < BREAKS.length-2) ? BREAKS[i+1] : null;
          const label = upper ? `${lower}&ndash;${upper}` : `≥ ${lower}`;
          rows.push({col: VIRIDIS[i], lab: label});
        }
        return rows;
      }
    """

    center_lat, center_lon = 41.828233054114776, -87.61244384080472
    html = f"""
<!DOCTYPE html><html><head>
  <style>
    html,body,#map{{height:100%;margin:0}}
    .legend-box{{background:#fff;padding:8px;border:1px solid #888;border-radius:4px;
                 font:12px/14px Arial;margin:8px}}
  </style>
  <script src="https://maps.googleapis.com/maps/api/js?key={api_key}"></script>
</head><body>
<div id="map"></div>
<script>
  const pts = {points_json};
  {color_js}

  // ---------- Create map ---------------------------------------------
  const map = new google.maps.Map(document.getElementById('map'), {{
    center: {{lat:{center_lat}, lng:{center_lon}}},
    zoom: 11,
    mapTypeControl:false, streetViewControl:false, fullscreenControl:false
  }});

  // ---------- Draw circles -------------------------------------------
  pts.forEach(p => {{
    const fillCol = pctToColor(p.pct);
    const circle = new google.maps.Circle({{
      strokeColor: '#FF073A',
      strokeOpacity: 1,
      strokeWeight: 2,
      fillColor: fillCol,
      fillOpacity: 0.8,
      map,
      center: {{lat:p.lat, lng:p.lon}},
      radius: 120
    }});

    const infow = new google.maps.InfoWindow();
    circle.addListener('click', () => {{
      infow.setContent(`<b>${{p.stopName}}</b><br>Bunching: ${{p.pct}} %`);
      infow.setPosition({{lat:p.lat, lng:p.lon}});
      infow.open({{map}});
    }});
  }});

  // ---------- Build fixed-bucket legend ------------------------------
  const legend = document.createElement('div');
  legend.className = 'legend-box';
  legend.innerHTML = '<b>Bunching&nbsp;(%)</b><br>';
  buildLegendRows().forEach(r => {{
    legend.innerHTML +=
      `<span style="display:inline-block;width:18px;height:10px;` +
      `background:${{r.col}};margin-right:4px"></span>${{r.lab}}<br>`;
  }});
  map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(legend);
</script>
</body></html>
"""
    components.html(html, height=520, scrolling=False)

    st.markdown(
        f"**Bunching definition:** headway < 50 % of scheduled frequency • "
        f"Time window: **{hr_start}:00 – {hr_end}:59**"
    )
    with st.expander("Show underlying numbers"):
        st.dataframe(
            plot_df[["stopName", "pct"]]
            .rename(columns={"pct": "bunching rate (%)"})
            .sort_values("bunching rate (%)", ascending=False)
        )

elif page == "NightRide Explorer":
    st.title("🚍 NightRide Explorer")
    st.markdown("### 🔍 Hourly Passenger Load Patterns on NightRide Routes")

    # 1. Load and filter data
    data = time_extraction()
    default_routes = ["North", "South", "East", "Central"]

    routes = st.multiselect(
        "Select NightRide routes to plot",
        options=default_routes,
        default=default_routes,
    )

    filtered = data[data["routeName"].isin(routes)].copy()

    # 2. Aggregate max passenger load by hour and route
    agg = filtered.groupby(["hour", "routeName"], as_index=False).agg(
        {"passengerLoad": "max"}
    )

    # 3. Create Altair line plot
    line_chart = (
        alt.Chart(agg)
        .mark_line(point=True)
        .encode(
            x=alt.X("hour:Q", title="Hour of Day"),
            y=alt.Y("passengerLoad:Q", title="Max Passenger Load"),
            color=alt.Color("routeName:N", title="Route"),
            tooltip=["hour", "routeName", "passengerLoad"],
        )
    )

    # 4. Add vertical rule at 4 PM (16:00)
    rule = (
        alt.Chart(pd.DataFrame({"hour": [16]}))
        .mark_rule(color="red", strokeDash=[5, 5])
        .encode(x="hour:Q")
    )

    text = (
        alt.Chart(
            pd.DataFrame(
                {
                    "hour": [16.1],
                    "passengerLoad": [agg["passengerLoad"].max() * 0.95],
                    "label": ["4 PM"],
                }
            )
        )
        .mark_text(align="left", color="red")
        .encode(x="hour:Q", y="passengerLoad:Q", text="label")
    )

    chart = (
        (line_chart + rule + text)
        .properties(title="Max Passenger Load by Hour (NightRide Routes)")
        .interactive()
    )

    # 5. Show chart
    st.altair_chart(chart, use_container_width=True)

    st.markdown("### 🔍 Key Takeaways")
    st.markdown(
        """
        - Evening peak begins at 4 PM (16:00) for most NightRide routes, with load ramping up significantly after that time.
        - The Central and East routes show the highest sustained demand between 16:00–21:00, indicating their role in transporting students during the evening.
        """
    )

    st.markdown("## 🛑 Top Stops by Total Passenger Load")

    # 6. Aggregate passenger load by stop
    top_stops = (
        filtered.groupby("stopName", as_index=False)
        .agg({"passengerLoad": "sum"})
        .sort_values("passengerLoad", ascending=False)
        .head(10)  # Top 10 stops
    )

    bar_chart = (
        alt.Chart(top_stops)
        .mark_bar()
        .encode(
            x=alt.X("passengerLoad:Q", title="Total Passenger Load"),
            y=alt.Y("stopName:N", sort="-x", title="Stop Name"),
            tooltip=["stopName", "passengerLoad"],
        )
        .properties(title="Top 10 Most Popular Stops (by Total Passenger Load)")
    )

    st.altair_chart(bar_chart, use_container_width=True)

    # 6. Filter data for late-night hours only (23:00 and later)
    LATE_NIGHT_START_HOUR = 23
    late_night = filtered[filtered["hour"] >= LATE_NIGHT_START_HOUR]

    # 7. Aggregate passenger load by stop
    top_late_stops = (
        late_night.groupby("stopName", as_index=False)
        .agg({"passengerLoad": "sum"})
        .sort_values("passengerLoad", ascending=False)
        .head(10)  # Show top 10 stops
    )

    # 8. Create bar chart
    bar_late_night = (
        alt.Chart(top_late_stops)
        .mark_bar()
        .encode(
            x=alt.X("passengerLoad:Q", title="Total Passenger Load"),
            y=alt.Y("stopName:N", sort="-x", title="Stop Name"),
            tooltip=["stopName", "passengerLoad"],
        )
        .properties(title="Top 10 Most Popular Stops After 11 PM")
    )

    st.altair_chart(bar_late_night, use_container_width=True)
