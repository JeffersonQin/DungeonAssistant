import pandas as pd
import numpy as np
from utils import io
import argparse
import tqdm


# trajectory, wifi, dataset file, arg input
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
    "--dataset",
    type=str,
    help="dataset file path",
)
parser.add_argument(
    "--output",
    type=str,
    default="errors.npy",
    help="output file path",
)

args = parser.parse_args()


wifi = pd.read_csv(args.wifi)

dataset = pd.read_csv(args.dataset)
dataset.fillna(-100, inplace=True)


# filter only AirPennNet
wifi = wifi[wifi["SSID"] == "AirPennNet"]
wifi = wifi[["BSSID", "level", "write_time"]]
# level to float
wifi["level"] = wifi["level"].astype(float)
# average
wifi = wifi.groupby(["BSSID", "write_time"]).mean().reset_index()


# ground truth
positions, timestamps = io.load_coordinates_and_timestamps(args.trajectory)
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


# nearest neighbor
mac_addresses = list(dataset.columns[4:])
ds_signals = dataset.drop(columns=["1", "2", "3", "write_time"])


err = []

print("validation count: ", len(set(list(wifi["write_time"]))))

for time in tqdm.tqdm(set(list(wifi["write_time"]))):
    if time not in list(pos_data[0]):
        continue
    strength = []
    for mac in mac_addresses:
        if mac in list(wifi[wifi["write_time"] == time]["BSSID"]):
            strength.append(
                wifi[(wifi["write_time"] == time) & (wifi["BSSID"] == mac)][
                    "level"
                ].values[0]
            )
        else:
            strength.append(-100)
    distances = np.linalg.norm(ds_signals.values - np.asarray(strength), axis=1)
    nearest_neighbor_row = np.argmin(distances)
    prediction = np.asarray(dataset.values[nearest_neighbor_row][:3])
    ground_truth = np.asarray(pos_data[pos_data[0] == time].values[0, 1:])
    err.append(np.linalg.norm(prediction - ground_truth))

    print(
        "error:", err[-1], ", prediction:", prediction, ", ground_truth:", ground_truth
    )

err = np.asarray(err)

print(
    "mean:",
    np.mean(err),
    ", std:",
    np.std(err),
    ", median:",
    np.median(err),
    ", max:",
    np.max(err),
    ", min:",
    np.min(err),
)

q25 = np.percentile(err, 25)
q75 = np.percentile(err, 75)

print("q25:", q25, ", q75:", q75)

np.save(args.output, err)
