"""Material coordinates on explicitly registered triangular surfaces.

Vertex UVs label material locations, independently of the registered 3-D shape.
Rebuild a physically validated mesh after changing its vertices; retain UVs to
transport a pattern through that declared deformation. No deformation solver,
automatic unwrap, cloth mechanics or contact inference is provided here.
"""
import numpy as np


def uv_array(values, count=None):
    try: uv = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc: raise ValueError('registered mapping needs finite Nx2 vertex_uv') from exc
    if uv.ndim != 2 or uv.shape[1] != 2 or len(uv) < 3 or not np.isfinite(uv).all():
        raise ValueError('registered mapping needs finite Nx2 vertex_uv')
    if count is not None and len(uv) != count:
        raise ValueError('vertex_uv count differs from registered geometry')
    return uv


def material_errors(part, spec):
    """Check the mapping against the actual part, never a parallel style mesh."""
    if spec.get('mapping', 'planar') != 'registered': return []
    try:
        if part.get('kind') != 'custom':
            raise ValueError('registered mapping requires indexed custom geometry')
        from registered_geometry import arrays
        vertices, faces = arrays(part['parameters'])
        uv = uv_array(spec.get('vertex_uv'), len(vertices))
        for face in faces:
            if len(face) != 3: raise ValueError('registered mapping requires explicit triangle faces')
            TriangleMap(vertices[face], uv[face])
        return []
    except (ValueError, TypeError, KeyError) as exc:
        return [part.get('id', '<part>') + ': ' + str(exc)]


def register_geometry(mesh, part, first_face):
    """Record only indices/counts; renderer still uses the registered mesh faces."""
    vertices = part['parameters']['vertices']; faces = part['parameters']['faces']
    if not hasattr(mesh, 'surface_vertex_counts'):
        mesh.surface_vertex_counts = {}; mesh.surface_face_indices = {}
    mesh.surface_vertex_counts[part['id']] = len(vertices)
    for index, face in enumerate(faces):
        mesh.surface_face_indices[first_face + index] = tuple(face)


def mesh_maps(mesh, materials):
    """Compile maps from the renderer's actual faces, including plan overrides."""
    result = {}
    for owner, spec in materials.items():
        if spec.get('mapping', 'planar') != 'registered': continue
        count = getattr(mesh, 'surface_vertex_counts', {}).get(owner)
        if count is None: raise ValueError(owner + ': registered material has no indexed geometry')
        uv = uv_array(spec.get('vertex_uv'), count)
        for index, name in mesh.face_owners.items():
            if name != owner: continue
            indices = getattr(mesh, 'surface_face_indices', {}).get(index)
            if indices is None or len(indices) != 3:
                raise ValueError(owner + ': registered material requires indexed triangle faces')
            result[index] = TriangleMap(mesh.faces[index][0], uv[list(indices)])
    return result


class TriangleMap:
    """Affine barycentric UV interpolation on one nondegenerate actual triangle.

    Sampling extrapolates outside the triangle because a rasterizer evaluates a
    bounding rectangle before masking it. The depth/ownership mask alone decides
    which samples are drawn. UV coordinates never alter that mask or geometry.
    """
    def __init__(self, vertices, vertex_uv):
        self.vertices = np.asarray(vertices, dtype=float)
        self.uv = uv_array(vertex_uv, 3)
        if self.vertices.shape != (3, 3) or not np.isfinite(self.vertices).all():
            raise ValueError('surface map needs three finite XYZ vertices')
        edges = self.vertices[1:] - self.vertices[0]
        if np.linalg.norm(np.cross(*edges)) <= 1e-9:
            raise ValueError('degenerate registered surface triangle')
        uv_edges = self.uv[1:] - self.uv[0]
        if abs(float(np.linalg.det(uv_edges))) <= 1e-12:
            raise ValueError('degenerate material UV triangle')
        self.inverse = np.linalg.solve(edges @ edges.T, edges)

    def coordinates(self, world):
        points = np.asarray(world, dtype=float)
        if points.shape[-1:] != (3,) or not np.isfinite(points).all():
            raise ValueError('finite XYZ surface samples required')
        bary = (points - self.vertices[0]) @ self.inverse.T
        uv = self.uv[0] + bary @ (self.uv[1:] - self.uv[0])
        return uv[..., 0], uv[..., 1]
