from flask import Flask, request
import time
import requests

app = Flask(__name__)

# memoria simple (guarda últimos envíos)
last_sent = {}

COOLDOWN = 36000  # 10 horas (en segundos)

BOT_TOKEN = "8773678152:AAFdUZiQJ4RnWeTULUYlWxnyOu1iZ3or9sE"
CHAT_ID = "-1003709795264"
THREAD_ID = 217  # tu topic

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    message = data.get("text", "")
    now = time.time()

    # filtro por mensaje repetido
    if message in last_sent:
        if now - last_sent[message] < COOLDOWN:
            return "Ignored (cooldown activo)"

    last_sent[message] = now

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, json={
        "chat_id": CHAT_ID,
        "message_thread_id": THREAD_ID,
        "text": message
    })

    return "Sent"

app.run(host="0.0.0.0", port=10000)