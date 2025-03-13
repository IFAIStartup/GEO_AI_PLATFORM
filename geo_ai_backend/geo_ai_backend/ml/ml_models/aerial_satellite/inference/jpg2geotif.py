import xml.etree.ElementTree as ET
import rasterio
from rasterio.transform import from_origin


def create_geotiff(jpg_path: str, jgw_path: str, aux_xml_path: str, save_tif_path: str) -> None:
    """
    Create a GeoTIFF file from a JPG image, JGW (world file), and AUX XML file.

    Args:
    jpg_path (str): Path to the JPG file.
    jgw_path (str): Path to the JGW file.
    aux_xml_path (str): Path to the AUX XML file.
    save_tif_path (str): Path where the resulting GeoTIFF file will be saved.
    """

    # Read georeferencing data from the JGW file
    with open(jgw_path) as file:
        jgw_data = file.readlines()
        jgw_data = [float(value.strip()) for value in jgw_data]

    # Read the CRS from the AUX XML file
    tree = ET.parse(aux_xml_path)
    root = tree.getroot()
    crs_wkt = root.find('SRS').text

    # Open the JPG image using Rasterio
    with rasterio.open(jpg_path) as src:
        image = src.read()

        # The affine transformation defines how image pixels correspond to geographic coordinates
        # from_origin creates a transformation from the coordinates of the top-left corner and pixel sizes
        transform = from_origin(
            jgw_data[4],  # X coordinate of the top-left corner (east offset)
            jgw_data[5],  # Y coordinate of the top-left corner (north offset)
            jgw_data[0],  # Horizontal pixel size
            -jgw_data[3]  # Vertical pixel size (negative to reverse the Y-axis direction)
        )

        # Create and write the GeoTIFF file
        with rasterio.open(
                save_tif_path,
                'w',
                driver='GTiff',
                height=image.shape[1],
                width=image.shape[2],
                count=src.count,
                dtype=image.dtype,
                crs=crs_wkt,  # Set CRS from AUX XML file
                transform=transform
        ) as dst:
            dst.write(image)


if __name__ == "__main__":
    create_geotiff(
        jpg_path=r"C:\Users\WinUser\works\presentation\GEO_AI_PLATFORM\geo_ai_backend\geo_ai_backend\ml\ml_models\aerial_satellite\inference\AAM DevelopedArea 30cm_1_3.jpg",
        jgw_path=r"C:\Users\WinUser\works\presentation\GEO_AI_PLATFORM\geo_ai_backend\geo_ai_backend\ml\ml_models\aerial_satellite\inference\AAM DevelopedArea 30cm_1_3.jgw",
        aux_xml_path=r"C:\Users\WinUser\works\presentation\GEO_AI_PLATFORM\geo_ai_backend\geo_ai_backend\ml\ml_models\aerial_satellite\inference\AAM DevelopedArea 30cm_1_3.jpg.aux.xml",
        save_tif_path=r"C:\Users\WinUser\works\presentation\GEO_AI_PLATFORM\geo_ai_backend\geo_ai_backend\ml\ml_models\aerial_satellite\inference\123.tif"
    )
