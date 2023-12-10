import open3d as o3d
import json
import time
import numpy as np
import argparse

from utils import o3dobj
from utils import io


# argument, one is the point cloud, the other is the trajectory
parser = argparse.ArgumentParser()
parser.add_argument(
    "--pointcloud", type=str, default="pointcloud.ply", help="point cloud file path"
)
parser.add_argument(
    "--trajectory", type=str, default="trajectory.jsonl", help="trajectory file path"
)
args = parser.parse_args()

pointcloud_file_path = args.pointcloud
trajectory_file_path = args.trajectory


def main():
    # Read point cloud
    cloud = o3d.io.read_point_cloud(pointcloud_file_path)

    # at origin, plot axis
    axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1, origin=[0, 0, 0])
    # visualize a box (0,0,0) -> (1,1,1)
    unit_block = o3dobj.get_o3d_unit_block_at_origin()
    # trajectory
    points, _ = io.load_coordinates_and_timestamps(trajectory_file_path)
    trajectory = o3dobj.get_o3d_trajectory_object(points, color=[1, 0, 0])

    # Visualize point cloud
    # o3d.visualization.draw_geometries([cloud, mesh_frame, line_set, trajectory_set])

    vis = o3d.visualization.Visualizer()
    vis.create_window()

    vis.add_geometry(cloud)
    vis.add_geometry(axis)
    vis.add_geometry(unit_block)
    vis.add_geometry(trajectory)

    radius = 0.1
    mesh = o3d.geometry.TriangleMesh.create_sphere(radius=radius)
    mesh.compute_vertex_normals()
    color = [0.9450980392, 0.5764705882, 0.7098039216]
    mesh.paint_uniform_color(color)

    vis.add_geometry(mesh)

    i = 0
    d = "forward"
    j = 0
    freq = 1
    last_position = np.array([0, 0, 0])

    while True:
        j = (j + 1) % freq

        if j == 0:
            mesh.translate(np.array(np.array(points[i]) - last_position))
            last_position = np.array(points[i])

            if d == "forward" and i < len(points) - 1:
                i += 1
            elif d == "forward" and i == len(points) - 1:
                d = "backward"
            elif d == "backward" and i > 0:
                i -= 1
            elif d == "backward" and i == 0:
                d = "forward"

            vis.update_geometry(mesh)

        vis.poll_events()
        vis.update_renderer()


if __name__ == "__main__":
    main()
