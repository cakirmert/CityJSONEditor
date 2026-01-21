"""
Mesh builder: converts CityJSON geometry boundaries into Blender meshes.
"""

import bpy

class Mesh:
    """Builds a Blender mesh object from CityJSON geometry boundaries."""

    def __init__(self, object, vertices, oid):
        # entire data of the object
        self.object = object
        # list of all vertices
        self.vertices = vertices
        # list which describes the faces mapped to the vertex indices
        self.vertexMaps = []
        # name/id of the object
        self.name = oid
        

    def extractVertexMapping(self):
        # create and store a list of the vertex mapping (faces)
        geometries = self.object.get('geometry', []) if isinstance(self.object, dict) else []
        for geom in geometries:
            boundaries = geom.get('boundaries') or []
            gtype = geom.get('type')
            if gtype == 'Solid':
                for shell in boundaries:
                    for face in shell:
                        if not face:
                            continue
                        # Only use the outer ring; holes are ignored to keep face counts aligned with semantics.
                        outer = face[0] if isinstance(face[0], list) else face
                        if outer:
                            self.vertexMaps.append(outer)
            elif gtype == 'MultiSurface':
                for face in boundaries:
                    if not face:
                        continue
                    outer = face[0] if isinstance(face[0], list) else face
                    if outer:
                        self.vertexMaps.append(outer)
            else:
                for face in boundaries:
                    if not face:
                        continue
                    if isinstance(face[0], list):
                        for ring in face:
                            if ring:
                                self.vertexMaps.append(ring)
                    else:
                        self.vertexMaps.append(face)
    
    def createBlenderMesh(self):
        # vertices used for defining blender meshes
        meshVertices = []
        # edges defined by vertex indices (not required if faces are made)
        edges = []
        # new face mapping values
        newFaces = []
        
        # Mapping from global vertex coordinates to local mesh index
        coord_to_idx = {}
        
        # only use vertices, that are part of the mesh
        for face in self.vertexMaps:
            # create new face array
            newFace = []
            # check vertex coordinate in face
            for value in face:
                try:
                    vertexCoords = tuple(self.vertices[value])
                except (IndexError, TypeError):
                    continue
                
                if vertexCoords in coord_to_idx:
                    newFace.append(coord_to_idx[vertexCoords])
                else:
                    new_idx = len(meshVertices)
                    meshVertices.append(list(vertexCoords))
                    coord_to_idx[vertexCoords] = new_idx
                    newFace.append(new_idx)
            # add the newly mapped face to the list of faces for the mesh
            if len(newFace) >= 3:
                newFaces.append(newFace)

        # creating a new mesh with the name of the object
        newMesh = bpy.data.meshes.new(self.name)
        # build the mesh from vertices and faces (edges not required)
        newMesh.from_pydata(meshVertices, edges, newFaces)
        # return the mesh so it can be handed over to the object  
        return newMesh    
        
    def execute(self):
        self.extractVertexMapping()
        mesh = self.createBlenderMesh()
        return mesh
