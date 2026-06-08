"""
app/main.py — Dashboard Interactivo de Inteligencia Restaurantera

4 secciones:
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
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.clustering import preparar_datos_clustering

# Config
st.set_page_config(
    page_title="Restaurant Intelligence",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Colores consistentes ────────────────────────────────────────────────────
HEADER_BG = "#1B2A4A"
ACCENT = "#E67E22"

# ─── Cargar datos ────────────────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Intentar cargar con clusters, fallback a limpios
    cluster_path = os.path.join(base, "data", "transacciones_con_clusters.csv")
    limpio_path = os.path.join(base, "data", "transacciones_limpias.csv")
    
    if os.path.exists(cluster_path):
        df = pd.read_csv(cluster_path, parse_dates=["Timestamp"])
    else:
        df = pd.read_csv(limpio_path, parse_dates=["Timestamp"])
        if "Cluster" not in df.columns:
            df["Cluster"] = -1  # placeholder si no hay clusters
    
    # Rellenar NaN en columnas críticas
    for col in ["Margen_Pct", "Propina_Pct", "Ticket_Por_Comensal", "Ratio_Bebida_Alimento"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    demanda_diaria = pd.read_csv(
        os.path.join(base, "data", "demanda_diaria.csv"),
        parse_dates=["Fecha"]
    ) if os.path.exists(os.path.join(base, "data", "demanda_diaria.csv")) else pd.DataFrame()
    
    demanda_horaria = pd.read_csv(
        os.path.join(base, "data", "demanda_horaria.csv"),
        parse_dates=["Fecha_Hora"]
    ) if os.path.exists(os.path.join(base, "data", "demanda_horaria.csv")) else pd.DataFrame()
    
    pronostico = pd.read_csv(
        os.path.join(base, "data", "pronostico_semanal.csv"),
        parse_dates=["Fecha"]
    ) if os.path.exists(os.path.join(base, "data", "pronostico_semanal.csv")) else pd.DataFrame()
    
    df_menu = pd.read_csv(os.path.join(base, "data", "menu_analisis.csv"))
    if os.path.exists(os.path.join(base, "data", "menu_analisis.csv")) else pd.DataFrame()
    
    return df, demanda_diaria, demanda_horaria, pronostico, df_menu

df, demanda_diaria, demanda_horaria, pronostico, df_menu = cargar_datos()

# ─── Sidebar ─────────────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/restaurant--v1.png", width=80)
st.sidebar.title("🍽️ Restaurant BI")
st.sidebar.markdown("---")

st.sidebar.header("📅 Filtros")
fecha_min = df["Timestamp"].min().date() if not df.empty else pd.Timestamp.now().date()
fecha_max = df["Timestamp"].max().date() if not df.empty else pd.Timestamp.now().date()

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
if not df.empty:
    mask = (df["Timestamp"].dt.date >= rango_fechas[0]) & \
           (df["Timestamp"].dt.date <= rango_fechas[1])
    dias_map = {0:"Lunes",1:"Martes",2:"Miércoles",3:"Jueves",4:"Viernes",5:"Sábado"}
    mask &= df["Dia_Semana"].map(dias_map).isin(dias_semana)
    if turno != "Todos":
        mask &= df["Turno"] == turno
    df_filtrado = df[mask].copy()
else:
    df_filtrado = df.copy()

st.title("🍽️ Sistema de Inteligencia Restaurantera")
st.markdown("*Traduciendo datos en decisiones — Dashboard Ejecutivo*")
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1: KPIs
# ══════════════════════════════════════════════════════════════════════════════
st.header("📊 Panel de Control Ejecutivo")

col1, col2, col3, col4 = st.columns(4)

with col1:
    ticket_prom = float(df_filtrado["Subtotal"].mean()) if not df_filtrado.empty else 0
    st.metric("Ticket Promedio", f"${ticket_prom:,.0f}",
              delta=f"${ticket_prom - float(df['Subtotal'].mean()):+,.0f} vs global")

with col2:
    ocupacion = float(df_filtrado["Comensales"].sum()) / max(float(df_filtrado["Capacidad_Mesa"].sum()), 1) * 100
    st.metric("Ocupación", f"{ocupacion:.1f}%")

with col3:
    margen_prom = float(df_filtrado["Margen_Pct"].mean()) if not df_filtrado.empty else 0
    st.metric("Margen Bruto Prom.", f"{margen_prom:.1f}%")

with col4:
    pago_dist = df_filtrado["Metodo_Pago"].value_counts(normalize=True) if not df_filtrado.empty else pd.Series()
    tarjeta_pct = pago_dist.get("Tarjeta Nacional", 0) + pago_dist.get("Tarjeta Internacional", 0)
    st.metric("💳 Tarjeta (Nal+Int)", f"{tarjeta_pct:.0%}")

st.markdown("---")

if not df_filtrado.empty:
    col1, col2 = st.columns(2)
    with col1:
        ingresos_diarios = df_filtrado.groupby(df_filtrado["Timestamp"].dt.date)["Subtotal"].sum().reset_index()
        ingresos_diarios.columns = ["Fecha", "Ingresos"]
        fig = px.line(ingresos_diarios, x="Fecha", y="Ingresos",
                      title="📈 Ingresos Diarios")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        pago_counts = df_filtrado["Metodo_Pago"].value_counts().reset_index()
        pago_counts.columns = ["Método", "Cantidad"]
        fig = px.pie(pago_counts, values="Cantidad", names="Método",
                      title="💳 Métodos de Pago",
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2: Segmentación
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.header("👥 Segmentación de Clientes")

if "Cluster" in df_filtrado.columns and df_filtrado["Cluster"].nunique() > 1:
    col1, col2 = st.columns([1, 1])
    with col1:
        features = preparar_datos_clustering(df_filtrado)
        features["Cluster"] = df_filtrado["Cluster"]
        fig = px.scatter_3d(
            features, x="Ticket_Por_Comensal", y="Ratio_Bebida_Alimento",
            z="Propina_Pct", color="Cluster",
            color_continuous_scale="Viridis",
            title="🧬 Segmentos (3D)",
            opacity=0.6
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📋 Perfiles Comerciales")
        cluster_desc = {
            0: "👔 **Corporativo Premium** — Alto gasto, propina generosa",
            1: "👪 **Familiar** — Gasto medio, estancia balanceada",
            2: "🍷 **Celebraciones** — Muchas bebidas, grupos grandes",
            3: "⚡ **Rápido** — Comensal individual, consumo eficiente"
        }
        for c in sorted(df_filtrado["Cluster"].unique()):
            subset = df_filtrado[df_filtrado["Cluster"] == c]
            name = cluster_desc.get(int(c), f"Cluster {c}")
            st.markdown(f"{name} — {len(subset)} transacciones")

        cluster_dist = df_filtrado["Cluster"].value_counts().reset_index()
        cluster_dist.columns = ["Cluster", "Cantidad"]
        fig = px.bar(cluster_dist, x="Cluster", y="Cantidad",
                      title="Distribución de Segmentos",
                      color="Cluster", color_continuous_scale="Viridis")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Ejecuta el pipeline completo para ver segmentación de clientes")

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3: Planificador de Turnos
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.header("📅 Planificador de Turnos Automatizado")

if not demanda_horaria.empty:
    col1, col2 = st.columns([2, 1])
    with col1:
        demanda_horaria["Hora_str"] = demanda_horaria["Hora"].apply(lambda h: f"{h:02d}:00")
        fig = px.box(demanda_horaria, x="Hora_str", y="Volumen_Ventas",
                      color="Turno",
                      title="⏰ Demanda por Hora",
                      labels={"Volumen_Ventas": "Transacciones", "Hora_str": "Hora"})
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("👥 Personal Recomendado")
        prom_hora = demanda_horaria.groupby("Hora")["Volumen_Ventas"].mean()
        pico_comida = max(prom_hora.get(13, 0), prom_hora.get(14, 0), prom_hora.get(15, 0))
        pico_cena = max(prom_hora.get(19, 0), prom_hora.get(20, 0), prom_hora.get(21, 0))
        st.metric("Pico Comida (13-16h)", f"~{pico_comida:.0f} transacciones")
        st.metric("Pico Cena (19-22h)", f"~{pico_cena:.0f} transacciones")
        st.info(
            "**Recomendación:**\n\n"
            f"• **Comida:** {max(3, int(pico_comida/15))} meseros + {max(2, int(pico_comida/20))} cocina\n"
            f"• **Cena:** {max(4, int(pico_cena/15))} meseros + {max(3, int(pico_cena/20))} cocina"
        )

    if not pronostico.empty:
        pronostico["Fecha_str"] = pronostico["Fecha"].dt.strftime("%a %d/%m")
        fig = px.bar(pronostico, x="Fecha_str", y="Volumen_Estimado",
                      color="Personal_Recomendado",
                      title="🔮 Pronóstico Semanal",
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Ejecuta el pipeline para ver el planificador de turnos")

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4: Optimizador de Menú
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.header("🍽️ Optimizador de Menú (Kasavana & Smith)")

if not df_menu.empty:
    col1, col2 = st.columns([1.5, 1])
    with col1:
        color_map = {
            "⭐ Estrella": "#2ECC71", "🐴 Caballo de Batalla": "#F1C40F",
            "🧩 Rompecabezas": "#3498DB", "🐕 Perro": "#E74C3C",
        }
        df_menu["Color"] = df_menu["Clasificacion"].map(color_map)
        fig = px.scatter(df_menu, x="Popularidad_Pct", y="Margen_Unitario",
                          size="Veces_Vendido", color="Clasificacion",
                          hover_name="Platillo", text="Platillo",
                          title="🎯 Matriz de Ingeniería de Menú",
                          color_discrete_map=color_map, size_max=50)
        med_pop = df_menu["Popularidad_Pct"].median()
        med_marg = df_menu["Margen_Unitario"].median()
        fig.add_hline(y=med_marg, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=med_pop, line_dash="dash", line_color="gray", opacity=0.5)
        fig.update_traces(textposition="top center", textfont_size=9)
        fig.update_layout(height=550)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💡 Recomendaciones Estratégicas")
        for _, row in df_menu.iterrows():
            if row["Clasificacion"].startswith("⭐"):
                rec = "✅ Mantener y promover activamente"
            elif row["Clasificacion"].startswith("🐴"):
                rec = "📈 Optimizar costos o aumentar precio"
            elif row["Clasificacion"].startswith("🧩"):
                rec = "🎯 Capacitar meseros para sugerirlo"
            else:
                rec = "⚠️ Considerar rediseño o sustitución"
            st.markdown(f"**{row['Clasificacion'].split()[0]} {row['Platillo']}** — ${row['Precio']:.0f} | Pop: {row['Popularidad_Pct']:.1f}%\n\n_{rec}_\n\n---")
else:
    st.info("Ejecuta el pipeline para ver el análisis de menú")

# ─── FOOTER ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("*🍽️ Restaurant Intelligence BI — Datos sintéticos de 20,371 transacciones*")

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown(f"**📊 Datos:** {len(df):,} transacciones")
if "Cluster" in df.columns and df["Cluster"].nunique() > 1:
    st.sidebar.markdown(f"**👥 Segmentos:** {df['Cluster'].nunique()}")
st.sidebar.markdown(f"**🍽️ Menú:** {len(df_menu)} platillos")
st.sidebar.markdown("---")
st.sidebar.markdown("**💡 Para usar con tus datos:**")
st.sidebar.markdown("1. Reemplaza `data/transacciones_raw.csv`")
st.sidebar.markdown("2. Ejecuta `python src/pipeline.py`")
st.sidebar.markdown("3. Recarga este dashboard")
st.sidebar.markdown("---")
st.sidebar.markdown("<sub>Hecho con ❤️ para dueños de PYMES restauranteras</sub>", unsafe_allow_html=True)