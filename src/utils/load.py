"""Shared data loading functionality for UGo Transportation Streamlit apps."""

import pandas as pd


def load_stop_events():
    """Load and prepare stop events data for analysis.

    Returns:
        pd.DataFrame: Processed stop events data with proper data types.
    """
    stop_events_df = pd.read_csv("data/ClinicDump-StopEvents.csv")
    stop_events_df["arrivalTime"] = pd.to_datetime(stop_events_df["arrivalTime"])
    stop_events_df["departureTime"] = pd.to_datetime(stop_events_df["departureTime"])
    stop_events_df["stopDurationSeconds"] = pd.to_numeric(
        stop_events_df["stopDurationSeconds"], errors="coerce"
    )
    return stop_events_df


def load_stop_events_march():
    """Load and prepare stop events data for analysis.

    Returns:
        pd.DataFrame: Processed stop events data with proper data types.
    """
    stop_events_df = pd.read_csv("data/ClinicDump-25-23-24-StopEvents.csv")
    stop_events_df["arrivalTime"] = pd.to_datetime(stop_events_df["arrivalTime"])
    stop_events_df["departureTime"] = pd.to_datetime(stop_events_df["departureTime"])
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
    df_sorted = stop_events_df.sort_values(by=["routeName", "stopName", "arrivalTime"])
    df_sorted["arrival_diff"] = (
        df_sorted.groupby(["routeName", "stopName"])["arrivalTime"]
        .diff()
        .dt.total_seconds()
    ) / 60
    df_valid = df_sorted.dropna(subset=["arrival_diff"])

    # Filter outliers
    lower = df_valid["arrival_diff"].quantile(0.05)
    upper = df_valid["arrival_diff"].quantile(0.95)

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
    stop_events_df["arrivalTime"] = pd.to_datetime(stop_events_df["arrivalTime"])
    stop_events_df["arrivalHour"] = stop_events_df["arrivalTime"].dt.hour
    stop_events_df["arrivalWeekday"] = stop_events_df[
        "arrivalTime"
    ].dt.dayofweek  # Monday=0, Sunday=6

    # schedule from UGo site
    schedule_map = {
        "Red Line/Arts Block": [
            ([0, 1, 2, 3, 4], 6.5, 21, 20)
        ],  # example: M-F 6:30am - 9:00pm
        "Friend Center/Metra": [([0, 1, 2, 3, 4], 5, 21, 30)],
        "Drexel": [([0, 1, 2, 3, 4], 5, 10, 10)],
        "Apostolic": [([0, 1, 2, 3, 4], 5, 10, 10)],
        "Apostolic/Drexel": [
            ([0, 1, 2, 3, 4], 10, 15, 15),
            ([0, 1, 2, 3, 4], 15, 24.5, 10),
        ],
        "Midway Metra": [
            ([0, 1, 2, 3, 4], 5.66, 9.66, 20),
            ([0, 1, 2, 3, 4], 15.5, 18.66, 20),
        ],
        "53rd Street Express": [
            ([0, 1, 2, 3, 4], 7, 8, 30),
            ([0, 1, 2, 3, 4], 8, 10.5, 15),
            ([0, 1, 2, 3, 4], 10.5, 18, 30),
        ],
        "Downtown Campus Connector": [([0, 1, 2, 3, 4], 6.5, 22, 20)],
    }

    def get_expected_freq(row):
        route = row["routeName"]
        hour = row["arrivalHour"] + row["arrivalTime"].minute / 60
        weekday = row["arrivalWeekday"]

        if "South Loop Shuttle" in route:
            return 60
        elif any(
            x in route for x in ["North", "South", "East", "Central", "Regents Express"]
        ):
            return 30

        for key, schedules in schedule_map.items():
            if key in route:
                for valid_days, start, end, freq in schedules:
                    if weekday in valid_days and start <= hour < end:
                        return freq
        return 30

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


def time_extraction():
    """Extract month number, week number, and day of week."""
    shuttle_data = load_stop_events_march()
    # extract the day of week (e.g., Mon, Tue...)
    shuttle_data["week_day"] = shuttle_data["arrivalTime"].dt.day_name()
    # extract month of the date
    shuttle_data["month"] = shuttle_data["arrivalTime"].dt.month_name()
    # extract day of the month
    shuttle_data["day_of_month"] = shuttle_data["arrivalTime"].dt.day
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
        df.groupby(["month", "month_week", "week_day", "routeName"])["passengerLoad"]
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
