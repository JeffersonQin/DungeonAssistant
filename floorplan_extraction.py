from utils import io
from utils import tfm
import open3d as o3d
import matplotlib.pyplot as plt
import argparse


parser = argparse.ArgumentParser()
parser.add_argument(
    "--pointcloud",
    type=str,
    default="dataset/processed/Equad-01/pc.ply",
    help="first point cloud file path (1 --[transform]-> 2)",
)
parser.add_argument(
    "--output",
    type=str,
    default="floorplan.png",
    help="output file path",
)
parser.add_argument(
    "--scale",
    type=int,
    default=10,
    help="scale of the floor plan",
)
args = parser.parse_args()

cloud = o3d.io.read_point_cloud(args.pointcloud)

floorplan, min_coords, max_coords = tfm.retrieve_floor_plan(cloud, scale=args.scale)

plt.imsave(args.output, floorplan, cmap="gray")
print(min_coords, max_coords)
