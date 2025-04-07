"""Unzips raw data files and extracts relevant CSVs for processing."""

import zipfile
from pathlib import Path

import pandas as pd

data_dir = Path("data")
output_dir = Path("data/unzipped")

# Create output directory for unzipped files if it doesn't exist
output_dir.mkdir(parents=True, exist_ok=True)

# Search for zip files
zip_files = list(data_dir.glob("*.zip"))

# Step 1: Unzip if zip files exist
if zip_files:
    zip_path = zip_files[0]
    print(f"Zip file found: {zip_path}")
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(output_dir)
        input_folder = output_dir
        print(f"Extracted contents to: {output_dir}")
    except zipfile.BadZipFile:
        print(f"Error: The file at {zip_path} is not a valid zip file.")
        exit(1)
else:
    print(f"No zip file found in: {data_dir}")
    input_folder = data_dir  # fallback to raw folder

# Step 2: Read NumShuttlesRunning CSV
try:
    pattern = "*25-23-24-NumShuttlesRunning*.csv"
    matches = list(input_folder.glob(pattern))
    if matches:
        shuttle_file = matches[0]
        print(f"Found NumShuttlesRunning file: {shuttle_file}")
        df_shuttles = pd.read_csv(shuttle_file)
        print("Loaded NumShuttlesRunning data:\n", df_shuttles.head())
    else:
        print("No file with 'NumShuttlesRunning' found.")
except Exception as e:
    print(f"Error reading NumShuttlesRunning file: {e}")

# Step 3: Read StopEvents CSV
try:
    pattern = "*25-23-24-StopEvents*.csv"
    matches = list(input_folder.glob(pattern))
    if matches:
        stop_file = matches[0]
        print(f"Found StopEvents file: {stop_file}")
        df_stops = pd.read_csv(stop_file)
        print("Loaded StopEvents data:\n", df_stops.head())
    else:
        print("No file with 'StopEvents' found.")
except Exception as e:
    print(f"Error reading StopEvents file: {e}")