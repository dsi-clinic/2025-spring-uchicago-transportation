
import pandas as pd
import streamlit as st

st.set_page_config(page_title="UGo Shuttle Rider Analysis", layout="wide")
st.title("🚍 UGo Shuttle Rider Waiting Patterns")
st.markdown("Analyze stop wait times by time of day and location to support better route and scheduling decisions.")


df = pd.read_csv("data/ClinicDump-StopEvents.csv")
df["arrivalTime"] = pd.to_datetime(df["arrivalTime"])
df["departureTime"] = pd.to_datetime(df["departureTime"])
df["stopDurationSeconds"] = pd.to_numeric(df["stopDurationSeconds"], errors="coerce")


df["hour"] = df["arrivalTime"].dt.hour


def get_time_block(hour):
    if 5 <= hour < 12:
        return "Morning (5AM–12PM)"
    elif 12 <= hour < 17:
        return "Afternoon (12PM–5PM)"
    elif 17 <= hour < 21:
        return "Evening (5PM–9PM)"
    else:
        return "Night (9PM–5AM)"

df["timeBlock"] = df["hour"].apply(get_time_block)


st.sidebar.header("Filter Options")
selected_stops = st.sidebar.multiselect("Select Stop(s):", options=sorted(df["stopName"].dropna().unique()), default=[])
selected_time_blocks = st.sidebar.multiselect("Select Time of Day:", options=df["timeBlock"].unique(), default=df["timeBlock"].unique())


filtered_df = df[
    (df["timeBlock"].isin(selected_time_blocks)) &
    (df["stopName"].isin(selected_stops) if selected_stops else True)
]

st.markdown(f"### Showing data for {len(filtered_df)} stop events")

st.write("#### ⏱️ Average Stop Duration by Stop")
avg_duration_by_stop = filtered_df.groupby("stopName")["stopDurationSeconds"].mean().sort_values(ascending=False)
st.bar_chart(avg_duration_by_stop)

st.write("#### ⏰ Average Stop Duration by Time of Day")
avg_duration_by_time = filtered_df.groupby("timeBlock")["stopDurationSeconds"].mean()
st.bar_chart(avg_duration_by_time)

# Optional: show table
if st.checkbox("Show filtered raw data"):
    st.dataframe(filtered_df)
