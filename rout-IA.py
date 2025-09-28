import pandas as pd
import networkx as nx
from rapidfuzz import process, fuzz

# Cargar stops.txt
stops_df = pd.read_csv("stops.txt")

# Crear diccionario stop_id -> stop_name
stop_id_to_name = dict(zip(stops_df["stop_id"], stops_df["stop_name"]))

# Cargar stop_times.txt
stop_times_df = pd.read_csv("stop_times.txt")

# Ordenar por trip_id y stop_sequence
stop_times_df = stop_times_df.sort_values(by=["trip_id", "stop_sequence"])

# Crear grafo
G = nx.Graph()

# Agrupar por trip_id y conectar estaciones en orden
for trip_id, group in stop_times_df.groupby("trip_id"):
    stop_ids = group["stop_id"].tolist()
    for i in range(len(stop_ids) - 1):
        a = stop_id_to_name.get(stop_ids[i])
        b = stop_id_to_name.get(stop_ids[i + 1])
        if a and b:
            G.add_edge(a, b)

# Coincidencia difusa
def buscar_estacion(nombre_usuario):
    return process.extractOne(nombre_usuario, list(G.nodes), scorer=fuzz.WRatio)[0]

# Ruta óptima
def calcular_ruta(origen, destino):
    est_origen = buscar_estacion(origen)
    est_destino = buscar_estacion(destino)
    try:
        return nx.shortest_path(G, source=est_origen, target=est_destino)
    except nx.NetworkXNoPath:
        return f"No hay ruta entre {est_origen} y {est_destino}"

# Interfaz dinámica
if __name__ == "__main__":
    print("Planificador de rutas TransMilenio (GTFS)")
    while True:
        origen = input("Ingrese estación de origen (o 'salir' para terminar): ")
        if origen.lower() == "salir":
            break
        destino = input("Ingrese estación de destino: ")
        ruta = calcular_ruta(origen, destino)
        print("\nRuta sugerida:")
        print(" -> ".join(ruta) if isinstance(ruta, list) else ruta)
