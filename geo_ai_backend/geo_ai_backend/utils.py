import os
import shutil
import zipfile
import numpy as np
import rasterio
import cv2
import csv
import concurrent.futures

from typing import List, Any, Dict, Generator, Optional
from multiprocessing import Process
from functools import partial


def create_dir(path: str) -> None:
    os.makedirs(path, mode=0o777, exist_ok=True)


def delete_file(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def delete_dir(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)


def copy_dir(origin: str, target: str, dirs_exist_ok=True) -> None:
    shutil.copytree(origin, target, dirs_exist_ok=dirs_exist_ok)


def copy_file_from_dir(filename: str, origin: str, target: str) -> None:
    if os.path.isdir(f"{origin}/{filename}"):
        shutil.copytree(f"{origin}/{filename}", f"{target}/{filename}")
    else:
        shutil.copy(f"{origin}/{filename}", f"{target}/{filename}")


def extractall_zip(path_zip: str, save_path: str) -> None:
    with zipfile.ZipFile(path_zip, "r") as zip_file:
        zip_file.extractall(save_path)


def pack_coordinates_files(path_img: str) -> str:
    name_zip = os.path.splitext(os.path.basename(path_img))[0] + ".zip"
    name_dir = os.path.dirname(path_img)
    path_zip = os.path.join(name_dir, name_zip)
    with zipfile.ZipFile(path_zip, "w") as zip:
        files = os.listdir(name_dir)
        for file in files:
            if file.endswith((".png", ".json", ".zip")):
                continue
            zip.write(os.path.join(name_dir, file), arcname=file)
    return path_zip


def replace_tif_files(path_img_dir: str, path_img_tif: str) -> None:
    local_dir_files = os.listdir(path_img_dir)
    for i in local_dir_files:
        if i.endswith(".tif"):
            os.replace(f"{path_img_dir}/{i}", f"{path_img_tif}/{i}")


def replace_las_files(path_img_dir: str, path_las: str) -> None:
    local_dir_files = os.listdir(path_img_dir)
    for i in local_dir_files:
        if i.endswith(".las"):
            os.replace(f"{path_img_dir}/{i}", f"{path_las}/{i}")


def get_jpg_from_tif(
    path_tif: str, path_img_save: str, resize: int = 10
) -> None:
    filename = os.path.split(path_tif)[-1]
    geo_coefs = {}
    coefs = ['A', 'B', 'C', 'D', 'E', 'F']
    # wf_coefs = ['A', 'D', 'B', 'E', 'C', 'F']
    with rasterio.open(path_tif) as src:
        img = src.read()
        img = np.moveaxis(img, 0, -1)
        img = img[:, :, :3]
        img = img.astype(np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # jgw_name = filename.rsplit(".", 1)[0] + ".jgw"
        # full_path_save_jgw = os.path.join(path_img_original_dir, jgw_name)
        for i in range(len(coefs)):
            geo_coefs[coefs[i]] = src.transform[i]
        # with open(full_path_save_jgw, 'w') as wf:
        #     for wf_coef in wf_coefs:
        #         wf.write(str(geo_coefs[wf_coef]) + '\n')

        image_name = filename.rsplit(".", 1)[0] + ".jpg"
        full_path_save = os.path.join(path_img_save, image_name)

        width = int(img.shape[1] / resize)
        height = int(img.shape[0] / resize)
        dim = (width, height)
        resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)

        cv2.imwrite(full_path_save, resized)


def change_resolution_jpg(path: str, save_path: str) -> None:
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    width = int(img.shape[1] / 10)
    height = int(img.shape[0] / 10)
    dim = (width, height)
    resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    cv2.imwrite(save_path, resized)


def pool_handler(func: partial, params: List[Any]) -> None:
    procs: List[Process] = []
    for i in params:
        proc = Process(target=func, args=(i,))
        procs.append(proc)
        proc.start()

    for proc in procs:
        proc.join()


def thread_pool(func: partial, params: List[Any]) -> List[Any]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        return [i for i in executor.map(func, params)]


class CSVReader:

    def __init__(self, path: str, columns: Optional[List[str]] = None) -> None:
        self.path = path
        self.columns = columns

    def _read_csv(self) -> List[Dict[str, Any]]:
        with open(self.path, mode='r', newline='') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter='\t')
            rows = [row for row in self._get_rows(csv_reader=csv_reader) if row]
        return rows

    def _get_rows(self, csv_reader: csv.DictReader) -> Generator:
        for i in csv_reader:
            if i:
                yield self._get_row(values=i)
            else:
                yield None

    def _get_row(self, values: Dict[str, Any]):
        return {col: values[col] for col in self.columns}

    @property
    def get_dict(self) -> List[Dict[str, Any]]:
        return self._read_csv()


class CSVWriter:

    def __init__(self, path: str, header: List[str], data: Dict[str, Any]) -> None:
        self.path = path
        self.header = header
        self.data = data

    def _writer(self) -> None:
        with open(self.path, mode="w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.header, delimiter=";")
            writer.writeheader()
            for row in self.data:
                writer.writerow(row)
    @property
    def writer(self) -> None:
        self._writer()
