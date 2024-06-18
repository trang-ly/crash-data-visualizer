# Crash Data Visualizer
This project visualizes the most recent 10,000 car crashes in 2024 in Virginia using a Folium map. The data is fetched from a GeoJSON service, processed, and plotted with colors to differentiate crash types. Clicking on each crash marker will display a popup with basic information about the crash, such as the date, time, severity, type, etc. More detailed information is available in the data.

## Features

- **Data Fetching**: Fetches car crash data in chunks using pagination from a GeoJSON service specific to Virginia.
- **Data Processing**: Extracts attributes and coordinates from the data, converts crash dates from Unix timestamp to human-readable format, and sorts data by crash date.
- **Data Selection**: Selects the most recent 10,000 crashes for visualization to ensure optimal performance.
- **Data Saving**: Saves the processed data to a CSV file.
- **Map Visualization**: Plots the crashes on a Folium map with different colors representing different collision types and displays popups with basic crash information.
- **HTML Output**: Saves the map as an HTML file for easy sharing and viewing.

## File Description

- **`2024_va_crash_data_marker.py`**: Main script to fetch data, process it, and generate the map.
- **`2024_va_crash_data.csv`**: CSV file containing the processed crash data.
- **`2024_va_crash_data_map.html`**: HTML file with the interactive map.
- **`screenshots/`**: Directory containing example screenshots of the map.

## Notes
- The crash data used in this project is specific to Virginia. More details can be found at the [source data link](https://services.arcgis.com/p5v98VHDX9Atv3l7/arcgis/rest/services/CrashData_test/FeatureServer).
- The number of crashes to be plotted is set to the most recent 10,000 to ensure the map remains responsive and performs well.
- You can adjust the number of crashes to be plotted by modifying the **`head(10000)`** parameter in the script.

## Usage

1. **Clone the Repository:**
   ```sh
   git clone https://github.com/trang-ly/crash-data-visualizer.git
   cd crash-data-visualizer

2. **Install the Required Python Packages:**
   ```sh
   pip install requests pandas folium

3. **Run the Script:**
   ```sh
   python 2024_va_crash_data_marker.py

## Example Screenshots
Here are some example screenshots of the generated map:


