import QtQuick
import QtQuick3D

Node {
    id: node

    // Resources
    Texture {
        id: runwaydrawing_png_texture
        objectName: "runwaydrawing.png"
        generateMipmaps: true
        mipFilter: Texture.Linear
        source: "maps/runwaydrawing.png"
    }
    PrincipledMaterial {
        id: material_material
        objectName: "Material"
        baseColor: "#ffcccccc"
        baseColorMap: runwaydrawing_png_texture
        roughness: 0.5
    }

    // Nodes:
    Node {
        id: rootNode
        objectName: "RootNode"
        Model {
            id: cube
            objectName: "Cube"
            rotation: Qt.quaternion(0.707107, -0.707107, 0, 0)
            scale: Qt.vector3d(1500, 50000, 50)
            source: "meshes/cube_001_mesh.mesh"
            materials: [
                material_material
            ]
        }
    }

    // Animations:
}
