import os
from typing import Tuple
import requests
from pathlib import Path
from arcgis.auth._error import ArcGISLoginError
from arcgis.gis import GIS, Item
from arcgis.features import FeatureLayerCollection
from geo_ai_backend.arcgis.schemas import TokenArcgisSchemas
from geo_ai_backend.arcgis.exceptions import (
    TypeFileCSVException,
    NotFoundFileException,
    FileCSVAlreadyExistsException,
    TypeFileZipException,
    ShapefileAlreadyExistsException,
    BadRequestTokenException,
)
from geo_ai_backend.config import settings
from fastapi import Request
import re


class GISService:
    HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        verify_cert: bool,
        arcgis_path: str,
        vite_arcgis_portal_user: str,
        client_host: str,
        arcgis_token: str,
    ) -> None:
        self.url = url
        self.username = username
        self.password = password
        self.verify_cert = verify_cert
        self.arcgis_path = arcgis_path
        self.vite_arcgis_portal_user = vite_arcgis_portal_user
        self.client_host = client_host
        self.arcgis_token = arcgis_token

    def _connection(self) -> GIS:
        try:
            gis = GIS(
                url=self.url,
                username=self.username,
                password=self.password,
                verify_cert=self.verify_cert,
            )
            return gis
        except ArcGISLoginError as e:
            raise e

    def upload_csv(self, csv_file_path, overwrite) -> Tuple[Item, GIS]:
        gis = self._connection()
        if not os.path.isfile(csv_file_path):
            raise NotFoundFileException
        if not csv_file_path.endswith(".csv"):
            raise TypeFileCSVException
        filename = Path(csv_file_path).name
        existing_items = gis.content.search(filename)
        for existing_item in existing_items:
            if existing_item is not None:
                if overwrite:
                    existing_item.delete()
                else:
                    raise FileCSVAlreadyExistsException
        csv_item = gis.content.add({}, csv_file_path)
        return csv_item, gis

    def change_capabilities_layer(self, feature_layer_item: Item, gis: GIS) -> None:
        layer_collection = FeatureLayerCollection(
            feature_layer_item.url, gis
        )
        update_params = {
            "hasStaticData": False,
            "capabilities": "Query,Update",
            "allowGeometryUpdates": False
        }
        layer_collection.manager.update_definition(update_params)

    def upload_layer(self, csv_file_path) -> str:
        csv_item = self.upload_csv(
            csv_file_path=csv_file_path, overwrite=settings.ARCGIS_OVERWRITE
        )
        feature_layer_item = csv_item[0].publish(overwrite=settings.ARCGIS_OVERWRITE)
        self.change_capabilities_layer(
            feature_layer_item=feature_layer_item, gis=csv_item[1]
        )
        return feature_layer_item.id

    def upload_shape_zip(self, shape_zip_path, overwrite) -> Tuple[Item, GIS]:
        gis = self._connection()
        if not os.path.isfile(shape_zip_path):
            raise NotFoundFileException
        if not shape_zip_path.endswith(".zip"):
            raise TypeFileZipException
        filename = Path(shape_zip_path).name
        existing_items = gis.content.search(filename)
        for existing_item in existing_items:
            if existing_item is not None:
                if overwrite:
                    existing_item.delete()
                else:
                    raise ShapefileAlreadyExistsException
        shapefile_items = gis.content.add({}, shape_zip_path)
        return shapefile_items, gis

    def upload_shape_layer(self, shape_zip_path) -> str:
        shapefile_items = self.upload_shape_zip(
            shape_zip_path=shape_zip_path, overwrite=settings.ARCGIS_OVERWRITE
        )
        feature_layer_item = shapefile_items[0].publish(
            overwrite=settings.ARCGIS_OVERWRITE, file_type="Shapefile"
        )
        self.change_capabilities_layer(
            feature_layer_item=feature_layer_item, gis=shapefile_items[1]
        )
        return feature_layer_item.id

    def set_referer(self, request: Request):
        client_host_original = request.headers.get("referer")
        client_host = re.search(r'https?://[^/]+', client_host_original).group()
        self.client_host = client_host

    @property
    def get_token_arcgis_token_service(self) -> TokenArcgisSchemas:
        payload = {
            "username": self.username,
            "password": self.password,
            "referer": self.client_host,
            "expiration": self.arcgis_token,
            "f": "json",
        }

        response = requests.post(
            url=f"{self.vite_arcgis_portal_user}{self.arcgis_path}",
            data=payload,
            headers=self.HEADERS,
            verify=False,
        )
        if response.status_code != 200:
            raise BadRequestTokenException
        data = response.json()
        return TokenArcgisSchemas(
            token=data["token"], expires=data["expires"], ssl=data["ssl"]
        )


gis_service = GISService(
    url=settings.ARCGIS_URL,
    username=settings.ARCGIS_LOGIN,
    password=settings.ARCGIS_PASSWORD,
    verify_cert=settings.ARCGIS_VERIFY_CERT,
    arcgis_path=settings.ARCGIS_PATH,
    vite_arcgis_portal_user=settings.ARCGIS_URL,
    client_host=settings.CLIENT_HOST,
    arcgis_token=settings.ACCESS_ARCGIS_TOKEN_EXPIRE_MINUTES,
)
