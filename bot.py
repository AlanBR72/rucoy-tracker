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
TEMPO_RECONEXAO = 180  # segundos (3 minutos)

ultimo_status = None
ultimo_evento = None
ultimo_logout = None
hora_login = None
mensagem_inicial_enviada = False
ultima_execucao_resumo = None
primeira_verificacao = True  # nova flag para primeira rodada

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
        if "tempo_online_h" in evento and "tempo_online_m" in evento:
            total_segundos += evento["tempo_online_h"] * 3600
            total_segundos += evento["tempo_online_m"] * 60

    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60

    if total_segundos > 0:
        enviar(f"📊 **Resumo diário de Alan Virtue**\n⏱ Total online: {horas}h {minutos}m")
    else:
        enviar(f"📊 **Resumo diário de Alan Virtue**\n⏱ Nenhum tempo online registrado hoje.")

# =========================
# BLOCO PRINCIPAL
# =========================
try:
    while True:
        agora = datetime.now(timezone.utc) + timedelta(hours=-3)
        hora_formatada = agora.strftime("%H:%M:%S")
        data_atual = agora.date()
        print(f"[{hora_formatada}] Verificando perfil...")

        status = verificar_status()
        print("Status:", status)

        # ------------------------
        # Mensagem inicial única
        # ------------------------
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

        # ------------------------
        # Login/Logout e reconexão rápida
        # ------------------------
        if status is not None and status != ultimo_status and status != ultimo_evento:
            hora_atual = agora

            if status == "online":
                # evita enviar login na primeira verificação
                if not primeira_verificacao:
                    if ultimo_logout and (hora_atual - ultimo_logout).total_seconds() <= TEMPO_RECONEXAO:
                        enviar(f"🔁 Alan Virtue reconectou rapidamente! ({int((hora_atual - ultimo_logout).total_seconds())}s)")
                    else:
                        enviar(f"🟢 Alan Virtue logou às {hora_formatada}")

                hora_login = hora_atual
                ultimo_evento = "online"
                ultimo_status = status

            elif status == "offline" and hora_login:
                tempo = hora_atual - hora_login
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
                ultimo_logout = hora_atual

        primeira_verificacao = False  # primeira rodada concluída

        # ------------------------
        # Resumo diário às 02:00
        # ------------------------
        if agora.hour == 2 and agora.minute == 0:
            if ultima_execucao_resumo != data_atual:
                resumo_diario()
                ultima_execucao_resumo = data_atual

        time.sleep(60)

except KeyboardInterrupt:
    enviar("🛑 Bot de monitoramento finalizado")
    print("Bot encerrado.")
