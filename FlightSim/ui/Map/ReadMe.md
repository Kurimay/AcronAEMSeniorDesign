# Map

Uses OpenStreetMap and MapTiler api to create map.
MapTiler allows the custom style that removes roads and highlights airports.  This is stored in style.json, and inside style.json is my (Kurimay) API key.  So if the map is not working, try putting your own API key there.

maplibre-gl.css and maplibre-gl.js are required documents for Maptiler I think.

map.py then calls the MapTiler API and draws the map, where the center of the map is at the location of the aircraft.  There is also some 2d graphics placed on top.
