import streamlit as st
import pandas as pd
import requests
import altair as alt
import pytz
import pyotp
import numpy as np
from dotenv import load_dotenv
import os

# ==============================
# CONFIGURAÇÕES DE LOGIN
# ==============================

load_dotenv()

PASSWORD_GESTOR = os.getenv("PASSWORD_GESTOR")
PASSWORD_ADMIN = os.getenv("PASSWORD_ADMIN")
SECRET_KEY = os.getenv("SECRET_KEY")

totp = pyotp.TOTP(SECRET_KEY)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "role" not in st.session_state:
    st.session_state.role = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# ==============================
# FUNÇÃO DE LOGIN
# ==============================
def login_screen():

    st.image("logo.png", width=250)

    st.title("Login necessário")

    password = st.text_input("Usúario:")
    code = st.text_input("Código MFA:")

    if st.button("Entrar"):
        if totp.verify(code):
            if password == PASSWORD_GESTOR:
                st.session_state.authenticated = True
                st.session_state.role = "gestor"
                st.rerun()

            elif password == PASSWORD_ADMIN:
                st.session_state.authenticated = True
                st.session_state.role = "admin"
                st.rerun()

            else:
                st.error("Senha incorreta.")
        else:
            st.error("Código MFA inválido.")

# =====================================
# SE O USUÁRIO NÃO ESTIVER LOGADO → LOGIN
# =====================================
if not st.session_state.authenticated:
    login_screen()
    st.stop()

# =====================================
# SIDEBAR COM NAVEGAÇÃO
# =====================================
st.sidebar.title(" Navegação")

if st.sidebar.button("📊 Dashboard"):
    st.session_state.page = "Dashboard"

if st.session_state.role == "admin":
    if st.sidebar.button("📜 Logs"):
        st.session_state.page = "Logs"

if st.sidebar.button("🚪 Sair"):
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.page = "Dashboard"
    st.rerun()

# =====================================
# CONFIGURAÇÕES GERAIS
# =====================================
API_URL = "https://backend-pi-o2zm.onrender.com/all"
BRAZIL_TIMEZONE = pytz.timezone('America/Sao_Paulo')

st.set_page_config(
    page_title="Dashboard de Monitoramento de Enchentes",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=10)
def carregar_dados():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()

        df = pd.DataFrame(response.json())
        if df.empty:
            return pd.DataFrame()

        df["createdAt"] = pd.to_datetime(df["createdAt"], utc=True)
        df["Data"] = df["createdAt"].dt.tz_convert(BRAZIL_TIMEZONE)
        df = df.sort_values(by="Data", ascending=False).reset_index(drop=True)
        df["DataHoraStr"] = df["Data"].dt.strftime("%d/%m %H:%M:%S")

        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()


# =====================================
# DASHBOARD COMPLETO (AGORA DENTRO DA FUNÇÃO)
# =====================================
def dashboard_page():
    st.title("🌧️ Dashboard - Monitoramento de Enchentes")

    df = carregar_dados()
    if df.empty:
        st.warning("Nenhum dado encontrado ou erro ao acessar a API.")
        return

    alerta_box = st.empty()

    def mostrar_alerta(nivel, distancia):
        nivel_limpo = (
            str(nivel).strip().lower().replace("í","i").replace("é","e")
        )

        if nivel_limpo == "enchentes":
            alerta_box.error(f"🚨 ALERTA MÁXIMO — ENCHENTES!\nDistância: **{distancia} cm**")
        elif nivel_limpo in ("medio",):
            alerta_box.warning(f"⚠️ Nível Médio — Distância: **{distancia} cm**")
        elif nivel_limpo == "normal":
            alerta_box.success(f"🟢 Normal — Distância: **{distancia} cm**")
        else:
            alerta_box.info(f"ℹ️ Nível Desconhecido ({nivel}) — {distancia} cm")

    # MÉTRICAS
    ultimo = df.iloc[0]

    distancia = ultimo["distancia"]
    nivel = ultimo["level"].upper()
    ultima_hora = ultimo["Data"].strftime("%H:%M:%S (%d/%m)")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Registros", len(df))
    col2.metric("Distância Atual (cm)", distancia)
    col3.metric("Nível Atual", nivel)
    col4.metric("Última Atualização", ultima_hora)

    mostrar_alerta(nivel, distancia)

    st.markdown("---")
    st.subheader("📈 Distância ao longo do tempo")

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x="Data:T",
            y="distancia:Q",
            color="level:N",
            tooltip=["DataHoraStr","distancia","level"]
        )
        .properties(height=350)
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)

    # --- VARIAÇÃO ---
    df["variacao"] = df["distancia"].diff() * -1
    df["MA_3"] = df["distancia"].rolling(3).mean()
    df["MA_7"] = df["distancia"].rolling(7).mean()
    df["timestamp"] = df["Data"].astype(int) / 10**9

    coef = np.polyfit(df["timestamp"], df["distancia"], 1)
    trend = np.poly1d(coef)
    df["tendencia"] = trend(df["timestamp"])


    st.markdown("---")
    st.subheader("📈 Médias móveis")

    graf_ma = (
        alt.Chart(df).mark_line(color="blue").encode(x="Data:T", y="MA_3:Q")
        +
        alt.Chart(df).mark_line(color="orange").encode(x="Data:T", y="MA_7:Q")
    )
    st.altair_chart(graf_ma, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 Tendência")

    graf_tendencia = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(x="Data:T", y="distancia:Q")
        +
        alt.Chart(df)
        .mark_line(color="red")
        .encode(x="Data:T", y="tendencia:Q")
    )
    st.altair_chart(graf_tendencia, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Últimas medições")

    st.dataframe(
        df[["distancia","level","Data"]],
        hide_index=True,
        use_container_width=True
    )


# =====================================
# LOGS — APENAS ADMINISTRADOR
# =====================================
def logs_page():
    st.title("📜 Logs de Auditoria")

    try:
        response = requests.get("https://backend-pi-o2zm.onrender.com/logs")
        logs = pd.DataFrame(response.json())
    except:
        st.error("Erro ao carregar logs.")
        return

    if logs.empty:
        st.warning("Nenhum log registrado.")
        return

    logs["createdAt"] = pd.to_datetime(logs["createdAt"])
    st.dataframe(logs, use_container_width=True)


# ================================
# RENDERIZAÇÃO DA PÁGINA
# ================================
if st.session_state.page == "Dashboard":
    dashboard_page()

elif st.session_state.page == "Logs" and st.session_state.role == "admin":
    logs_page()

else:
    st.error("Acesso negado.")
