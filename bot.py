import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# -----------------------
# CONFIGURAÇÃO
# -----------------------
url = "https://www.rucoyonline.com/characters/Bank%20Of%20Alan"
webhook = "https://discord.com/api/webhooks/1480607736155607121/1b-QFXqNgVHFkQuJlzWoX9M0ZI4pzYZcFBWpWVkHB9fMfxQoNuDTf778KwgMll3rDGXm"
ultimo_status = None      # status atual do site: "online" ou "offline"
ultimo_evento = None      # último evento enviado ao Discord
hora_login = None         # hora do login

# -----------------------
# FUNÇÃO DE ENVIO AO DISCORD
# -----------------------
def enviar(msg):
    try:
        r = requests.post(webhook, json={"content": msg}, timeout=10)
        if r.status_code == 204:
            print("✅ Mensagem enviada ao Discord")
        elif r.status_code == 429:  # rate-limit
            retry = r.json().get("retry_after", 5)
            print(f"⏳ Rate limit do Discord. Esperando {retry} segundos...")
            time.sleep(retry)
        else:
            print("❌ Erro ao enviar mensagem:", r.status_code, r.text)
    except Exception as e:
        print("❌ Falha ao enviar mensagem:", e)

# -----------------------
# FUNÇÃO PARA VERIFICAR STATUS NO SITE
# -----------------------
def verificar_status():
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        texto = soup.text.lower()
        return "online" if "currently online" in texto else "offline"
    except Exception as e:
        print("❌ Falha ao acessar o site:", e)
        return None

# =========================
# BLOCO PRINCIPAL
# =========================

# variável global para inicialização
mensagem_inicial_enviada = False

try:
    status = verificar_status()
    ultimo_status = status
    ultimo_evento = None
    hora_login = None

    if not mensagem_inicial_enviada:
        emoji = "🟢" if status == "online" else "🔴"
        mensagem_inicio = (
            "🚀 **Rucoy Tracker iniciado**\n\n"
            "👤 Personagem: **Bank Of Alan**\n"
            f"📡 Status atual: **{emoji} {status.upper()}**\n"
            "⏱ Verificação: **1 minuto**"
        )
        enviar(mensagem_inicio)
        mensagem_inicial_enviada = True  # marca como enviada

    if status == "online":
        hora_login = datetime.now()

    while True:
        status = verificar_status()

        if status is not None and status != ultimo_status and status != ultimo_evento:
            hora_atual = datetime.now()

            if status == "online":
                hora_login = hora_atual
                enviar(f"🟢 Bank Of Alan logou às {hora_atual.strftime('%H:%M:%S')}")
                ultimo_evento = "online"

            elif status == "offline" and hora_login:
                tempo = hora_atual - hora_login
                horas = tempo.seconds // 3600
                minutos = (tempo.seconds % 3600) // 60
                enviar(
                    f"🔴 Bank Of Alan deslogou às {hora_atual.strftime('%H:%M:%S')}\n"
                    f"⏱ Tempo online: {horas}h {minutos}m"
                )
                ultimo_evento = "offline"

            ultimo_status = status

        time.sleep(60)

except KeyboardInterrupt:
    enviar("🛑 Bot de monitoramento finalizado")
    print("Bot encerrado.")
