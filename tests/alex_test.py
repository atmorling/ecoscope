import ecoscope

# Initialize EcoMap by setting the zoom level and center
m = ecoscope.mapping.EcoMap(center=(0.0236, 37.9062), zoom=6, height=800, width=1000, static=False, control_scale=True, measure_control=False)

# Add two tiled basemaps (OSM and Google satellite)
m.add_basemap("OpenStreetMap")
m.add_tile_layer(
    url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    name="Google Satellite",
    attribution="Google",
    opacity=0.5,
)

m.add_scale_bar()


m.to_html("./ecomap.html")