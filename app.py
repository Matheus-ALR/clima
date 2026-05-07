from dotenv import load_dotenv
from flask import Flask, request, render_template
import os

from weather_service import buscar_clima_por_cidade

# Carrega variáveis do .env (local) ou ambiente (Render)
load_dotenv()

app = Flask(__name__)

@app.route("/", methods=['GET'])
def home():
    cidade = request.args.get('cidade', '').strip()
    weather = None
    error = None

    if cidade:
        result = buscar_clima_por_cidade(cidade)
        if result["error"]:
            error = result["message"]
        else:
            weather = result["data"]

    return render_template("index.html", weather=weather, error=error, cidade=cidade)

if __name__ == "__main__":
    # Porta dinâmica para o Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)