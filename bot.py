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
estado_file = "estado_bot.json"

TEMPO_RECONEXAO = 180

ultimo_status = None
ultimo_logout = None
hora_login = None

mensagem_online_id = None

mensagem_inicial_enviada = False
ultima_execucao_resumo = None
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

            data = r.json()

            return data["id"]

    except Exception as e:
        print("Erro enviar id:", e)

    return None


def editar_mensagem(msg_id, texto):

    try:

        requests.patch(webhook + f"/messages/{msg_id}", json={"content": texto})

    except Exception as e:
        print("Erro editar msg:", e)


# -----------------------
# VERIFICAR STATUS
# -----------------------

def verificar_status():

    try:

        r = requests.get(url, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        texto = soup.text.lower()

        return "online" if "currently online" in texto else "offline"

    except Exception as e:

        print("Erro site:", e)

        return None


# -----------------------
# HISTÓRICO
# -----------------------

def carregar_historico():

    if not os.path.exists(historico_file):
        return []

    try:

        with open(historico_file, "r") as f:

            conteudo = f.read().strip()

            if not conteudo:
                return []

            return json.loads(conteudo)

    except:

        return []


def salvar_historico(evento):

    historico = carregar_historico()

    historico.append(evento)

    with open(historico_file, "w") as f:

        json.dump(historico, f, indent=2)


def limpar_historico():

    if os.path.exists(historico_file):

        os.remove(historico_file)

        print("🧹 Histórico limpo")


# -----------------------
# ESTADO BOT
# -----------------------

def carregar_estado():

    if not os.path.exists(estado_file):
        return {}

    try:

        with open(estado_file, "r") as f:

            conteudo = f.read().strip()

            if not conteudo:
                return {}

            return json.loads(conteudo)

    except:

        return {}


def salvar_estado():

    estado = {

        "ultimo_status": ultimo_status,

        "hora_login": hora_login.strftime("%H:%M:%S") if hora_login else None,

        "mensagem_inicial_enviada": mensagem_inicial_enviada
    }

    with open(estado_file, "w") as f:

        json.dump(estado, f, indent=2)


def resetar_estado():

    global ultimo_logout

    ultimo_logout = None

    salvar_estado()

    print("♻️ Estado resetado")


# -----------------------
# RESUMO DIÁRIO
# -----------------------

def resumo_diario():

    historico = carregar_historico()

    total_segundos = 0

    for evento in historico:

        total_segundos += evento["tempo_online_h"] * 3600
        total_segundos += evento["tempo_online_m"] * 60

    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60

    if total_segundos > 0:

        enviar(
            f"📊 **Resumo diário de Alan Virtue**\n"
            f"_⏱ Total online: {horas}h {minutos}m_"
        )

    else:

        enviar(
            "📊 **Resumo diário de Alan Virtue**\n"
            "_⏱ Nenhum tempo online registrado hoje._"
        )


# -----------------------
# CARREGAR ESTADO
# -----------------------

estado = carregar_estado()

ultimo_status = estado.get("ultimo_status")

mensagem_inicial_enviada = estado.get("mensagem_inicial_enviada", False)

hora_login_str = estado.get("hora_login")

if hora_login_str:

    agora = datetime.now(timezone.utc) + timedelta(hours=-3)

    h, m, s = map(int, hora_login_str.split(":"))

    hora_login = agora.replace(hour=h, minute=m, second=s)


# =========================
# LOOP PRINCIPAL
# =========================

try:

    while True:

        agora = datetime.now(timezone.utc) + timedelta(hours=-3)

        hora_formatada = agora.strftime("%H:%M:%S")

        data_atual = agora.date()

        print(f"[{hora_formatada}] Verificando perfil")

        status = verificar_status()

        print("Status:", status)


        # MENSAGEM INICIAL

        if not mensagem_inicial_enviada:

            emoji = "🟢" if status == "online" else "🔴"

            enviar(
                "🚀 **Rucoy Tracker iniciado**\n\n"
                "👤 **Personagem:** Alan Virtue\n"
                f"📡 **Status atual:** {emoji} {status.capitalize()}\n"
                "⏱ Verificação: 1 minuto"
            )

            mensagem_inicial_enviada = True

            salvar_estado()


        # LOGIN / LOGOUT

        if status and status != ultimo_status:

            hora_atual = agora


            if status == "online":

                if not primeira_verificacao:

                    if ultimo_logout and (hora_atual - ultimo_logout).total_seconds() <= TEMPO_RECONEXAO:

                        enviar("🔁 Alan Virtue reconectou rapidamente")

                    else:

                        enviar(f"🟢 Alan Virtue logou às {hora_formatada}")


                hora_login = hora_atual

                mensagem_online_id = enviar_e_pegar_id(

                    "🟢 **Alan Virtue está online**\n\n"
                    "⏱ Tempo online: 0h 0m"

                )

                ultimo_status = status

                salvar_estado()


            elif status == "offline" and hora_login:

                tempo = hora_atual - hora_login

                horas = tempo.seconds // 3600

                minutos = (tempo.seconds % 3600) // 60

                enviar(

                    f"🔴 Alan Virtue deslogou às {hora_formatada}\n"
                    f"⏱ Tempo online: {horas}h {minutos}m"

                )

                salvar_historico({

                    "tempo_online_h": horas,

                    "tempo_online_m": minutos

                })

                ultimo_status = status

                ultimo_logout = hora_atual

                hora_login = None

                mensagem_online_id = None

                salvar_estado()


        primeira_verificacao = False


        # ATUALIZAR TEMPO ONLINE

        if hora_login and mensagem_online_id:

            tempo = agora - hora_login

            horas = tempo.seconds // 3600

            minutos = (tempo.seconds % 3600) // 60

            editar_mensagem(

                mensagem_online_id,

                f"🟢 **Alan Virtue está online**\n\n"
                f"⏱ Tempo online: {horas}h {minutos}m"

            )


        # RESUMO DIÁRIO

        if agora.hour == 2 and agora.minute <= 1:

            if ultima_execucao_resumo != data_atual:

                resumo_diario()

                limpar_historico()

                resetar_estado()

                enviar(

                    "📅 Novo dia iniciado para Alan Virtue\n"
                    "⏱ Monitoramento reiniciado"

                )

                ultima_execucao_resumo = data_atual


        print("⏳ Aguardando próxima verificação...")

        time.sleep(60)


except KeyboardInterrupt:

    enviar("🛑 Bot encerrado")
