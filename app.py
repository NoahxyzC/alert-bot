from flask import Flask, request
import time
import requests
import re

app = Flask(__name__)

# Diccionario para evitar spam
last_sent = {}
COOLDOWN = 36000  # 10 horas

# Configuración de Telegram
BOT_TOKEN = "8773678152:AAFdUZiQJ4RnWeTULUYlWxnyOu1iZ3or9sE"
CHAT_ID = "-1003709795264"
THREAD_ID = 217

def calcular_niveles(mensaje):
    """
    Extrae el precio y calcula SL (1.5%) y TP (5%) según el tipo de alerta.
    """
    try:
        # Extraer el precio usando expresiones regulares (busca un número decimal después de 'Precio:')
        match_precio = re.search(r"Precio:\s*([\d.]+)", mensaje)
        if not match_precio:
            return mensaje # Si no hay precio, devuelve el original

        precio_entrada = float(match_precio.group(1))
        
        # Determinar si es SHORT o LONG
        es_short = "SHORT" in mensaje.upper()
        
        if es_short:
            # En SHORT: SL arriba (+), TP abajo (-)
            sl_precio = precio_entrada * 1.015
            tp_precio = precio_entrada * 0.95
            tipo = "SHORT 🔴"
        else:
            # En LONG (por defecto): SL abajo (-), TP arriba (+)
            sl_precio = precio_entrada * 0.985
            tp_precio = precio_entrada * 1.05
            tipo = "LONG 🟢"

        # Extraer el Activo (ej: XRPUSDT)
        match_activo = re.search(r"Activo:\s*(\w+)", mensaje)
        activo = match_activo.group(1) if match_activo else "Desconocido"

        # Construir el nuevo mensaje profesional
        nuevo_mensaje = (
            f"🚨 **NUEVA ALERTA {tipo}** 🚨\n\n"
            f"**Activo:** {activo}\n"
            f"**Precio Entrada:** {precio_entrada:.4f}\n"
            f"---------------------------\n"
            f"🛑 **STOP LOSS (1.5%):** {sl_precio:.4f}\n"
            f"✅ **TAKE PROFIT (5%):** {tp_precio:.4f}\n\n"
            f"⚠️ *Gestiona tu riesgo.*"
        )
        return nuevo_mensaje

    except Exception as e:
        print(f"Error al calcular: {e}")
        return mensaje

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print("DATA RECIBIDA:", data)

        raw_message = data.get("text", "Mensaje vacío")
        now = time.time()

        # Filtro de Spam (Cooldown)
        if raw_message in last_sent:
            if now - last_sent[raw_message] < COOLDOWN:
                print("IGNORADO POR COOLDOWN")
                return "Ignored"

        last_sent[raw_message] = now

        # Procesar y mejorar el mensaje
        final_message = calcular_niveles(raw_message)

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": CHAT_ID,
            "message_thread_id": THREAD_ID,
            "text": final_message,
            "parse_mode": "Markdown" # Permite negritas y formato lindo
        }

        print("ENVIANDO A TELEGRAM:", payload)

        response = requests.post(url, json=payload)
        return "OK"

    except Exception as e:
        print("ERROR TOTAL:", str(e))
        return "Error"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
