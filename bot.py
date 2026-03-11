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
INTERVALO_VERIFICACAO = 60
INTERVALO_UPDATE = 600

# separar webhook
partes = webhook.split("/")
WEBHOOK_ID = partes[-2]
WEBHOOK_TOKEN = partes[-1]

# -----------------------
# ESTADO
# -----------------------

ultimo_status = None
hora_login = None
ultimo_logout = None
reconexoes = []
message_id = None

ultimo_update = None
primeira_verificacao = True
ultima_execucao_resumo = None

# -----------------------
# DISCORD
# -----------------------

def enviar(msg):
    try:
        requests.post(webhook, json={"content": msg}, timeout=10)
    except:
        pass


def criar_painel(msg):
    global message_id

    try:
        r = requests.post(
            webhook + "?wait=true",
            json={"content": msg},
            timeout=10
        )

        if r.status_code == 200:
            data = r.json()
            message_id = data["id"]
            salvar_estado()
            print("📩 Painel criado")

    except Exception as e:
        print("Erro criar painel:", e)


def editar_painel(msg):

    if not message_id:
        criar_painel(msg)
        return

    try:

        url_edit = f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{WEBHOOK_TOKEN}/messages/{message_id}"

        r = requests.patch(
            url_edit,
            json={"content": msg},
            timeout=10
        )

        if r.status_code == 200:
            print("✏️ Painel atualizado")

    except Exception as e:
        print("Erro editar:", e)


# -----------------------
# STATUS DO SITE
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
            return json.load(f)
    except:
        return []


def salvar_historico(evento):

    hist = carregar_historico()
    hist.append(evento)

    with open(historico_file, "w") as f:
        json.dump(hist, f, indent=2)


def limpar_historico():

    if os.path.exists(historico_file):
        os.remove(historico_file)


# -----------------------
# ESTADO BOT
# -----------------------

def salvar_estado():

    estado = {
        "ultimo_status": ultimo_status,
        "hora_login": hora_login.isoformat() if hora_login else None,
        "ultimo_logout": ultimo_logout.isoformat() if ultimo_logout else None,
        "reconexoes": reconexoes,
        "message_id": message_id
    }

    with open(estado_file, "w") as f:
        json.dump(estado, f, indent=2)


def carregar_estado():

    global ultimo_status, hora_login, ultimo_logout, reconexoes, message_id

    if not os.path.exists(estado_file):
        return

    try:

        with open(estado_file, "r") as f:
            estado = json.load(f)

        ultimo_status = estado.get("ultimo_status")

        if estado.get("hora_login"):
            hora_login = datetime.fromisoformat(estado["hora_login"])

        if estado.get("ultimo_logout"):
            ultimo_logout = datetime.fromisoformat(estado["ultimo_logout"])

        reconexoes = estado.get("reconexoes", [])
        message_id = estado.get("message_id")

        print("📂 Estado restaurado")

    except Exception as e:
        print("Erro estado:", e)


def limpar_estado():

    if os.path.exists(estado_file):
        os.remove(estado_file)


# -----------------------
# RESUMO DIÁRIO
# -----------------------

def resumo_diario():

    historico = carregar_historico()

    total_segundos = 0
    sessoes = len(historico)

    for evento in historico:
        total_segundos += evento["tempo_online_h"] * 3600
        total_segundos += evento["tempo_online_m"] * 60

    horas_online = total_segundos // 3600
    minutos_online = (total_segundos % 3600) // 60

    segundos_dia = 24 * 3600
    offline_segundos = segundos_dia - total_segundos

    if offline_segundos < 0:
        offline_segundos = 0

    horas_off = offline_segundos // 3600
    minutos_off = (offline_segundos % 3600) // 60

    recon_count = len(reconexoes)

    enviar(
        "📊 **Resumo diário — Alan Virtue**\n\n"
        f"⏱ **Tempo online:** _{horas_online}h {minutos_online}m_\n"
        f"🔌 **Sessões:** _{sessoes}_\n"
        f"🔁 **Reconexões:** _{recon_count}_\n"
        f"📉 **Tempo offline:** _{horas_off}h {minutos_off}m_"
    )


# -----------------------
# INICIAR
# -----------------------

carregar_estado()

print("🚀 Bot iniciado")

# -----------------------
# LOOP
# -----------------------

try:

    while True:

        agora = datetime.now(timezone.utc) + timedelta(hours=-3)

        hora_formatada = agora.strftime("%H:%M:%S")
        data_atual = agora.date()

        print(f"[{hora_formatada}] Verificando perfil")

        status = verificar_status()

        print("Status:", status)

        # LOGIN
        if status == "online" and ultimo_status != "online":

            if not primeira_verificacao:

                if ultimo_logout:

                    diff = (agora - ultimo_logout).total_seconds()

                    if diff <= TEMPO_RECONEXAO:

                        reconexoes.append(
                            f"_🔁 Alan Virtue reconectou rapidamente ({int(diff)}s) [{hora_formatada}]_"
                        )

                    else:

                        enviar(f"🟢 **Alan Virtue logou às {hora_formatada}**")

                else:

                    enviar(f"🟢 **Alan Virtue logou às {hora_formatada}**")

            hora_login = agora
            ultimo_update = None
            ultimo_status = "online"

            salvar_estado()

        # PAINEL ONLINE
        if status == "online" and hora_login:

            if (
                ultimo_update is None
                or (agora - ultimo_update).total_seconds() >= INTERVALO_UPDATE
            ):

                tempo = agora - hora_login

                horas = tempo.seconds // 3600
                minutos = (tempo.seconds % 3600) // 60

                msg = (
                    "📊 **Alan Virtue Tracker**\n\n"
                    "**🟢 Status:** _Online_\n"
                    f"**🕒 Logado às:** _{hora_login.strftime('%H:%M')}_\n"
                    f"⏱ **Sessão atual:** _{horas}h {minutos}m_\n"
                )

                if reconexoes:
                    msg += "\n".join(reconexoes)

                editar_painel(msg)

                ultimo_update = agora

        # LOGOUT
        if status == "offline" and ultimo_status == "online" and hora_login:

            tempo = agora - hora_login

            horas = tempo.seconds // 3600
            minutos = (tempo.seconds % 3600) // 60

            enviar(
                "📊 **Alan Virtue Tracker**\n\n"
                "**🔴 Status:** _Offline_\n"
                f"**🕒 Deslogou às:** _{hora_formatada}_\n"
                f"⏱ **Sessão durou:** _{horas}h {minutos}m_"
            )

            salvar_historico({
                "tempo_online_h": horas,
                "tempo_online_m": minutos
            })

            hora_login = None
            ultimo_logout = agora
            ultimo_status = "offline"
            reconexoes = []
            message_id = None

            salvar_estado()

        primeira_verificacao = False

        # RESUMO DIÁRIO
        if agora.hour == 2 and agora.minute <= 1:

            if ultima_execucao_resumo != data_atual:

                resumo_diario()

                limpar_historico()
                limpar_estado()

                enviar(
                    "📅 **Novo dia iniciado para Alan Virtue**\n"
                    "_⏱ Monitoramento reiniciado_"
                )

                ultima_execucao_resumo = data_atual

        print("⏳ Aguardando próxima verificação...")

        time.sleep(INTERVALO_VERIFICACAO)

except KeyboardInterrupt:

    enviar("🛑 Bot encerrado")

    print("Bot finalizado")
