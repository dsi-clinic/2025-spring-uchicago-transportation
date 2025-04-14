"""Unzips raw data files and extracts relevant CSVs for processing."""

import zipfile
from pathlib import Path

import pandas as pd


def read_csv_files(pattern):
    """Read all CSV files matching a given pattern in the input folder.

    Parameters:
        pattern (str): The glob pattern to match files.
    """
    matches = list(input_folder.glob(pattern))
    if matches:
        shuttle_file = matches[0]
        print(f"Found file: {shuttle_file}")
        df_shuttles = pd.read_csv(shuttle_file)
        print(f"Loaded {df_shuttles.shape[0]} rows of data")
        if df_shuttles.shape[0] == 0:
            raise Exception(f"No rows loaded from {pattern}")
    else:
        print("No file with 'NumShuttlesRunning' found.")

    return df_shuttles


if __name__ == "__main__":
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

    # Read NumShuttlesRunning CSV
    try:
        pattern = "*25-23-24-NumShuttlesRunning*.csv"
        NumShuttleRunning = read_csv_files(pattern)
        # TODO SAVE TO CORRECT DIRECTORY
        NumShuttleRunning.to_csv("NumShuttleRunning.tsv", sep="\t", index=False)
        print(f"TSV files for {pattern} are created")
    except Exception as e:
        print(f"Error reading NumShuttlesRunning file: {e}")

    # Read StopEvents CSV
    try:
        pattern = "*25-23-24-StopEvents*.csv"
        StopEvents = read_csv_files(pattern)
        # TODO SAVE TO CORRECT DIRECTORY
        StopEvents.to_csv(data_dir + "StopEvents.tsv", sep="\t", index=False)
        print(f"TSV files for {pattern} are created")
    except Exception as e:
        print(f"Error reading StopEvents file: {e}")
