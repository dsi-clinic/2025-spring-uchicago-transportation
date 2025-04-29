"""Unzips raw data files and extracts relevant CSVs for processing."""

import zipfile
from pathlib import Path

import pandas as pd


def read_csv_files(pattern):
    """Read all CSV files matching a given pattern in the input folder.

    Parameters:
        pattern (str): The glob pattern to match files.
    """
    df_shuttles = pd.read_csv(pattern)
    print(f"Loaded {df_shuttles.shape[0]} rows of data")
    if df_shuttles.shape[0] == 0:
        raise Exception(f"No rows loaded from {pattern}")
    return df_shuttles

def load_data():
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
            print(f"Extracted contents to: {output_dir}")
        except zipfile.BadZipFile:
            print(f"Error: The file at {zip_path} is not a valid zip file.")
            exit(1)
    else:
        print(f"No zip file found in: {data_dir}")
        input_folder = data_dir  # fallback to raw folder

    # Read 25-23-24-NumShuttlesRunning CSV
    try:
        pattern = "ClinicDump-25-23-24-NumShuttlesRunning.csv"
        url = "https://uchicago.box.com/shared/static/qyu4niqtd4lnsixgix4twsvsko1t9hfd.csv"
        NumShuttleRunning = read_csv_files(url)
        NumShuttleRunning.to_csv(
            output_dir / "25-23-24-NumShuttleRunning.tsv", sep="\t", index=False
        )
        print(f"TSV files for {pattern} are created")
    except Exception as e:
        print(f"Error reading NumShuttlesRunning file: {e}")

    # Read 25-24-24-StopEvents CSV
    try:
        pattern = "ClinicDump-25-23-24-StopEvents.csv"
        url = "https://uchicago.box.com/shared/static/2xhk7qazepe3xpmsenpzwoeuc4qwk48q.csv"
        StopEvents = read_csv_files(url)
        StopEvents.to_csv(output_dir / "25-23-24-StopEvents.tsv", sep="\t", index=False)
        print(f"TSV files for {pattern} are created")
    except Exception as e:
        print(f"Error reading StopEvents file: {e}")

    # Read NumShuttlesRunning CSV
    try:
        pattern = "ClinicDump-NumShuttlesRunning.csv"
        url = "https://uchicago.box.com/shared/static/178lhqvdkzyempiot2cvd9gep70n5upr.csv"
        NumShuttleRunning = read_csv_files(url)
        NumShuttleRunning.to_csv(
            output_dir / "NumShuttleRunning.tsv", sep="\t", index=False
        )
        print(f"TSV files for {pattern} are created")
    except Exception as e:
        print(f"Error reading NumShuttlesRunning file: {e}")

    # Read StopEvents CSV
    try:
        pattern = "ClinicDump-StopEvents.csv"
        url = "https://uchicago.box.com/shared/static/ycdc81r3eqkskz3tykjdj2rdbnvpoc6m.csv"
        StopEvents = read_csv_files(url)
        StopEvents.to_csv(output_dir / "StopEvents.tsv", sep="\t", index=False)
        print(f"TSV files for {pattern} are created")
    except Exception as e:
        print(f"Error reading StopEvents file: {e}")

def main():
    load_data()

if __name__ == "__main__":
    main()
