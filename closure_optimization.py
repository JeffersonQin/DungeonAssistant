import json
import argparse
import os
import os.path as osp
import time
import open3d as o3d
import numpy as np
import copy

from utils import io


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
parser.add_argument("--output_dir", type=str, help="output directory")
args = parser.parse_args()


def pairwise_registration(source, target):
    """Pairwise registration

    Args:
        source: source point cloud
        target: target point cloud

    Returns:
        transformation_icp: transformation matrix
        information_icp: information matrix
    """
    print("Apply point-to-plane ICP")
    icp_coarse = o3d.pipelines.registration.registration_icp(
        source,
        target,
        max_correspondence_distance_coarse,
        np.identity(4),
        o3d.pipelines.registration.TransformationEstimationPointToPlane(),
    )
    icp_fine = o3d.pipelines.registration.registration_icp(
        source,
        target,
        max_correspondence_distance_fine,
        icp_coarse.transformation,
        o3d.pipelines.registration.TransformationEstimationPointToPlane(),
        criteria=o3d.pipelines.registration.ICPConvergenceCriteria(
            relative_fitness=0.000001, relative_rmse=0.000001, max_iteration=50
        ),
    )
    transformation_icp = icp_fine.transformation
    information_icp = (
        o3d.pipelines.registration.get_information_matrix_from_point_clouds(
            source, target, max_correspondence_distance_fine, icp_fine.transformation
        )
    )
    return transformation_icp, information_icp


def full_registration(
    pcds,
    max_correspondence_distance_coarse,
    max_correspondence_distance_fine,
    only_circle=False,
    only_last=False,
):
    """Do full registration"""
    pose_graph = o3d.pipelines.registration.PoseGraph()
    odometry = np.identity(4)
    pose_graph.nodes.append(o3d.pipelines.registration.PoseGraphNode(odometry))
    n_pcds = len(pcds)
    # if only_circle:
    #     for source_id in range(n_pcds):
    #         print("Full registration: source_id: " + str(source_id))
    #         target_id = (source_id + 1) % n_pcds
    #         transformation_icp, information_icp = pairwise_registration(
    #             pcds[source_id], pcds[target_id]
    #         )
    #         odometry = np.dot(transformation_icp, odometry)
    #         pose_graph.nodes.append(
    #             o3d.pipelines.registration.PoseGraphNode(np.linalg.inv(odometry))
    #         )
    #         pose_graph.edges.append(
    #             o3d.pipelines.registration.PoseGraphEdge(
    #                 source_id,
    #                 target_id,
    #                 transformation_icp,
    #                 information_icp,
    #                 uncertain=False,
    #             )
    #         )
    # elif only_last:
    #     for source_id in range(n_pcds):
    #         print("Full registration: source_id: " + str(source_id))
    #         target_id = (source_id + 1) % n_pcds
    #         if target_id == 0:
    #             transformation_icp, information_icp = pairwise_registration(
    #                 pcds[source_id], pcds[target_id]
    #             )
    #             odometry = np.dot(transformation_icp, odometry)
    #             uncertain = True
    #         else:
    #             transformation_icp = np.identity(4)
    #             information_icp = (
    #                 o3d.pipelines.registration.get_information_matrix_from_point_clouds(
    #                     pcds[source_id], pcds[target_id], max_correspondence_distance_fine, transformation_icp
    #                 )
    #             )
    #             odometry = np.identity(4)
    #             uncertain = False
    #         pose_graph.nodes.append(
    #             o3d.pipelines.registration.PoseGraphNode(np.linalg.inv(odometry))
    #         )
    #         pose_graph.edges.append(
    #             o3d.pipelines.registration.PoseGraphEdge(
    #                 source_id,
    #                 target_id,
    #                 transformation_icp,
    #                 information_icp,
    #                 uncertain=uncertain,
    #             )
    #         )
    # else:
    for source_id in range(n_pcds):
        for target_id in range(source_id + 1, n_pcds):
            transformation_icp, information_icp = pairwise_registration(
                pcds[source_id], pcds[target_id]
            )
            print("Build o3d.pipelines.registration.PoseGraph")
            if target_id == source_id + 1:  # odometry case
                odometry = np.dot(transformation_icp, odometry)
                pose_graph.nodes.append(
                    o3d.pipelines.registration.PoseGraphNode(np.linalg.inv(odometry))
                )
                pose_graph.edges.append(
                    o3d.pipelines.registration.PoseGraphEdge(
                        source_id,
                        target_id,
                        transformation_icp,
                        information_icp,
                        uncertain=False,
                    )
                )
            else:  # loop closure case
                pose_graph.edges.append(
                    o3d.pipelines.registration.PoseGraphEdge(
                        source_id,
                        target_id,
                        transformation_icp,
                        information_icp,
                        uncertain=True,
                    )
                )
    return pose_graph


voxel_size = 0.02
pcds, pcds_down, _, _ = io.load_point_clouds(
    args.pointcloud_base,
    args.pointcloud_prefix,
    args.merge_cnt,
    overlap_discard_num=0,
    voxel_size=voxel_size,
)


print("Full registration ...")

max_correspondence_distance_coarse = voxel_size * 150
max_correspondence_distance_fine = voxel_size * 15
with o3d.utility.VerbosityContextManager(o3d.utility.VerbosityLevel.Debug) as cm:
    pose_graph = full_registration(
        pcds_down,
        max_correspondence_distance_coarse,
        max_correspondence_distance_fine,
    )


print("Optimizing PoseGraph ...")

option = o3d.pipelines.registration.GlobalOptimizationOption(
    max_correspondence_distance=max_correspondence_distance_fine,
    edge_prune_threshold=0.1,
    reference_node=0,
    preference_loop_closure=2,
)
gloabl_criteria = o3d.pipelines.registration.GlobalOptimizationConvergenceCriteria()
gloabl_criteria.max_iteration = 200
with o3d.utility.VerbosityContextManager(o3d.utility.VerbosityLevel.Debug) as cm:
    o3d.pipelines.registration.global_optimization(
        pose_graph,
        o3d.pipelines.registration.GlobalOptimizationLevenbergMarquardt(),
        gloabl_criteria,
        option,
    )


print("Transform points and display")

color_1 = [0.9450980392, 0.5764705882, 0.7098039216]
color_2 = [0.11, 0.72, 0.89]

pcds_down_transformed = []

for point_id in range(len(pcds_down)):
    print(pose_graph.nodes[point_id].pose)
    pcds_down_transformed.append(copy.deepcopy(pcds_down[point_id]))
    pcds_down_transformed[point_id].transform(pose_graph.nodes[point_id].pose)

    pcds_down_transformed[point_id].paint_uniform_color(color_1)
    pcds_down[point_id].paint_uniform_color(color_2)

    np.save(
        osp.join(args.output_dir, f"transform_{point_id:02d}.npy"),
        pose_graph.nodes[point_id].pose,
    )

o3d.visualization.draw_geometries(pcds_down + pcds_down_transformed)
