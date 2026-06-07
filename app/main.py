"""
app/main.py — Dashboard Interactivo de Inteligencia Restaurantera

Streamlit app con 4 secciones:
1. Panel de Control Ejecutivo (KPIs Financieros)
2. Segmentación de Clientes (Clusters)
3. Planificador de Turnos Automatizado
4. Optimizador de Menú (Kasavana & Smith)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.clustering import preparar_datos_clustering

# ─── Configuración de página ──────────────────────────────────────────────
st.set_page_config(
    page_title="Restaurant Intelligence",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Cargar datos ─────────────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    df = pd.read_csv(os.path.join(base, "data", "transacciones_limpias.csv"),
                     parse_dates=["Timestamp"])
    demanda_diaria = pd.read_csv(os.path.join(base, "data", "demanda_diaria.csv"),
                                  parse_dates=["Fecha"])
    demanda_horaria = pd.read_csv(os.path.join(base, "data", "demanda_horaria.csv"),
                                   parse_dates=["Fecha_Hora"])
    pronostico = pd.read_csv(os.path.join(base, "data", "pronostico_semanal.csv"),
                              parse_dates=["Fecha"])
    df_menu = pd.read_csv(os.path.join(base, "data", "menu_analisis.csv"))
    return df, demanda_diaria, demanda_horaria, pronostico, df_menu

df, demanda_diaria, demanda_horaria, pronostico, df_menu = cargar_datos()

# ─── Sidebar ───────────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/restaurant--v1.png", width=80)
st.sidebar.title("🍽️ Restaurant BI")
st.sidebar.markdown("---")

# Filtros
st.sidebar.header("📅 Filtros")
fecha_min = df["Timestamp"].min().date()
fecha_max = df["Timestamp"].max().date()

rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max,
)

dias_semana = st.sidebar.multiselect(
    "Días de la semana",
    options=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"],
    default=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"],
)

turno = st.sidebar.radio("Turno", ["Todos", "Comida", "Cena"])

# Aplicar filtros
mask = (df["Timestamp"].dt.date >= rango_fechas[0]) & \
       (df["Timestamp"].dt.date <= rango_fechas[1])

dias_map = {0:"Lunes",1:"Martes",2:"Miércoles",3:"Jueves",4:"Viernes",5:"Sábado"}
mask &= df["Dia_Semana"].map(dias_map).isin(dias_semana)

if turno != "Todos":
    mask &= df["Turno"] == turno

df_filtrado = df[mask].copy()

# ─── HEADER ─────────────────────────────────────────────────────────────────
st.title("🍽️ Sistema de Inteligencia Restaurantera")
st.markdown("*Traduciendo datos en decisiones — Dashboard Ejecutivo*")
st.markdown("---")

# ─── SECCIÓN 1: KPIs Financieros ───────────────────────────────────────────
st.header("📊 Panel de Control Ejecutivo")

col1, col2, col3, col4 = st.columns(4)

with col1:
    ticket_prom = df_filtrado["Subtotal"].mean()
    st.metric("Ticket Promedio", f"${ticket_prom:,.0f}",
              delta=f"${ticket_prom - df['Subtotal'].mean():+,.0f} vs global")

with col2:
    ocupacion = df_filtrado["Comensales"].sum() / df_filtrado["Capacidad_Mesa"].sum() * 100
    st.metric("Ocupación Eficiente", f"{ocupacion:.1f}%")

with col3:
    margen_prom = df_filtrado["Margen_Pct"].mean()
    st.metric("Margen Bruto Promedio", f"{margen_prom:.1f}%")

with col4:
    pago_dist = df_filtrado["Metodo_Pago"].value_counts(normalize=True)
    st.metric("💳 Tarjeta (Nal+Int)", f"{pago_dist.get('Tarjeta Nacional',0)+pago_dist.get('Tarjeta Internacional',0):.0%}")

st.markdown("---")

# Gráficos de KPIs
col1, col2 = st.columns(2)

with col1:
    # Ingresos diarios
    ingresos_diarios = df_filtrado.groupby(df_filtrado["Timestamp"].dt.date)["Subtotal"].sum().reset_index()
    ingresos_diarios.columns = ["Fecha", "Ingresos"]
    fig = px.line(ingresos_diarios, x="Fecha", y="Ingresos",
                  title="📈 Ingresos Diarios",
                  labels={"Ingresos": "Ingresos ($)"})
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Distribución de métodos de pago
    pago_counts = df_filtrado["Metodo_Pago"].value_counts().reset_index()
    pago_counts.columns = ["Método", "Cantidad"]
    colores = {"Efectivo": "#2E86AB", "Tarjeta Nacional": "#A23B72",
               "Tarjeta Internacional": "#F18F01"}
    fig = px.pie(pago_counts, values="Cantidad", names="Método",
                  title="💳 Distribución de Métodos de Pago",
                  color="Método", color_discrete_map=colores)
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

# ─── SECCIÓN 2: Segmentación ───────────────────────────────────────────────
st.markdown("---")
st.header("👥 Segmentación de Clientes")

cluster_colors = {0: "#2E86AB", 1: "#A23B72", 2: "#F18F01", 3: "#4A9C6F"}

col1, col2 = st.columns([1, 1])

with col1:
    # Scatter 3D de clusters
    features = preparar_datos_clustering(df_filtrado)
    if "Cluster" in df_filtrado.columns:
        features["Cluster"] = df_filtrado["Cluster"]
        
        fig = px.scatter_3d(
            features, x="Ticket_Por_Comensal", y="Ratio_Bebida_Alimento",
            z="Propina_Pct", color="Cluster",
            color_continuous_scale="Viridis",
            title="🧬 Segmentos de Clientes (3D)",
            labels={
                "Ticket_Por_Comensal": "Ticket por comensal ($)",
                "Ratio_Bebida_Alimento": "Ratio Bebida/Alimento",
                "Propina_Pct": "Propina (%)"
            },
            opacity=0.6
        )
        fig.update_layout(height=450, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📋 Perfiles Comerciales")
    
    perfiles_texto = """
    | Segmento | Perfil | Ticket | Propina |
    |----------|--------|--------|---------|
    | **Cluster 0** | 👔 **Corporativo Premium** — Cenas de negocio, alto gasto | > $200 | > 14% |
    | **Cluster 1** | 👪 **Familiar** — Comida balanceada, ticket medio | $100-$200 | 10-14% |
    """
    st.markdown(perfiles_texto)
    
    # Distribución de clusters
    cluster_dist = df_filtrado["Cluster"].value_counts().reset_index()
    cluster_dist.columns = ["Cluster", "Cantidad"]
    cluster_dist["Cluster"] = cluster_dist["Cluster"].astype(str)
    
    fig = px.bar(cluster_dist, x="Cluster", y="Cantidad",
                  title="Distribución de Segmentos",
                  color="Cluster", color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

# ─── SECCIÓN 3: Planificador de Turnos ──────────────────────────────────────
st.markdown("---")
st.header("📅 Planificador de Turnos Automatizado")

col1, col2 = st.columns([2, 1])

with col1:
    # Demanda horaria
    demanda_hora_filtrada = demanda_horaria.copy()
    if not demanda_hora_filtrada.empty:
        demanda_hora_filtrada["Hora_str"] = demanda_hora_filtrada["Hora"].apply(
            lambda h: f"{h:02d}:00"
        )
        
        fig = px.box(demanda_hora_filtrada, x="Hora_str", y="Volumen_Ventas",
                      color="Turno",
                      title="⏰ Distribución de Demanda por Hora",
                      labels={"Volumen_Ventas": "Transacciones",
                              "Hora_str": "Hora"})
        fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("👥 Recomendación de Personal")
    
    # Promedios por hora
    if not demanda_hora_filtrada.empty:
        prom_hora = demanda_hora_filtrada.groupby("Hora")["Volumen_Ventas"].mean()
        pico_comida = prom_hora[13:16].max() if 13 in prom_hora.index else 0
        pico_cena = prom_hora[19:22].max() if 19 in prom_hora.index else 0
        
        st.metric("Pico Comida (13-16h)", f"~{pico_comida:.0f} transacciones")
        st.metric("Pico Cena (19-22h)", f"~{pico_cena:.0f} transacciones")
        
        st.info(
            "**Recomendación:**\n\n"
            f"• **Comida:** {max(3, int(pico_comida/15))} meseros + "
            f"{max(2, int(pico_comida/20))} cocina\n"
            f"• **Cena:** {max(4, int(pico_cena/15))} meseros + "
            f"{max(3, int(pico_cena/20))} cocina"
        )

# Pronóstico semanal
st.subheader("🔮 Pronóstico Próxima Semana")

if not pronostico.empty:
    pronostico["Fecha_str"] = pronostico["Fecha"].dt.strftime("%a %d/%m")
    
    fig = px.bar(pronostico, x="Fecha_str", y="Volumen_Estimado",
                  color="Personal_Recomendado",
                  title="Volumen Estimado por Día + Personal Recomendado",
                  labels={"Volumen_Estimado": "Transacciones estimadas",
                          "Fecha_str": "Día", "Personal_Recomendado": "Personal"},
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

# ─── SECCIÓN 4: Optimizador de Menú ────────────────────────────────────────
st.markdown("---")
st.header("🍽️ Optimizador de Menú (Kasavana & Smith)")

col1, col2 = st.columns([1.5, 1])

with col1:
    # Matriz de burbujas
    color_map = {
        "⭐ Estrella": "#2ECC71",
        "🐴 Caballo de Batalla": "#F1C40F",
        "🧩 Rompecabezas": "#3498DB",
        "🐕 Perro": "#E74C3C",
    }
    
    df_menu["Color"] = df_menu["Clasificacion"].map(color_map)
    
    fig = px.scatter(
        df_menu, x="Popularidad_Pct", y="Margen_Unitario",
        size="Veces_Vendido", color="Clasificacion",
        hover_name="Platillo", text="Platillo",
        title="🎯 Matriz de Ingeniería de Menú",
        labels={
            "Popularidad_Pct": "Popularidad (%)",
            "Margen_Unitario": "Margen Unitario ($)",
            "Veces_Vendido": "Veces vendido"
        },
        color_discrete_map=color_map,
        size_max=50
    )
    
    # Líneas divisorias
    mediana_pop = df_menu["Popularidad_Pct"].median()
    mediana_margen = df_menu["Margen_Unitario"].median()
    
    fig.add_hline(y=mediana_margen, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=mediana_pop, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(height=550, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("💡 Recomendaciones Estratégicas")
    
    for _, row in df_menu.iterrows():
        emoji = row["Clasificacion"].split()[0]
        if row["Clasificacion"].startswith("⭐"):
            rec = "✅ Mantener y promover activamente"
        elif row["Clasificacion"].startswith("🐴"):
            rec = "📈 Optimizar costos o aumentar precio"
        elif row["Clasificacion"].startswith("🧩"):
            rec = "🎯 Capacitar meseros para sugerirlo"
        else:
            rec = "⚠️ Considerar rediseño o sustitución"
        
        st.markdown(
            f"**{emoji} {row['Platillo']}** — ${row['Precio']:.0f} | "
            f"Pop: {row['Popularidad_Pct']:.1f}%\n\n"
            f"_{rec}_\n\n---"
        )

# ─── FOOTER ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "*🍽️ Restaurant Intelligence BI — Procesado con rigor matemático "
    "para dueños de PYMES restauranteras*"
)