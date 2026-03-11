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

TEMPO_RECONEXAO = 180  # segundos (3 minutos)

ultimo_status = None
ultimo_evento = None
ultimo_logout = None
hora_login = None
mensagem_inicial_enviada = False
ultima_execucao_resumo = None
primeira_verificacao = True


# -----------------------
# FUNÇÕES DISCORD
# -----------------------
def enviar(msg):
    try:
        r = requests.post(webhook, json={"content": msg}, timeout=10)

        if r.status_code == 204:
            print("✅ Mensagem enviada ao Discord")

        elif r.status_code == 429:
            retry = r.json().get("retry_after", 5)
            print(f"⏳ Rate limit. Esperando {retry}s")
            time.sleep(retry)

        else:
            print("❌ Erro Discord:", r.status_code, r.text)

    except Exception as e:
        print("❌ Falha ao enviar mensagem:", e)


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
        print("❌ Falha ao acessar o site:", e)
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

    except Exception as e:
        print("⚠️ Erro ao carregar histórico:", e)
        return []


def salvar_historico(evento):
    historico = carregar_historico()
    historico.append(evento)

    temp = historico_file + ".tmp"

    with open(temp, "w") as f:
        json.dump(historico, f, indent=2)

    os.replace(temp, historico_file)


# -----------------------
# ESTADO DO BOT
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

    except Exception as e:
        print("⚠️ Erro ao carregar estado:", e)
        return {}


def salvar_estado():
    estado = {
        "ultimo_status": ultimo_status,
        "ultimo_evento": ultimo_evento,
        "hora_login": hora_login.strftime("%H:%M:%S") if hora_login else None,
        "mensagem_inicial_enviada": mensagem_inicial_enviada
    }

    temp = estado_file + ".tmp"

    with open(temp, "w") as f:
        json.dump(estado, f, indent=2)

    os.replace(temp, estado_file)


# -----------------------
# RESUMO DIÁRIO
# -----------------------
def resumo_diario():
    historico = carregar_historico()

    total_segundos = 0

    for evento in historico:
        if "tempo_online_h" in evento:
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
        # LIMPAR E RESETAR DATABASES
        # -----------------------
        def limpar_historico():
    try:
        if os.path.exists(historico_file):
            os.remove(historico_file)
            print("🧹 Histórico diário limpo")
    except Exception as e:
        print("⚠️ Erro ao limpar histórico:", e)


def resetar_estado():
    global ultimo_evento, ultimo_logout

    try:
        ultimo_evento = None
        ultimo_logout = None

        salvar_estado()

        print("♻️ Estado do bot resetado")

historico_file = "historico.json"
estado_file = "estado_bot.json"

TEMPO_RECONEXAO = 180

ultimo_status = None
ultimo_evento = None
ultimo_logout = None
hora_login = None

mensagem_inicial_enviada = False
ultima_execucao_resumo = None
primeira_verificacao = True


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
            print(f"⏳ Rate limit {retry}s")
            time.sleep(retry)

        else:
            print("❌ Discord erro:", r.status_code)

    except Exception as e:
        print("Erro webhook:", e)


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

    temp = historico_file + ".tmp"

    with open(temp, "w") as f:
        json.dump(historico, f, indent=2)

    os.replace(temp, historico_file)


def limpar_historico():

    try:
        if os.path.exists(historico_file):
            os.remove(historico_file)
            print("🧹 Histórico limpo")

    except Exception as e:
        print("Erro limpar histórico:", e)


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
        "ultimo_evento": ultimo_evento,
        "hora_login": hora_login.strftime("%H:%M:%S") if hora_login else None,
        "mensagem_inicial_enviada": mensagem_inicial_enviada
    }

    temp = estado_file + ".tmp"

    with open(temp, "w") as f:
        json.dump(estado, f, indent=2)

    os.replace(temp, estado_file)


def resetar_estado():

    global ultimo_evento, ultimo_logout

    try:

        ultimo_evento = None
        ultimo_logout = None

        salvar_estado()

        print("♻️ Estado resetado")

    except Exception as e:
        print("Erro reset estado:", e)


# -----------------------
# RESUMO DIÁRIO
# -----------------------
def resumo_diario():

    historico = carregar_historico()

    total_segundos = 0

    for evento in historico:

        if "tempo_online_h" in evento:

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
ultimo_evento = estado.get("ultimo_evento")
mensagem_inicial_enviada = estado.get("mensagem_inicial_enviada", False)

hora_login_str = estado.get("hora_login")

if hora_login_str:

    try:

        agora = datetime.now(timezone.utc) + timedelta(hours=-3)

        h, m, s = map(int, hora_login_str.split(":"))

        hora_login = agora.replace(hour=h, minute=m, second=s)

    except:

        hora_login = None


# =========================
# LOOP PRINCIPAL
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
        # MENSAGEM INICIAL
        # ------------------------
        if not mensagem_inicial_enviada:

            emoji = "🟢" if status == "online" else "🔴"

            enviar(
                "🚀 **_Rucoy Tracker iniciado_**\n\n"
                "👤 **Personagem: _Alan Virtue_**\n"
                f"📡 **Status atual: _{emoji} {status.capitalize()}_**\n"
                "⏱ **Verificação: _1 Minuto_**"
            )

            mensagem_inicial_enviada = True
            salvar_estado()

        # ------------------------
        # LOGIN / LOGOUT
        # ------------------------
        if status is not None and status != ultimo_status:

            hora_atual = agora

            if status == "online":

                if not primeira_verificacao:

                    if ultimo_logout and (hora_atual - ultimo_logout).total_seconds() <= TEMPO_RECONEXAO:

                        enviar(
                            f"🔁 _Alan Virtue reconectou rapidamente ({int((hora_atual - ultimo_logout).total_seconds())}s)_"
                        )

                    else:

                        enviar(
                            f"🟢 **Alan Virtue** _logou às {hora_formatada}_"
                        )

                hora_login = hora_atual
                ultimo_evento = "online"
                ultimo_status = status

                salvar_estado()

            elif status == "offline" and hora_login:

                tempo = hora_atual - hora_login

                horas = tempo.seconds // 3600
                minutos = (tempo.seconds % 3600) // 60

                enviar(
                    f"🔴 **Alan Virtue** _deslogou às {hora_formatada}_\n"
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
                hora_login = None

                salvar_estado()

        primeira_verificacao = False

        # ------------------------
        # RESUMO DIÁRIO
        # ------------------------
        if agora.hour == 2 and agora.minute <= 1:

            if ultima_execucao_resumo != data_atual:

                resumo_diario()

                limpar_historico()
                resetar_estado()

                enviar(
                    "📅 **Novo dia iniciado para Alan Virtue**\n"
                    "⏱ _Monitoramento reiniciado_"
                )

                ultima_execucao_resumo = data_atual

        time.sleep(60)


except KeyboardInterrupt:

    enviar("🛑 **Bot de monitoramento finalizado.**")
    print("Bot encerrado.")






