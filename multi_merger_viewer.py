import json
import argparse
import os
import os.path as osp
import time
import open3d as o3d
import numpy as np
import copy

from utils import o3dobj
from utils import io
from utils import tfm


parser = argparse.ArgumentParser()
parser.add_argument(
    "--pointcloud_base",
    type=str,
    help="base dir of point clouds",
)
parser.add_argument(
    "--pointcloud_prefix",
    type=str,
    help="prefix of point cloud file name",
)
parser.add_argument(
    "--merge_cnt",
    type=int,
    default=1,
    help="number of continuous (by folder names) point clouds to merge together",
)
parser.add_argument(
    "--transformation_dir",
    type=str,
    default="",
    help="directory storing transformation matrix files, default to be empty",
)
parser.add_argument(
    "--overlap_discard_num",
    type=int,
    default=0,
    help="number of overlap frames to discard",
)
parser.add_argument(
    "--pointcloud_out", type=str, default="out.ply", help="output point cloud file name"
)
parser.add_argument(
    "--trajectory_out",
    type=str,
    default="out.jsonl",
    help="output trajectory file name",
)
args = parser.parse_args()


def main():
    """Main function"""

    # axis
    axis_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
        size=1, origin=[0, 0, 0]
    )
    # unit block
    unit_block = o3dobj.get_o3d_unit_block_at_origin()

    # point clouds
    clouds, _, position_arr, timestamp_arr = io.load_point_clouds(
        args.pointcloud_base,
        args.pointcloud_prefix,
        args.merge_cnt,
        args.overlap_discard_num,
    )

    # transform clouds
    matrices = io.load_transformation_matrices(args.transformation_dir)
    tfm.transform_clouds_and_trajectories(clouds, position_arr, matrices)

    # trajectory
    # points
    points = []
    for positions in position_arr:
        points.extend(positions)
    trajectory = o3dobj.get_o3d_trajectory_object(points, color=[1, 0, 0])
    # timestamps
    timestamps = []
    for ts in timestamp_arr:
        timestamps.extend(ts)

    # merge point clouds
    cloud_out = copy.deepcopy(clouds[0])

    for cloud in clouds[1:]:
        cloud_out = cloud_out + copy.deepcopy(cloud)

    # save point cloud
    o3d.io.write_point_cloud(args.pointcloud_out, cloud_out)

    # save trajectory to jsonl
    io.save_coodinates_and_timestamps(args.trajectory_out, points, timestamps)

    # add more for visualization
    clouds.append(trajectory)
    clouds.append(axis_frame)
    clouds.append(unit_block)

    # Visualize point cloud
    o3d.visualization.draw_geometries(clouds)


if __name__ == "__main__":
    main()
