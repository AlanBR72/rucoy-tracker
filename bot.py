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

CHAR_NAME = "Pravus Alan"

url = "https://www.rucoyonline.com/characters/Pravus%20Alan"

webhook = "https://discord.com/api/webhooks/1508611045143347240/5tA0ZwCJsLyzxMV2U62vckVVPSk68XGzrklf5zpgpQd7dtI37F3HPjwDzFy_pm8cQKMg"

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
xp_total_dia = 0

resumo_pendente = False

# -----------------------
# JSON
# -----------------------

stats_memoria = {
    "level": "?",
    "magic": "?",
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
# STATS (LEVEL / MAGIC / DEF)
# -----------------------

def pegar_stats():

    personagem = CHAR_NAME

    stats = {
        "level": None,
        "magic": None,
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


    # MAGIC
    try:

        r = requests.get(
            "https://www.rucoyonline.com/highscores/magic/2016/1",
            timeout=10
        )

        soup = BeautifulSoup(r.text, "html.parser")

        for row in soup.find_all("tr"):

            cols = row.find_all("td")

            if len(cols) >= 3:

                nome = cols[1].text.strip().replace("Online","").strip()

                if nome == personagem:

                    stats["magic"] = int(cols[2].text.strip())
                    break

    except Exception as e:

        print("Erro ao pegar magic:", e)


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

    # Garante valores numéricos seguros para comparação.
    level_antigo = stats_antigos.get("level") or 0
    magic_antigo = stats_antigos.get("magic") or 0
    defense_antigo = stats_antigos.get("defense") or 0

    # Atualiza cada stat da memória separadamente.
    # Assim, uma falha em um stat não impede os outros de atualizarem.
    for chave in ["level", "magic", "defense"]:
        if stats_atuais.get(chave) is not None:
            stats_memoria[chave] = stats_atuais[chave]
        elif stats_antigos.get(chave) is not None:
            stats_memoria[chave] = stats_antigos[chave]

    if stats_antigos:

        if stats_atuais.get("level") is not None and stats_atuais["level"] > level_antigo:

            enviar(
f"""🎉 **Level Up!**

🏅 `{level_antigo} ➜ {stats_atuais['level']}`

🕒 `{datetime.now(BRASIL).strftime('%H:%M')}`"""
)

        if stats_atuais.get("magic") is not None and stats_atuais["magic"] > magic_antigo:

            enviar(
f"""🪄 **Magic Up!**

🪄 `{magic_antigo} ➜ {stats_atuais['magic']}`

🕒 `{datetime.now(BRASIL).strftime('%H:%M')}`"""
)

        if stats_atuais.get("defense") is not None and stats_atuais["defense"] > defense_antigo:

            enviar(
f"""🛡️ **Defense Up!**

🛡️ `{defense_antigo} ➜ {stats_atuais['defense']}`

🕒 `{datetime.now(BRASIL).strftime('%H:%M')}`"""
)

    # Preserva o valor antigo quando alguma consulta retornar None.
    # Isso evita gravar null no stats.json e quebrar comparações futuras.
    stats_salvar = stats_antigos.copy()

    for chave in ["level", "magic", "defense"]:
        if stats_atuais.get(chave) is not None:
            stats_salvar[chave] = stats_atuais[chave]

    # Só salva quando existe pelo menos um stat válido.
    if any(stats_salvar.get(chave) is not None for chave in ["level", "magic", "defense"]):
        salvar_json(stats_file, stats_salvar)

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

def formatar_xp(valor):

    if valor >= 1_000_000_000:
        texto = f"{valor / 1_000_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{texto}kkk"

    elif valor >= 1_000_000:
        return f"{valor // 1_000_000}kk"

    else:
        return str(valor)

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
    global xp_total_dia, xp_sessao_total, xp_inicio_sessao

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

    xp_texto = ""

    if xp_total_dia >= 10_000_000:
        xp_texto = f"\n💰 XP total: `+{formatar_xp(xp_total_dia)}`"

    enviar(

f"""📊 **Resumo diário — {CHAR_NAME}**

🕑 Tempo online: `{horas_online}h {minutos_online}m`
📴 Tempo offline: `{horas_off}h {minutos_off}m`

🔌 Sessões: `{sessoes}`
🔁 Reconexões: `{reconexoes_dia}`{xp_texto}

🕒 Gerado às `{datetime.now(BRASIL).strftime('%H:%M')}`"""
)

    salvar_json(historico_file,[])
    salvar_json(estado_file,{})
    reconexoes_dia = 0

    # RESET XP
    xp_total_dia = 0
    xp_sessao_total = 0
    xp_inicio_sessao = None

    enviar("_🧹 Dados do dia limpos com sucesso_")

    print("🧹 Histórico e estado resetados")

# -----------------------
# PAINEL ONLINE
# -----------------------

def painel_online():

    tempo = datetime.now(BRASIL) - hora_login

    total_segundos = int(tempo.total_seconds())
    h = total_segundos // 3600
    m = (total_segundos % 3600) // 60

    level = stats_memoria["level"]
    magic = stats_memoria["magic"]
    defense = stats_memoria["defense"]

    xp_atual = pegar_xp()

    xp_inicial_texto = "Indisponível"
    xp_atual_texto = "Indisponível"
    xp_ganho_texto = "Calculando..."

    if xp_inicio_sessao is not None:
        xp_inicial_texto = f"{xp_inicio_sessao:,}".replace(",", ".")

    if xp_atual is not None:
        xp_atual_texto = f"{xp_atual:,}".replace(",", ".")

    if xp_inicio_sessao is not None and xp_atual is not None:
        ganho_atual = max(0, xp_atual - xp_inicio_sessao)
        xp_ganho_texto = f"+{formatar_xp(ganho_atual)}"

    recon_text = ""

    if reconexoes:
        recon_text = (
            f"\n\n🔁 Reconexões: `{len(reconexoes)}`\n"
            + "\n".join(reconexoes)
        )

    return f"""📊 **{CHAR_NAME} Tracker**

🟢 Online desde `{hora_login.strftime('%H:%M')}`
⌛ Sessão: `{h}h {m}m`

🔷 XP inicial: `{xp_inicial_texto}`
🔶 XP atual: `{xp_atual_texto}`
📈 XP ganho: `{xp_ganho_texto}`

🏅 Level `{level}` • 🪄 Magic `{magic}` • 🛡 Defense `{defense}`{recon_text}

🕒 Atualizado às `{datetime.now(BRASIL).strftime('%H:%M')}`"""

# -----------------------
# PAINEL OFFLINE
# -----------------------

def painel_offline():

    tempo = hora_logout - hora_login

    total_segundos = int(tempo.total_seconds())
    h = total_segundos // 3600
    m = (total_segundos % 3600) // 60

    level = stats_memoria["level"]
    magic = stats_memoria["magic"]
    defense = stats_memoria["defense"]

    xp_texto = ""

    if xp_sessao_total >= 10_000_000:
        xp_texto = f"\n\n💰 XP da sessão: `+{formatar_xp(xp_sessao_total)}`"

    recon_text = ""

    if reconexoes:
        recon_text = (
            f"\n\n🔁 Reconexões: `{len(reconexoes)}`\n"
            + "\n".join(reconexoes)
        )

    return f"""📊 **{CHAR_NAME} Tracker**

🔴 Offline às `{hora_logout.strftime('%H:%M')}`
⌛ Sessão: `{h}h {m}m`{xp_texto}

🏅 Level `{level}` • 🪄 Magic `{magic}` • 🛡 Defense `{defense}`{recon_text}

🕒 Encerrado às `{hora_logout.strftime('%H:%M')}`"""

# -----------------------
# INICIO
# -----------------------

print("⚠️  Bot reiniciado ou reconectado")

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

        # -----------------------
        # RESUMO PENDENTE (FORÇADO SE JÁ ESTÁ OFFLINE)
        # -----------------------
        if resumo_pendente and status == "offline" and ultimo_status == "offline":

            print("📊 Enviando resumo (offline sem evento)...")

            resumo_diario()
            resumo_pendente = False

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

                    ganho = 0

                    if xp_inicio_sessao is not None and xp_final is not None:
                        ganho = max(0, xp_final - xp_inicio_sessao)
                        xp_sessao_total += ganho
                        xp_total_dia += ganho
                        xp_inicio_sessao = xp_final

                    linha_reconexao = f"`{agora.strftime('%H:%M')}` ({offline_time}s)"

                    if ganho >= 5_000_000:
                        linha_reconexao += f" • `+{formatar_xp(ganho)}`"

                    reconexoes.append(linha_reconexao)

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

                    ganho = 0

                    if xp_inicio_sessao is not None and xp_final is not None:
                        ganho = max(0, xp_final - xp_inicio_sessao)
                        xp_sessao_total += ganho
                        xp_total_dia += ganho
                        xp_inicio_sessao = xp_final

                    linha_reconexao = f"`{datetime.now(BRASIL).strftime('%H:%M')}` ({recon_time}s)"

                    if ganho >= 5_000_000:
                        linha_reconexao += f" • `+{formatar_xp(ganho)}`"

                    reconexoes.append(linha_reconexao)

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

            # 🔴 LOGOUT REAL
            if not reconectou:

                xp_final = pegar_xp()

                if xp_inicio_sessao is not None and xp_final is not None:

                    ganho = max(0, xp_final - xp_inicio_sessao)
                    xp_sessao_total += ganho
                    xp_total_dia += ganho

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
                # RESUMO PENDENTE (APÓS LOGOUT)
                # -----------------------
                if resumo_pendente:

                    print("📊 Enviando resumo após logout...")

                    resumo_diario()
                    resumo_pendente = False

        # -----------------------
        # UPDATE PAINEL
        # -----------------------
        if status == "online" and mensagem_painel_id:

            if not ultimo_update_painel or (agora - ultimo_update_painel).seconds >= TEMPO_ATUALIZACAO_PAINEL:

                editar(mensagem_painel_id, painel_online())
                ultimo_update_painel = agora

        # -----------------------
        # RESUMO DIÁRIO
        # -----------------------
        if agora.hour == 2 and agora.minute == 0:
            
            resumo_pendente = True
            print("📊 Resumo diário pendente...")
            time.sleep(60)

        salvar_estado()

        time.sleep(60)

    except Exception as e:

        erro = traceback.format_exc()

        print("ERRO:", erro)

        enviar(f"🚨 **Erro no bot**\n```{erro}```")

        salvar_estado()

        time.sleep(60)