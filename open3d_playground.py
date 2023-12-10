import open3d as o3d
import numpy as np

from utils import o3dobj


def main():
    # at origin, plot axis
    axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1, origin=[0, 0, 0])
    # visualize a box (0,0,0) -> (1,1,1)
    unit_block = o3dobj.get_o3d_unit_block_at_origin()

    vis = o3d.visualization.Visualizer()
    vis.create_window()

    vis.add_geometry(axis)
    vis.add_geometry(unit_block)

    # sphere mesh
    radius = 1.0
    mesh = o3d.geometry.TriangleMesh.create_sphere(radius=radius)
    mesh.compute_vertex_normals()
    color = [1, 0, 0]
    mesh.paint_uniform_color(color)

    vis.add_geometry(mesh)

    i = 0
    d = 'up'
    j = 0
    freq = 5
    unit = 0.1
    height = 5

    while True:
        j = (j + 1) % freq

        if j == 0:
            if d == 'up' and i < height / unit:
                mesh.translate(np.array([0, unit, 0]))
                i += 1
            elif d == 'up' and i >= height / unit:
                d = 'down'
            elif d == 'down' and i > 0:
                mesh.translate(np.array([0, -unit, 0]))
                i -= 1
            elif d == 'down' and i <= 0:
                d = 'up'

        vis.update_geometry(mesh)

        vis.poll_events()
        vis.update_renderer()


if __name__ == "__main__":
    main()
