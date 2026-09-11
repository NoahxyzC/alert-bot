from flask import Flask, request
import time
import requests
import re

app = Flask(__name__)

# Control de spam: Tiempo de espera entre alertas del mismo activo (ej: 15 minutos = 900 segundos)
last_sent = {}
COOLDOWN_SEGUNDOS = 900  

BOT_TOKEN = "8773678152:AAFdUZiQJ4RnWeTULUYlWxnyOu1iZ3or9sE"
CHAT_ID = "-1003709795264"
THREAD_ID = 217

def formatear_mensaje_simple(mensaje):
    try:
        # Extraer Precio
        match_precio = re.search(r"Precio:\s*([\d.]+)", mensaje, re.IGNORECASE)
        precio_entrada = match_precio.group(1) if match_precio else "N/A"
        
        # Extraer Activo
        match_activo = re.search(r"Activo:\s*([A-Z0-9/._]+)", mensaje, re.IGNORECASE)
        activo = match_activo.group(1) if match_activo else "Activo"

        # Identificar dirección para manejar el filtro anti-spam (cooldown)
        es_short = any(kw in mensaje.upper() for kw in ["SHORT", "ALTA", "VIOLETA"])
        tipo_key = "SHORT" if es_short else "LONG"

        # Extraer el texto descriptivo que envías desde TradingView
        if match_precio:
            posicion_precio = mensaje.find(match_precio.group(1))
            mensaje_extra = mensaje[posicion_precio + len(match_precio.group(1)):].strip()
            # Limpiamos las barras verticales del JSON
            mensaje_extra = mensaje_extra.replace("|", "").strip()
        else:
            mensaje_extra = mensaje

        # Construir el mensaje final simplificado
        nuevo_mensaje = (
            f"🔔 **ALERTA DE ZONA** 🔔\n\n"
            f"**Par:** `{activo}`\n"
            f"**Precio:** `{precio_entrada}`\n"
            f"---------------------------\n"
            f"📊 {mensaje_extra}"
        )

        return nuevo_mensaje, activo, tipo_key

    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        return mensaje, "GENERAL", "UNKNOWN"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print("DATA RECIBIDA:", data)

        raw_message = data.get("text", "Mensaje vacío")
        now = time.time()

        final_message, activo, tipo_key = formatear_mensaje_simple(raw_message)

        # Filtro anti-spam: Clave única por activo y dirección (ej: "BTCUSDT_SHORT")
        alert_key = f"{activo}_{tipo_key}"

        if alert_key in last_sent:
            tiempo_transcurrido = now - last_sent[alert_key]
            if tiempo_transcurrido < COOLDOWN_SEGUNDOS:
                print(f"IGNORADO: {alert_key} en cooldown ({int(tiempo_transcurrido)}s de {COOLDOWN_SEGUNDOS}s)")
                return "Ignored by Cooldown", 200

        last_sent[alert_key] = now

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "message_thread_id": THREAD_ID,
            "text": final_message,
            "parse_mode": "Markdown"
        }

        requests.post(url, json=payload)
        return "OK", 200

    except Exception as e:
        print("ERROR TOTAL:", str(e))
        return "Error", 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
