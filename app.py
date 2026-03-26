from flask import Flask, request
import time
import requests

app = Flask(__name__)

last_sent = {}

COOLDOWN = 36000  # 10 horas

BOT_TOKEN = "8773678152:AAFdUZiQJ4RnWeTULUYlWxnyOu1iZ3or9sE"
CHAT_ID = "-1003709795264"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("DATA:", data)

    message = data.get("text", "Mensaje vacío")
    now = time.time()

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

    print("TELEGRAM:", response.text)

    return "OK"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
