from pathlib import Path
from zipfile import ZipFile
import pandas as pd
import geopandas as gpd
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
from tqdm import tqdm

from const import (
    ZIP_DIR,
    EXTRACT_XML_DIR,
    OUTPUT_DIR,
    MERGE_FILE_PATTERN,
    FILTER_POLYGON_PATH,
    MERGED_SHAPEFILE_NAME,
)


def unzip_all_zipfiles(zip_dir: Path, output_dir: Path) -> None:
    # Iterate over all files in the specified directory
    for zip_file in tqdm(zip_dir.glob("*.zip")):
        with ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(output_dir)


def merge_all_xmls(xml_dir: Path) -> gpd.GeoDataFrame:
    df_list = []

    for xml_file in tqdm(xml_dir.glob(f"*{MERGE_FILE_PATTERN}*.xml")):
        polygons = extract_polygon_info(xml_file)
        df_list.append(polygons)

    merged_df = pd.concat(df_list, ignore_index=True)

    return gpd.GeoDataFrame(merged_df, geometry="geometry")


def extract_polygon_info(xml_file: str) -> gpd.GeoDataFrame:
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Namespace dictionary to handle XML namespaces
    namespaces = {
        "gml": "http://www.opengis.net/gml/3.2",
        "fgd": "http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema",
    }

    polygons = []

    # Iterate through each BldA element
    for blda in root.findall(".//fgd:BldA", namespaces):
        polygon_info = {}
        polygon_info["type"] = (
            blda.find(".//fgd:type", namespaces).text
            if blda.find(".//fgd:type", namespaces) is not None
            else None
        )

        # Extract polygon coordinates
        pos_list = blda.findall(".//gml:posList", namespaces)
        for pos in pos_list:
            coords = pos.text.strip().split()
            # Create a list of tuples for the coordinates
            polygon_info["coordinates"] = [
                (float(coords[i + 1]), float(coords[i]))
                for i in range(0, len(coords), 2)
            ]
            # Create a shapely Polygon object
            polygon_info["geometry"] = Polygon(polygon_info["coordinates"])
            del polygon_info["coordinates"]

        polygons.append(polygon_info)
    return gpd.GeoDataFrame(polygons)


def create_shapefile(gdf: gpd.GeoDataFrame, output_file: str) -> None:
    gdf.to_file(output_file, driver="ESRI Shapefile")


def filter_with_shp(gdf: list[dict], filter_polygon_path: Path):
    gdf.set_geometry("geometry", inplace=True, crs="EPSG:4326")
    spatial_index = gdf.sindex

    filter_gdf = gpd.read_file(filter_polygon_path)
    filter_union = filter_gdf.unary_union

    possible_matches_index = list(spatial_index.intersection(filter_union.bounds))
    possible_matches = gdf.iloc[possible_matches_index]
    precise_matches = possible_matches[possible_matches.intersects(filter_union)]

    return precise_matches


def main():
    print("Unzipping...")
    unzip_all_zipfiles(ZIP_DIR, EXTRACT_XML_DIR)

    print("Extract and Merge all xmls...")
    gdf = merge_all_xmls(EXTRACT_XML_DIR)

    if FILTER_POLYGON_PATH is not None:
        print("filtering...")
        gdf = filter_with_shp(gdf, FILTER_POLYGON_PATH)

    print("Saving...")
    create_shapefile(gdf, OUTPUT_DIR / MERGED_SHAPEFILE_NAME)


if __name__ == "__main__":
    main()
