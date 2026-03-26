from flask import Flask, request
import time
import requests

app = Flask(__name__)

# memoria simple (guarda últimos envíos)
last_sent = {}

COOLDOWN = 36000  # 10 horas

BOT_TOKEN = "TU_TOKEN_AQUI"
CHAT_ID = "-1003709795264"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("DATA RECIBIDA:", data)  # DEBUG

    message = data.get("text", "Mensaje vacío")
    now = time.time()

    # filtro cooldown
    if message in last_sent:
        if now - last_sent[message] < COOLDOWN:
            print("IGNORADO POR COOLDOWN")
            return "Ignored"

    last_sent[message] = now

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message
    })

    print("RESPUESTA TELEGRAM:", response.text)  # DEBUG

    return "Sent"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
