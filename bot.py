import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

url = "https://www.rucoyonline.com/characters/Bank%20Of%20Alan"
webhook = "https://discord.com/api/webhooks/1480607736155607121/1b-QFXqNgVHFkQuJlzWoX9M0ZI4pzYZcFBWpWVkHB9fMfxQoNuDTf778KwgMll3rDGXm"
ultimo_status = None
hora_login = None

def enviar(msg):
    try:
        r = requests.post(webhook, json={"content": msg}, timeout=10)
        if r.status_code == 204:
            print("✅ Mensagem enviada ao Discord")
        elif r.status_code == 429:
            retry = r.json().get("retry_after", 5)
            print(f"⏳ Rate limit. Esperando {retry} segundos...")
            time.sleep(retry)
        else:
            print("❌ Erro:", r.status_code, r.text)
    except Exception as e:
        print("❌ Falha:", e)

def verificar_status():
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    texto = soup.text.lower()

    if "currently online" in texto:
        return "online"
    else:
        return "offline"

try:
    # pega status inicial
    status = verificar_status()
    ultimo_status = status

    # monta mensagem inicial
    emoji = "🟢" if status == "online" else "🔴"
    mensagem_inicio = (
        "🚀 **Rucoy Tracker iniciado**\n\n"
        "👤 Personagem: **Bank Of Alan**\n"
        f"📡 Status atual: **{emoji} {status.upper()}**\n"
        "⏱ Verificação: **1 minuto**"
    )

    # envia apenas uma vez
    enviar(mensagem_inicio)

    if status == "online":
        hora_login = datetime.now()

    # loop principal
    while True:
        agora = datetime.now().strftime("%H:%M:%S")
        print(f"[{agora}] Verificando perfil...")

        status = verificar_status()
        print("Status:", status)

        # só envia mensagem se status mudou
        if status != ultimo_status and status is not None:
            hora_atual = datetime.now()

            if status == "online":
                hora_login = hora_atual
                enviar(f"🟢 Bank Of Alan logou às {hora_atual.strftime('%H:%M:%S')}")

            elif status == "offline" and hora_login:
                tempo = hora_atual - hora_login
                horas = tempo.seconds // 3600
                minutos = (tempo.seconds % 3600) // 60
                enviar(
                    f"🔴 Bank Of Alan deslogou às {hora_atual.strftime('%H:%M:%S')}\n"
                    f"⏱ Tempo online: {horas}h {minutos}m"
                )

            # atualiza status depois de enviar mensagem
            ultimo_status = status

        time.sleep(60)

except KeyboardInterrupt:
    enviar("🛑 Bot de monitoramento finalizado")
    print("Bot encerrado.")

