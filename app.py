from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import os
import traceback
from qa_dashboard_generator import ComprehensiveQADashboard

app = Flask(__name__)
CORS(app, origins=["*"])  # Permitir todos los orígenes por ahora

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
        
        # Validar request
        if not request.json:
            return jsonify({"error": "Request body debe ser JSON"}), 400
            
        excel_url = request.json.get("url")
        if not excel_url:
            return jsonify({"error": "Missing 'url' in request body"}), 400
            
        print(f"📥 URL recibida: {excel_url}")
        
        # Descargar archivo Excel
        print("⬇️ Descargando archivo Excel...")
        response = requests.get(excel_url, timeout=30)
        response.raise_for_status()  # Lanza excepción si hay error HTTP
        
        print(f"✅ Archivo descargado, tamaño: {len(response.content)} bytes")
        
        # Guardar archivo temporalmente
        excel_file_path = "reporte_tarjetas.xlsx"
        with open(excel_file_path, "wb") as f:
            f.write(response.content)
            
        print("💾 Archivo guardado localmente")
        
        # Verificar que el archivo existe y no está vacío
        if not os.path.exists(excel_file_path) or os.path.getsize(excel_file_path) == 0:
            return jsonify({"error": "El archivo Excel descargado está vacío o corrupto"}), 400
            
        # Generar dashboard
        print("🔨 Generando dashboard...")
        dashboard = ComprehensiveQADashboard(excel_path=excel_file_path)
        dashboard.save_dashboard("qa-dashboard.html")
        
        # Verificar que el dashboard se generó
        if not os.path.exists("qa-dashboard.html"):
            return jsonify({"error": "Error al generar el dashboard HTML"}), 500
            
        print("✅ Dashboard generado exitosamente")
        
        # Limpiar archivo temporal
        try:
            os.remove(excel_file_path)
            print("🧹 Archivo temporal eliminado")
        except:
            pass  # No importa si no se puede eliminar
            
        return jsonify({
            "status": "✅ Dashboard generado con éxito",
            "dashboard_url": "/qa-dashboard.html",
            "timestamp": str(os.environ.get('TIMESTAMP', 'unknown'))
        }), 200
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error descargando archivo: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 400
        
    except Exception as e:
        error_msg = f"Error interno: {str(e)}"
        print(f"❌ {error_msg}")
        print("🔍 Traceback completo:")
        traceback.print_exc()
        return jsonify({"error": error_msg}), 500

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
        print(f"❌ Error sirviendo dashboard: {str(e)}")
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
