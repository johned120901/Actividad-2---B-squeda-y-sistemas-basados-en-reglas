import pandas as pd
import networkx as nx
from rapidfuzz import process

# ==============================
# 1. Cargar archivos GTFS
# ==============================
stops = pd.read_csv("stops.txt")
stop_times = pd.read_csv("stop_times.txt")
trips = pd.read_csv("trips.txt")
routes = pd.read_csv("routes.txt")

# ==============================
# 2. Diccionario de estaciones
# ==============================
estaciones = {
    row["stop_id"]: {
        "nombre": row["stop_name"],
        "lat": row["stop_lat"],
        "lon": row["stop_lon"]
    }
    for _, row in stops.iterrows()
}

# ==============================
# 3. Seleccionar un trip_id representativo por cada route_id
# ==============================
representativos = trips.groupby("route_id").first().reset_index()

# Hacer merge eficiente
stop_times_filtrado = stop_times.merge(
    representativos[["trip_id", "route_id"]],
    on="trip_id"
).merge(
    routes[["route_id", "route_short_name"]],
    on="route_id"
)

# ==============================
# 4. Construcción de servicios
# ==============================
servicios = []
for (route_name, trip_id), group in stop_times_filtrado.groupby(["route_short_name", "trip_id"]):
    estaciones_seq = list(group.sort_values("stop_sequence")["stop_id"])
    if len(estaciones_seq) > 1:
        servicios.append((route_name, estaciones_seq))

print(f"Servicios cargados: {len(servicios)}")
print(f"Estaciones cargadas: {len(estaciones)}")

# ==============================
# 5. Construcción del grafo
# ==============================
G = nx.Graph()

# nodos
for stop_id, data in estaciones.items():
    G.add_node(stop_id, nombre=data["nombre"], pos=(data["lon"], data["lat"]))

# aristas
for route_name, estaciones_seq in servicios:
    for i in range(len(estaciones_seq) - 1):
        a, b = estaciones_seq[i], estaciones_seq[i + 1]
        if G.has_edge(a, b):
            G[a][b]["rutas"].add(route_name)
        else:
            G.add_edge(a, b, rutas={route_name}, peso=1)

# ==============================
# 6. Función de mejor ruta
# ==============================
def buscar_estacion(nombre):
    candidatos = stops["stop_name"].unique()
    mejor = process.extractOne(nombre, candidatos, score_cutoff=60)
    if mejor:
        stop_id = stops.loc[stops["stop_name"] == mejor[0], "stop_id"].values[0]
        return stop_id, mejor[0]
    return None, None

def mejor_ruta(origen_nombre, destino_nombre):
    origen_id, origen_real = buscar_estacion(origen_nombre)
    destino_id, destino_real = buscar_estacion(destino_nombre)

    if not origen_id or not destino_id:
        return None

    path = nx.shortest_path(G, origen_id, destino_id, weight="peso")

    ruta = []
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        rutas = ", ".join(G[a][b]["rutas"])
        ruta.append(f"{estaciones[a]['nombre']} → {estaciones[b]['nombre']} ({rutas})")

    return origen_real, destino_real, ruta

# ==============================
# 7. Ejecución interactiva
# ==============================
if __name__ == "__main__":
    print("\nPlanificador de Rutas TransMilenio (GTFS)\n")

    origen = input("Ingrese estación de origen: ")
    destino = input("Ingrese estación de destino: ")

    ruta = mejor_ruta(origen, destino)

    if ruta:
        origen_real, destino_real, pasos = ruta
        print(f"\nRuta óptima de {origen_real} a {destino_real}:\n")
        for paso in pasos:
            print("  -", paso)
    else:
        print("No se encontraron estaciones con esos nombres.")