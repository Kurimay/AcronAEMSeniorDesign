import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

View3D {
    id: mainView
    anchors.fill: parent

    environment: ExtendedSceneEnvironment { 
        clearColor: "#4061ac" 
        backgroundMode: SceneEnvironment.Color 

        fog: Fog {
            enabled: true
            color: "#4061ac" 
            depthEnabled: true
            depthNear: 500000 
            depthFar: 5000000
            density: 1
            depthCurve: 3
        }
    }

    // --- CAMERA ---
    Node {
        position: Qt.vector3d(nav.posX, nav.posY, nav.posZ)
        eulerRotation: Qt.vector3d(nav.pitch, -nav.hdg, -nav.roll)

        PerspectiveCamera {
            id: camera
            clipNear: 100
            clipFar: 10000000
            fieldOfView: 80
        }
    }

    // --- LIGHTING ---
    DirectionalLight { 
        eulerRotation.x: -30 
        brightness: 3
    }
    

    // --- COORDINATE MATH ---
    readonly property real refLat: 45.0  
    readonly property real refLon: -93.0 
    readonly property real mPerLat: 111120.0
    readonly property real mPerLon: 80000.0 

    function getPos(lat, lon, ele) {
        let xMeters = (lon - refLon) * mPerLon;
        let zMeters = (lat - refLat) * mPerLat;
        let yMeters = (ele || 186) - 5000;

        // MULTIPLY X and Z by 100 to match the 100x runway/map scale
        return Qt.vector3d(xMeters * 100, yMeters, -zMeters * 100);
    }

    Model {
        position: Qt.vector3d(0, 186, 0) 
        scale: Qt.vector3d(80000.0 * 2 , 259, 111120.0 * 2) 

        geometry: HeightFieldGeometry {
            source: "MSP_map_scaled.png"
            smoothShading: true
        }

        materials: [
            PrincipledMaterial {
                baseColor: "#4b9642"
                baseColorMap: Texture { source: "MSP_map_scaled_colors.png" }

                // Water mask
                //  use the emissive channel to show water
                emissiveMap: Texture { source: "invertedwatermask.png" }
                emissiveFactor: Qt.vector3d(0.01, 0.02, 0.15) 

                // High reflectivity
                metalnessMap: Texture { source: "invertedwatermask.png" }
                metalness: 0.7 

                roughnessMap: Texture { source: "invertedwatermask.png" }
                roughness: 0.05 

                specularAmount: 0.8
                specularTint: Qt.vector3d(0.8, 0.9, 1.0)
            }
        ]
    }

    // --- RUNWAY & AIRPORT RENDERER ---
    Repeater3D {
        model: runwayModel 

        delegate: Node {
            id: runwayNode
            position: getPos(modelData.lat, modelData.lon, modelData.elevation_m)

            // RUNWAY AS A custom model
            Runway {
                id: runwayModelInstance
                visible: modelData.type === "runway"

                property real targetWidth: modelData.width ?? 30.0
                property real targetLength: modelData.length ?? 1000.0

                scale: Qt.vector3d(
                    targetWidth / 30.0,
                    1.0,
                    targetLength / 1000.0
                )

                eulerRotation.y: (modelData.heading ?? 0) + 90
            }


            // AIRPORT CENTER MARKERS
            // Model {
            //     visible: modelData.type === "airport_center"
            //     geometry: SphereGeometry { radius: 8000 } 
            //     materials: [
            //         PrincipledMaterial {
            //             baseColor: "cyan"
            //             emissiveFactor: Qt.vector3d(0, 1, 1)
            //             specularAmount: 0.0
            //         }
            //     ]
            // }
        }
    }
}