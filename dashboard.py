import streamlit as st
import pandas as pd
import requests
import altair as alt
import pytz
import time

API_URL = "https://backend-pi-o2zm.onrender.com/all"

st.set_page_config(
    page_title="Dashboard de Monitoramento de Enchentes",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌧️ Dashboard - Monitoramento de Enchentes")

# ========== FUNÇÃO DE REFRESH AUTOMÁTICO ==========
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh >= 15:  
    st.session_state.last_refresh = time.time()
    st.experimental_rerun()

# =====================================================

BRAZIL_TIMEZONE = pytz.timezone('America/Sao_Paulo')

@st.cache_data(ttl=30)
def carregar_dados():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        df = pd.DataFrame(response.json())

        if df.empty:
            return pd.DataFrame()

        if "createdAt" in df.columns:
            df["createdAt"] = pd.to_datetime(df["createdAt"], utc=True)
            df["DataHoraBRT"] = df["createdAt"].dt.tz_convert(BRAZIL_TIMEZONE)
            df = df.sort_values(by="DataHoraBRT", ascending=False).reset_index(drop=True)

        return df

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()


df = carregar_dados()

if df.empty:
    st.warning("Nenhum dado encontrado ou erro ao acessar a API.")
    st.stop()

# ====================== MÉTRICAS =========================

total_registros = len(df)
ultimo = df.iloc[0]

distancia_atual = ultimo.get("distancia", "N/A")
nivel_atual = ultimo.get("level", "N/A")
ultima_hora = ultimo["DataHoraBRT"].strftime("%H:%M:%S em %d/%m")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total de Registros", total_registros)
col2.metric("Distância Atual (cm)", distancia_atual)
col3.metric("Último Nível", nivel_atual)
col4.metric("Última Atualização (BRT)", ultima_hora)

st.markdown("---")

# ====================== GRÁFICO TEMPORAL =========================

st.subheader("📈 Distância Registrada ao Longo do Tempo")

if "DataHoraBRT" in df.columns and "distancia" in df.columns:
    grafico_df = df.copy()
    grafico_df["DataHoraStr"] = grafico_df["DataHoraBRT"].dt.strftime("%d/%m %H:%M:%S")

    chart = (
        alt.Chart(grafico_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("DataHoraBRT:T", title="Data e Hora (BRT)"),
            y=alt.Y("distancia:Q", title="Distância (cm)"),
            color=alt.Color("level:N", title="Nível"),
            tooltip=["DataHoraStr", "distancia", "level"]
        )
        .properties(height=350)
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)
else:
    st.info("Dados insuficientes para gerar o gráfico temporal.")

st.markdown("---")

# ====================== GRÁFICO DE FREQUÊNCIA =========================

st.subheader("📊 Frequência por Nível de Alerta")

freq = df["level"].value_counts().reset_index()
freq.columns = ["Nível", "Quantidade"]

graf_barras = (
    alt.Chart(freq)
    .mark_bar()
    .encode(
        x="Nível:N",
        y="Quantidade:Q",
        color="Nível:N"
    )
    .properties(title="Ocorrências por Nível de Alerta")
)

st.altair_chart(graf_barras, use_container_width=True)

st.markdown("---")

# ====================== TABELA =========================

st.subheader("📋 Últimas Medições (BRT)")

st.dataframe(
    df[["distancia", "level", "DataHoraBRT"]]
    .rename(columns={
        "distancia": "Distância (cm)",
        "level": "Nível",
        "DataHoraBRT": "Data e Hora"
    }),
    use_container_width=True,
    hide_index=True
)
