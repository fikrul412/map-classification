import base64
from io import BytesIO
from PIL import Image
from flask_cors import CORS
from flask import Flask, jsonify, request 
from utils import fetch_data_by_year, compute_dry_coefficient, predict
import numpy as np
import joblib

model = joblib.load('model_a.pkl')
scaler = joblib.load("scaler.pkl")
pca = joblib.load("pca.pkl")

app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:5173"}},
    supports_credentials=True
)

"""
DATE   : tuple(QDate) (start_date, end_date)
WIDTH  : int
HEIGHT : int
bbox   : list[xmin,ymin,xmax,ymax]
"""

colorMap = {
    10: (0, 100, 0),     
    20: (255, 187, 34),   
    30: (255, 255, 76),   
    40: (240, 150, 255),  
    50: (250, 0, 0),     
    60: (180, 180, 180),  
    70: (240, 240, 240),  
    80: (0, 100, 200),    
    90: (0, 150, 160),    
    95: (0, 200, 0),      
    100: (250, 230, 160) 
}

@app.route("/map", methods=["POST"])
def hello():
    a = request.get_json()
    year = a.get("year")
    bbox = a.get("bbox")
    client_id = a.get("client_id")
    client_password = a.get("client_password")

    arr_imgs, profile = fetch_data_by_year(year, bbox, client_id, client_password)
    arr_imgs, profile = compute_dry_coefficient(arr_imgs, profile)

    img_label = predict(arr_imgs, profile)

    y, x = img_label.shape
    rgb = np.zeros((y, x, 3), dtype=np.uint8)
    for val, color in colorMap.items():
        rgb[img_label == val] = color

    unique, counts = np.unique(img_label, return_counts=True)
    hist = {int(u): int(c) for u, c in zip(unique, counts)}

    # Convert image ke base64
    buffer = BytesIO()
    Image.fromarray(rgb).save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()

    return jsonify({
        "status": 200,
        "histogram": hist,
        "image_base64": f"data:image/png;base64,{img_base64}"
    })

  
if __name__=='__main__': 
   app.run(debug=True)

