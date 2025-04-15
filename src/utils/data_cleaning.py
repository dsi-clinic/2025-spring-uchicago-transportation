"""Unzips raw data files and extracts relevant CSVs for processing."""

import zipfile
from pathlib import Path
import glob
import pandas as pd

def read_csv_files(matches):
    """Read all CSV files matching a given pattern in the input folder by finding the file recursively.

    Parameters:
        matches (str): The glob pattern to match files.
    """
    if not matches:
        raise FileNotFoundError("Target CSV not found in extracted zip content.")
    df_shuttles = pd.read_csv(matches[0])
    print(f"Loaded {df_shuttles.shape[0]} rows of data")
    if df_shuttles.shape[0] == 0:
        raise Exception(f"No rows loaded from {matches[0]}")
    return df_shuttles


if __name__ == "__main__":
    data_dir = Path("data")
    unzipped_dir = Path("data/unzipped")
    output_dir = Path("data/processed")

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
                zip_ref.extractall(unzipped_dir)
            input_folder = unzipped_dir
            print(f"Extracted contents to: {unzipped_dir}")
        except zipfile.BadZipFile:
            print(f"Error: The file at {zip_path} is not a valid zip file.")
            exit(1)
    else:
        print(f"No zip file found in: {data_dir}")
        input_folder = data_dir

    # Read 25-23-24-NumShuttlesRunning CSV
    try:
        matches = list(unzipped_dir.rglob("ClinicDump-25-23-24-NumShuttlesRunning.csv"))
        NumShuttleRunning = read_csv_files(matches)
        NumShuttleRunning.to_csv(
            output_dir / "25-23-24-NumShuttleRunning.tsv", sep="\t", index=False
        )
        print(f"TSV files for {matches} are created")
    except Exception as e:
        print(f"Error reading NumShuttlesRunning file: {e}")

    # Read 25-24-24-StopEvents CSV
    try:
        matches = list(unzipped_dir.rglob("ClinicDump-25-23-24-StopEvents.csv"))
        StopEvents = read_csv_files(matches)
        StopEvents.to_csv(output_dir / "25-23-24-StopEvents.tsv", sep="\t", index=False)
        print(f"TSV files for {matches} are created")
    except Exception as e:
        print(f"Error reading StopEvents file: {e}")

    # Read NumShuttlesRunning CSV
    try:
        matches = list(unzipped_dir.rglob("ClinicDump-NumShuttlesRunning.csv"))
        NumShuttleRunning = read_csv_files(matches)
        NumShuttleRunning.to_csv(
            output_dir / "NumShuttleRunning.tsv", sep="\t", index=False
        )
        print(f"TSV files for {matches} are created")
    except Exception as e:
        print(f"Error reading NumShuttlesRunning file: {e}")

    # Read StopEvents CSV
    try:
        matches = list(unzipped_dir.rglob("ClinicDump-StopEvents.csv"))
        StopEvents = read_csv_files(matches)
        StopEvents.to_csv(output_dir / "StopEvents.tsv", sep="\t", index=False)
        print(f"TSV files for {matches} are created")
    except Exception as e:
        print(f"Error reading StopEvents file: {e}")
