"""
clustering.py — Segmentación Inteligente de Consumo (K-Means)

Implementa:
- K-Means con scikit-learn
- Determinación óptima de clusters (Elbow + Silhouette)
- Perfiles comerciales traducidos al lenguaje del dueño
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings("ignore")


def preparar_datos_clustering(df):
    """
    Prepara las características para clustering por mesa:
    - Ticket promedio por comensal
    - Ratio Bebida/Alimento
    - Porcentaje de propina
    """
    features = df[["Ticket_Por_Comensal", "Ratio_Bebida_Alimento", "Propina_Pct"]].copy()
    return features


def determinar_k_optimo(features, max_k=10):
    """
    Determina el número óptimo de clusters usando:
    - Método del Codo (inercia)
    - Silhouette Score
    
    Retorna el k recomendado y gráficos de diagnóstico (datos).
    """
    inertias = []
    sil_scores = []
    K_range = range(2, max_k + 1)
    
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(features)
        inertias.append(kmeans.inertia_)
        sil_scores.append(silhouette_score(features, kmeans.labels_))
    
    # Elegir k con mayor Silhouette Score
    k_optimo = K_range[np.argmax(sil_scores)]
    
    print("📊 Diagnóstico de clusters:")
    for k, inercia, sil in zip(K_range, inertias, sil_scores):
        indicador = " ← ÓPTIMO" if k == k_optimo else ""
        print(f"   k={k}: Inercia={inercia:.0f}, Silhouette={sil:.4f}{indicador}")
    
    return k_optimo, inertias, sil_scores


def aplicar_kmeans(features, k):
    """Aplica K-Means con k clusters."""
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features_scaled)
    
    print(f"✅ K-Means aplicado con k={k}")
    print(f"   Centroides (escalados):\n{np.round(kmeans.cluster_centers_, 3)}")
    
    return labels, kmeans, scaler


def traducir_perfiles(features, labels, k):
    """
    Traduce los clusters abstractos en perfiles comerciales claros.
    """
    df_temp = features.copy()
    df_temp["Cluster"] = labels
    
    perfiles = {}
    for i in range(k):
        grupo = df_temp[df_temp["Cluster"] == i]
        stats = {
            "ticket_promedio": grupo["Ticket_Por_Comensal"].mean(),
            "ratio_bebida": grupo["Ratio_Bebida_Alimento"].mean(),
            "propina_pct": grupo["Propina_Pct"].mean(),
            "tamano": len(grupo),
        }
        perfiles[i] = stats
        
        # Generar nombre comercial
        ticket = stats["ticket_promedio"]
        bebida = stats["ratio_bebida"]
        propina = stats["propina_pct"]
        pct = stats["tamano"] / len(df_temp) * 100
        
        if ticket > 200 and propina > 14:
            nombre = "👔 Corporativo Premium — Cenas de negocio, alto gasto, propina generosa"
        elif ticket > 150 and bebida > 0.35:
            nombre = "🍷 Celebraciones — Grupos grandes, muchas bebidas, estancia larga"
        elif ticket > 100:
            nombre = "👪 Familiar — Comida balanceada, ticket medio, propina estándar"
        else:
            nombre = "⚡ Rápido — Comensal individual, ticket bajo, consumo eficiente"
        
        print(f"\n   Cluster {i} ({pct:.1f}% de clientes):")
        print(f"      → {nombre}")
        print(f"      Ticket prom.: ${stats['ticket_promedio']:.2f}")
        print(f"      Ratio bebida: {stats['ratio_bebida']:.2f}")
        print(f"      Propina: {stats['propina_pct']:.1f}%")
    
    return perfiles


def run_clustering(df):
    """Ejecuta el pipeline completo de clustering."""
    print("=" * 55)
    print("🔬 SEGMENTACIÓN DE CLIENTES (K-Means)")
    print("=" * 55)
    
    features = preparar_datos_clustering(df)
    k_optimo, _, _ = determinar_k_optimo(features)
    labels, modelo, scaler = aplicar_kmeans(features, k_optimo)
    perfiles = traducir_perfiles(features, labels, k_optimo)
    
    df["Cluster"] = labels
    
    return df, modelo, scaler


if __name__ == "__main__":
    from data_cleaner import cargar_datos, limpiar_dataset
    df = cargar_datos("../data/transacciones_raw.csv")
    df = limpiar_dataset(df)
    df, _, _ = run_clustering(df)
    print(f"\n✅ Clustering completado. {df['Cluster'].nunique()} segmentos identificados.")