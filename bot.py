import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timezone, timedelta

# -----------------------
# CONFIG
# -----------------------

url = "https://www.rucoyonline.com/characters/Alan%20Virtue"
webhook = "https://discord.com/api/webhooks/1480607736155607121/1b-QFXqNgVHFkQuJlzWoX9M0ZI4pzYZcFBWpWVkHB9fMfxQoNuDTf778KwgMll3rDGXm"

TEMPO_RECONEXAO = 180
intervalo_update = 600  # 10 minutos

ultimo_status = None
ultimo_logout = None
hora_login = None
hora_offline = None

mensagem_status_id = None
ultimo_update_msg = None

mensagem_inicial_enviada = False
primeira_verificacao = True


# -----------------------
# DISCORD
# -----------------------

def enviar(msg):

    try:

        r = requests.post(webhook, json={"content": msg})

        if r.status_code == 204:
            print("✅ Mensagem enviada")

    except Exception as e:
        print("Erro webhook:", e)


def enviar_e_pegar_id(msg):

    try:

        r = requests.post(webhook + "?wait=true", json={"content": msg})

        if r.status_code == 200:
            return r.json()["id"]

    except Exception as e:
        print("Erro mensagem id:", e)

    return None


def editar_mensagem(msg_id, texto):

    try:
        requests.patch(webhook + f"/messages/{msg_id}", json={"content": texto})

    except Exception as e:
        print("Erro editar msg:", e)


# -----------------------
# STATUS
# -----------------------

def verificar_status():

    try:

        r = requests.get(url, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        texto = soup.text.lower()

        return "online" if "currently online" in texto else "offline"

    except:

        return None


# =========================
# LOOP PRINCIPAL
# =========================

try:

    while True:

        agora = datetime.now(timezone.utc) + timedelta(hours=-3)

        hora_formatada = agora.strftime("%H:%M:%S")

        print(f"[{hora_formatada}] Verificando perfil")

        status = verificar_status()

        print("Status:", status)


        # ------------------------
        # MENSAGEM INICIAL
        # ------------------------

        if not mensagem_inicial_enviada:

            emoji = "🟢" if status == "online" else "🔴"

            enviar(
                "🚀 **Rucoy Tracker iniciado**\n\n"
                "👤 **Personagem:** Alan Virtue\n"
                f"📡 **Status atual:** {emoji} {status.capitalize()}\n"
                "⏱ Verificação: 1 minuto"
            )

            mensagem_inicial_enviada = True


        # ------------------------
        # LOGIN / LOGOUT
        # ------------------------

        if status and status != ultimo_status:

            hora_atual = agora


            if status == "online":

                if not primeira_verificacao:

                    if ultimo_logout and (hora_atual - ultimo_logout).total_seconds() <= TEMPO_RECONEXAO:

                        enviar(
                            f"🔁 Alan Virtue reconectou rapidamente ({int((hora_atual - ultimo_logout).total_seconds())}s)"
                        )

                    else:

                        enviar(f"🟢 Alan Virtue logou às {hora_formatada}")

                hora_login = hora_atual
                hora_offline = None

                mensagem_status_id = enviar_e_pegar_id(

                    "🟢 **Alan Virtue está online**\n\n"
                    "⏱ Tempo online: 0h 0m"

                )

                ultimo_update_msg = agora


            elif status == "offline":

                enviar(f"🔴 Alan Virtue deslogou às {hora_formatada}")

                hora_login = None
                hora_offline = agora
                ultimo_logout = agora

                mensagem_status_id = enviar_e_pegar_id(

                    "🔴 **Alan Virtue está offline**\n\n"
                    "⏱ Tempo offline: 0h 0m"

                )

                ultimo_update_msg = agora


            ultimo_status = status


        # ------------------------
        # ATUALIZAÇÃO A CADA 10 MIN
        # ------------------------

        if mensagem_status_id:

            if not ultimo_update_msg or (agora - ultimo_update_msg).total_seconds() >= intervalo_update:

                if status == "online" and hora_login:

                    tempo = agora - hora_login

                    horas = tempo.seconds // 3600
                    minutos = (tempo.seconds % 3600) // 60

                    editar_mensagem(

                        mensagem_status_id,

                        f"🟢 **Alan Virtue está online**\n\n"
                        f"⏱ Tempo online: {horas}h {minutos}m"

                    )

                elif status == "offline" and hora_offline:

                    tempo = agora - hora_offline

                    horas = tempo.seconds // 3600
                    minutos = (tempo.seconds % 3600) // 60

                    editar_mensagem(

                        mensagem_status_id,

                        f"🔴 **Alan Virtue está offline**\n\n"
                        f"⏱ Tempo offline: {horas}h {minutos}m"

                    )

                ultimo_update_msg = agora


        primeira_verificacao = False

        print("⏳ Aguardando próxima verificação...")

        time.sleep(60)


except KeyboardInterrupt:

    enviar("🛑 Bot encerrado")
