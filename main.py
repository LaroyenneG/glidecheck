from typing import Final
import requests
import csv
from io import StringIO
import geopy
from geopy.distance import geodesic
from lxml import etree
import matplotlib.pyplot as plt

MAX_GLIDE_RATIO: Final[float] = 60.0

AIRPORTS_DATA_URL: Final[str] = "https://ourairports.com/data/airports.csv"


def download_airports_csv() -> str:
    try:
        response = requests.get(AIRPORTS_DATA_URL, verify=False)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise Exception(f"Failed to download airports data: {str(e)}")


def load_airports_data():
    csv_data = download_airports_csv()
    csv_reader = csv.DictReader(StringIO(csv_data))
    return list(csv_reader)


def parse_tcx_gps_data_in_tcx(file_path):
    ns = {
        'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'
    }

    tree = etree.parse(file_path)
    root = tree.getroot()

    results = []

    trackpoints = root.xpath('.//tcx:Trackpoint', namespaces=ns)

    for tp in trackpoints:
        lat = tp.xpath('./tcx:Position/tcx:LatitudeDegrees/text()', namespaces=ns)
        lon = tp.xpath('./tcx:Position/tcx:LongitudeDegrees/text()', namespaces=ns)
        alt = tp.xpath('./tcx:AltitudeMeters/text()', namespaces=ns)

        if lat and lon and alt:
            results.append((
                float(lat[0]),
                float(lon[0]),
                float(alt[0])
            ))

    return results


def search_nearest_airport(flight_data, airports):
    nearest_airport = None
    min_distance = float('inf')

    points = [flight_data[0], flight_data[len(flight_data) // 2], flight_data[1]]
    for point in points:
        point_coords = (point[0], point[1])
        for airport in airports:
            if airport['latitude_deg'] and airport['longitude_deg']:
                airport_coords = (float(airport['latitude_deg']), float(airport['longitude_deg']))
                distance = geodesic(point_coords, airport_coords).kilometers
                if distance < min_distance:
                    min_distance = distance
                    nearest_airport = airport

    return nearest_airport


def compute_glide_ratio(airport, point):
    terrain_elevation = float(airport["elevation_ft"]) / 3.28
    terrain_latitude = float(airport["latitude_deg"])
    terrain_longitude = float(airport["longitude_deg"])
    terrain_min_alt = terrain_elevation + 250

    distance_m = geodesic((terrain_latitude, terrain_longitude), (point[0], point[1])).meters

    altitude = (point[2] - terrain_min_alt)

    return distance_m / altitude if altitude > 0 and distance_m > 1000 else 0


def compute_glide_ratios(airport, fd):
    glide_ratios = []
    for point in fd:
        glide_ratio = compute_glide_ratio(airport, point)
        if glide_ratio > 0:
            glide_ratios.append(min(max(glide_ratio, 0), MAX_GLIDE_RATIO))
    return glide_ratios


def main():
    airports = load_airports_data()
    print("airports found: ", len(airports))

    file = "C:\\Users\\guill\Downloads\\activity_19502971901.tcx"
    fd = parse_tcx_gps_data_in_tcx(file)

    airport = search_nearest_airport(fd, airports)

    print("Airport found: ", airport["ident"])

    glide_ratios = compute_glide_ratios(airport, fd)

    plt.figure(figsize=(10, 6))
    plt.plot(range(len(glide_ratios)), glide_ratios)
    plt.title('Glide Ratios Over Time')
    plt.xlabel('Point Number')
    plt.ylabel('Glide Ratio')
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()
