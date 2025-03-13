import os
import shutil
import zipfile
from typing import List

import tritonclient.http as httpclient

from geo_ai_backend.utils import copy_dir


def create_dir(path: str) -> None:
    os.makedirs(path, mode=0o777, exist_ok=True)


def delete_file(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def delete_dir(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)


def extractall_zip(img_save_path_zip: str, img_save_path: str) -> None:
    with zipfile.ZipFile(img_save_path_zip, "r") as zip_file:
        zip_file.extractall(img_save_path)


def get_path_from_dir(path_img: str) -> List[str]:
    local_dir = os.listdir(path_img)
    arr_paths = [f"{path_img}/{i}" for i in local_dir]
    return arr_paths


def copy_ml_from_nextcloud(folder: str):
    copy_dir(
        origin=f"static/nextcloud/airflow/files/{folder}",
        target=f"static/static/models/{folder}",
    )


def zip_directory(folder_path: str, zip_file: str):
    zip_file = zipfile.ZipFile(f"{zip_file}.zip", "w")
    for folder_name, subfolders, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(folder_name, filename)
            zip_file.write(file_path)
    zip_file.close()


def read_in_chunks(file_object, size: int):
    while True:
        data = file_object.read(size)
        if not data:
            break
        yield data


class InferenceServerManager:
    def __init__(self, url: str, port: str, timeout: float = 60000) -> None:
        self.connect = httpclient.InferenceServerClient(
            url=f"{url}:{port}",
            connection_timeout=timeout,
            network_timeout=timeout,
            concurrency=4
        )

    def __enter__(self):
        return self.connect

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.connect.close()
