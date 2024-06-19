import requests
from datetime import datetime
import pandas as pd
import folium

all_features = []

# Initial URL of the GeoJSON data with a query for 2024 crashes (Max Record Count: 2000)
url = ("https://services.arcgis.com/p5v98VHDX9Atv3l7/arcgis/rest/services/CrashData_test/FeatureServer/0/query?"
       "outFields=*&where=CRASH_DT%20%3E=%20%272024-01-01%27%20AND%20CRASH_DT%20%3C=%20%272024-12-31%27&f=geojson")

offset = 0
while True:
    # Construct URL with offset
    page_url = f"{url}&resultOffset={offset}"

    response = requests.get(page_url)
    data = response.json()

    # Extract features from current page
    features = data["features"]
    all_features.extend(features)

    offset += 2000
    if len(features) < 2000:
        break

# Extract attributes and coordinates
rows = []
for feature in all_features:
    attributes = feature["properties"]
    coordinates = feature["geometry"]["coordinates"]
    attributes["longitude"] = coordinates[0]
    attributes["latitude"] = coordinates[1]

    # Convert CRASH_DT from Unix timestamp to MM/DD/YYYY format
    crash_date = attributes.get("CRASH_DT", "")
    if crash_date:
        # Convert milliseconds to seconds for the datetime conversion
        crash_date = datetime.utcfromtimestamp(crash_date / 1000).strftime("%m/%d/%Y")
        attributes["CRASH_DT"] = crash_date

    rows.append(attributes)

df = pd.DataFrame(rows)

# Sort by crash date and select the most recent 10,000 crashes
df["CRASH_DT"] = pd.to_datetime(df["CRASH_DT"], format="%m/%d/%Y")
df = df.sort_values(by="CRASH_DT", ascending=False).head(10000)

output_csv = "2024_va_crash_data.csv"
df.to_csv(output_csv, index=False)
print(f"CSV file saved: {output_csv}")

# Create a base map centered on average latitude and longitude
base_map = folium.Map(location=[df["latitude"].mean(), df["longitude"].mean()], zoom_start=12)

# Create a base map centered on Virginia with a zoom level to show the entire state
# virginia_coords = [37.4316, -78.6569]
# base_map = folium.Map(location=virginia_coords, zoom_start=7)

total_crashes = 0

# Get unique collision types from the dataset
unique_collision_types = df["COLLISION_TYPE"].unique()
# Define a color map for collision types
collision_type_colors = {}
colors = ["blue", "orange", "skyblue", "yellow", "limegreen", "red", "hotpink", "black"]
# Assign colors to unique collision types
for i, collision_type in enumerate(unique_collision_types):
    collision_type_colors[collision_type] = colors[i % len(colors)]  # Wrap around colors if more types than colors

# Add markers with popups to the map and count total crashes
for index, row in df.iterrows():
    # Access collision type and other attributes
    object_id = row["OBJECTID"] if "OBJECTID" in row else "N/A"
    document_nbr = row["DOCUMENT_NBR"] if "DOCUMENT_NBR" in row else "N/A"
    crash_military_tm = row["CRASH_MILITARY_TM"] if "CRASH_MILITARY_TM" in row else "N/A"
    crash_severity = row["CRASH_SEVERITY"] if "CRASH_SEVERITY" in row else "N/A"
    collision_type = row["COLLISION_TYPE"] if "COLLISION_TYPE" in row else "Other"

    # Determine marker color based on collision type
    color = collision_type_colors.get(collision_type, "black")

    # Construct popup HTML
    popup_text = f"""
        <b>Object ID:</b> {object_id}<br>
        <b>Document NBR:</b> {document_nbr}<br>
        <b>Crash Date:</b> {row.get("CRASH_DT", "N/A")}<br>
        <b>Crash Military Time:</b> {crash_military_tm}<br>
        <b>Crash Severity:</b> {crash_severity}<br>
        <b>Collision Type:</b> {collision_type}<br>
        """

    # Add marker to the map
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(base_map)

    total_crashes += 1

# Save the map to an HTML file
output_map = "2024_va_crash_data_map.html"
base_map.save(output_map)
print(f"Map saved: {output_map}")

print(f"Total crashes: {total_crashes}")
