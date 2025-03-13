import cv2
import numpy as np
import tritonclient.http as httpclient
import math
from geo_ai_backend.ml.ml_models.HAT.inference.utils import add_padding, getWKT_PRJ
import os
import rasterio
from affine import Affine


def img_preproc(img: np.ndarray) -> np.ndarray or tuple:
    """
    Preprocess image for inference
    :param img: image to preprocess
    :return: preprocessed image, padding
    """
    h, w = img.shape[:2]
    h_add, w_add = 0, 0
    if h % 16 != 0:
        h_add = 16 - h % 16

    if w % 16 != 0:
        w_add = 16 - w % 16

    # add padding
    if h_add != 0 or w_add != 0:
        img = add_padding(img, (w + w_add, h + h_add))

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB, dst=img)
    img = img.astype(np.float32, copy=False)
    img = np.transpose(img, (2, 0, 1))
    img = img.reshape((1, *img.shape))
    img /= 255.0
    return img, (h_add, w_add)


def img_postproc(img: np.ndarray, padding=None) -> np.ndarray:
    """
    Postprocess image after inference
    :param img: image to postprocess
    :param padding: padding to remove
    :return: postprocessed image
    """
    img = img.reshape(img.shape[1:])
    img = np.clip(img, 0., 1., out=img)
    img = np.transpose(img, (1, 2, 0))
    img *= 255.0
    img = img.round(out=img)
    img = img.astype(np.uint8, copy=False)

    if padding is not None and padding != (0, 0):
        h_add, w_add = padding
        img = img[h_add:img.shape[0] - h_add, w_add:img.shape[1] - w_add, :]

    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img


def tile_inference_triton(img_in: np.ndarray, model_name: str,
                          triton_client: httpclient.InferenceServerClient, tile_size=256,
                          tile_pad=16) -> np.ndarray:
    """It will first crop input images to tiles, and then process each tile.
    Finally, all the processed tiles are merged into one images.
    Modified from: https://github.com/ata4/esrgan-launcher
    """

    height, width = img_in.shape[:2]

    tiles_x = math.ceil(width / tile_size)
    tiles_y = math.ceil(height / tile_size)

    output_rows = []

    # loop over all tiles
    for y in range(tiles_y):
        output_row_tiles = []

        for x in range(tiles_x):
            # extract tile from input image
            ofs_x = x * tile_size
            ofs_y = y * tile_size

            # input tile area on total image
            input_start_x = ofs_x
            input_end_x = min(ofs_x + tile_size, width)
            input_start_y = ofs_y
            input_end_y = min(ofs_y + tile_size, height)

            # input tile area on total image with padding
            input_start_x_pad = max(input_start_x - tile_pad, 0)
            input_end_x_pad = min(input_end_x + tile_pad, width)
            input_start_y_pad = max(input_start_y - tile_pad, 0)
            input_end_y_pad = min(input_end_y + tile_pad, height)

            # input tile dimensions
            input_tile_width = input_end_x - input_start_x
            input_tile_height = input_end_y - input_start_y
            tile_idx = y * tiles_x + x + 1
            input_tile = img_in[input_start_y_pad:input_end_y_pad, input_start_x_pad:input_end_x_pad].copy()
            input_tile, (h_add, w_add) = img_preproc(input_tile)

            # upscale tile
            output_tile = inference_triton(input_tile, model_name, triton_client)

            # print(f'\tTile {tile_idx}/{tiles_x * tiles_y}')

            scale = output_tile.shape[2] / input_tile.shape[2]

            # output tile area without padding
            output_start_x_tile = int((input_start_x - input_start_x_pad) * scale)
            output_end_x_tile = int(output_start_x_tile + input_tile_width * scale)
            output_start_y_tile = int((input_start_y - input_start_y_pad) * scale)
            output_end_y_tile = int(output_start_y_tile + input_tile_height * scale)

            # put tile into row container
            output_tile = output_tile[:, :, output_start_y_tile: output_end_y_tile,
                          output_start_x_tile: output_end_x_tile]
            output_tile = img_postproc(output_tile)
            output_row_tiles.append(output_tile)

        output_row = np.concatenate(output_row_tiles, axis=1)
        output_rows.append(output_row)
        del output_row_tiles

    output = np.concatenate(output_rows, axis=0)

    return output


def inference_triton(img_in: np.ndarray, model_name: str,
                     triton_client: httpclient.InferenceServerClient) -> np.ndarray:
    """
    Inference image with Triton
    :param img_in: image to inference
    :param model_name: model name
    :param triton_client: Triton client
    :return: Super resolution image
    """
    inputs = httpclient.InferInput("input", img_in.shape, datatype="FP32")
    inputs.set_data_from_numpy(img_in, binary_data=True)

    outputs = httpclient.InferRequestedOutput("output", binary_data=True)

    results = triton_client.infer(model_name=model_name, inputs=[inputs], outputs=[outputs])
    inference_output = results.as_numpy('output')
    return inference_output


def inference_pipeline(img_in: np.ndarray, model_name: str, triton_client: httpclient.InferenceServerClient) -> np.ndarray:
    """
    End-to-end inference pipeline
    :param img_in: image to inference
    :param model_name: model name
    :param triton_server_url: Triton connect
    :return: Super resolution image
    """
    img_out = tile_inference_triton(img_in, model_name, triton_client, tile_size=128, tile_pad=16)
    return img_out


def superresolution_image(
    img_path: str,
    img_save_path: str,
    model_name: str,
    triton_client: httpclient.InferenceServerClient
) -> bool:
    img_name, img_extension = os.path.splitext(img_path)
    img_save_name, _ = os.path.splitext(img_save_path)
    geo_coefs = {}
    coefs = ['A', 'D', 'B', 'E', 'C', 'F']
    if img_extension == '.jpg':
        jgw_path = img_name + '.jgw'
        if os.path.exists(jgw_path):
            with open(jgw_path) as jgw:
                for coef in coefs:
                    geo_coefs[coef] = float(jgw.readline()[:-1])
        img0 = cv2.imread(img_path)
    elif img_extension == '.tif':
        coefs = ['A', 'B', 'C', 'D', 'E', 'F']
        with rasterio.open(img_path) as img_tif:
            for i in range(len(coefs)):
                geo_coefs[coefs[i]] = img_tif.transform[i]
            crs = img_tif.crs
            img0 = img_tif.read()
        img0 = np.transpose(img0, (1, 2, 0))
        img0 = cv2.cvtColor(img0, cv2.COLOR_RGB2BGR)
    else:
        img0 = cv2.imread(img_path)
    img_out = inference_pipeline(img0, model_name, triton_client)
    if bool(geo_coefs):
        a_coef_scale = img0.shape[1] / img_out.shape[1]
        e_coef_scale = img0.shape[0] / img_out.shape[0]
        geo_coefs['A'] = geo_coefs['A'] * a_coef_scale
        geo_coefs['E'] = geo_coefs['E'] * e_coef_scale
    if img_extension == '.jpg':
        with open(img_save_name + ".jgw", 'w') as wf:
            for coef in geo_coefs.values():
                wf.write(str(coef) + '\n')

    elif img_extension == '.tif':
        img_out = cv2.cvtColor(img_out, cv2.COLOR_BGR2RGB)
        img_out = np.transpose(img_out, (2, 0, 1))

        epsg = str(crs).split(':')[-1]
        prj_data = getWKT_PRJ(epsg)
        with open(img_save_name + '.prj', 'w') as prj_file:
            prj_file.write(prj_data)

        with rasterio.open(
            img_save_path,
            'w',
            driver='GTiff',
            height=img_out.shape[1],
            width=img_out.shape[2],
            count=img_out.shape[0],
            dtype=img_out.dtype,
            crs=crs,
            transform=Affine(*geo_coefs.values())
        ) as dst:
            dst.write(img_out)
            return True

    status = cv2.imwrite(img_save_path, img_out)
    return status

