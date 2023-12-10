import copy
import os
import os.path as osp
import open3d as o3d
import json
import numpy as np
import time
import datetime
import pytz


def load_point_clouds(
    pointcloud_base, pointcloud_prefix, merge_cnt, overlap_discard_num, voxel_size=0.0
):
    """load point clouds from a directory. the dir should look like
    pointcloud_base
    | -- xxx
        | -- {pointcloud_prefix}{xxx}_unaligned.ply
    | -- xxx
        | -- {pointcloud_prefix}{xxx}_unaligned.ply
    Args:
        pointcloud_base: base dir
        pointcloud_prefix: file name prefix
        merge_cnt: merge count, i.e. number of continuous point cloud files to merge together
            if merge_cnt = 1, then no merge. if merge_cnt = 2, then [0, 1, 2, 3] => [0+1, 2+3]
        overlap_discard_num: number of overlap frames to discard,
            i.e. [0, 1200], [600, 1800] => [0, 1200], [1200, 1800]
            and the number should be 600
        voxel_size (float, optional): voxel_size used for downsampling. Defaults to 0.0.

    Returns: (clouds, clouds_down)
        clouds: list of point clouds
        clouds_down: list of downsampled point clouds
        [locations]: list of list of locations
        [timestamps]: list of list of timestamps
    """
    clouds_down = []
    clouds = []
    position_arr = []
    timestamp_arr = []

    initial = True

    # load point clouds
    dirs = os.listdir(pointcloud_base)
    # sort
    dirs.sort()
    for num in dirs:
        cloud = o3d.io.read_point_cloud(
            osp.join(
                pointcloud_base,
                num,
                pointcloud_prefix + num + "_unaligned.ply",
            )
        )

        # if want to load transformation matrix
        if osp.exists(osp.join(pointcloud_base, num, "transform.npy")):
            transform = np.load(osp.join(pointcloud_base, num, "transform.npy"))
            cloud.transform(transform)

        clouds.append(cloud)

        print("loaded point cloud " + num)

        positions, timestamps = load_coordinates_and_timestamps(
            osp.join(pointcloud_base, num, pointcloud_prefix + num + ".jsonl")
        )

        if initial:
            initial = False
        else:
            positions = positions[overlap_discard_num:]
            timestamps = timestamps[overlap_discard_num:]

        position_arr.append(positions)
        timestamp_arr.append(timestamps)

    merged_clouds = []
    merged_positions = []
    merged_timestamps = []

    cnt = 0
    while cnt < len(clouds):
        print(f"merged point cloud starting {cnt}")

        cloud = copy.deepcopy(clouds[cnt])
        positions = copy.deepcopy(position_arr[cnt])
        timestamps = copy.deepcopy(timestamp_arr[cnt])
        for i in range(cnt + 1, min(cnt + merge_cnt, len(clouds))):
            cloud = cloud + clouds[i]
            positions.extend(position_arr[i])
            timestamps.extend(timestamp_arr[i])
        merged_clouds.append(cloud)
        merged_positions.append(positions)
        merged_timestamps.append(timestamps)
        cnt += merge_cnt

    print(f"point clouds merge complete, {len(merged_clouds)} generated")
    print(f"positions merge complete, {len(merged_positions)} generated")
    print(f"timestamps merge complete, {len(merged_timestamps)} generated")

    clouds = merged_clouds
    position_arr = merged_positions
    timestamp_arr = merged_timestamps

    if voxel_size == 0.0:
        return clouds, clouds_down, position_arr, timestamp_arr

    for cloud in clouds:
        # downsample
        cloud_down = cloud.voxel_down_sample(voxel_size=voxel_size)

        clouds_down.append(cloud_down)

    return clouds, clouds_down, position_arr, timestamp_arr


def load_coordinates_and_timestamps(json_file):
    """Given json file get coordinates and timestamps

    Args:
        json_file (str): json file dir

    Returns:
        points, timestamps
    """

    points = []
    timestamps = []

    initial_unix_timestamp = None
    initial_inacurate_timestamp = None

    with open(json_file, encoding="utf-8") as f:
        while True:
            line = f.readline()
            if not line:
                break
            if line.strip()[0] == "{":
                data = json.loads(line)

                if "location" in data.keys():
                    # new way of storing location
                    # custom way of script

                    # timestamp
                    timestamps.append(data["timestamp"])

                    # position
                    position = np.array(data["location"])
                else:
                    # legacy way of multiscan format
                    if initial_unix_timestamp is None:
                        if "timestamp_unix" not in data.keys():
                            # legacy version of data
                            # if used the orignal version of multiscan
                            # then there will not be timestamp_unix
                            # try to parse from filename
                            base_name = osp.basename(json_file)
                            timestamp_str = base_name[:15]
                            # convert to unix timestamp
                            # YYYYMMDDTHHMMSS
                            # Convert the current datetime to a Unix timestamp
                            datetime_obj = datetime.datetime.strptime(
                                timestamp_str, "%Y%m%dT%H%M%S"
                            )
                            initial_unix_timestamp = int(datetime_obj.timestamp())
                        else:
                            initial_unix_timestamp = data["timestamp_unix"]
                    if initial_inacurate_timestamp is None:
                        initial_inacurate_timestamp = data["timestamp"]

                    # calculate the timestamp
                    timestamp = (
                        data["timestamp"] - initial_inacurate_timestamp
                    ) + initial_unix_timestamp * 1000000000
                    timestamps.append(timestamp)

                    # position
                    transform = data["transform"]

                    # Extract the position from the transform matrix
                    position = transform[
                        -4:-1
                    ]  # Extract the first 3 elements of the last column
                    position = np.array([position[0], position[1], position[2]])

                points.append(position)

    return points, timestamps


def load_transformation_matrices(transformation_dir: str):
    """load transformation matrices under a directory, sort them.
        if no dir, return empty list

    Args:
        transformation_dir (str): transformation matrices directory

    Return a list of transformation matrices, sorted by filename
    """
    matrices = []

    if transformation_dir == "":
        return matrices

    file_names = os.listdir(transformation_dir)
    # sort
    file_names.sort()

    for matrix_name in file_names:
        matrix_dir = osp.join(transformation_dir, matrix_name)

        # load matrix
        matrix = np.load(matrix_dir, allow_pickle=True)

        matrices.append(matrix)

    return matrices


def save_coodinates_and_timestamps(json_file, points, timestamps):
    """save coordinates and timestamps to json file

    Args:
        json_file (str): json file dir
        points (list[np.array(3,)]): points to be saved
        timestamps (list[float]): timestamps to be saved
    """
    with open(json_file, "w", encoding="utf-8") as f:
        for i in range(len(points)):
            data = {}
            data["timestamp"] = timestamps[i]
            data["location"] = points[i].tolist()
            f.write(json.dumps(data) + "\n")
