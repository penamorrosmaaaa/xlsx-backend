from flask import Flask, request, send_file
from flask_cors import CORS
import requests
import os
from qa_dashboard_generator import ComprehensiveQADashboard

app = Flask(__name__)
CORS(app)  # 👈 habilita CORS

@app.route("/")
def home():
    return "✅ Backend online"

@app.route("/generate", methods=["POST"])
def generate_dashboard():
    try:
        excel_url = request.json.get("url")
        if not excel_url:
            return {"error": "Missing 'url' in request body"}, 400

        response = requests.get(excel_url)
        with open("reporte_tarjetas.xlsx", "wb") as f:
            f.write(response.content)

        dashboard = ComprehensiveQADashboard()
        dashboard.save_dashboard("qa-dashboard.html")

        return {"status": "✅ Dashboard generado con éxito"}, 200
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/qa-dashboard.html")
def serve_dashboard():
    if not os.path.exists("qa-dashboard.html"):
        return "❌ Aún no se ha generado el dashboard. Sube un archivo Excel primero.", 404
    return send_file("qa-dashboard.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
