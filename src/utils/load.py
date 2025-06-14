"""Shared data loading functionality for UGo Transportation Streamlit apps."""

from pathlib import Path

import pandas as pd


def load_stop_events():
    """Load and prepare stop events data for analysis.

    Returns:
        pd.DataFrame: Processed stop events data with proper data types.
    """
    file_path = Path("data/processed/StopEvents.tsv")
    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path.resolve()}")
    stop_events_df = pd.read_csv(file_path, sep="\t")
    stop_events_df["arrivalTime"] = (
        pd.to_datetime(stop_events_df["arrivalTime"], utc=True)
        .dt.tz_convert("America/Chicago")
        .dt.tz_localize(None)
    )
    stop_events_df["departureTime"] = (
        pd.to_datetime(stop_events_df["departureTime"], utc=True)
        .dt.tz_convert("America/Chicago")
        .dt.tz_localize(None)
    )
    stop_events_df["stopDurationSeconds"] = pd.to_numeric(
        stop_events_df["stopDurationSeconds"], errors="coerce"
    )
    return stop_events_df


def load_stop_events_march():
    """Load and prepare 25-23-24 stop events data for analysis.

    Returns:
        pd.DataFrame: Processed stop events data with proper data types.
    """
    file_path = Path("data/processed/25-23-24-StopEvents.tsv")
    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path.resolve()}")
    stop_events_df = pd.read_csv(file_path, sep="\t")
    stop_events_df["arrivalTime"] = (
        pd.to_datetime(stop_events_df["arrivalTime"], utc=True)
        .dt.tz_convert("America/Chicago")
        .dt.tz_localize(None)
    )
    stop_events_df["departureTime"] = (
        pd.to_datetime(stop_events_df["departureTime"], utc=True)
        .dt.tz_convert("America/Chicago")
        .dt.tz_localize(None)
    )
    stop_events_df["stopDurationSeconds"] = pd.to_numeric(
        stop_events_df["stopDurationSeconds"], errors="coerce"
    )
    return stop_events_df


def process_arrival_times(stop_events_df):
    """Process arrival time differences and filter outliers.

    Args:
        stop_events_df (pd.DataFrame): Stop events data

    Returns:
        tuple: (filtered_df, variances_df, medians_df) - Filtered dataframe and summary stats
    """
    stop_events_df = stop_events_df[stop_events_df["expectedFreq"].notna()]
    stop_events_df["serviceDate"] = stop_events_df["arrivalTime"].dt.date
    df_sorted = stop_events_df.sort_values(
        by=["routeName", "stopName", "serviceDate", "arrivalTime"]
    )
    df_sorted["arrival_diff"] = (
        df_sorted.groupby(["routeName", "stopName", "serviceDate"])["arrivalTime"]
        .diff()
        .dt.total_seconds()
    ) / 60
    df_valid = df_sorted.dropna(subset=["arrival_diff"])

    # Filter outliers
    lower = df_valid["arrival_diff"].quantile(0.1)
    upper = df_valid["arrival_diff"].quantile(0.9)

    df_valid = df_valid.copy()
    df_valid["isOutlier"] = df_valid["arrival_diff"].apply(
        lambda x: x < lower or x > upper if pd.notna(x) else False
    )

    df_filtered = df_valid[~df_valid["isOutlier"]]

    # Calculate standard deviations
    variances = (
        df_filtered.groupby(["routeName", "stopName"])["arrival_diff"]
        .std()
        .reset_index()
    )
    variances = variances.rename(columns={"arrival_diff": "arrival_stdev"})

    # Calculate medians
    medians = (
        df_filtered.groupby(["routeName", "stopName"])["arrival_diff"]
        .median()
        .reset_index()
    )
    medians = medians.rename(columns={"arrival_diff": "arrival_median"})

    return df_filtered, variances, medians


def assign_expected_frequencies(stop_events_df):
    """Add expected frequency flags to stop events based on route and time."""
    stop_events_df["arrivalHour"] = stop_events_df["arrivalTime"].dt.hour
    stop_events_df["arrivalWeekday"] = stop_events_df[
        "arrivalTime"
    ].dt.dayofweek  # Monday=0, Sunday=6

    # schedule from UGo site
    schedule_map = {
        "Red Line/Arts Block": [
            ([0, 1, 2, 3, 4], 6.5, 21, 10)
        ],  # example: M-F 6:30am - 9:00pm
        "Friend Center/Metra": [([0, 1, 2, 3, 4], 5, 21, 30)],
        "Drexel": [([0, 1, 2, 3, 4], 5, 10, 10)],
        "Apostolic": [([0, 1, 2, 3, 4], 5, 10, 10)],
        "Apostolic/Drexel": [
            ([0, 1, 2, 3, 4], 10, 15, 15),
            ([0, 1, 2, 3, 4], 15, 24.5, 10),
        ],
        "Midway Metra": [
            ([0, 1, 2, 3, 4], 5.66, 9.66, 15),
            ([0, 1, 2, 3, 4], 15.5, 18.66, 15),
        ],
        "53rd Street Express": [
            ([0, 1, 2, 3, 4], 7, 8, 30),
            ([0, 1, 2, 3, 4], 8, 10.5, 15),
            ([0, 1, 2, 3, 4], 10.5, 18, 30),
        ],
        "Downtown Campus Connector": [
            ([0, 1, 2, 3, 4], 6.5, 22, 20),
        ],
        "Regents Express": [([0, 1, 2, 3, 4], 5.33, 21, 30)],
        "North": [
            ([0, 1, 2, 3, 4, 5, 6], 16, 23, 15),
            ([0, 1, 2, 3, 4, 5, 6], 23, 28, 30),
        ],
        "East": [
            ([0, 1, 2, 3, 4, 5, 6], 16, 23, 15),
            ([0, 1, 2, 3, 4, 5, 6], 23, 28, 30),
        ],
        "Central": [
            ([0, 1, 2, 3, 4, 5, 6], 16, 23, 15),
            ([0, 1, 2, 3, 4, 5, 6], 23, 28, 30),
        ],
        "South": [
            ([0, 1, 2, 3, 4, 5, 6], 16, 23, 15),
            ([0, 1, 2, 3, 4, 5, 6], 23, 28, 30),
        ],
        "South Loop Shuttle": [([4, 5], 18, 24.5, 60)],
    }

    def get_expected_freq(row):
        route = row["routeName"].strip()
        hour = row["arrivalHour"] + row["arrivalTime"].minute / 60
        weekday = row["arrivalWeekday"]

        EARLY_MORNING_CUTOFF_HOUR = 4

        if 0 <= hour < EARLY_MORNING_CUTOFF_HOUR:
            hour += 24

        schedules = schedule_map.get(route, [])
        for valid_days, start, end, freq in schedules:
            if weekday in valid_days and start <= hour < end:
                return freq
        return pd.NA

    stop_events_df["expectedFreq"] = stop_events_df.apply(get_expected_freq, axis=1)

    return stop_events_df


def calculate_route_mean_durations():
    """Calculate mean stop durations by route.

    Returns:
        pd.DataFrame: Mean stop durations by route
    """
    data_stopevents = load_stop_events()
    mean_durations = data_stopevents.groupby("routeName")["stopDurationSeconds"].mean()
    result = mean_durations.to_frame().T
    return result


def get_time_block(hour):
    """Returns a time block label based on the given hour.

    Args:
        hour (int): The hour of the day (0-23).

    Returns:
        str: A string indicating the time block.
    """
    MORNING_START = 5
    MORNING_END = 12
    AFTERNOON_END = 17
    EVENING_END = 21

    if MORNING_START <= hour < MORNING_END:
        return "Morning (5AM–12PM)"
    elif MORNING_END <= hour < AFTERNOON_END:
        return "Afternoon (12PM–5PM)"
    elif AFTERNOON_END <= hour < EVENING_END:
        return "Evening (5PM–9PM)"
    else:
        return "Night (9PM–5AM)"


def add_time_blocks(df):
    """Add time block labels to the dataframe.

    Args:
        df (pd.DataFrame): DataFrame with 'arrivalTime' column

    Returns:
        pd.DataFrame: DataFrame with added 'hour' and 'timeBlock' columns
    """
    time_block_df = df.copy()
    time_block_df["hour"] = time_block_df["arrivalTime"].dt.hour
    time_block_df["timeBlock"] = time_block_df["hour"].apply(get_time_block)
    return time_block_df


def add_traffic_flag(stop_events_df):
    """Adds a traffic flag (low, mid, high) to each stopName based on event frequency.

    Args:
        stop_events_df (pd.DataFrame): Stop events data.

    Returns:
        pd.DataFrame: Same dataframe with new 'trafficFlag' column.
    """
    stop_counts = stop_events_df["stopName"].value_counts()
    low_thresh = stop_counts.quantile(0.33)
    mid_thresh = stop_counts.quantile(0.66)

    def flag(count):
        if count <= low_thresh:
            return "low"
        elif count <= mid_thresh:
            return "mid"
        else:
            return "high"

    flag_df = (
        stop_counts.rename("eventCount")
        .reset_index()
        .rename(columns={"index": "stopName"})
    )
    flag_df["trafficFlag"] = flag_df["eventCount"].apply(flag)

    stop_events_df = stop_events_df.merge(
        flag_df[["stopName", "trafficFlag"]], on="stopName", how="left"
    )
    return stop_events_df


def load_holdover_data():
    """Returns a DataFrame mapping routeName to holdover stop and duration."""
    data = {
        "route": [
            "53rd Street Express",
            "Apostolic",
            "Apostolic/Drexel",
            "Central",
            "Downtown Campus Connector",
            "Drexel",
            "East",
            "Friend Center/Metra",
            "Gleacher Express",
            "Midway Metra AM",
            "Midway Metra PM",
            "North",
            "Red Line/Arts Block",
            "Regents Express",
            "South",
        ],
        "holdover_stop": [
            "Logan Center",
            "Kenwood/63rd",
            "Goldblatt Pavilion",
            "Reynolds Club",
            None,
            "Drexel Garage",
            "Reynolds Club",
            "Goldblatt Pavilion",
            None,
            None,
            None,
            "Reynolds Club",
            "Logan Center",
            "Law",
            "60th/Ellis",
        ],
        "duration": [
            "6 minutes",
            "7 minutes",
            "5 minutes",
            "4 minutes",
            None,
            "10 minutes",
            "3 minutes",
            "5 minutes",
            None,
            None,
            None,
            "3 minutes",
            "7 minutes",
            "6 minutes",
            "6 minutes",
        ],
    }

    holdover_df = pd.DataFrame(data)

    # add numeric minutes column (0 if no holdover)
    holdover_df["durationMinutes"] = (
        holdover_df["duration"]
        .fillna("0 minutes")
        .str.replace(" minutes", "", regex=False)
        .astype(int)
    )

    return holdover_df


def time_extraction():
    """Extract month number, week number, and day of week."""
    shuttle_data = load_stop_events_march()
    shuttle_data["date"] = shuttle_data["arrivalTime"].dt.date
    # extract the day of week (e.g., Mon, Tue...)
    shuttle_data["week_day"] = shuttle_data["arrivalTime"].dt.day_name()
    # extract month of the date
    shuttle_data["month"] = shuttle_data["arrivalTime"].dt.month_name()
    # extract day of the month
    shuttle_data["day_of_month"] = shuttle_data["arrivalTime"].dt.day
    # extract the hour of date
    shuttle_data["hour"] = shuttle_data["arrivalTime"].dt.hour
    # define week of month based on day ranges
    shuttle_data["month_week"] = pd.cut(
        shuttle_data["day_of_month"],
        bins=[0, 7, 14, 21, 28, 31],
        labels=[1, 2, 3, 4, 5],
        right=True,
    ).astype(int)
    return shuttle_data


def aggregate_by_time(df):
    """Aggregate passenger load by month, week, weekday, and route."""
    agg_df = (
        df.groupby(["month", "month_week", "week_day", "routeName", "date"])[
            "passengerLoad"
        ]
        .sum()
        .reset_index()
    )
    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    agg_df["week_day"] = pd.Categorical(
        agg_df["week_day"], categories=day_order, ordered=True
    )
    return agg_df


def get_route_level_ridership_vs_variance():
    """Returns one row per route with:

    - average std dev of arrival time
    - average daily ridership (from passengerLoad)
    """
    data = load_stop_events()
    _, variances, _ = process_arrival_times(data)
    route_variance = (
        variances.groupby("routeName")["arrival_stdev"].mean().reset_index()
    )
    data["date"] = data["arrivalTime"].dt.date
    daily_ridership = (
        data.groupby(["routeName", "date"])["passengerLoad"].sum().reset_index()
    )
    avg_daily_ridership = (
        daily_ridership.groupby("routeName")["passengerLoad"]
        .mean()
        .reset_index()
        .rename(columns={"passengerLoad": "avg_daily_boardings"})
    )
    result = route_variance.merge(avg_daily_ridership, on="routeName")
    return result
