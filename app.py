import json
import os
import random
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
# 2. MOTOR COMBINATORIO DE BYES Y PAREJAS
# -----------------------------------------------------------------------------
def normalizar_par(j1, j2):
    return tuple(sorted([j1, j2]))


def seleccionar_byes_equitativos(jugadores_ordenados, conteo_byes, cantidad_byes):
    """Elige los jugadores que descansan priorizando menor cantidad de Byes previos."""
    if cantidad_byes <= 0:
        return []
    total = len(jugadores_ordenados)
    candidatos = sorted(
        enumerate(jugadores_ordenados),
        key=lambda item: (conteo_byes.get(item[1], 0), -(total - item[0])),
    )
    return [nombre for _, nombre in candidatos[:cantidad_byes]]


def emparejar_por_ranking(en_juego, usadas):
    """Arma parejas siguiendo el orden del ranking: (0 con 2) y (1 con 3) por bloque de 4."""
    disponibles = list(en_juego)
    parejas = []

    while len(disponibles) >= 4:
        bloque = disponibles[:4]
        disponibles = disponibles[4:]

        candidatos_pares = [
            (bloque[0], bloque[2]),
            (bloque[1], bloque[3]),
            (bloque[0], bloque[1]),
            (bloque[2], bloque[3]),
            (bloque[0], bloque[3]),
            (bloque[1], bloque[2]),
        ]

        usados_en_bloque = set()
        pares_bloque = []
        for a, b in candidatos_pares:
            if a in usados_en_bloque or b in usados_en_bloque:
                continue
            clave = normalizar_par(a, b)
            if clave not in usadas:
                pares_bloque.append([a, b])
                usados.add(clave)
                usados_en_bloque.update([a, b])
            if len(pares_bloque) == 2:
                break

        if len(pares_bloque) < 2:
            pares_bloque = [
                [bloque[0], bloque[2]],
                [bloque[1], bloque[3]],
            ]

        parejas.extend(pares_bloque)

    return parejas


def generar_ronda_completa(activos_ordenados, historial_parejas, conteo_byes):
    """Genera mesas de 4 jugadores según el orden del ranking y lista de Byes."""
    residuo = len(activos_ordenados) % 4
    byes = seleccionar_byes_equitativos(activos_ordenados, conteo_byes, residuo)
    en_juego = [j for j in activos_ordenados if j not in byes]

    usadas = {normalizar_par(p[0], p[1]) for p in historial_parejas if len(p) == 2}
    parejas = emparejar_por_ranking(en_juego, usadas)

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
        d["DIF"] = d["PF"] - d["PC"]
        lista_stats.append(d)

    lista_stats.sort(key=lambda x: (x["JG"], x["DIF"], x["PF"]), reverse=True)
    return lista_stats


# -----------------------------------------------------------------------------
# 4. ESTADO INICIAL DE SESION
# -----------------------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "vista" not in st.session_state:
    st.session_state.vista = "puerta"
if "torneos" not in st.session_state:
    st.session_state.torneos = cargar_estado_general()
if "torneo_actual" not in st.session_state:
    st.session_state.torneo_actual = None
if "modalidad_temp" not in st.session_state:
    st.session_state.modalidad_temp = None
if "torneo_a_eliminar" not in st.session_state:
    st.session_state.torneo_a_eliminar = None


# -----------------------------------------------------------------------------
# 5. PANTALLA DE CLAVE
# -----------------------------------------------------------------------------
if not st.session_state.autenticado:
    st.title("Torneo Liga")
    st.markdown("*Sistema creado por Franz Lameda*")
    st.markdown("### Acceso Autorizado")
    clave = st.text_input("Ingrese la clave de acceso:", type="password")
    if st.button("Iniciar Sesión"):
        if clave == CLAVE_ACCESO:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Clave incorrecta. Intente nuevamente.")
    st.stop()


# -----------------------------------------------------------------------------
# 6. PUERTA PRINCIPAL
# -----------------------------------------------------------------------------
if st.session_state.vista == "puerta":
    st.title("Torneo Liga")
    st.markdown("*Sistema creado por Franz Lameda*")
    st.markdown("### Seleccione una opción")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("TORNEOS", use_container_width=True):
            st.session_state.torneo_a_eliminar = None
            st.session_state.vista = "lista_torneos"
            st.rerun()
    with col2:
        if st.button("NUEVO TORNEO", type="primary", use_container_width=True):
            st.session_state.vista = "elegir_modalidad"
            st.rerun()


# -----------------------------------------------------------------------------
# 7. ELEGIR MODALIDAD
# -----------------------------------------------------------------------------
elif st.session_state.vista == "elegir_modalidad":
    st.title("Nuevo Torneo")
    if st.button("⬅ Volver al Inicio"):
        st.session_state.vista = "puerta"
        st.rerun()

    st.markdown("### Seleccione la modalidad del torneo")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚡ TORNEO RELÁMPAGO", use_container_width=True):
            st.session_state.modalidad_temp = "Relámpago"
            st.session_state.vista = "crear_torneo"
            st.rerun()
    with col2:
        if st.button("🏆 TORNEO DE LIGA", type="primary", use_container_width=True):
            st.session_state.modalidad_temp = "De Liga"
            st.session_state.vista = "crear_torneo"
            st.rerun()


# -----------------------------------------------------------------------------
# 8. CONFIGURAR TORNEO
# -----------------------------------------------------------------------------
elif st.session_state.vista == "crear_torneo":
    mod = st.session_state.modalidad_temp
    st.title(f"Nuevo
