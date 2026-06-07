"""
forecasting.py — Predicción Operativa y Flujo de Demanda

Analiza estacionalidad y pronostica:
- Volumen de ventas horario y diario
- Ingresos esperados por turno
- Matriz de predicción para optimización de personal
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")


def agregar_demanda_diaria(df):
    """Agrega transacciones a nivel diario para forecast."""
    df_diario = df.copy()
    df_diario["Fecha"] = df_diario["Timestamp"].dt.date
    df_diario["Fecha"] = pd.to_datetime(df_diario["Fecha"])
    
    demanda = df_diario.groupby("Fecha").agg(
        Volumen_Ventas=("ID_Transaccion", "count"),
        Ingresos_Totales=("Subtotal", "sum"),
        Ticket_Promedio=("Subtotal", "mean"),
        Comensales_Totales=("Comensales", "sum"),
    ).reset_index()
    
    demanda["Dia_Semana"] = demanda["Fecha"].dt.dayofweek
    demanda["Es_FinDeSemana"] = demanda["Dia_Semana"] >= 5
    demanda["Mes"] = demanda["Fecha"].dt.month
    
    return demanda


def agregar_demanda_horaria(df):
    """Agrega transacciones a nivel horario."""
    df_hora = df.copy()
    df_hora["Fecha_Hora"] = df_hora["Timestamp"].dt.floor("h")
    
    demanda = df_hora.groupby("Fecha_Hora").agg(
        Volumen_Ventas=("ID_Transaccion", "count"),
        Ingresos=("Subtotal", "sum"),
    ).reset_index()
    
    demanda["Hora"] = demanda["Fecha_Hora"].dt.hour
    demanda["Dia_Semana"] = demanda["Fecha_Hora"].dt.dayofweek
    demanda["Turno"] = demanda["Hora"].apply(lambda h: "Comida" if h < 17 else "Cena")
    demanda["Es_FinDeSemana"] = demanda["Dia_Semana"] >= 5
    
    return demanda


def analizar_estacionalidad(demanda_diaria):
    """Analiza patrones de estacionalidad en los datos."""
    print("\n📅 ANÁLISIS DE ESTACIONALIDAD:")
    
    # Por día de la semana
    por_dia = demanda_diaria.groupby("Dia_Semana")["Volumen_Ventas"].mean()
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    print("\n   Volumen promedio por día:")
    for d, vol in zip(dias, por_dia):
        print(f"      {d}: {vol:.0f} transacciones")
    
    # Finde vs semana
    finde = demanda_diaria[demanda_diaria["Es_FinDeSemana"]]["Volumen_Ventas"].mean()
    semana = demanda_diaria[~demanda_diaria["Es_FinDeSemana"]]["Volumen_Ventas"].mean()
    print(f"\n   📊 Finde: {finde:.0f} txn/día vs Semana: {semana:.0f} txn/día")
    print(f"      Incremento finde: {((finde/semana)-1)*100:.0f}%")
    
    # Por mes (estacionalidad anual)
    por_mes = demanda_diaria.groupby("Mes")["Ingresos_Totales"].sum()
    meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    print("\n   Ingresos por mes:")
    for m, ing in zip(meses, por_mes):
        bar = "█" * int(ing / por_mes.max() * 30)
        print(f"      {m}: ${ing:>8,.0f} {bar}")
    
    return por_dia, por_mes


def pronosticar_semana(demanda_diaria):
    """
    Genera pronóstico simple para la próxima semana basado en
    promedios históricos por día de semana con tendencia.
    """
    print("\n🔮 PRONÓSTICO PARA PRÓXIMA SEMANA:")
    
    # Última fecha en datos
    ultima_fecha = demanda_diaria["Fecha"].max()
    
    # Tendencia lineal simple (crecimiento semanal)
    demanda_diaria["Semana"] = demanda_diaria["Fecha"].dt.isocalendar().week.astype(int)
    prom_por_semana = demanda_diaria.groupby("Semana")["Volumen_Ventas"].sum()
    if len(prom_por_semana) > 1:
        x = np.arange(len(prom_por_semana))
        y = prom_por_semana.values
        coef = np.polyfit(x, y, 1)
        tendencia_semanal = coef[0]
    else:
        tendencia_semanal = 0
    
    # Pronóstico por día de la próxima semana
    promedios_dia = demanda_diaria.groupby("Dia_Semana")["Volumen_Ventas"].mean()
    resultado = []
    
    for i in range(7):
        fecha_pred = ultima_fecha + timedelta(days=i + 1)
        dia_sem = fecha_pred.weekday()
        
        if dia_sem in promedios_dia.index:
            base = promedios_dia[dia_sem]
        else:
            base = 0
        
        vol_estimado = max(0, round(base))
        
        # Asignar personal necesario
        if vol_estimado > 80:
            personal = "ALTA — 6 meseros + 4 cocina"
        elif vol_estimado > 55:
            personal = "MEDIA — 4 meseros + 3 cocina"
        elif vol_estimado > 35:
            personal = "NORMAL — 3 meseros + 2 cocina"
        else:
            personal = "BAJA — 2 meseros + 1 cocina"
        
        dias_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        print(f"\n   {dias_es[dia_sem]} ({fecha_pred.strftime('%d/%m')}):")
        print(f"      📈 Volumen estimado: {vol_estimado} transacciones")
        print(f"      👥 Personal recomendado: {personal}")
        
        resultado.append({
            "Fecha": fecha_pred,
            "Dia": dias_es[dia_sem],
            "Volumen_Estimado": vol_estimado,
            "Personal_Recomendado": personal,
        })
    
    return pd.DataFrame(resultado)


def run_forecasting(df):
    """Ejecuta el pipeline completo de forecasting."""
    print("=" * 55)
    print("📈 PREDICCIÓN OPERATIVA Y FLUJO DE DEMANDA")
    print("=" * 55)
    
    demanda_diaria = agregar_demanda_diaria(df)
    demanda_horaria = agregar_demanda_horaria(df)
    
    analizar_estacionalidad(demanda_diaria)
    pronostico = pronosticar_semana(demanda_diaria)
    
    return demanda_diaria, demanda_horaria, pronostico


if __name__ == "__main__":
    from data_cleaner import cargar_datos, limpiar_dataset
    df = cargar_datos("../data/transacciones_raw.csv")
    df = limpiar_dataset(df)
    _, _, pronostico = run_forecasting(df)
    print(f"\n✅ Pronóstico generado para {len(pronostico)} días.")