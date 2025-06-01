from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import os
import traceback
from qa_dashboard_generator import ComprehensiveQADashboard

# 🟣 Supabase config
SUPABASE_URL = "https://liomseivquhgogbnwron.supabase.co"
SUPABASE_BUCKET = "files"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxpb21zZWl2cXVoZ29nYm53cm9uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg3MzQzMzgsImV4cCI6MjA2NDMxMDMzOH0.PDOowFEDylMBdo3ZOUtl8bVaCP1Zf8TOsc7D8tKVj40"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

# 🟢 Auto-generación al iniciar el servidor
def descargar_excel_desde_supabase():
    try:
        print("🔄 Buscando archivo más reciente en Supabase...")
        response = requests.get(f"{SUPABASE_URL}/storage/v1/object/list/{SUPABASE_BUCKET}", headers=HEADERS)
        response.raise_for_status()
        archivos = response.json()
        archivos.sort(key=lambda x: x["created_at"], reverse=True)
        archivo_mas_reciente = archivos[0]["name"]

        url_descarga = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{archivo_mas_reciente}"
        excel = requests.get(url_descarga)
        with open("reporte_tarjetas.xlsx", "wb") as f:
            f.write(excel.content)
        print("✅ Excel descargado de Supabase")

        dashboard = ComprehensiveQADashboard(excel_path="reporte_tarjetas.xlsx")
        dashboard.save_dashboard("qa-dashboard.html")
        print("✅ Dashboard regenerado automáticamente")
    except Exception as e:
        print(f"⚠️ No se pudo regenerar dashboard: {e}")

# 🚀 Flask app
app = Flask(__name__)
CORS(app, origins=["*"])

@app.before_first_request
def auto_generate_if_possible():
    descargar_excel_desde_supabase()

@app.route("/")
def home():
    return jsonify({
        "status": "✅ Backend online",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/generate (POST)",
            "dashboard": "/qa-dashboard.html (GET)",
            "health": "/ (GET)"
        }
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": os.environ.get('TIMESTAMP', 'unknown')})

@app.route("/generate", methods=["POST"])
def generate_dashboard():
    try:
        print("🔄 Iniciando generación de dashboard...")
        if not request.json:
            return jsonify({"error": "Request body debe ser JSON"}), 400
        excel_url = request.json.get("url")
        if not excel_url:
            return jsonify({"error": "Missing 'url' in request body"}), 400

        print(f"📥 URL recibida: {excel_url}")
        response = requests.get(excel_url, timeout=30)
        response.raise_for_status()
        with open("reporte_tarjetas.xlsx", "wb") as f:
            f.write(response.content)
        print("✅ Archivo descargado")

        dashboard = ComprehensiveQADashboard(excel_path="reporte_tarjetas.xlsx")
        dashboard.save_dashboard("qa-dashboard.html")

        if not os.path.exists("qa-dashboard.html"):
            return jsonify({"error": "Error al generar el dashboard HTML"}), 500

        try:
            os.remove("reporte_tarjetas.xlsx")
        except:
            pass

        return jsonify({
            "status": "✅ Dashboard generado con éxito",
            "dashboard_url": "/qa-dashboard.html"
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error descargando archivo: {str(e)}"}), 400

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route("/qa-dashboard.html")
def serve_dashboard():
    try:
        if not os.path.exists("qa-dashboard.html"):
            return jsonify({
                "error": "❌ Aún no se ha generado el dashboard. Sube un archivo Excel primero.",
                "suggestion": "Usa el endpoint /generate primero"
            }), 404
        return send_file(
            "qa-dashboard.html",
            mimetype='text/html',
            as_attachment=False,
            download_name='qa-dashboard.html'
        )
    except Exception as e:
        return jsonify({"error": f"Error sirviendo dashboard: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Iniciando servidor en puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
