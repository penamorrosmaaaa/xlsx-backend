from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import os
import traceback
from qa_dashboard_generator import ComprehensiveQADashboard

app = Flask(__name__)
CORS(app, origins=["*"])

EXCEL_FILE = "reporte_tarjetas.xlsx"
HTML_FILE = "qa-dashboard.html"

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
        print(f"✅ Archivo descargado, tamaño: {len(response.content)} bytes")

        with open(EXCEL_FILE, "wb") as f:
            f.write(response.content)
        print("💾 Archivo guardado localmente")

        if not os.path.exists(EXCEL_FILE) or os.path.getsize(EXCEL_FILE) == 0:
            return jsonify({"error": "El archivo Excel está vacío o corrupto"}), 400

        print("🔨 Generando dashboard...")
        dashboard = ComprehensiveQADashboard(excel_path=EXCEL_FILE)
        dashboard.save_dashboard(HTML_FILE)

        if not os.path.exists(HTML_FILE):
            return jsonify({"error": "Error al generar el dashboard HTML"}), 500

        print("✅ Dashboard generado exitosamente")

        try:
            os.remove(EXCEL_FILE)
            print("🧹 Archivo temporal eliminado")
        except:
            pass

        return jsonify({
            "status": "✅ Dashboard generado con éxito",
            "dashboard_url": f"/{HTML_FILE}",
            "timestamp": str(os.environ.get('TIMESTAMP', 'unknown'))
        }), 200

    except requests.exceptions.RequestException as e:
        print(f"❌ Error descargando archivo: {str(e)}")
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        print(f"❌ Error interno: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/qa-dashboard.html")
def serve_dashboard():
    try:
        if not os.path.exists(HTML_FILE):
            return jsonify({
                "error": "❌ Aún no se ha generado el dashboard. Sube un archivo Excel primero.",
                "suggestion": "Usa el endpoint /generate primero"
            }), 404

        return send_file(HTML_FILE, mimetype='text/html', as_attachment=False)
    except Exception as e:
        print(f"❌ Error sirviendo dashboard: {str(e)}")
        return jsonify({"error": f"Error sirviendo dashboard: {str(e)}"}), 500

@app.before_first_request
def auto_generate_if_possible():
    try:
        if os.path.exists(EXCEL_FILE):
            print("📁 Se encontró un Excel anterior. Generando dashboard automáticamente...")
            dashboard = ComprehensiveQADashboard(excel_path=EXCEL_FILE)
            dashboard.save_dashboard(HTML_FILE)
            print("✅ Dashboard regenerado automáticamente")
        else:
            print("⚠️ No se encontró Excel previo. Esperando subida desde el frontend.")
    except Exception as e:
        print(f"❌ Error al generar dashboard automáticamente: {e}")

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
