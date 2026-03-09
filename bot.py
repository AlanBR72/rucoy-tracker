from flask import Flask
import threading
import os

from bs4 import BeautifulSoup
import requests
import time
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot online"

def rodar_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=rodar_web).start()

print("🌐 Servidor web iniciado")
enviar("🧪 Teste de webhook - bot iniciado")

url = "https://www.rucoyonline.com/characters/Bank%20Of%20Alan"
webhook = "https://discord.com/api/webhooks/1391526244511907900/X4qA3HTFE9NLO2klBMO3LzxvrLQKoQZWEPITkYWY5f0ws9PmREUp4mXa9F1kCvROKEv8"

ultimo_status = None
hora_login = None

def enviar(msg):
    try:
        r = requests.post(webhook, json={"content": msg})

        if r.status_code == 204:
            print("✅ Mensagem enviada ao Discord")
        else:
            print("❌ Erro ao enviar:", r.status_code, r.text)

    except Exception as e:
        print("❌ Falha ao enviar mensagem:", e)

def verificar_status():
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    texto = soup.text.lower()

    if "currently online" in texto:
        return "online"
    else:
        return "offline"

try:

    status = verificar_status()
    ultimo_status = status

    agora = datetime.now().strftime("%H:%M:%S")

    emoji = "🟢" if status == "online" else "🔴"

    mensagem_inicio = (
        "🚀 **Rucoy Tracker iniciado**\n\n"
        "👤 Personagem: **Bank Of Alan**\n"
        f"📡 Status atual: **{emoji} {status.upper()}**\n"
        "⏱ Verificação: **1 minuto**"
    )

    enviar(mensagem_inicio)

    if status == "online":
        hora_login = datetime.now()

    while True:
        agora = datetime.now().strftime("%H:%M:%S")
        print(f"[{agora}] Verificando perfil...")

        status = verificar_status()
        print("Status:", status)

        if status != ultimo_status:

            hora_atual = datetime.now()

            if status == "online":
                hora_login = hora_atual
                enviar(f"🟢 Bank Of Alan logou às {hora_atual.strftime('%H:%M:%S')}")

            if status == "offline":
                if hora_login:
                    tempo = hora_atual - hora_login
                    horas = tempo.seconds // 3600
                    minutos = (tempo.seconds % 3600) // 60

                    enviar(
                        f"🔴 Bank Of Alan deslogou às {hora_atual.strftime('%H:%M:%S')}\n"
                        f"⏱ Tempo online: {horas}h {minutos}m"
                    )

            ultimo_status = status

        time.sleep(60)

except KeyboardInterrupt:

    enviar("🛑 Bot de monitoramento finalizado")
    print("Bot encerrado.")




