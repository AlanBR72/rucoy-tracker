import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import pytz
import json
import os
import traceback

# -----------------------
# CONFIG
# -----------------------

CHAR_NAME = "Alan Virtue"

url = "https://www.rucoyonline.com/characters/Alan%20Virtue"

webhook = "https://discord.com/api/webhooks/1480607736155607121/1b-QFXqNgVHFkQuJlzWoX9M0ZI4pzYZcFBWpWVkHB9fMfxQoNuDTf778KwgMll3rDGXm"

historico_file = "historico.json"
estado_file = "estado_bot.json"
stats_file = "stats.json"

TEMPO_RECONEXAO = 180
TEMPO_ATUALIZACAO_PAINEL = 300

BRASIL = pytz.timezone("America/Sao_Paulo")

# -----------------------
# VARIÁVEIS
# -----------------------

ultimo_status = None
hora_login = None
hora_logout = None

mensagem_painel_id = None

reconexoes = []
reconexoes_dia = 0

ultimo_update_painel = None

xp_inicio_sessao = None
xp_sessao_total = 0

# -----------------------
# JSON
# -----------------------

stats_memoria = {
    "level": "?",
    "melee": "?",
    "defense": "?"
}

def carregar_json(file):

    if not os.path.exists(file):
        return {}

    try:
        with open(file,"r") as f:
            return json.load(f)
    except:
        return {}

def salvar_json(file,data):

    with open(file,"w") as f:
        json.dump(data,f,indent=2)

# -----------------------
# DISCORD
# -----------------------

def enviar(msg):

    try:
        requests.post(webhook,json={"content":msg})
    except:
        print("Erro ao enviar mensagem")

def enviar_e_pegar_id(msg):

    try:

        r = requests.post(webhook+"?wait=true",json={"content":msg})

        if r.status_code in [200,201]:
            return r.json()["id"]

    except Exception as e:

        print("⚠️ Erro Discord:",e)

    return None

def editar(msg_id,msg):

    try:

        requests.patch(webhook+"/messages/"+msg_id,json={"content":msg})

        print("🔄 Painel atualizado")

    except Exception as e:

        print("Erro editar:",e)

# -----------------------
# STATUS SITE
# -----------------------

def verificar_status():

    try:

        r = requests.get(url,timeout=10)

        soup = BeautifulSoup(r.text,"html.parser")

        texto = soup.text.lower()

        if "currently online" in texto:
            return "online"

        return "offline"

    except Exception as e:

        erro = f"⚠️ Erro ao acessar site: {e}"

        print(erro)

        enviar(erro)

        return None

# -----------------------
# STATS (LEVEL / MELEE / DEF)
# -----------------------

def pegar_stats():

    personagem = CHAR_NAME

    stats = {
        "level": None,
        "melee": None,
        "defense": None
    }

    # LEVEL (perfil)
    try:

        r = requests.get(url, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        texto = soup.text

        if "Level" in texto:
            stats["level"] = int(texto.split("Level")[1].split()[0])

    except Exception as e:

        print("Erro ao pegar level:", e)


    # MELEE
    try:

        r = requests.get(
            "https://www.rucoyonline.com/highscores/melee/2016/1",
            timeout=10
        )

        soup = BeautifulSoup(r.text, "html.parser")

        for row in soup.find_all("tr"):

            cols = row.find_all("td")

            if len(cols) >= 3:

                nome = cols[1].text.strip().replace("Online","").strip()

                if nome == personagem:

                    stats["melee"] = int(cols[2].text.strip())
                    break

    except Exception as e:

        print("Erro ao pegar melee:", e)


    # DEFENSE
    try:

        r = requests.get(
            "https://www.rucoyonline.com/highscores/defense/2016/1",
            timeout=10
        )

        soup = BeautifulSoup(r.text, "html.parser")

        for row in soup.find_all("tr"):

            cols = row.find_all("td")

            if len(cols) >= 3:

                nome = cols[1].text.strip().replace("Online","").strip()

                if nome == personagem:

                    stats["defense"] = int(cols[2].text.strip())
                    break

    except Exception as e:

        print("Erro ao pegar defense:", e)

    return stats

def verificar_stats():

    global stats_memoria

    stats_antigos = carregar_json(stats_file)
    stats_atuais = pegar_stats()

    if not stats_atuais:
        return

    # atualizar memória apenas se pegou stats válidos
    if stats_atuais["level"]:
        stats_memoria = stats_atuais

    if stats_antigos:

        if stats_atuais["level"] and stats_atuais["level"] > stats_antigos.get("level", 0):

            enviar(
f"""🎉 **LEVEL UP**

{stats_antigos['level']} → {stats_atuais['level']}"""
)

        if stats_atuais["melee"] and stats_atuais["melee"] > stats_antigos.get("melee", 0):

            enviar(
f"""🗡 **MELEE UP**

{stats_antigos['melee']} → {stats_atuais['melee']}"""
)

        if stats_atuais["defense"] and stats_atuais["defense"] > stats_antigos.get("defense", 0):

            enviar(
f"""🛡 **DEFENSE UP**

{stats_antigos['defense']} → {stats_atuais['defense']}"""
)

    salvar_json(stats_file, stats_atuais)

def pegar_xp():

    personagem = CHAR_NAME

    try:

        r = requests.get(
            "https://www.rucoyonline.com/highscores/experience",
            timeout=10
        )

        soup = BeautifulSoup(r.text, "html.parser")

        for row in soup.find_all("tr"):

            cols = row.find_all("td")

            if len(cols) >= 4:

                nome = cols[1].text.strip().replace("Online","").strip()

                if nome == personagem:

                    xp = int(cols[3].text.strip().replace(",", ""))
                    return xp

    except Exception as e:
        print("Erro ao pegar XP:", e)

    return None

# -----------------------
# HISTÓRICO
# -----------------------

def carregar_historico():

    if not os.path.exists(historico_file):
        return []

    try:
        with open(historico_file,"r") as f:
            return json.load(f)
    except:
        return []

def salvar_historico(evento):

    historico = carregar_historico()

    historico.append(evento)

    with open(historico_file,"w") as f:
        json.dump(historico,f,indent=2)

# -----------------------
# ESTADO BOT
# -----------------------

def salvar_estado():

    data = {

        "ultimo_status":ultimo_status,
        "hora_login":str(hora_login) if hora_login else None,
        "hora_logout":str(hora_logout) if hora_logout else None,
        "painel_id":mensagem_painel_id

    }

    salvar_json(estado_file,data)

def carregar_estado():

    global ultimo_status,hora_login,hora_logout,mensagem_painel_id

    data = carregar_json(estado_file)

    ultimo_status = data.get("ultimo_status")

    if data.get("hora_login"):
        hora_login = datetime.fromisoformat(data["hora_login"])

    if data.get("hora_logout"):
        hora_logout = datetime.fromisoformat(data["hora_logout"])

    mensagem_painel_id = data.get("painel_id")

# -----------------------
# RESUMO DIÁRIO
# -----------------------

def resumo_diario():

    global reconexoes_dia

    historico = carregar_historico()

    total_online = 0
    sessoes = len(historico)

    for e in historico:

        total_online += e["tempo_online_h"]*3600
        total_online += e["tempo_online_m"]*60

    horas_online = total_online//3600
    minutos_online = (total_online%3600)//60

    total_dia = 86400

    offline = total_dia-total_online

    horas_off = offline//3600
    minutos_off = (offline%3600)//60

    enviar(

f"""📊 **_Resumo diário — {CHAR_NAME}_**

⏱ **Tempo online:** _{horas_online}h {minutos_online}m_
🔌 **Sessões:** _{sessoes}_
🔁 **Reconexões:** _{reconexoes_dia}_
📉 **Tempo offline:** _{horas_off}h {minutos_off}m_"""
)

    salvar_json(historico_file,[])
    salvar_json(estado_file,{})
    reconexoes_dia = 0

    enviar("_🧹 Dados do dia limpos com sucesso_")

    print("🧹 Histórico e estado resetados")

# -----------------------
# PAINEL ONLINE
# -----------------------

def painel_online():

    tempo = datetime.now(BRASIL) - hora_login

    h = tempo.seconds // 3600
    m = (tempo.seconds % 3600) // 60

    recon_text = ""

    if reconexoes:
        recon_text = "\n".join(reconexoes)

    level = stats_memoria["level"]
    melee = stats_memoria["melee"]
    defense = stats_memoria["defense"]

    return f"""📊  **_{CHAR_NAME} Tracker_**  📊

🟢  **Status:** _Online_
🕒  **Logado às:** _{hora_login.strftime('%H:%M')}_
⌛  **Sessão atual:** _{h}h {m}m_

{recon_text}

━━━━━━━━━━━━━━

🔥 **Stats atuais** 🔥

🏅 _Level_ → **{level}**
🗡 _Melee_ → **{melee}**
🛡 _Defense_ → **{defense}**"""

# -----------------------
# PAINEL OFFLINE
# -----------------------

def painel_offline():

    tempo = hora_logout - hora_login

    h = tempo.seconds//3600
    m = (tempo.seconds%3600)//60

    xp_texto = ""

    if xp_sessao_total > 0:
        xp_texto = f"\n💰 **XP da sessão:** _+{xp_sessao_total:,} XP_"

    return f"""📊 **_{CHAR_NAME} Tracker_** 📊

🔴 **Status:** _Offline_
🕒 Deslogou às: _{hora_logout.strftime('%H:%M')}_
⌛ Sessão durou: _{h}h {m}m_{xp_texto}"""

# -----------------------
# INICIO
# -----------------------

print("⚠️ Bot reiniciado ou reconectado")

enviar("**_⚠️ Bot reiniciado ou reconectado_**")

carregar_estado()
verificar_stats()

# -----------------------
# LOOP
# -----------------------

while True:

    try:

        agora = datetime.now(BRASIL)

        print(f"[{agora.strftime('%H:%M:%S')}] verificando...")

        status = verificar_status()

        if status is None:
            time.sleep(60)
            continue


        # LOGIN
        if status == "online" and ultimo_status != "online":

            if hora_logout:

                offline_time = (agora - hora_logout).seconds

                if offline_time <= TEMPO_RECONEXAO:

                    xp_final = pegar_xp()

                    msg_recon = f"_🔁 Reconectou ({offline_time}s) [{agora.strftime('%H:%M')}]_"
                    reconexoes.append(msg_recon)

                # XP ganho
                if xp_inicio_sessao and xp_final:

                    ganho = xp_final - xp_inicio_sessao
                    xp_sessao_total += ganho

                    if ganho >= 5_000_000:

                        msg_xp = f"_**💰 XP GAIN →** +{ganho:,} XP_"
                        reconexoes.append(msg_xp)

                    xp_inicio_sessao = xp_final  # reset pra próxima contagem

                    # limitar histórico visual
                    reconexoes_dia += 1

                    print("🔁 Reconexão detectada")

                    # ⭐ VERIFICAR STATS APÓS RECONEXÃO
                    time.sleep(5)
                    verificar_stats()

                    if mensagem_painel_id:
                        editar(mensagem_painel_id, painel_online())

                    ultimo_status = "online"
                    hora_logout = None
                    continue

            hora_login = agora
            reconexoes.clear()
            xp_inicio_sessao = pegar_xp()
            xp_sessao_total = 0

            mensagem_painel_id = enviar_e_pegar_id(painel_online())
            ultimo_update_painel = agora

            print("🟢 Painel ONLINE criado")

            ultimo_status = "online"


        # LOGOUT
        if status == "offline" and ultimo_status == "online":

            print("⏳ Possível logout, aguardando reconexão...")

            hora_logout = agora
            reconectou = False
            tempo_espera = 0

            while tempo_espera < TEMPO_RECONEXAO:

                time.sleep(30)
                tempo_espera += 30

                status_check = verificar_status()

                print(f"🔎 Checando reconexão... {tempo_espera}s")

                if status_check == "online":

                    recon_time = (datetime.now(BRASIL) - hora_logout).seconds

                    xp_final = pegar_xp()

                    msg_recon = f"_🔁 Reconectou ({recon_time}s) [{agora.strftime('%H:%M')}]_"
                    reconexoes.append(msg_recon)

                # XP ganho
                if xp_inicio_sessao and xp_final:

                    ganho = xp_final - xp_inicio_sessao
                    xp_sessao_total += ganho

                    if ganho >= 5_000_000:

                        msg_xp = f"_**💰 XP GAIN →** +{ganho:,} XP_"
                        reconexoes.append(msg_xp)

                    xp_inicio_sessao = xp_final  # reset pra próxima contagem

                    # limitar histórico visual
                    reconexoes_dia += 1

                    print("🔁 Reconexão detectada")

                    # ⭐ VERIFICAR STATS APÓS RECONEXÃO
                    time.sleep(5)
                    verificar_stats()

                    if mensagem_painel_id:
                        editar(mensagem_painel_id, painel_online())

                    ultimo_status = "online"
                    hora_logout = None
                    reconectou = True
                    break


            if not reconectou:

                # 🔴 CALCULAR XP FINAL DA SESSÃO
                xp_final = pegar_xp()

                if xp_inicio_sessao and xp_final:

                    ganho = xp_final - xp_inicio_sessao
                    xp_sessao_total += ganho

                # 🔴 AGORA ENVIA O PAINEL
                mensagem_painel_id = enviar_e_pegar_id(painel_offline())
                ultimo_update_painel = agora

                tempo = hora_logout - hora_login
# -----------------------
# LOOP
# -----------------------

while True:

    try:

        agora = datetime.now(BRASIL)

        print(f"[{agora.strftime('%H:%M:%S')}] verificando...")

        status = verificar_status()

        if status is None:
            time.sleep(60)
            continue


        # -----------------------
        # LOGIN
        # -----------------------
        if status == "online" and ultimo_status != "online":

            if hora_logout:

                offline_time = (agora - hora_logout).seconds

                if offline_time <= TEMPO_RECONEXAO:

                    xp_final = pegar_xp()

                    msg_recon = f"_🔁 Reconectou ({offline_time}s) [{agora.strftime('%H:%M')}]_"
                    reconexoes.append(msg_recon)

                    # XP ganho
                    if xp_inicio_sessao and xp_final:

                        ganho = xp_final - xp_inicio_sessao
                        xp_sessao_total += ganho

                        if ganho >= 5_000_000:
                            msg_xp = f"_**💰 XP GAIN →** +{formatar_xp(ganho)} XP_"
                            reconexoes.append(msg_xp)

                        xp_inicio_sessao = xp_final

                    reconexoes = reconexoes[-6:]
                    reconexoes_dia += 1

                    print("🔁 Reconexão detectada")

                    time.sleep(5)
                    verificar_stats()

                    if mensagem_painel_id:
                        editar(mensagem_painel_id, painel_online())

                    ultimo_status = "online"
                    hora_logout = None
                    continue

            # LOGIN NORMAL
            hora_login = agora
            reconexoes.clear()
            xp_inicio_sessao = pegar_xp()
            xp_sessao_total = 0

            mensagem_painel_id = enviar_e_pegar_id(painel_online())
            ultimo_update_painel = agora

            print("🟢 Painel ONLINE criado")

            ultimo_status = "online"


        # -----------------------
        # LOGOUT
        # -----------------------
        if status == "offline" and ultimo_status == "online":

            print("⏳ Possível logout, aguardando reconexão...")

            hora_logout = agora
            reconectou = False
            tempo_espera = 0

            while tempo_espera < TEMPO_RECONEXAO:

                time.sleep(30)
                tempo_espera += 30

                status_check = verificar_status()

                print(f"🔎 Checando reconexão... {tempo_espera}s")

                if status_check == "online":

                    recon_time = (datetime.now(BRASIL) - hora_logout).seconds

                    xp_final = pegar_xp()

                    msg_recon = f"_🔁 Reconectou ({recon_time}s) [{datetime.now(BRASIL).strftime('%H:%M')}]_"
                    reconexoes.append(msg_recon)

                    # XP ganho
                    if xp_inicio_sessao and xp_final:

                        ganho = xp_final - xp_inicio_sessao
                        xp_sessao_total += ganho

                        if ganho >= 5_000_000:
                            msg_xp = f"_**💰 XP GAIN →** +{formatar_xp(ganho)} XP_"
                            reconexoes.append(msg_xp)

                        xp_inicio_sessao = xp_final

                    reconexoes = reconexoes[-6:]
                    reconexoes_dia += 1

                    print("🔁 Reconexão detectada")

                    time.sleep(5)
                    verificar_stats()

                    if mensagem_painel_id:
                        editar(mensagem_painel_id, painel_online())

                    ultimo_status = "online"
                    hora_logout = None
                    reconectou = True
                    break


            # 🔴 LOGOUT DEFINITIVO
            if not reconectou:

                xp_final = pegar_xp()

                if xp_inicio_sessao and xp_final:

                    ganho = xp_final - xp_inicio_sessao
                    xp_sessao_total += ganho

                mensagem_painel_id = enviar_e_pegar_id(painel_offline())
                ultimo_update_painel = agora

                tempo = hora_logout - hora_login

                salvar_historico({
                    "tempo_online_h": tempo.seconds // 3600,
                    "tempo_online_m": (tempo.seconds % 3600) // 60
                })

                print("🔴 Painel OFFLINE enviado")

                time.sleep(5)
                verificar_stats()

                ultimo_status = "offline"


        # -----------------------
        # UPDATE PAINEL
        # -----------------------
        if status == "online" and mensagem_painel_id:

            if not ultimo_update_painel or (agora - ultimo_update_painel).seconds >= TEMPO_ATUALIZACAO_PAINEL:

                editar(mensagem_painel_id, painel_online())
                ultimo_update_painel = agora


        # RESUMO DIÁRIO
        if agora.hour == 2 and agora.minute == 0:

            resumo_diario()
            time.sleep(60)


        salvar_estado()

        time.sleep(60)

    except Exception as e:

        erro = traceback.format_exc()

        print("ERRO:", erro)

        enviar(f"🚨 **Erro no bot**\n```{erro}```")

        salvar_estado()

        time.sleep(60)

