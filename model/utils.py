import os, calendar, requests, rasterio
from rasterio.io import MemoryFile
from datetime import datetime
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import numpy as np
import joblib
import pandas as pd

reduced_feature = 3 # Depends on the model you use
segments_count = 10000 # Depends on the model you use

def fetch_data_by_year(YEAR: int, bbox, CLIENT_ID, CLIENT_PASSWORD):
    """
    YEAR   : int (misal 2022)
    WIDTH  : int
    HEIGHT : int
    bbox   : list[xmin, ymin, xmax, ymax]
    CLIENT_ID, CLIENT_PASSWORD : str
    folder : str, folder output
    """

    outputs = []

    RATIO = bbox[0] - bbox[2]

    WIDTH = abs((bbox[2] - bbox[0]) / RATIO * 512) 
    HEIGHT = abs((bbox[3] - bbox[1]) / RATIO * 512)

    logs = []
    print("DIMENSI:", WIDTH, HEIGHT)

    [118.519135, -6.035408, 120.395050, -5.159334]

    # AUTH
    client = BackendApplicationClient(client_id=CLIENT_ID)
    oauth = OAuth2Session(client=client)
    token = oauth.fetch_token(
        token_url="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        client_secret=CLIENT_PASSWORD,
        include_client_id=True
    )
    logs.append("Token berhasil diperoleh")

    url = "https://sh.dataspace.copernicus.eu/api/v1/process"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token['access_token']}"
    }

    # FETCH MONTHS
    for month in range(1, 3):
        last_day = calendar.monthrange(YEAR, month)[1]
        start_str = f"{YEAR}-{month:02d}-01T00:00:00Z"
        end_str   = f"{YEAR}-{month:02d}-{last_day}T23:59:59Z"
        print(f"Processing {start_str} -> {end_str}")
        data = {
            "input": {
                "bounds": {"bbox": bbox},
                "data": [{
                    "type": "sentinel-1-grd",
                    "dataFilter": {
                        "timeRange": {"from": start_str, "to": end_str},
                        "mosaickingOrder": "leastRecent",
                        "resolution": "HIGH",
                        "acquisitionMode": "IW",
                        "polarization": "DV",
                        "orbitDirection": "ASCENDING"
                    },
                    "processing": {
                        "backCoeff": "GAMMA0_ELLIPSOID",
                        "speckleFilter": {
                            "type": "LEE",
                            "windowSizeX": 5,
                            "windowSizeY": 5
                        }
                    }
                }]
            },
            "output": {
                "width": int(WIDTH),
                "height": int(HEIGHT),
                "responses": [{
                    "identifier": "default",
                    "format": {"type": "image/tiff"}
                }]
            },
            "evalscript": """
            //VERSION=3
            function setup() {
                return {
                    input: [{ bands: ["VV", "VH"] }],
                    output: [{ id: "default", bands: 5, sampleType: "FLOAT32" }]
                };
            }
            function evaluatePixel(s) {
                var ratio = s.VH / (s.VV + 1e-10);
                var diff  = s.VV - s.VH;
                var rvi   = (4 * s.VH) / (s.VV + s.VH + 1e-10);
                return { default: [s.VV, s.VH, ratio, diff, rvi] };
            }
            """
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            logs.append(f"Failed: {month} -> {response.status_code}")
            continue

        with MemoryFile(response.content) as memfile:
            with memfile.open() as src:
                img = src.read()
                profile = src.profile

        outputs.append(img)


    logs.append("COMPLETED")
    return outputs, profile

"""
(5, 545, 512)
(5, 545, 512)
"""
def compute_dry_coefficient(arr_imgs, profile):
    """
    Menghitung dry coefficient dari semua .tif di folder input_path.
    Output akan punya jumlah band yang sama dengan file input (5 band).
    """

    band_count, _, _ = arr_imgs[0].shape
    bands = []

    for b in range(0, band_count):
        band_stack = np.array([img[b] for img in arr_imgs], dtype=np.float32)
       
        Q1 = np.percentile(band_stack, 25, axis=0)
        mask = band_stack <= Q1

        sum_val = np.sum(band_stack * mask, axis=0)
        count = np.sum(mask, axis=0)

        band_dry_coeff = np.divide(sum_val, np.where(count == 0, 1, count), dtype=np.float32)
        bands.append(band_dry_coeff)

    bands = np.array(bands)
    return bands, profile

def predict(arr_imgs, profile):
    from main import model, pca, scaler
    bands_test = np.moveaxis(arr_imgs, 0, 2)
    y, x, c = bands_test.shape

    print(bands_test.shape)

    from scipy.interpolate import NearestNDInterpolator

    _, _, c = bands_test.shape

    for i in range(c):
        data = bands_test[:, :, i]
        if np.all(np.isnan(data)):
            bands_test[:, :, i] = 0
            continue

        mask = np.where(~np.isnan(data))
        interp = NearestNDInterpolator(np.transpose(mask), data[mask])
        bands_test[:, :, i] = interp(*np.indices(data.shape))
    
    parralel_bands_val = list()
    for i in range(c):
        parralel_bands_val.append(np.ravel(bands_test[:, :, i]))

    parralel_bands_val = np.moveaxis(np.array(parralel_bands_val), 0, 1 )

    parralel_bands_val_scaler = scaler.transform(parralel_bands_val)
    parralel_bands_val_pca = pca.transform(parralel_bands_val_scaler)

    pcs_norm = list()
    for i in range(reduced_feature):
        size = y*x
        temp = np.reshape(parralel_bands_val_pca[0 : size, i], (y, x))
        pcs_norm.append(temp)

    pcs_norm = np.array(pcs_norm)
    pcs_norm = np.moveaxis(pcs_norm, 0, -1)

    from skimage.segmentation import slic
    i = 0

    segments = slic(
        pcs_norm,
        n_segments=segments_count,
        compactness=1,
        sigma=1,
        channel_axis=2,
        start_label=1
    )

    print(segments.shape)
    for i in range(reduced_feature):
        print(pcs_norm[:, :, i].shape)

    mask_series = list()

    i = 0
    def add_smth(row, i):
        return f"{i}{int(row)}"
    mask_series = pd.Series(np.ravel(segments)).apply(lambda x: add_smth(x, chr(i + 65)))

    band_labels = []
    temp_df = pd.DataFrame(mask_series)
    for j in range(reduced_feature):
        label = f"band{j}"
        temp_df[label] = np.ravel(pcs_norm[:, :, j])
        if label not in band_labels:
            band_labels.append(f"band{j}")

    temp = temp_df.groupby(temp_df.columns[0], sort = False)[band_labels].median()

    lb_obj = list(temp.index.values)
    df_sample = temp

    y_pred = model.predict(df_sample)
    df_pred = np.ravel(y_pred)

    # Tampilkan value_counts untuk tiap objek
    print("Value counts per predicted class:")
    print(pd.Series(y_pred).value_counts())


    temp = pd.DataFrame(df_pred).value_counts()

    dict_obj = {}
    i = 0
    for key in lb_obj:
        dict_obj[key] = y_pred[i]
        i += 1

    img_arr = np.array([dict_obj[val] for val in mask_series])
    img_arr = np.reshape(img_arr, (y, x))

    return img_arr