from flask import Flask, request
import time
import requests
import re

app = Flask(__name__)

# Control de spam: 15 minutos (900 segundos) de espera entre la misma alerta para el mismo activo
last_sent = {}
COOLDOWN_SEGUNDOS = 900  

# Tus credenciales exactas
BOT_TOKEN = "8773678152:AAFdUZiQJ4RnWeTULUYlWxnyOu1iZ3or9sE"
CHAT_ID = "-1003709795264"
THREAD_ID = 217

def formatear_mensaje_terminal(mensaje):
    try:
        # 1. Extraer Precio
        match_precio = re.search(r"Precio:\s*([\d.]+)", mensaje, re.IGNORECASE)
        precio_entrada = match_precio.group(1) if match_precio else "N/A"
        
        # 2. Extraer Activo
        match_activo = re.search(r"Activo:\s*([A-Z0-9/._]+)", mensaje, re.IGNORECASE)
        activo = match_activo.group(1) if match_activo else "Activo"

        # 3. Detectar la dirección y asignar colores/títulos Cyber-Terminal
        mensaje_upper = mensaje.upper()
        
        if "SHORT" in mensaje_upper:
            titulo = "🔴▰▰▰ **SHORT ZONE** ▰▰▰🔴"
            tipo_key = "SHORT"
        elif "LONG" in mensaje_upper:
            titulo = "🟢▰▰▰ **LONG ZONE** ▰▰▰🟢"
            tipo_key = "LONG"
        elif "CRUCE" in mensaje_upper or "MEDIA" in mensaje_upper:
            titulo = "⚪▰▰▰ **REBALANCEO** ▰▰▰⚪"
            tipo_key = "CRUCE"
        else:
            titulo = "⚠️▰▰▰ **ZONA DE INTERÉS** ▰▰▰⚠️"
            tipo_key = "INFO"

        # 4. Construir el diseño final
        nuevo_mensaje = (
            f"⚡ **[ ALERTA DE SISTEMA ]** ⚡\n\n"
            f"{titulo}\n\n"
            f"⮞ **TICKER:** `{activo}`\n"
            f"⮞ **PRICE:** `{precio_entrada}`"
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

        # Darle formato al mensaje
        final_message, activo, tipo_key = formatear_mensaje_terminal(raw_message)

        # Filtro anti-spam: Clave única (ej: "CYBERUSDT_SHORT")
        alert_key = f"{activo}_{tipo_key}"

        if alert_key in last_sent:
            tiempo_transcurrido = now - last_sent[alert_key]
            if tiempo_transcurrido < COOLDOWN_SEGUNDOS:
                print(f"IGNORADO: {alert_key} en cooldown ({int(tiempo_transcurrido)}s de {COOLDOWN_SEGUNDOS}s)")
                return "Ignored by Cooldown", 200

        # Registrar el envío
        last_sent[alert_key] = now

        # Enviar a Telegram
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "message_thread_id": THREAD_ID,
            "text": final_message,
            "parse_mode": "Markdown"
        }

        respuesta = requests.post(url, json=payload)
        print("RESPUESTA TELEGRAM:", respuesta.text)
        return "OK", 200

    except Exception as e:
        print("ERROR TOTAL:", str(e))
        return "Error", 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
