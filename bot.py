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

# -----------------------
# ESTADO
# -----------------------

ultimo_status = None
hora_login = None
ultimo_logout = None
reconexoes = []

ultimo_update = None
primeira_verificacao = True
ultima_execucao_resumo = None

# -----------------------
# DISCORD
# -----------------------

def enviar(msg):
    try:
        r = requests.post(webhook, json={"content": msg}, timeout=10)

        if r.status_code == 204:
            print("✅ Mensagem enviada")

        elif r.status_code == 429:
            retry = r.json().get("retry_after", 5)
            print(f"⏳ Rate limit do Discord. Esperando {retry}s")
            time.sleep(retry)

        else:
            print("❌ Erro Discord:", r.status_code)

    except Exception as e:
        print("❌ Falha webhook:", e)


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
        print("❌ Erro ao acessar site:", e)
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


# -----------------------
# ESTADO DO BOT
# -----------------------

def salvar_estado():

    estado = {
        "ultimo_status": ultimo_status,
        "hora_login": hora_login.isoformat() if hora_login else None,
        "ultimo_logout": ultimo_logout.isoformat() if ultimo_logout else None,
        "reconexoes": reconexoes
    }

    with open(estado_file, "w") as f:
        json.dump(estado, f, indent=2)


def carregar_estado():

    global ultimo_status, hora_login, ultimo_logout, reconexoes

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

        print("📂 Estado restaurado")

    except Exception as e:

        print("⚠️ Erro ao carregar estado:", e)


def limpar_estado():

    if os.path.exists(estado_file):
        os.remove(estado_file)


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

    enviar(
        f"📊 **Resumo diário de Alan Virtue**\n"
        f"_⏱ Total online: {horas}h {minutos}m_"
    )


# -----------------------
# INICIAR
# -----------------------

carregar_estado()

print("🚀 Bot iniciado")

# -----------------------
# LOOP PRINCIPAL
# -----------------------

try:

    while True:

        agora = datetime.now(timezone.utc) + timedelta(hours=-3)

        hora_formatada = agora.strftime("%H:%M:%S")

        data_atual = agora.date()

        print(f"[{hora_formatada}] Verificando perfil")

        status = verificar_status()

        print("Status:", status)

        # -----------------------
        # LOGIN
        # -----------------------

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


        # -----------------------
        # UPDATE ONLINE
        # -----------------------

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

                enviar(msg)

                ultimo_update = agora


        # -----------------------
        # LOGOUT
        # -----------------------

        if status == "offline" and ultimo_status == "online" and hora_login:

            tempo = agora - hora_login

            horas = tempo.seconds // 3600
            minutos = (tempo.seconds % 3600) // 60

            enviar(
                "📊 **Alan Virtue Tracker**\n\n"
                "🔴 Status: Offline\n"
                f"🕒 Deslogou às: {hora_formatada}\n"
                f"⏱ Sessão durou: {horas}h {minutos}m"
            )

            salvar_historico(
                {
                    "tempo_online_h": horas,
                    "tempo_online_m": minutos
                }
            )

            hora_login = None
            ultimo_logout = agora
            ultimo_status = "offline"
            reconexoes = []

            salvar_estado()

        primeira_verificacao = False

        # -----------------------
        # RESUMO DIÁRIO
        # -----------------------

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

