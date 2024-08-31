import os
from dotenv import load_dotenv
import asyncio
import aiohttp
import pandas as pd
import psycopg2
import folium

# Load environment variables from .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Initial URL of the GeoJSON data with a query for 2024 crashes
base_url = "https://services.arcgis.com/p5v98VHDX9Atv3l7/arcgis/rest/services/CrashData_test/FeatureServer/0/query?outFields=*&where=CRASH_DT%20%3E=%20%272024-01-01%27%20AND%20CRASH_DT%20%3C=%20%272024-12-31%27&f=geojson"


# Asynchronous function to fetch data from a single page
async def fetch_page(session, url):
    try:
        async with session.get(url) as response:
            return await response.json()
    except aiohttp.ClientError as e:
        print(f"HTTP request failed: {e}")
        return None


# Asynchronous function to fetch all data with pagination
async def fetch_all_pages(url):
    offset = 0
    all_features = []
    async with aiohttp.ClientSession() as session:
        while True:
            # Construct URL with pagination
            page_url = f"{url}&resultOffset={offset}"
            # Fetch data from the current page
            data = await fetch_page(session, page_url)
            features = data.get("features", [])
            # Add features to the list
            all_features.extend(features)

            if len(features) < 2000:
                break
            # Increment offset for the next page
            offset += 2000
    return all_features


# Main function to run the asynchronous fetch and process data
async def main():
    all_features = await fetch_all_pages(base_url)

    # Process data, convert to pandas DataFrame
    rows = []
    for feature in all_features:
        attributes = feature["properties"]
        geometry = feature.get("geometry")

        if geometry is not None:
            coordinates = geometry.get("coordinates")
            if coordinates:
                attributes["longitude"] = coordinates[0]
                attributes["latitude"] = coordinates[1]
            else:
                attributes["longitude"] = None
                attributes["latitude"] = None
        else:
            attributes["longitude"] = None
            attributes["latitude"] = None

        rows.append(attributes)

    df = pd.DataFrame(rows)

    # Convert Unix timestamps to readable dates
    df["CRASH_DT"] = pd.to_datetime(df["CRASH_DT"], unit="ms")

    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()

    cursor.execute("DROP TABLE crash_data")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crash_data (
            id SERIAL PRIMARY KEY,
            crash_id VARCHAR,
            crash_date DATE,
            severity VARCHAR,
            collision_type VARCHAR,
            longitude FLOAT,
            latitude FLOAT
        )
        """)
    conn.commit()

    # Insert data
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO crash_data (crash_id, crash_date, severity, collision_type, longitude, latitude)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (row.get("DOCUMENT_NBR"), row.get("CRASH_DT"), row.get("CRASH_SEVERITY"),
                  row.get("COLLISION_TYPE"), row.get("longitude"), row.get("latitude")))
    conn.commit()

    print("Data stored in PostgreSQL database.")

    # Query the most recent 10,000 crashes
    df_recent = pd.read_sql_query("""
            SELECT * FROM crash_data
            ORDER BY crash_date DESC
            LIMIT 10000
        """, conn)

    # Create a map with crash markers
    base_map = folium.Map(location=[df_recent["latitude"].mean(), df_recent["longitude"].mean()], zoom_start=12)

    unique_collision_types = df["COLLISION_TYPE"].unique()

    # Define a color palette with 16 distinct colors
    unique_colors = [
        "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2",
        "#D55E00", "#CC79A7", "#999999", "#F0E442", "#E69F00",
        "#56B4E9", "#009E73", "#0072B2", "#D55E00", "#CC79A7",
        "#999999"
    ]

    # Ensure there are at least 16 colors
    assert len(unique_colors) >= 16, "Need at least 16 colors for 16 collision types."

    # Assign a unique color to each collision type
    collision_type_colors = {collision_type: unique_colors[i % len(unique_colors)]
                             for i, collision_type in enumerate(unique_collision_types)}

    # Populate markers with data
    for _, row in df_recent.iterrows():
        if pd.notnull(row["latitude"]) and pd.notnull(row["longitude"]):
            color = collision_type_colors.get(row["collision_type"], "black")
            popup_text = f"""
                <b>Crash ID:</b> {row.get("crash_id", "N/A")}<br>
                <b>Crash Date:</b> {row.get("crash_date", "N/A")}<br>
                <b>Severity:</b> {row.get("severity", "N/A")}<br>
                <b>Collision Type:</b> {row.get("collision_type", "N/A")}<br>
                """
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_text, max_width=300)
            ).add_to(base_map)

    # Save the map to an HTML file
    output_map = "2024_crash_data_map.html"
    base_map.save(output_map)
    print(f"Map saved: {output_map}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    # Python environment
    asyncio.run(main())
