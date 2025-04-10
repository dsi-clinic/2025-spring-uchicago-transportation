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
    df_filtered = df_valid[
        (df_valid["arrival_diff"] >= lower) & (df_valid["arrival_diff"] <= upper)
    ]

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
