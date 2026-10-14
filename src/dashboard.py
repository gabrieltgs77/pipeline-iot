"""Dashboard Streamlit de temperaturas IoT.

Uso:
    streamlit run src/dashboard.py
"""
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

from config import get_engine

st.set_page_config(page_title="Dashboard de Temperaturas IoT", layout="wide")

VIEWS_PERMITIDAS = {"avg_temp_por_dispositivo", "leituras_por_hora", "temp_max_min_por_dia"}


@st.cache_resource
def engine():
    return get_engine()


@st.cache_data(ttl=300)
def load_data(view_name):
    """Carrega os dados de uma view do PostgreSQL."""
    if view_name not in VIEWS_PERMITIDAS:
        raise ValueError(f"View desconhecida: {view_name}")
    return pd.read_sql(text(f"SELECT * FROM {view_name}"), engine())


@st.cache_data(ttl=300)
def load_resumo():
    query = """
        SELECT COUNT(*)::int AS total,
               ROUND(AVG(temperature)::numeric, 1)::float AS media,
               MIN(noted_at) AS inicio,
               MAX(noted_at) AS fim
        FROM temperature_readings
    """
    return pd.read_sql(text(query), engine()).iloc[0]


st.title("Dashboard de Temperaturas IoT")
st.caption("Pipeline: CSV (Kaggle) → Python → PostgreSQL (Docker) → Views SQL → Streamlit")

try:
    resumo = load_resumo()
except Exception as erro:
    st.error("Não foi possível conectar ao banco. Verifique se o container está rodando "
             "(docker compose up -d) e se a ingestão foi executada (python src/ingest.py).")
    st.code(str(erro))
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Total de leituras", f"{resumo['total']:,}".replace(",", "."))
c2.metric("Temperatura média", f"{resumo['media']} °C")
c3.metric("Período", f"{resumo['inicio']:%d/%m/%Y} a {resumo['fim']:%d/%m/%Y}")

# Gráfico 1: Média de temperatura por dispositivo
st.header("Média de Temperatura por Dispositivo")
df_avg_temp = load_data("avg_temp_por_dispositivo")
fig1 = px.bar(df_avg_temp, x="device_id", y="avg_temp", text="avg_temp",
              labels={"device_id": "Dispositivo", "avg_temp": "Temperatura média (°C)"})
st.plotly_chart(fig1, width="stretch")

# Gráfico 2: Contagem de leituras por hora
st.header("Leituras por Hora do Dia")
df_leituras_hora = load_data("leituras_por_hora")
fig2 = px.line(df_leituras_hora, x="hora", y="contagem", markers=True,
               labels={"hora": "Hora do dia", "contagem": "Nº de leituras"})
st.plotly_chart(fig2, width="stretch")

# Gráfico 3: Temperaturas máximas e mínimas por dia
st.header("Temperaturas Máximas e Mínimas por Dia")
df_temp_max_min = load_data("temp_max_min_por_dia")
fig3 = px.line(df_temp_max_min, x="data", y=["temp_max", "temp_min"],
               labels={"data": "Data", "value": "Temperatura (°C)", "variable": "Medida"})
st.plotly_chart(fig3, width="stretch")
