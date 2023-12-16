import pandas as pd
import numpy as np
import argparse

from utils import io


parser = argparse.ArgumentParser()
parser.add_argument(
    "--trajectory",
    type=str,
    help="trajectory file path",
)
parser.add_argument(
    "--wifi",
    type=str,
    help="wifi file path",
)
parser.add_argument(
    "--output",
    type=str,
    default="signal.csv",
    help="output file path",
)
args = parser.parse_args()


if __name__ == "__main__":
    positions, timestamps = io.load_coordinates_and_timestamps(args.trajectory)
    wifi = pd.read_csv(args.wifi)

    # filter only AirPennNet
    wifi = wifi[wifi["SSID"] == "AirPennNet"]
    wifi = wifi[["BSSID", "level", "write_time"]]
    # level to float
    wifi["level"] = wifi["level"].astype(float)
    # average
    wifi = wifi.groupby(["BSSID", "write_time"]).mean().reset_index()
    # create table
    wifi = wifi.pivot(index="write_time", columns="BSSID", values="level").reset_index()

    # process trajectory
    timestamps = np.rint(np.asarray(timestamps) / 1e9)
    positions = np.asarray(positions)
    # concate timestamps and positions
    pos_data = np.concatenate((timestamps.reshape(-1, 1), positions), axis=1)
    # group by first column (timestamp)
    # then average the rest of the columns
    pos_data = pd.DataFrame(pos_data).groupby(0).mean()
    pos_data.reset_index(inplace=True)
    # convert column 0 from timestamp to form such as 2023-12-07 19:43:23
    # timezone is current timezone
    pos_data[0] = pd.to_datetime(pos_data[0], unit="s", utc=True).dt.tz_convert(
        "US/Eastern"
    )
    pos_data[0] = pos_data[0].dt.strftime("%Y-%m-%d %H:%M:%S")

    # merge
    merged_df = pd.merge(pos_data, wifi, left_on=0, right_on="write_time", how="left")
    merged_df.drop(columns=[0], inplace=True)

    merged_df.to_csv(args.output, index=False)
