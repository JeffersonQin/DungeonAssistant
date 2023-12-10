import json
import argparse
import os
import os.path as osp
import time
import open3d as o3d
import numpy as np
import copy
import matplotlib.pyplot as plt

from utils import o3dobj
from utils import io
from utils import tfm


parser = argparse.ArgumentParser()
parser.add_argument(
    "--pointcloud1",
    type=str,
    default="pointcloud1.ply",
    help="first point cloud file path (1 --[transform]-> 2)",
)
parser.add_argument(
    "--pointcloud2",
    type=str,
    default="pointcloud2.ply",
    help="second point cloud file path (1 --[transform]-> 2)",
)
parser.add_argument(
    "--trajectory1",
    type=str,
    default="trajectory1.json",
    help="first trajectory file path",
)
parser.add_argument(
    "--trajectory2",
    type=str,
    default="trajectory2.json",
    help="second trajectory file path",
)
parser.add_argument(
    "--fast_cache",
    type=str,
    default="",
    help="transformation cache of fast global registration if available. default is none",
)
parser.add_argument(
    "--icp_cache",
    type=str,
    default="",
    help="transformation cache of icp if available. default is none",
)
parser.add_argument(
    "--voxel_size_fgr",
    type=float,
    default=0.05,
    help="voxel size for global fast registration downsampling. default is 0.05",
)
parser.add_argument(
    "--voxel_size_icp",
    type=float,
    default=0.05,
    help="voxel size for icp downsampling. default is 0.05",
)
parser.add_argument("--skip_icp", action="store_true", help="skip icp and only run fgr")
parser.add_argument(
    "--transformed_trajectory_out",
    type=str,
    default="trajectory_1.jsonl",
    help="output trajectory of the transformed trajectory 1 (to trajectory 2)",
)
args = parser.parse_args()

pointcloud_file_path_1 = args.pointcloud1
pointcloud_file_path_2 = args.pointcloud2
trajectory_file_path_1 = args.trajectory1
trajectory_file_path_2 = args.trajectory2


def preprocess_point_cloud(pcd, voxel_size):
    """Downsamples the point cloud and computes the normals and FPFH features"""
    print(f":: Downsample with a voxel size {voxel_size:.3f}.")
    pcd_down = pcd.voxel_down_sample(voxel_size)

    radius_normal = voxel_size * 2
    print(f":: Estimate normal with search radius {radius_normal:.3f}.")
    pcd_down.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30)
    )

    radius_feature = voxel_size * 5
    print(f":: Compute FPFH feature with search radius {radius_feature:.3f}.")
    pcd_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        pcd_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_feature, max_nn=100),
    )
    return pcd_down, pcd_fpfh


def prepare_dataset(voxel_size):
    """Loads two point clouds and downsamples them."""
    print(":: Load two point clouds")
    source = o3d.io.read_point_cloud(pointcloud_file_path_1)
    target = o3d.io.read_point_cloud(pointcloud_file_path_2)

    source_down, source_fpfh = preprocess_point_cloud(source, voxel_size)
    target_down, target_fpfh = preprocess_point_cloud(target, voxel_size)
    return source, target, source_down, target_down, source_fpfh, target_fpfh


def execute_fast_global_registration(
    source_down, target_down, source_fpfh, target_fpfh, voxel_size
):
    """Performs fast global registration on the downsampled point clouds"""
    distance_threshold = voxel_size * 0.5
    print(
        f":: Apply fast global registration with distance threshold {distance_threshold:.3f}"
    )
    result = o3d.pipelines.registration.registration_fgr_based_on_feature_matching(
        source_down,
        target_down,
        source_fpfh,
        target_fpfh,
        o3d.pipelines.registration.FastGlobalRegistrationOption(
            maximum_correspondence_distance=distance_threshold
        ),
    )
    return result


def execute_vanilla_icp(source, target):
    """Performs vanilla ICP on the point clouds"""
    estimation = o3d.pipelines.registration.TransformationEstimationPointToPlane()

    max_correspondence_distance = 0.5
    # Convergence-Criteria for Vanilla ICP
    criteria = o3d.pipelines.registration.ICPConvergenceCriteria(
        relative_fitness=0.000001, relative_rmse=0.000001, max_iteration=50
    )

    result = o3d.pipelines.registration.registration_icp(
        source,
        target,
        max_correspondence_distance,
        estimation_method=estimation,
        criteria=criteria,
    )
    return result


if __name__ == "__main__":
    voxel_size_fgr = args.voxel_size_fgr
    voxel_size_icp = args.voxel_size_icp

    (
        cloud_1,
        cloud_2,
        cloud_1_down,
        cloud_2_down,
        cloud_1_fpfh,
        cloud_2_fpfh,
    ) = prepare_dataset(voxel_size=voxel_size_fgr)

    color_1 = [0.9450980392, 0.5764705882, 0.7098039216]
    color_2 = [0.11, 0.72, 0.89]

    cloud_1.paint_uniform_color(color_1)
    cloud_2.paint_uniform_color(color_2)

    cloud_1_down.paint_uniform_color(color_1)
    cloud_2_down.paint_uniform_color(color_2)

    # axis
    axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1, origin=[0, 0, 0])
    # unit block
    unit_block = o3dobj.get_o3d_unit_block_at_origin()

    # Visualize point cloud
    print("Initial preview ... Close window to continue")
    o3d.visualization.draw_geometries([cloud_1_down, cloud_2_down, axis, unit_block])

    # FGR
    transformation_fast = None
    if args.fast_cache != "":
        if osp.exists(args.fast_cache):
            print("Loading fast global registration cache from: ", args.fast_cache)
            transformation_fast = np.load(args.fast_cache, allow_pickle=True)

    if transformation_fast is None:
        print(
            "Fast global registration cache not found. Running fast global registration..."
        )
        start = time.time()

        with o3d.utility.VerbosityContextManager(
            o3d.utility.VerbosityLevel.Debug
        ) as cm:
            result_fast = execute_fast_global_registration(
                cloud_1_down, cloud_2_down, cloud_1_fpfh, cloud_2_fpfh, voxel_size_fgr
            )

        print(f"Fast global registration took {(time.time() - start):.3f} sec.\n")
        print(result_fast)

        transformation_fast = result_fast.transformation
        np.save("registration_fgr.npy", transformation_fast)

    cloud_1.transform(transformation_fast)

    # Visualize point cloud
    print("FGR preview ... Close window to continue")
    o3d.visualization.draw_geometries([cloud_1, cloud_2, axis, unit_block])

    # Vanilla ICP
    if not args.skip_icp:
        (
            _,
            _,
            cloud_1_down,
            cloud_2_down,
            _,
            _,
        ) = prepare_dataset(voxel_size=voxel_size_icp)

        cloud_1_down.transform(transformation_fast)

        transformation_icp = None
        if args.icp_cache != "":
            if osp.exists(args.icp_cache):
                print("Loading icp cache from: ", args.icp_cache)
                transformation_icp = np.load(args.icp_cache, allow_pickle=True)

        if transformation_icp is None:
            print("ICP cache not found. Running ICP...")

            s = time.time()

            with o3d.utility.VerbosityContextManager(
                o3d.utility.VerbosityLevel.Debug
            ) as cm:
                result_icp = execute_vanilla_icp(cloud_1_down, cloud_2_down)

            icp_time = time.time() - s

            print("Time taken by ICP: ", icp_time)
            print("Inlier Fitness: ", result_icp.fitness)
            print("Inlier RMSE: ", result_icp.inlier_rmse)

            transformation_icp = result_icp.transformation
            np.save("registration_icp.npy", transformation_icp)

        cloud_1.transform(transformation_icp)
    else:
        transformation_icp = np.identity(4)

    if trajectory_file_path_1 != "":
        # trajectory
        points_1, timestamps_1 = io.load_coordinates_and_timestamps(
            trajectory_file_path_1
        )

        # transformation
        points_1 = tfm.transform_trajectory(points_1, transformation_fast)
        points_1 = tfm.transform_trajectory(points_1, transformation_icp)

        trajectory_1 = o3dobj.get_o3d_trajectory_object(points_1, color=[1, 0, 0])
    else:
        trajectory_1 = None

    if trajectory_file_path_2 != "":
        points_2, _ = io.load_coordinates_and_timestamps(trajectory_file_path_2)
        trajectory_2 = o3dobj.get_o3d_trajectory_object(points_2, color=[0, 1, 0])
    else:
        trajectory_2 = None

    # save trajectory 1
    io.save_coodinates_and_timestamps(
        args.transformed_trajectory_out, points_1, timestamps_1
    )

    disp = [cloud_1, cloud_2, axis, unit_block, trajectory_1, trajectory_2]

    disp = [x for x in disp if x is not None]

    # Visualize point cloud
    o3d.visualization.draw_geometries(disp)
