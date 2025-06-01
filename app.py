from flask import Flask, request, send_file
import requests
from qa_dashboard_generator import ComprehensiveQADashboard
import os  # Necesario para verificar existencia del archivo

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Backend online"

@app.route("/generate", methods=["POST"])
def generate_dashboard():
    try:
        excel_url = request.json.get("url")
        if not excel_url:
            return {"error": "Missing 'url' in request body"}, 400

        # Descargar el archivo desde la URL pública
        response = requests.get(excel_url)
        with open("reporte_tarjetas.xlsx", "wb") as f:
            f.write(response.content)

        # Generar el dashboard con la clase
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

# Render requiere que el backend escuche en el puerto especificado por la variable de entorno PORT
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
