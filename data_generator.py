"""
data_generator.py — Generación de dataset sintético de restaurante premium

Genera 20,000+ transacciones con 1 año de histórico, incluyendo:
- Detalle de consumo por mesa (platillos y bebidas)
- Costos de producción, propinas, métodos de pago
- Estacionalidad realista (fines de semana, horas pico)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

# ─── Menú del Restaurante ───────────────────────────────────────────────────
# Cada platillo: (nombre, precio_venta, costo_producción, categoría)
MENU_ITEMS = [
    # Entradas
    ("Tartar de Atún", 185, 52, "Entrada"),
    ("Carpaccio de Res", 210, 63, "Entrada"),
    ("Gazpacho Andaluz", 145, 38, "Entrada"),
    ("Ostiones Rockefeller (6pz)", 240, 78, "Entrada"),
    ("Ensalada César", 165, 45, "Entrada"),
    
    # Platos Fuertes
    ("Filete Wagyu 300g", 520, 210, "Fuerte"),
    ("Salmón Glaseado", 380, 148, "Fuerte"),
    ("Risotto de Hongos", 310, 95, "Fuerte"),
    ("Lomo de Cerdo Confitado", 290, 108, "Fuerte"),
    ("Pulpo a la Gallega", 420, 172, "Fuerte"),
    ("Pasta Alfredo con Camarón", 350, 120, "Fuerte"),
    ("Catch of the Day", 450, 185, "Fuerte"),
    
    # Bebidas
    ("Copa de Vino Tinto", 120, 48, "Bebida"),
    ("Copa de Vino Blanco", 120, 48, "Bebida"),
    ("Margarita Artesanal", 145, 38, "Bebida"),
    ("Cerveza Artesanal", 85, 32, "Bebida"),
    ("Agua Mineral", 45, 8, "Bebida"),
    ("Refresco Importado", 55, 12, "Bebida"),
    
    # Postres
    ("Tiramisú Clásico", 140, 42, "Postre"),
    ("Crème Brûlée", 155, 50, "Postre"),
    ("Helado Artesanal (2 bochas)", 95, 25, "Postre"),
]

# ─── Mesas del restaurante ──────────────────────────────────────────────────
MESAS = [
    (1, 2), (2, 2), (3, 4), (4, 4), (5, 4),
    (6, 6), (7, 6), (8, 8), (9, 4), (10, 2),
    (11, 4), (12, 6), (13, 4), (14, 2), (15, 4),
]  # (ID_Mesa, Capacidad)

MESEROS = [f"M{i:03d}" for i in range(1, 13)]  # 12 meseros

METODOS_PAGO = ["Efectivo", "Tarjeta Nacional", "Tarjeta Internacional"]

# Probabilidades de método de pago (día de semana vs fin de semana)
PROB_PAGO_SEMANA = [0.25, 0.55, 0.20]
PROB_PAGO_FINDE = [0.35, 0.40, 0.25]

# Probabilidad de propina según método de pago (% del subtotal)
PROPINA_PCT = {
    "Efectivo": (0.08, 0.12),
    "Tarjeta Nacional": (0.10, 0.15),
    "Tarjeta Internacional": (0.12, 0.18),
}


def generar_dias_operacion(year=2026):
    """Genera lista de fechas hábiles (lun-sáb, cerrado domingos)."""
    start = datetime(year, 1, 1)
    end = datetime(year, 12, 31)
    dias = []
    for i in range((end - start).days + 1):
        d = start + timedelta(days=i)
        if d.weekday() != 6:  # domingo = 6
            dias.append(d)
    return dias


def generar_una_transaccion(fecha, idx):
    """Genera una transacción realista para una fecha y hora dadas."""
    
    # ── Hora de apertura según día ──
    es_finde = fecha.weekday() >= 5  # sábado=5
    if es_finde:
        hora_apertura, hora_cierre = 12, 23  # finde abren más temprano
    else:
        hora_apertura, hora_cierre = 13, 22  # entre semana
    
    hora = random.randint(hora_apertura, hora_cierre)
    minuto = random.choice([0, 15, 30, 45])
    timestamp = fecha.replace(hour=hora, minute=minuto, second=0)
    
    # ── Seleccionar mesa ──
    id_mesa, capacidad = random.choice(MESAS)
    
    # ── Número de comensales (1 a capacidad) ──
    num_comensales = random.randint(1, capacidad)
    
    # ── Seleccionar mesero ──
    id_mesero = random.choice(MESEROS)
    
    # ── Generar consumo (cada comensal pide 1-4 items) ──
    items_consumidos = []
    for _ in range(num_comensales):
        # Cada comensal pide 1-4 items
        num_items_persona = random.choices(
            [1, 2, 3, 4], 
            weights=[0.05, 0.35, 0.45, 0.15]
        )[0]
        for _ in range(num_items_persona):
            items_consumidos.append(random.choice(MENU_ITEMS))
    
    # ── Calcular totales ──
    subtotal = sum(item[1] for item in items_consumidos)
    costo_produccion = sum(item[2] for item in items_consumidos)
    
    # ── Método de pago ──
    prob_pago = PROB_PAGO_FINDE if es_finde else PROB_PAGO_SEMANA
    metodo = random.choices(METODOS_PAGO, weights=prob_pago)[0]
    
    # ── Propina ──
    propina_min, propina_max = PROPINA_PCT[metodo]
    propina_pct = random.uniform(propina_min, propina_max)
    propina = round(subtotal * propina_pct, 2)
    
    # ── Detalle de consumo como string ──
    detalle = " | ".join([f"{item[0]}(${item[1]})" for item in items_consumidos])
    
    return {
        "ID_Transaccion": f"TXN-{idx:06d}",
        "Timestamp": timestamp,
        "ID_Mesa": id_mesa,
        "Capacidad_Mesa": capacidad,
        "Comensales": num_comensales,
        "ID_Mesero": id_mesero,
        "Detalle_Consumo": detalle,
        "Num_Items": len(items_consumidos),
        "Costo_Produccion_Total": round(costo_produccion, 2),
        "Subtotal": round(subtotal, 2),
        "Propinas": propina,
        "Metodo_Pago": metodo,
        "Dia_Semana": timestamp.strftime("%A"),
        "Hora": hora,
        "Es_FinDeSemana": es_finde,
        "Turno": "Comida" if hora < 17 else "Cena",
    }


def generar_dataset():
    """Genera el dataset completo con 20,000+ transacciones."""
    print("🍽️  Generando dataset de restaurante premium...")
    
    dias = generar_dias_operacion(2026)
    print(f"   Días de operación: {len(dias)}")
    
    registros = []
    idx = 0
    
    for fecha in dias:
        # Número de transacciones por día (más los fines de semana)
        es_finde = fecha.weekday() >= 5
        num_txns = random.randint(70, 110) if es_finde else random.randint(45, 75)
        
        for _ in range(num_txns):
            idx += 1
            registros.append(generar_una_transaccion(fecha, idx))
    
    df = pd.DataFrame(registros)
    
    # Añadir columna de margen
    df["Margen_Bruto"] = df["Subtotal"] - df["Costo_Produccion_Total"]
    df["Margen_Pct"] = round((df["Margen_Bruto"] / df["Subtotal"]) * 100, 2)
    df["Propina_Pct"] = round((df["Propinas"] / df["Subtotal"]) * 100, 2)
    df["Ticket_Por_Comensal"] = round(df["Subtotal"] / df["Comensales"], 2)
    df["Ratio_Bebida_Alimento"] = 0.0  # se calculará post-procesamiento
    
    print(f"✅ Dataset generado: {len(df)} transacciones")
    print(f"   Período: {df['Timestamp'].min()} → {df['Timestamp'].max()}")
    print(f"   Ingresos totales: ${df['Subtotal'].sum():,.2f}")
    print(f"   Ticket promedio: ${df['Subtotal'].mean():.2f}")
    
    return df


if __name__ == "__main__":
    df = generar_dataset()
    df.to_csv("data/transacciones_raw.csv", index=False)
    print("💾 Guardado en data/transacciones_raw.csv")
