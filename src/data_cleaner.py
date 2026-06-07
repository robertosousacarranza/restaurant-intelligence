"""
data_cleaner.py — Limpieza, validación y feature engineering

Maneja:
- Valores nulos (NaN)
- Duplicados
- Anomalías en cobros
- Cálculo de Ratio Bebida/Alimento
- Normalización de nombres de columnas
"""

import pandas as pd
import numpy as np


def cargar_datos(ruta="data/transacciones_raw.csv"):
    """Carga el dataset crudo."""
    df = pd.read_csv(ruta, parse_dates=["Timestamp"])
    print(f"📂 Cargados {len(df):,} registros desde {ruta}")
    return df


def limpiar_dataset(df):
    """
    Pipeline completo de limpieza.
    - Elimina duplicados exactos
    - Maneja valores nulos
    - Filtra anomalías (subtotal < 0, costo > subtotal con margen > 3 desv)
    - Calcula Ratio Bebida/Alimento
    """
    print("🧹 Iniciando limpieza...")
    original_len = len(df)
    
    # 1. Duplicados exactos
    duplicados = df.duplicated().sum()
    df = df.drop_duplicates()
    print(f"   Duplicados eliminados: {duplicados}")
    
    # 2. Valores nulos
    nulos_por_columna = df.isnull().sum()
    cols_con_nulos = nulos_por_columna[nulos_por_columna > 0]
    if len(cols_con_nulos) > 0:
        print(f"   Columnas con nulos:\n{cols_con_nulos}")
        # Estrategia: rellenar nulos numéricos con mediana
        for col in cols_con_nulos.index:
            if df[col].dtype in ["float64", "int64"]:
                df[col].fillna(df[col].median(), inplace=True)
            else:
                df[col].fillna("Desconocido", inplace=True)
        print("   ✅ Nulos manejados")
    else:
        print("   ✅ Sin valores nulos")
    
    # 3. Anomalías en cobros
    # Subtotal negativo o cero
    anomalias_subtotal = (df["Subtotal"] <= 0).sum()
    df = df[df["Subtotal"] > 0]
    
    # Costo de producción > Subtotal (pérdida absoluta) — posible pero atípico si es > 3 sigma
    df["Margen_Bruto"] = df["Subtotal"] - df["Costo_Produccion_Total"]
    media_margen = df["Margen_Bruto"].mean()
    std_margen = df["Margen_Bruto"].std()
    anomalias_margen = (df["Margen_Bruto"] < media_margen - 3 * std_margen).sum()
    df = df[df["Margen_Bruto"] >= media_margen - 3 * std_margen]
    
    # Propinas negativas
    anomalias_propina = (df["Propinas"] < 0).sum()
    df = df[df["Propinas"] >= 0]
    
    print(f"   Subtotal ≤ 0 eliminados: {anomalias_subtotal}")
    print(f"   Margen atípico (< 3σ) eliminados: {anomalias_margen}")
    print(f"   Propinas negativas eliminadas: {anomalias_propina}")
    
    # 4. Calcular Ratio Bebida/Alimento
    df = calcular_ratio_bebida_alimento(df)
    
    # 5. Feature engineering temporal
    df["Dia_Semana_Num"] = df["Timestamp"].dt.dayofweek  # 0=lun, 6=dom
    df["Mes"] = df["Timestamp"].dt.month
    df["Semana_Anio"] = df["Timestamp"].dt.isocalendar().week.astype(int)
    
    eliminados = original_len - len(df)
    print(f"   Total registros eliminados: {eliminados} ({eliminados/original_len*100:.1f}%)")
    print(f"✅ Dataset limpio: {len(df):,} registros")
    
    return df


def calcular_ratio_bebida_alimento(df):
    """
    Calcula el ratio Bebida/Alimento por transacción analizando 
    el Detalle_Consumo.
    
    Busca items de bebida en el string de detalle y cuenta proporción.
    """
    # Palabras clave de bebidas en los nombres del menú
    bebidas_keywords = [
        "Vino", "Margarita", "Cerveza", "Agua Mineral", 
        "Refresco", "Copa de"
    ]
    
    ratios = []
    for detalle in df["Detalle_Consumo"]:
        items = detalle.split(" | ")
        total_items = len(items)
        bebidas = sum(1 for item in items if any(
            bk.lower() in item.lower() for bk in bebidas_keywords
        ))
        ratio = bebidas / total_items if total_items > 0 else 0
        ratios.append(ratio)
    
    df["Ratio_Bebida_Alimento"] = ratios
    return df


def guardar_dataset(df, ruta="data/transacciones_limpias.csv"):
    """Guarda el dataset procesado."""
    df.to_csv(ruta, index=False)
    print(f"💾 Guardado en {ruta}")
    return ruta


if __name__ == "__main__":
    df = cargar_datos()
    df_limpio = limpiar_dataset(df)
    guardar_dataset(df_limpio)
    
    print("\n📊 Resumen estadístico rápido:")
    print(df_limpio[["Subtotal", "Costo_Produccion_Total", "Propinas", "Margen_Bruto"]].describe())
