import rasterio
import json

a = rasterio.open('sentinel1_2021_01.tif')

a_1 = a.read(1)

b = json.dumps(a_1.tolist())
print(type(b))