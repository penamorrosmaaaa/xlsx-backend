from flask import Flask, request, jsonify
import pandas as pd
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Python backend corriendo"

@app.route("/generar-dashboard", methods=["POST"])
def generar_dashboard():
    try:
        url = request.json.get("url")
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": "No se pudo descargar el archivo"}), 400

        with open("archivo.xlsx", "wb") as f:
            f.write(response.content)

        df = pd.read_excel("archivo.xlsx")
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        df.fillna("", inplace=True)
        df["rechazada"] = df["aceptado/rechazado"].str.lower() == "rechazada"
        df["aceptada"] = df["aceptado/rechazado"].str.lower() == "aceptado"

        html = df.to_html(index=False)
        return html

    except Exception as e:
        return jsonify({"error": str(e)}), 500

