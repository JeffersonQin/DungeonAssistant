import numpy as np
import copy


def transform_trajectory(points, transformation):
    """transform trajectory points with transformation matrix

    Args:
        points (o3d.geometry.PointCloud): trajectory points
        transformation (numpy.array): transformation matrix

    Returns:
        numpy.array: transformed trajectory points
    """
    if len(points) == 0:
        return points
    if points is None:
        return points

    # Convert the list of positions to a NumPy array
    positions_array = np.array(points)

    # Add a fourth column of ones to the positions array
    positions_homogeneous = np.hstack(
        (positions_array, np.ones((positions_array.shape[0], 1)))
    )

    # Apply the transformation matrix to the positions
    transformed_positions_homogeneous = np.dot(positions_homogeneous, transformation.T)

    # Remove the fourth column of ones from the transformed positions
    transformed_positions = transformed_positions_homogeneous[:, :3]

    return transformed_positions


def transform_clouds_and_trajectories(clouds, trajectories, matrices):
    """inplace transformation of array of clouds and trajectories

    Args:
        clouds (list[o3d.geometry.PointCloud]): clouds to be transformed
        trajectories (list[list[numpy.array]]): list of list of points to be transformed
        matrices (list[numpy.array]): list of transformation matrices
    """
    for i in range(min(len(matrices), len(clouds), len(trajectories))):
        clouds[i].transform(matrices[i])
        trajectories[i] = transform_trajectory(trajectories[i], matrices[i])


def retrieve_floor_plan(cloud, scale=100):
    """retrieve floor plan from point cloud

    Args:
        cloud: point cloud

    Returns:
        floor plan (image), min_coords, max_coords
    """
    cloud_xy = copy.deepcopy(np.asarray(cloud.points))[:, (0, 2)]
    # turn them into 2d floor plan image
    cloud_xy = np.round(cloud_xy * scale).astype(np.int32)

    min_coords = np.min(cloud_xy, axis=0)
    max_coords = np.max(cloud_xy, axis=0)
    image_size = np.abs(max_coords - min_coords) + 1
    cloud_xy -= min_coords

    floor_plan = np.zeros(image_size)
    floor_plan[cloud_xy[:, 0], cloud_xy[:, 1]] = 1

    return floor_plan, min_coords, max_coords
