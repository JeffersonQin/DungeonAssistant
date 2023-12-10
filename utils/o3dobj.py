import open3d as o3d


def get_o3d_unit_block_at_origin():
    """Returns a unit block at origin"""
    # visualize a box (0,0,0) -> (1,1,1)
    print("Let's draw a box using o3d.geometry.LineSet.")
    points = [
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [1, 1, 0],
        [0, 0, 1],
        [1, 0, 1],
        [0, 1, 1],
        [1, 1, 1],
    ]
    lines = [
        [0, 1],
        [0, 2],
        [1, 3],
        [2, 3],
        [4, 5],
        [4, 6],
        [0, 4],
        [1, 5],
        [2, 6],
        [5, 7],
        [6, 7],
        [3, 7],
    ]
    colors = [[1, 0, 0] for _ in range(len(lines) - 3)]
    # [0,0,1] for the (1,1,1) coordinate, others are [1,0,0]
    for _ in range(3):
        colors.append([0, 0, 1])
    line_set = o3d.geometry.LineSet(
        points=o3d.utility.Vector3dVector(points),
        lines=o3d.utility.Vector2iVector(lines),
    )
    line_set.colors = o3d.utility.Vector3dVector(colors)

    return line_set


def get_o3d_trajectory_object(points, color=(1, 0, 0)):
    """Returns an o3d LineSet object from a list of points

    Args:
        points (list[np.array(3,)]): points to be visualized
        color (tuple, optional): Defaults to (1, 0, 0).
    """

    def transform_o3d_format(points):
        """Converts a list of points to o3d geometry for visualization"""
        lines = []
        for i in range(len(points) - 1):
            lines.append([i, i + 1])
        return points, lines

    points, lines = transform_o3d_format(points)

    colors = [color for _ in range(len(lines))]

    trajectory_set = o3d.geometry.LineSet(
        points=o3d.utility.Vector3dVector(points),
        lines=o3d.utility.Vector2iVector(lines),
    )
    trajectory_set.colors = o3d.utility.Vector3dVector(colors)

    return trajectory_set
