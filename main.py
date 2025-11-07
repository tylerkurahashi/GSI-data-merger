import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Union
from zipfile import ZipFile

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from tqdm import tqdm

from const import (
    EXTRACT_XML_DIR,
    FILTER_POLYGON_PATH,
    MERGE_FILE_PATTERN,
    MERGED_SHAPEFILE_NAME,
    OUTPUT_DIR,
    ZIP_DIR,
)


def unzip_all_zipfiles(zip_dir: Path, output_dir: Path) -> None:
    # Iterate over all files in the specified directory
    output_dir.mkdir(exist_ok=True, parents=True)
    for zip_file in tqdm(zip_dir.glob("*.zip")):
        with ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(output_dir)


def merge_all_xmls(xml_dir: Path) -> gpd.GeoDataFrame:
    df_list = []

    for xml_file in tqdm(xml_dir.rglob(f"*{MERGE_FILE_PATTERN}*.xml")):
        # Skip hidden files and system files
        if xml_file.name.startswith('.'):
            continue

        # Skip if not a file
        if not xml_file.is_file():
            continue

        try:
            polygons = extract_polygon_info(xml_file)
            df_list.append(polygons)
        except ET.ParseError as e:
            print(f"Warning: Failed to parse {xml_file}: {e}")
            continue
        except Exception as e:
            print(f"Warning: Error processing {xml_file}: {e}")
            continue

    merged_df = pd.concat(df_list, ignore_index=True)

    return gpd.GeoDataFrame(merged_df, geometry="geometry")


def extract_polygon_info(xml_file: Union[Path, str]) -> gpd.GeoDataFrame:
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

    gdf = gpd.GeoDataFrame(polygons)
    gdf.set_geometry("geometry", inplace=True, crs="EPSG:4326")
    return gdf


def create_shapefile(gdf: gpd.GeoDataFrame, output_file: Path) -> None:
    output_file.parent.mkdir(exist_ok=True, parents=True)
    gdf.to_file(output_file, driver="ESRI Shapefile")
    gdf.to_file(output_file.with_suffix(".geojson"), driver="GeoJSON")


def filter_with_shp(gdf: list[dict], filter_polygon_path: Union[Path, None]):
    gdf.set_geometry("geometry", inplace=True, crs="EPSG:4326")
    spatial_index = gdf.sindex

    filter_gdf = gpd.read_file(filter_polygon_path)
    filter_union = filter_gdf.unary_union

    possible_matches_index = list(spatial_index.intersection(filter_union.bounds))
    possible_matches = gdf.iloc[possible_matches_index]
    precise_matches = possible_matches[possible_matches.intersects(filter_union)]

    return precise_matches



def main():
    print(list(ZIP_DIR.glob("*")))
    for dir in ZIP_DIR.glob("*"):
        if dir.name == ".DS_Store":
            continue
        print(f"Unzipping {dir.name}...")
        unzip_all_zipfiles(dir, EXTRACT_XML_DIR / dir.name)

        print("Extract and Merge all xmls...")
        gdf = merge_all_xmls(EXTRACT_XML_DIR / dir.name)

        if FILTER_POLYGON_PATH is not None:
            print("filtering...")
            gdf = filter_with_shp(gdf, FILTER_POLYGON_PATH)

        print("Saving...")
        create_shapefile(gdf, OUTPUT_DIR / dir.name / MERGED_SHAPEFILE_NAME)


if __name__ == "__main__":
    main()
