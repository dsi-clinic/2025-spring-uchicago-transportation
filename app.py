"""Multipage Streamlit app for UGo Transportation analysis."""

import json
import re

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
        "Rider Waiting Patterns by Stop",
        "Rider Waiting Patterns by Traffic Level",
        "Bus Stop Variance Explorer",
        "Time Series Analysis",
        "Bunching Exploration",
        "Connector Bunching Map",
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
if page == "Rider Waiting Patterns by Stop":
    st.markdown("""
    **How to use this page:**
    1. Expand **Filters** to choose your **Route**, one or more **Stops**, and a **Time block**.
    2. **Top chart:** Average stop duration per stop (95th-pct outliers removed).
       - Holdover stops are highlighted in **yellow**.
    3. **Bottom chart:** Average stop duration _across all_ time blocks for your selection.
    4. Expand the **Outliers** section at the bottom to inspect individual events above the 95th percentile.
    """)

    # ── Data load & filters ───────────────────────────────────────────────
    df_events = load_stop_events()
    df_events = add_time_blocks(df_events)
    df_events = add_traffic_flag(df_events)

    with st.expander("🔍 Filters", expanded=False):
        c1, c2, c3 = st.columns([2, 3, 2])
        with c1:
            routes = sorted(df_events["routeName"].dropna().unique())
            selected_route = st.selectbox("Select Route:", routes)
        with c2:
            stops = (
                df_events.query("routeName == @selected_route")["stopName"]
                .dropna()
                .unique()
            )
            selected_stops = st.multiselect("Select Stops:", sorted(stops))
        with c3:
            tblocks = sorted(df_events["timeBlock"].dropna().unique())
            selected_time_block = st.selectbox("Select Time Period:", tblocks)

    if not selected_stops:
        st.info("Please select at least one stop above to see the charts.")
        st.stop()

    filtered_events = df_events.query(
        "routeName == @selected_route "
        "and stopName in @selected_stops "
        "and timeBlock == @selected_time_block"
    ).copy()
    filtered_events["stopDurationMinutes"] = filtered_events["stopDurationSeconds"] / 60

    # ── Outlier split ────────────────────────────────────────────────────
    thr = filtered_events["stopDurationMinutes"].quantile(0.95)
    core = filtered_events[filtered_events["stopDurationMinutes"] <= thr].copy()
    outliers = filtered_events[filtered_events["stopDurationMinutes"] > thr].copy()

    # ── Holdover merge ───────────────────────────────────────────────────
    # 1) normalize both sides
    core["route_key"] = core["routeName"].apply(normalize_route)
    core["stop_key"] = core["stopName"].apply(normalize_stop)
    core["stop_key"] = core["stop_key"].replace(
        {
            "logan cneter": "logan center for arts",  ##proper name
            "logan center": "logan center for arts",  ##catch misspelling
            "drexel garage": "drexel garage",
        }
    )

    hold = load_holdover_data()
    hold["route_key"] = hold["route"].apply(normalize_route)
    hold["stop_key"] = hold["holdover_stop"].apply(normalize_stop)

    # 2) patch in our handful of special cases
    special_stop_map = {
        "law": "law school",  # “Law” → “Law School (N)”
        "goldblatt pavillion": "goldblatt pavilion",  # fix typo
        "60th and ellis": "60th st. and ellis",  # drop “(SE Corner)”
        "logan cneter": "logan center for arts",  # catch misspelling
        "logan center": "logan center for arts",  # proper name
    }
    hold["stop_key"] = hold["stop_key"].replace(special_stop_map)
    hold["stop_key"] = hold["stop_key"].replace(special_stop_map)

    # 3) merge on the unified keys
    merged = core.merge(
        hold,
        how="left",
        on=["route_key", "stop_key"],
    )

    # 4) flag holdovers
    merged["isHoldover"] = merged["durationMinutes"].fillna(0) > 0

    # ── Charts ────────────────────────────────────────────────────────────

    # Avg by Stop
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

    # ── Avg by Time Block  ────────────────
    avg_time = (
        filtered_events.groupby("timeBlock")["stopDurationMinutes"].mean().reset_index()
    )

    chart2 = (
        alt.Chart(avg_time)
        .mark_bar()
        .encode(
            x=alt.X(
                "timeBlock:N",
                title="Time of Day",
                axis=alt.Axis(labelAngle=-45, labelPadding=10),  # tilt + pad labels
            ),
            y=alt.Y(
                "stopDurationMinutes:Q",
                title="Avg Duration (min)",
                scale=alt.Scale(
                    domain=[0, avg_time["stopDurationMinutes"].max() * 1.1]
                ),
            ),
            tooltip=["timeBlock", "stopDurationMinutes"],
        )
        .properties(
            title="Avg Stop Duration Across Time Blocks",
            height=500,  # taller chart
            padding={"left": 50, "right": 10, "top": 20, "bottom": 80},
        )
    )

    st.write("")  # add a blank line above
    st.altair_chart(chart2, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
elif page == "Rider Waiting Patterns by Traffic Level":
    df_events = load_stop_events()
    df_events = add_time_blocks(df_events)
    df_events = add_traffic_flag(df_events)

    selected_time_block = st.selectbox(
        "Select Time Period for Analysis:",
        options=sorted(df_events["timeBlock"].dropna().unique()),
    )
    df2 = df_events[df_events["timeBlock"] == selected_time_block].copy()
    df2["stopDurationMinutes"] = df2["stopDurationSeconds"] / 60

    thr2 = df2["stopDurationMinutes"].quantile(0.95)
    df2["isOutlier"] = df2["stopDurationMinutes"] > thr2

    st.markdown(
        f"> **Note:** {df2['isOutlier'].sum()} events exceed {thr2:.1f} min and are flagged as outliers."
    )
    st.title("🚍 UGo Shuttle Rider Waiting Patterns (By Traffic Level)")

    chart3 = (
        alt.Chart(df2)
        .mark_bar()
        .encode(
            x=alt.X(
                "trafficFlag:N", sort=["low", "mid", "high"], title="Traffic Level"
            ),
            y=alt.Y("count():Q", title="Number of Stops"),
            tooltip=["trafficFlag", "count()"],
        )
        .properties(title="Number of Stops by Traffic Level", width=900, height=400)
    )
    st.altair_chart(chart3, use_container_width=True)

    chart4 = (
        alt.Chart(df2)
        .mark_point(filled=True, size=60, opacity=0.6)
        .encode(
            x=alt.X("trafficFlag:N", title="Traffic Level"),
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
            height=400,
        )
    )
    st.altair_chart(chart4, use_container_width=True)


elif page == "Bus Stop Variance Explorer":
    stop_events_df = load_stop_events()
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
    stop_events_df = stop_events_df[stop_events_df["expectedFreq"].notna()]
    _, variances, medians = process_arrival_times(stop_events_df)

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

elif page == "Connector Bunching Map":
    st.title("Downtown Connector – Stop-level Bunching")

    # ── Google Maps API key ------------------------------------
    api_key = st.secrets.get("GOOGLE_MAPS_KEY")

    # ── Coordinates for the stops -----------------
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

    # ── calculate bunching: can be changed -------------------------
    ROUTE_KEY = "Downtown Campus Connector"
    temp_df = assign_expected_frequencies(load_stop_events())
    temp_df = temp_df[temp_df["routeName"].str.contains(ROUTE_KEY, na=False)]
    temp_df = (
        temp_df.assign(date=temp_df["arrivalTime"].dt.date)
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

    hr_start, hr_end = st.slider(
        "Select hour range",
        0,
        23,
        (7, 10),
        1,
        format="%0dh",
        help="Arrivals whose *hour* falls in this range are counted.",
    )
    temp_df = temp_df[temp_df["arrivalTime"].dt.hour.between(hr_start, hr_end)]
    bunching = (
        temp_df.assign(
            is_bunched=temp_df["headway_min"] < 0.5 * temp_df["expectedFreq"]
        )
        .groupby("stopName")["is_bunched"]
        .mean()
        .reset_index(name="bunching_rate")
    )

    # 3 ── merge coords & serialize to JSON -----------------------
    plot_df = (
        bunching.merge(coord_df, on="stopName", how="left")
        .dropna(subset=["lat", "lon"])
        .assign(pct=lambda d: (d["bunching_rate"] * 100).round(1))
    )
    points_json = json.dumps(
        plot_df[["stopName", "lat", "lon", "pct"]].to_dict("records")
    )
    # 4 ── build the tiny HTML/JS page ----------------------------
    color_js = """
        // -------- viridis 7-bucket helper ---------------------------------
        function pctToColor(p){
            const lim = [0,15,30,45,60,75,90,100];
            // 7 viridis hex codes (light → dark)
            const col = ['#FDE725','#B4DE2C','#6DCD59',
                    '#35B779','#1F9E89','#31688E','#440154'];
            for(let i=0;i<lim.length-1;i++){
            if(p <= lim[i+1]) return col[i];
            }
            return col[col.length-1];
        }
    """

    center_lat, center_lon = 41.828233054114776, -87.61244384080472
    html = f"""
<!DOCTYPE html><html><head>
  <style>html,body,#map{{height:100%;margin:0}}</style>
  <script src="https://maps.googleapis.com/maps/api/js?key={api_key}"></script>
</head><body>
<div id="map"></div>
<script>
  const pts = {points_json};
  {color_js}

  const map = new google.maps.Map(document.getElementById('map'), {{
    center: {{lat:{center_lat}, lng:{center_lon}}},
    zoom: 11,
    mapTypeControl:false, streetViewControl:false, fullscreenControl:false
  }});

  pts.forEach(p => {{
    const col = pctToColor(p.pct);
    const circle = new google.maps.Circle({{
      strokeColor: col, strokeOpacity: 0.9, strokeWeight: 1,
      fillColor: col,   fillOpacity: 0.8,
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
</script>
</body></html>
"""
    components.html(html, height=520, scrolling=False)

    st.markdown(
        f"**Bunching definition:** headway < 50 % of scheduled frequency  •  "
        f"Time window: **{hr_start}:00 – {hr_end}:59**"
    )
    with st.expander("Show underlying numbers"):
        st.dataframe(
            plot_df[["stopName", "pct"]]
            .rename(columns={"pct": "bunching rate (%)"})
            .sort_values("bunching rate (%)", ascending=False)
        )
