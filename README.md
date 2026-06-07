# 🍽️ Restaurant Intelligence — Sistema de BI para PYMES Restauranteras

## 🎯 Objetivo

Sistema integral de inteligencia de negocios que traduce datos transaccionales crudos de un restaurante en **decisiones de alto impacto operativo y financiero** para dueños de PYMES sin formación técnica. Construido con rigor matemático y desplegado como aplicación web interactiva.

## 🏗️ Arquitectura del Sistema

```
restaurant-intelligence/
├── data/                  # Datasets crudos y procesados (protegidos por .gitignore)
├── src/                   # Módulos de Python para análisis
│   ├── data_cleaner.py    # Carga, limpieza y validación de datos
│   ├── clustering.py      # K-Means + determinación óptima de clusters
│   ├── forecasting.py     # Series de tiempo + pronóstico semanal
│   ├── menu_engineering.py# Matriz de Kasavana & Smith
│   └── pipeline.py        # Orquestador del pipeline completo
├── app/
│   └── main.py            # Dashboard Streamlit (4 secciones)
├── requirements.txt       # Dependencias con versiones fijas
├── README.md              # Esta documentación
└── .gitignore             # Archivos ignorados
```

## 🧠 Rigor Matemático

### 1. Segmentación Inteligente (K-Means)
- Algoritmo de agrupamiento no supervisado con `scikit-learn`.
- Número óptimo de clusters determinado por **Silhouette Score**.
- Variables: Ticket por comensal, Ratio Bebida/Alimento, Porcentaje de Propina.
- Normalización con `StandardScaler`.

### 2. Predicción Operativa
- Análisis de estacionalidad (efecto finde/semana, horas pico).
- Pronóstico semanal con tendencia lineal.
- Matriz de predicción para optimización de turnos de personal.

### 3. Ingeniería de Menú (Kasavana & Smith)
- Cálculo del Índice de Popularidad y Margen de Contribución.
- Clasificación automática en 4 categorías: ⭐ Estrella, 🐴 Caballo de Batalla, 🧩 Rompecabezas, 🐕 Perro.
- Recomendaciones estratégicas automatizadas.

## 🚀 Cómo Ejecutar Localmente

### 1. Clonar el repositorio
```bash
git clone <url-del-repo>
cd restaurant-intelligence
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Ejecutar el pipeline de datos
```bash
python3 src/pipeline.py
```
Esto genera: limpieza → clustering → forecasting → menú engineering.

### 4. Lanzar el Dashboard
```bash
streamlit run app/main.py
```
Se abrirá en `http://localhost:8501`.

## 📊 Dashboard — Secciones

1. **Panel Ejecutivo** — KPIs financieros con filtros dinámicos.
2. **Segmentación** — Visualización 3D de clusters con perfiles comerciales.
3. **Planificador de Turnos** — Pronóstico semanal + recomendación de personal.
4. **Optimizador de Menú** — Matriz interactiva de Kasavana & Smith.

## 🔬 Dataset

Dataset sintético de **20,371 transacciones** con 1 año de histórico de un restaurante premium. Variables incluyen: ID_Transaccion, Timestamp, ID_Mesa, Capacidad, Mesero, Detalle_Consumo, Costo_Producción, Subtotal, Propinas, Método_Pago.

## 👤 Autor

**Roberto Sousa Carranza** — Matemático | Análisis Cuantitativo y Ciencia de Datos
