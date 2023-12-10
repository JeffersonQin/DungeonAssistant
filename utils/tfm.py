import numpy as np


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
