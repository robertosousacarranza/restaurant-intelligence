"""
generate_report.py — Genera reporte PDF del análisis restaurantero
Salida: data/reporte_restaurante.pdf
"""

import os, sys, subprocess
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.chdir(BASE)

from src.data_cleaner import cargar_datos, limpiar_dataset
from src.clustering import run_clustering
from src.forecasting import run_forecasting
from src.menu_engineering import run_menu_engineering


def generar_reporte():
    """Ejecuta pipeline y genera PDF con resultados."""
    print("📊 Generando reporte PDF...")
    df = cargar_datos("data/transacciones_raw.csv")
    df = limpiar_dataset(df)
    df, _, _ = run_clustering(df)
    dd, dh, pron = run_forecasting(df)
    dm = run_menu_engineering(df)

    M = {}
    M["inicio"] = df["Timestamp"].min().strftime("%d/%m/%Y")
    M["fin"] = df["Timestamp"].max().strftime("%d/%m/%Y")
    M["txns"] = f"{len(df):,}"
    M["ing"] = "\$" + f"{df['Subtotal'].sum():,.2f}"
    M["tkt"] = "\$" + f"{df['Subtotal'].mean():,.2f}"
    M["mar"] = f"{df['Margen_Pct'].mean():.1f}\\%"
    M["pro"] = "\$" + f"{df['Propinas'].mean():.2f}"
    M["com"] = f"{df['Comensales'].sum():,}"
    M["ocu"] = f"{df['Comensales'].sum()/df['Capacidad_Mesa'].sum()*100:.1f}%"
    M["clu"] = str(df["Cluster"].nunique())
    M["itm"] = str(len(dm))

    pd_ = df["Metodo_Pago"].value_counts(normalize=True)
    M["ef"] = f"{pd_.get('Efectivo',0)*100:.1f}%"
    M["tn"] = f"{pd_.get('Tarjeta Nacional',0)*100:.1f}%"
    M["ti"] = f"{pd_.get('Tarjeta Internacional',0)*100:.1f}%"

    pdia = dd.groupby("Dia_Semana")["Volumen_Ventas"].mean()
    for k, i in [("Lun",0),("Mar",1),("Mie",2),("Jue",3),("Vie",4),("Sab",5)]:
        M["v"+k] = str(round(pdia.get(i,0)))

    mc = dm["Clasificacion"].value_counts()
    for k, v in [("est","⭐ Estrella"),("cab","🐴 Caballo"),("rom","🧩 Rompec"),("per","🐕 Perro")]:
        M[k] = str(int(mc.get(v, 0)))

    top = dm.sort_values("Popularidad_Pct", ascending=False).iloc[0]
    M["topn"] = top["Platillo"]
    M["topp"] = f"{top['Popularidad_Pct']:.1f}%"
    M["topm"] = "\$" + f"{top['Margen_Unitario']:.2f}"

    fecha = datetime.now().strftime("%d de %B de %Y")

    # Generar LaTeX por partes para evitar escapes
    lines = [
        "\\documentclass[10pt,letterpaper]{article}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage[T1]{fontenc}",
        "\\usepackage[margin=0.7in]{geometry}",
        "\\usepackage{mathpazo}",
        "\\usepackage{xcolor}",
        "\\usepackage{booktabs}",
        "\\usepackage{tabularx}",
        "\\usepackage{hyperref}",
        "\\pagestyle{empty}",
        "",
        "\\definecolor{primary}{HTML}{1B2A4A}",
        "\\definecolor{accent}{HTML}{E67E22}",
        "\\hypersetup{colorlinks=true,urlcolor=accent,linkcolor=primary}",
        "",
        "\\begin{document}",
        "",
        "\\begin{center}",
        "    {\\color{primary}\\Huge\\textbf{Restaurant Intelligence BI}}\\\\[4pt]",
        "    {\\large\\textbf{Reporte de An\\'alisis Restaurantero}}\\\\[6pt]",
        "    {\\small Generado el " + fecha + " por el pipeline automatizado}",
        "\\end{center}",
        "",
        "{\\color{accent}\\rule{\\linewidth}{1.5pt}}",
        "\\vspace{10pt}",
        "",
        "\\section*{Resumen Ejecutivo}",
        "",
        "\\begin{tabularx}{\\linewidth}{lX}",
        "    \\toprule",
        "    \\textbf{M\\'etrica} & \\textbf{Valor} \\\\",
        "    \\midrule",
        "    Per\\'iodo analizado & " + M["inicio"] + " -- " + M["fin"] + " \\\\",
        "    Transacciones & " + M["txns"] + " \\\\",
        "    Ingresos totales & " + M["ing"] + " \\\\",
        "    Ticket promedio & " + M["tkt"] + " \\\\",
        "    Comensales totales & " + M["com"] + " \\\\",
        "    Ocupaci\\'on promedio & " + M["ocu"] + " \\\\",
        "    Margen bruto promedio & " + M["mar"] + " \\\\",
        "    Propina promedio & " + M["pro"] + " \\\\",
        "    Segmentos de clientes & " + M["clu"] + " \\\\",
        "    \\'Items en men\\'u & " + M["itm"] + " \\\\",
        "    \\bottomrule",
        "\\end{tabularx}",
        "",
        "\\section*{An\\'alisis de Ingresos y Operaci\\'on}",
        "",
        "Los ingresos totales del per\\'iodo ascienden a \\textbf{" + M["ing"] + "} con un ticket promedio de \\textbf{" + M["tkt"] + "}. El margen bruto promedio es de \\textbf{" + M["mar"] + "}, indicando una operaci\\'on saludable.",
        "",
        "\\subsection*{Distribuci\\'on de M\\'etodos de Pago}",
        "\\begin{itemize}",
        "    \\item Efectivo: " + M["ef"],
        "    \\item Tarjeta Nacional: " + M["tn"],
        "    \\item Tarjeta Internacional: " + M["ti"],
        "\\end{itemize}",
        "",
        "\\section*{Demanda por D\\'ia}",
        "\\begin{tabularx}{\\linewidth}{lX}",
        "    \\toprule \\textbf{D\\'ia} & \\textbf{Volumen Promedio} \\\\ \\midrule",
        "    Lunes & " + M["vLun"] + " transacciones \\\\",
        "    Martes & " + M["vMar"] + " transacciones \\\\",
        "    Mi\\'ercoles & " + M["vMie"] + " transacciones \\\\",
        "    Jueves & " + M["vJue"] + " transacciones \\\\",
        "    Viernes & " + M["vVie"] + " transacciones \\\\",
        "    S\\'abado & " + M["vSab"] + " transacciones \\\\",
        "    \\bottomrule",
        "\\end{tabularx}",
        "",
        "\\section*{Segmentaci\\'on de Clientes}",
        "",
        "Se identificaron \\textbf{" + M["clu"] + " segmentos} de clientes mediante K-Means clustering con optimizaci\\'on por Silhouette Score. Cada segmento representa un perfil de consumo distinto que permite personalizar la experiencia del servicio y las estrategias de marketing.",
        "",
        "\\section*{Ingenier\\'ia de Men\\'u (Kasavana \\& Smith)}",
        "",
        "El men\\'u se clasific\\'o en las 4 categor\\'ias estrat\\'egicas de la industria restaurantera:",
        "\\begin{itemize}",
        "    \\item Estrellas (alta popularidad, alto margen): " + M["est"] + " items",
        "    \\item Caballos de Batalla (alta popularidad, bajo margen): " + M["cab"] + " items",
        "    \\item Rompecabezas (baja popularidad, alto margen): " + M["rom"] + " items",
        "    \\item Perros (baja popularidad, bajo margen): " + M["per"] + " items",
        "\\end{itemize}",
        "",
        "El platillo m\\'as popular es \\textbf{" + M["topn"] + "} con " + M["topp"] + " de popularidad y un margen unitario de " + M["topm"] + ".",
        "",
        "\\section*{Recomendaciones Estrat\\'egicas}",
        "\\begin{enumerate}",
        "    \\item \\textbf{Optimizar personal:} Aumentar personal en pico de cena (19--22h) donde la demanda es consistentemente mayor.",
        "    \\item \\textbf{Promover rompecabezas:} Capacitar al personal para sugerir platillos con alto margen pero baja popularidad.",
        "    \\item \\textbf{Gestionar pagos:} Si el efectivo domina, considerar incentivos para pagos digitales.",
        "    \\item \\textbf{Ajustar men\\'u:} Revisar los platillos clasificados como ``Perro'' para redise\\'no o sustituci\\'on.",
        "    \\item \\textbf{Monitorear:} Actualizar este reporte peri\\'odicamente para detectar cambios estacionales.",
        "\\end{enumerate}",
        "",
        "\\vfill",
        "\\begin{center}",
        "    {\\color{gray}\\small Generado por Restaurant Intelligence BI \\textbullet\\ Datos actualizados con cada ejecuci\\'on del pipeline}",
        "\\end{center}",
        "",
        "\\end{document}",
    ]

    tex = "\n".join(lines)
    os.chdir("data")
    with open("reporte_restaurante.tex", "w", encoding="utf-8") as f:
        f.write(tex)

    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "reporte_restaurante.tex"],
                       capture_output=True, timeout=30)

    for ext in [".aux", ".log", ".out"]:
        p = f"reporte_restaurante{ext}"
        if os.path.exists(p):
            os.remove(p)

    pdf = os.path.join(os.getcwd(), "reporte_restaurante.pdf")
    print(f"✅ Reporte PDF: {pdf}")
    print(f"   Tamaño: {os.path.getsize(pdf)/1024:.0f} KB")
    return pdf


if __name__ == "__main__":
    generar_reporte()
