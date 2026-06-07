"""
pipeline.py — Orquestador del pipeline completo

Ejecuta: Limpieza → Clustering → Forecasting → Menú Engineering
Guarda resultados intermedios para el dashboard.
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_cleaner import cargar_datos, limpiar_dataset, guardar_dataset
from clustering import run_clustering
from forecasting import run_forecasting
from menu_engineering import run_menu_engineering


def ejecutar_pipeline(ruta_datos="data/transacciones_raw.csv"):
    """Ejecuta el pipeline completo y retorna todos los resultados."""
    print("=" * 55)
    print("🏗️  PIPELINE COMPLETO — SISTEMA DE INTELIGENCIA")
    print("   PARA PYMES RESTAURANTERAS")
    print("=" * 55)
    
    # 1. Carga y limpieza
    print("\n━━━ FASE 1: ADQUISICIÓN Y LIMPIEZA ━━━")
    df = cargar_datos(ruta_datos)
    df = limpiar_dataset(df)
    guardar_dataset(df, "data/transacciones_limpias.csv")
    
    # 2. Clustering
    print("\n━━━ FASE 2.1: SEGMENTACIÓN ━━━")
    df, modelo_kmeans, scaler = run_clustering(df)
    
    # 3. Forecasting
    print("\n━━━ FASE 2.2: PREDICCIÓN OPERATIVA ━━━")
    demanda_diaria, demanda_horaria, pronostico = run_forecasting(df)
    
    # 4. Menú Engineering
    print("\n━━━ FASE 2.3: INGENIERÍA DE MENÚ ━━━")
    df_menu = run_menu_engineering(df)
    
    # ── Guardar resultados para el dashboard ──
    demanda_diaria.to_csv("data/demanda_diaria.csv", index=False)
    demanda_horaria.to_csv("data/demanda_horaria.csv", index=False)
    pronostico.to_csv("data/pronostico_semanal.csv", index=False)
    df_menu.to_csv("data/menu_analisis.csv", index=False)
    print("\n💾 Resultados guardados en data/")
    
    # Resumen ejecutivo
    print("\n" + "=" * 55)
    print("📋 RESUMEN EJECUTIVO")
    print("=" * 55)
    print(f"   Transacciones analizadas: {len(df):,}")
    print(f"   Segmentos de clientes: {df['Cluster'].nunique()}")
    print(f"   Items en menú: {len(df_menu)}")
    print(f"   Ingresos totales: ${df['Subtotal'].sum():,.2f}")
    print(f"   Margen bruto promedio: {df['Margen_Pct'].mean():.1f}%")
    print(f"   Propina promedio: {df['Propinas'].mean():.2f}")
    print("=" * 55)
    
    return {
        "df": df,
        "demanda_diaria": demanda_diaria,
        "demanda_horaria": demanda_horaria,
        "pronostico": pronostico,
        "df_menu": df_menu,
        "modelo_kmeans": modelo_kmeans,
        "scaler": scaler,
    }


if __name__ == "__main__":
    resultados = ejecutar_pipeline()
    print("\n🎉 Pipeline completado exitosamente!")
