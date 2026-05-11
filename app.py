from flask import Flask, request
import time
import requests
import re

app = Flask(__name__)

last_sent = {}
COOLDOWN = 36000  # 10 horas

BOT_TOKEN = "8773678152:AAFdUZiQJ4RnWeTULUYlWxnyOu1iZ3or9sE"
CHAT_ID = "-1003709795264"
THREAD_ID = 217

def calcular_niveles(mensaje):
    try:
        # 1. Extraer Precio (Busca el número después de 'Precio:')
        match_precio = re.search(r"Precio:\s*([\d.]+)", mensaje, re.IGNORECASE)
        if not match_precio:
            return mensaje
        
        precio_entrada = float(match_precio.group(1))
        
        # 2. Extraer Activo (Busca el nombre después de 'Activo:')
        match_activo = re.search(r"Activo:\s*([A-Z0-9/._]+)", mensaje, re.IGNORECASE)
        activo = match_activo.group(1) if match_activo else "Activo"

        # 3. Determinar Dirección (Short vs Long)
        es_short = "SHORT" in mensaje.upper()
        
        if es_short:
            sl_precio = precio_entrada * 1.015
            tp_precio = precio_entrada * 0.95
            tipo = "SHORT 🔴"
        else:
            sl_precio = precio_entrada * 0.985
            tp_precio = precio_entrada * 1.05
            tipo = "LONG 🟢"

        # 4. Capturar mensaje extra (Todo lo que esté después del precio)
        # Buscamos qué hay después del número del precio
        posicion_precio = mensaje.find(match_precio.group(1))
        mensaje_extra = mensaje[posicion_precio + len(match_precio.group(1)):].strip()
        
        # Limpiar el mensaje extra de saltos de línea innecesarios
        mensaje_extra = mensaje_extra.replace("\n", " ").strip()

        # 5. Construir el mensaje final
        nuevo_mensaje = (
            f"🚨 **ALERTA {tipo}** 🚨\n\n"
            f"**Instrumento:** `{activo}`\n"
            f"**Entrada:** `{precio_entrada:.4f}`\n"
            f"---------------------------\n"
            f"🛑 **SL (1.5%):** `{sl_precio:.4f}`\n"
            f"✅ **TP (5%):** `{tp_precio:.4f}`\n"
        )

        # Si hay un comentario extra, lo agregamos con un estilo diferente
        if mensaje_extra and len(mensaje_extra) > 2:
            nuevo_mensaje += f"---------------------------\n💬 **Nota:** *{mensaje_extra}*"

        return nuevo_mensaje

    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        return mensaje

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print("DATA RECIBIDA:", data)

        raw_message = data.get("text", "Mensaje vacío")
        now = time.time()

        if raw_message in last_sent:
            if now - last_sent[raw_message] < COOLDOWN:
                print("IGNORADO POR COOLDOWN")
                return "Ignored"

        last_sent[raw_message] = now
        final_message = calcular_niveles(raw_message)

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "message_thread_id": THREAD_ID,
            "text": final_message,
            "parse_mode": "Markdown"
        }

        requests.post(url, json=payload)
        return "OK"

    except Exception as e:
        print("ERROR TOTAL:", str(e))
        return "Error"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
