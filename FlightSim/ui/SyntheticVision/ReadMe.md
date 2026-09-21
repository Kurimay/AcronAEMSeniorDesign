# Synthetic Vision

This is completely unnecessary but I thought it would be cool so that is mostly why I made it.

The synthetic vision system uses PyQt6-3D to make the 3d graphics. You can press T to toggle it.  Right now it is kind of useless because we don't have collision with the terrain, but the idea is that collision would be added so that the synthetic vision is actually useful.

The terrain mesh is made from a 2 degree by 2 degree area height map around the Twin Cities.  Height and water maps were obtained from usgs.gov, Shuttle Radar Topography Mission (SRTM).

These maps were downloaded as geotiff. They were combined and converted to png using QGIS software.
bigterrain.qml builds the terrain with water and runways, while terrainbuild.py makes it a PyQt window and sets up the camera.

Runways are obtained from OpenStreetMap using the Overpass API. airportgetter.py gets airports longitude, latitude, heading, length and width if they are listed.  Unfortunately many runways are missing data, so not all runways are actually build in our program.

The runway in the program is a model and texture that I made.  It is a pain to get any custom mesh into PyQt3d because I just got a bunch of errors when trying to import an FBX or OBJ.  You have to use Balsam to convert the FBX.  For example when I did this, the input was funway.fbx, and the output was Runway.qml, /maps, and /meshes.  There is a forum post somewhere with a console command, but I don't have the link to it and I cant find it. Sorry.