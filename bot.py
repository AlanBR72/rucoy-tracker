import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timezone, timedelta
import json
import os

# -----------------------
# CONFIGURAÇÃO
# -----------------------
url = "https://www.rucoyonline.com/characters/Alan%20Virtue"
webhook = "https://discord.com/api/webhooks/1480607736155607121/1b-QFXqNgVHFkQuJlzWoX9M0ZI4pzYZcFBWpWVkHB9fMfxQoNuDTf778KwgMll3rDGXm"
historico_file = "historico.json"

ultimo_status = None
ultimo_evento = None
hora_login = None

# -----------------------
# FUNÇÕES
# -----------------------
def enviar(msg):
    try:
        r = requests.post(webhook, json={"content": msg}, timeout=10)
        if r.status_code == 204:
            print("✅ Mensagem enviada ao Discord")
        elif r.status_code == 429:
            retry = r.json().get("retry_after", 5)
            print(f"⏳ Rate limit do Discord. Esperando {retry} segundos...")
            time.sleep(retry)
        else:
            print("❌ Erro ao enviar mensagem:", r.status_code, r.text)
    except Exception as e:
        print("❌ Falha ao enviar mensagem:", e)

def verificar_status():
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        texto = soup.text.lower()
        return "online" if "currently online" in texto else "offline"
    except Exception as e:
        print("❌ Falha ao acessar o site:", e)
        return None

def carregar_historico():
    if os.path.exists(historico_file):
        with open(historico_file, "r") as f:
            return json.load(f)
    return []

def salvar_historico(evento):
    historico = carregar_historico()
    historico.append(evento)
    with open(historico_file, "w") as f:
        json.dump(historico, f, indent=2)

def resumo_diario():
    historico = carregar_historico()
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    total_segundos = 0

    for evento in historico:
        if "hora" in evento:
            # converter hora de string para datetime do dia atual
            hora_evento = datetime.strptime(evento["hora"], "%H:%M:%S").replace(
                year=hoje.year, month=hoje.month, day=hoje.day
            )
            if evento["evento"] == "logout":
                total_segundos += evento.get("tempo_online_h", 0) * 3600
                total_segundos += evento.get("tempo_online_m", 0) * 60

    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60

    if total_segundos > 0:
        enviar(f"📊 **Resumo diário de Alan Virtue**\n⏱ Total online: {horas}h {minutos}m")
    else:
        enviar(f"📊 **Resumo diário de Alan Virtue**\n⏱ Nenhum tempo online registrado hoje.")

# =========================
# BLOCO PRINCIPAL
# =========================
mensagem_inicial_enviada = False

try:
    status = verificar_status()
    ultimo_status = status
    ultimo_evento = None

    if not mensagem_inicial_enviada:
        emoji = "🟢" if status == "online" else "🔴"
        mensagem_inicio = (
            "🚀 **Rucoy Tracker iniciado**\n\n"
            "👤 Personagem: **Alan Virtue**\n"
            f"📡 Status atual: **{emoji} {status.upper()}**\n"
            "⏱ Verificação: **1 minuto**"
        )
        enviar(mensagem_inicio)
        mensagem_inicial_enviada = True

    if status == "online":
        hora_login = datetime.now(timezone.utc) + timedelta(hours=-3)

    # controle para resumo diário (executar 1 vez por dia)
    ultima_execucao_resumo = None

    while True:
        agora = datetime.now(timezone.utc) + timedelta(hours=-3)
        hora_formatada = agora.strftime("%H:%M:%S")
        data_atual = agora.date()
        print(f"[{hora_formatada}] Verificando perfil...")

        status = verificar_status()
        print("Status:", status)

        if status is not None and status != ultimo_status and status != ultimo_evento:
            if status == "online":
                hora_login = agora
                enviar(f"🟢 Alan Virtue logou às {hora_formatada}")
                salvar_historico({"evento": "login", "hora": hora_formatada})
                ultimo_evento = "online"

            elif status == "offline" and hora_login:
                tempo = agora - hora_login
                horas = tempo.seconds // 3600
                minutos = (tempo.seconds % 3600) // 60
                enviar(
                    f"🔴 Alan Virtue deslogou às {hora_formatada}\n"
                    f"⏱ Tempo online: {horas}h {minutos}m"
                )
                salvar_historico({
                    "evento": "logout",
                    "hora": hora_formatada,
                    "tempo_online_h": horas,
                    "tempo_online_m": minutos
                })
                ultimo_evento = "offline"

            ultimo_status = status

        # ------------------------
        # envia resumo diário às 23:59
        # ------------------------
        if agora.hour == 23 and agora.minute == 59:
            if ultima_execucao_resumo != data_atual:
                resumo_diario()
                ultima_execucao_resumo = data_atual

        time.sleep(60)

except KeyboardInterrupt:
    enviar("🛑 Bot de monitoramento finalizado")
    print("Bot encerrado.")
