import json
import os
import streamlit as st

st.set_page_config(
    page_title="Torneo Liga - Franz Lameda", page_icon="🀁", layout="wide"
)

CLAVE_ACCESO = "POETA1479"
ARCHIVO_ESTADO = "torneos_estado.json"


# -----------------------------------------------------------------------------
# 1. PERSISTENCIA Y CARGA DE DATOS
# -----------------------------------------------------------------------------
def cargar_estado_general():
    if os.path.exists(ARCHIVO_ESTADO):
        try:
            with open(ARCHIVO_ESTADO, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def guardar_estado_general(torneos):
    with open(ARCHIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(torneos, f, ensure_ascii=False, indent=4)


# -----------------------------------------------------------------------------
# 2. MOTOR COMBINATORIO DE BYES Y PAREJAS SIN REPETICION
# -----------------------------------------------------------------------------
def normalizar_par(j1, j2):
    return tuple(sorted([j1, j2]))


def seleccionar_byes_equitativos(jugadores_ordenados, conteo_byes, cantidad_byes):
    """Elige los jugadores que descansan priorizando menor cantidad de Byes previos."""
    if cantidad_byes <= 0:
        return []
    # Orden estable: primero menos Byes acumulados; en empate, menor prioridad en ranking (final de la lista)
    total = len(jugadores_ordenados)
    candidatos = sorted(
        enumerate(jugadores_ordenados),
        key=lambda item: (conteo_byes.get(item[1], 0), -(total - item[0])),
    )
    return [nombre for _, nombre in candidatos[:cantidad_byes]]


def resolver_mesas_sin_repetir(jugadores_mesa, parejas_usadas):
    """Devuelve lista de parejas [[a, b], ...] para N/2 parejas evitando parejas repetidas."""
    n = len(jugadores_mesa)
    if n < 4 or n % 2 != 0:
        return None

    def backtrack(restantes, elegidas, usadas_actuales):
        if not restantes:
            return elegidas
        primero = restantes[0]
        for idx in range(1, len(restantes)):
            companero = restantes[idx]
            clave = normalizar_par(primero, companero)
            if clave not in usadas_actuales:
                nuevas_usadas = set(usadas_actuales)
                nuevas_usadas.add(clave)
                siguiente = restantes[1:idx] + restantes[idx + 1 :]
                sol = backtrack(
                    siguiente, elegidas + [[primero, companero]], nuevas_usadas
                )
                if sol is not None:
                    return sol
        return None

    return backtrack(list(jugadores_mesa), [], set(parejas_usadas))


def generar_ronda_completa(activos_ordenados, historial_parejas, conteo_byes):
    """Genera mesas de 4 jugadores y lista de Byes sin repetir parejas cuando es posible."""
    residuo = len(activos_ordenados) % 4
    byes = seleccionar_byes_equitativos(activos_ordenados, conteo_byes, residuo)
    en_juego = [j for j in activos_ordenados if j not in byes]

    usadas = {normalizar_par(p[0], p[1]) for p in historial_parejas if len(p) == 2}
    parejas = resolver_mesas_sin_repetir(en_juego, usadas)

    if parejas is None:
        # Si el cupo combinatorio de parejas únicas ya se agotó por cantidad de rondas,
        # prioriza las parejas con menor frecuencia histórica en vez de fallar.
        frecuencia = {}
        for p in historial_parejas:
            if len(p) == 2:
                k = normalizar_par(p[0], p[1])
                frecuencia[k] = frecuencia.get(k, 0) + 1

        def backtrack_min_rep(restantes, elegidas, freq_actual):
            if not restantes:
                return elegidas
            primero = restantes[0]
            opciones = []
            for idx in range(1, len(restantes)):
                companero = restantes[idx]
                clave = normalizar_par(primero, companero)
                opciones.append((freq_actual.get(clave, 0), idx, companero, clave))
            opciones.sort(key=lambda x: x[0])

            for _, idx, companero, clave in opciones:
                siguiente = restantes[1:idx] + restantes[idx + 1 :]
                nuevo_freq = dict(freq_actual)
                nuevo_freq[clave] = nuevo_freq.get(clave, 0) + 1
                sol = backtrack_min_rep(
                    siguiente, elegidas + [[primero, companero]], nuevo_freq
                )
                if sol is not None:
                    return sol
            return None

        parejas = backtrack_min_rep(list(en_juego), [], frecuencia) or []

    mesas = {}
    num_mesas = len(parejas) // 2
    for m_idx in range(num_mesas):
        mesas[f"mesa_{m_idx + 1}"] = {
            "pareja_A": parejas[2 * m_idx],
            "pareja_B": parejas[2 * m_idx + 1],
            "pts_A": 0,
            "pts_B": 0,
        }

    return mesas, byes


def reconstruir_historiales(datos_t):
    """Recalcula historial_parejas y conteo_byes desde las rondas registradas."""
    historial_parejas = []
    conteo_byes = {j: 0 for j in datos_t.get("atletas", [])}

    for r_str in sorted(
        datos_t.get("resultados_rondas", {}).keys(),
        key=lambda x: int(x) if str(x).isdigit() else 0,
    ):
        r_data = datos_t["resultados_rondas"][r_str]
        for jb in r_data.get("byes", []):
            conteo_byes[jb] = conteo_byes.get(jb, 0) + 1
        for m_data in r_data.get("mesas", {}).values():
            p_a = m_data.get("pareja_A", [])
            p_b = m_data.get("pareja_B", [])
            if len(p_a) == 2:
                historial_parejas.append(list(p_a))
            if len(p_b) == 2:
                historial_parejas.append(list(p_b))

    return historial_parejas, conteo_byes


# -----------------------------------------------------------------------------
# 3. CALCULO DE RANKING
# -----------------------------------------------------------------------------
def calcular_ranking(datos_t):
    meta = datos_t["meta"]
    stats = {}

    jugadores_unicos = list(dict.fromkeys(datos_t["atletas"]))

    for jug in jugadores_unicos:
        stats[jug] = {
            "nombre": jug,
            "JG": 0,
            "JP": 0,
            "PF": 0,
            "PC": 0,
            "DIF": 0,
            "amonestaciones": datos_t.get("amonestaciones", {}).get(jug, 0),
            "activo": jug not in datos_t.get("retirados", []),
        }

    for r_data in datos_t.get("resultados_rondas", {}).values():
        mesas = r_data.get("mesas", {})
        byes = r_data.get("byes", [])

        for jug_bye in byes:
            if jug_bye in stats:
                stats[jug_bye]["JG"] += 1
                stats[jug_bye]["PF"] += meta
                stats[jug_bye]["PC"] += meta // 2

        for datos_mesa in mesas.values():
            pareja_a = list(dict.fromkeys(datos_mesa.get("pareja_A", [])))
            pareja_b = list(dict.fromkeys(datos_mesa.get("pareja_B", [])))
            pts_a = datos_mesa.get("pts_A", 0)
            pts_b = datos_mesa.get("pts_B", 0)

            if pts_a > pts_b:
                for j in pareja_a:
                    if j in stats:
                        stats[j]["JG"] += 1
                for j in pareja_b:
                    if j in stats:
                        stats[j]["JP"] += 1
            elif pts_b > pts_a:
                for j in pareja_b:
                    if j in stats:
                        stats[j]["JG"] += 1
                for j in pareja_a:
                    if j in stats:
                        stats[j]["JP"] += 1

            for j in pareja_a:
                if j in stats:
                    stats[j]["PF"] += pts_a
                    stats[j]["PC"] += pts_b

            for j in pareja_b:
                if j in stats:
                    stats[j]["PF"] += pts_b
                    stats[j]["PC"] += pts_a

    lista_stats = []
    for jug, d in stats.items():
        penalizacion = d["amonestaciones"]
        if penalizacion > 0:
            d["PF"] = max(0, d["PF"] - penalizacion)
        d["DIF
