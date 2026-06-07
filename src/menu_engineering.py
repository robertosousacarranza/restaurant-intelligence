"""
menu_engineering.py — Ingeniería de Menú (Matriz de Kasavana & Smith)

Calcula:
- Índice de Popularidad de cada platillo
- Margen de Contribución
- Clasifica en: Estrella, Caballo de Batalla, Rompecabezas, Perro
"""

import pandas as pd
import numpy as np
import re


def extraer_items_del_menu(df):
    """
    Extrae todos los items del menú a partir del Detalle_Consumo
    y calcula popularidad y margen.
    """
    print("🔍 Extrayendo items del menú de las transacciones...")
    
    # Lista de platillos conocidos (del generador)
    platillos_conocidos = [
        "Tartar de Atún", "Carpaccio de Res", "Gazpacho Andaluz",
        "Ostiones Rockefeller", "Ensalada César",
        "Filete Wagyu 300g", "Salmón Glaseado", "Risotto de Hongos",
        "Lomo de Cerdo Confitado", "Pulpo a la Gallega",
        "Pasta Alfredo con Camarón", "Catch of the Day",
        "Copa de Vino Tinto", "Copa de Vino Blanco",
        "Margarita Artesanal", "Cerveza Artesanal",
        "Agua Mineral", "Refresco Importado",
        "Tiramisú Clásico", "Crème Brûlée", "Helado Artesanal",
    ]
    
    # Mapa de precio y costo para cada platillo
    menu_info = {
        "Tartar de Atún": (185, 52, "Entrada"),
        "Carpaccio de Res": (210, 63, "Entrada"),
        "Gazpacho Andaluz": (145, 38, "Entrada"),
        "Ostiones Rockefeller": (240, 78, "Entrada"),
        "Ensalada César": (165, 45, "Entrada"),
        "Filete Wagyu 300g": (520, 210, "Fuerte"),
        "Salmón Glaseado": (380, 148, "Fuerte"),
        "Risotto de Hongos": (310, 95, "Fuerte"),
        "Lomo de Cerdo Confitado": (290, 108, "Fuerte"),
        "Pulpo a la Gallega": (420, 172, "Fuerte"),
        "Pasta Alfredo con Camarón": (350, 120, "Fuerte"),
        "Catch of the Day": (450, 185, "Fuerte"),
        "Copa de Vino Tinto": (120, 48, "Bebida"),
        "Copa de Vino Blanco": (120, 48, "Bebida"),
        "Margarita Artesanal": (145, 38, "Bebida"),
        "Cerveza Artesanal": (85, 32, "Bebida"),
        "Agua Mineral": (45, 8, "Bebida"),
        "Refresco Importado": (55, 12, "Bebida"),
        "Tiramisú Clásico": (140, 42, "Postre"),
        "Crème Brûlée": (155, 50, "Postre"),
        "Helado Artesanal": (95, 25, "Postre"),
    }
    
    # Contar frecuencias
    frecuencias = {p: 0 for p in platillos_conocidos}
    total_items_vendidos = 0
    
    for detalle in df["Detalle_Consumo"]:
        for platillo in platillos_conocidos:
            if platillo in detalle:
                frecuencias[platillo] += 1
                total_items_vendidos += 1
    
    # Calcular métricas
    resultados = []
    for platillo, freq in frecuencias.items():
        precio, costo, categoria = menu_info[platillo]
        margen = precio - costo
        popularidad = freq / total_items_vendidos * 100  # porcentaje
        margen_pct = margen / precio * 100
        
        resultados.append({
            "Platillo": platillo,
            "Categoria": categoria,
            "Precio": precio,
            "Costo": costo,
            "Margen_Unitario": margen,
            "Margen_Pct": round(margen_pct, 1),
            "Veces_Vendido": freq,
            "Popularidad_Pct": round(popularidad, 2),
        })
    
    df_menu = pd.DataFrame(resultados)
    df_menu = df_menu.sort_values("Popularidad_Pct", ascending=False)
    
    print(f"   {len(df_menu)} platillos/bebidas únicos identificados")
    print(f"   Total de ítems vendidos: {total_items_vendidos:,}")
    
    return df_menu, total_items_vendidos


def clasificar_kasavana_smith(df_menu):
    """
    Clasifica cada item en la Matriz de Kasavana & Smith:
    
    Popularidad: media de popularidad como umbral
    Margen: media del margen unitario como umbral
    
    ┌─────────────────────┬────────────────────┬───────────────────┐
    │                     │  Alto Margen       │   Bajo Margen     │
    ├─────────────────────┼────────────────────┼───────────────────┤
    │  Alta Popularidad   │  ⭐ Estrella       │  🐴 Caballo       │
    │  Baja Popularidad   │  🧩 Rompecabezas   │  🐕 Perro         │
    └─────────────────────┴────────────────────┴───────────────────┘
    """
    print("\n📊 MATRIZ DE KASAVANA & SMITH:")
    
    mediana_popularidad = df_menu["Popularidad_Pct"].median()
    mediana_margen = df_menu["Margen_Unitario"].median()
    
    print(f"   Punto de corte popularidad: {mediana_popularidad:.1f}%")
    print(f"   Punto de corte margen: ${mediana_margen:.2f}")
    
    def clasificar(row):
        popular = row["Popularidad_Pct"] >= mediana_popularidad
        alto_margen = row["Margen_Unitario"] >= mediana_margen
        
        if popular and alto_margen:
            return "⭐ Estrella"
        elif popular and not alto_margen:
            return "🐴 Caballo de Batalla"
        elif not popular and alto_margen:
            return "🧩 Rompecabezas"
        else:
            return "🐕 Perro"
    
    df_menu["Clasificacion"] = df_menu.apply(clasificar, axis=1)
    
    # Mostrar resultados
    for cat in ["⭐ Estrella", "🐴 Caballo de Batalla", "🧩 Rompecabezas", "🐕 Perro"]:
        items = df_menu[df_menu["Clasificacion"] == cat]
        if len(items) > 0:
            print(f"\n   {cat} ({len(items)} items):")
            for _, row in items.iterrows():
                print(f"      • {row['Platillo']:35s} | ${row['Precio']:>3.0f} | "
                      f"Pop:{row['Popularidad_Pct']:5.1f}% | Margen:${row['Margen_Unitario']:>3.0f}")
    
    return df_menu


def generar_recomendaciones(df_menu):
    """Genera recomendaciones estratégicas automatizadas."""
    print("\n💡 RECOMENDACIONES ESTRATÉGICAS:")
    
    estrellas = df_menu[df_menu["Clasificacion"] == "⭐ Estrella"]
    caballos = df_menu[df_menu["Clasificacion"] == "🐴 Caballo de Batalla"]
    rompecabezas = df_menu[df_menu["Clasificacion"] == "🧩 Rompecabezas"]
    perros = df_menu[df_menu["Clasificacion"] == "🐕 Perro"]
    
    if len(estrellas) > 0:
        print("\n   ⭐ ESTRELLAS — Mantener y promover:")
        for _, r in estrellas.iterrows():
            print(f"      • {r['Platillo']}: Destacar en menú, priorizar en sugerencias")
    
    if len(caballos) > 0:
        print("\n   🐴 CABALLOS DE BATALLA — Optimizar costos:")
        for _, r in caballos.iterrows():
            print(f"      • {r['Platillo']}: Negociar costo con proveedor o "
                  f"aumentar precio ligeramente (elasticidad alta)")
    
    if len(rompecabezas) > 0:
        print("\n   🧩 ROMPECABEZAS — Mayor potencial:")
        for _, r in rompecabezas.iterrows():
            print(f"      • {r['Platillo']}: Capacitar meseros para sugerirlo, "
                  f"crear promoción especial, mejorar descripción")
    
    if len(perros) > 0:
        print("\n   🐕 PERROS — Revisar rentabilidad:")
        for _, r in perros.iterrows():
            print(f"      • {r['Platillo']}: Considerar rediseño, cambio de precio o "
                  f"sustitución del platillo")


def run_menu_engineering(df):
    """Ejecuta el pipeline completo de ingeniería de menú."""
    print("=" * 55)
    print("🍽️  INGENIERÍA DE MENÚ (Kasavana & Smith)")
    print("=" * 55)
    
    df_menu, total = extraer_items_del_menu(df)
    df_menu = clasificar_kasavana_smith(df_menu)
    generar_recomendaciones(df_menu)
    
    return df_menu


if __name__ == "__main__":
    from data_cleaner import cargar_datos, limpiar_dataset
    df = cargar_datos("../data/transacciones_raw.csv")
    df = limpiar_dataset(df)
    df_menu = run_menu_engineering(df)
    print(f"\n✅ Análisis de menú completado.")