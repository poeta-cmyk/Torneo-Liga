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
# 2. MOTOR DE CALCULO Y RANKING
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

    for r_key, ronda_data in datos_t.get("resultados_rondas", {}).items():
        mesas = ronda_data.get("mesas", {})
        byes = ronda_data.get("byes", [])

        for jug_bye in byes:
            if jug_bye in stats:
                stats[jug_bye]["JG"] += 1
                stats[jug_bye]["PF"] += meta
                stats[jug_bye]["PC"] += meta // 2

        for m_key, datos_mesa in mesas.items():
            pareja_a = list(set(datos_mesa.get("pareja_A", [])))
            pareja_b = list(set(datos_mesa.get("pareja_B", [])))
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

    lista_stats.sort(
        key=lambda x: (x["JG"], x["DIF"], x["PF"]), reverse=True
    )
    return lista_stats


# -----------------------------------------------------------------------------
# 3. PANTALLA DE CLAVE
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
# 4. PUERTA PRINCIPAL
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
# 5. ELEGIR MODALIDAD
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
# 6. CONFIGURAR TORNEO
# -----------------------------------------------------------------------------
elif st.session_state.vista == "crear_torneo":
    mod = st.session_state.modalidad_temp
    st.title(f"Nuevo Torneo ({mod})")
    if st.button("⬅ Cambiar Modalidad"):
        st.session_state.vista = "elegir_modalidad"
        st.rerun()

    with st.form("form_nuevo_torneo"):
        nombre_torneo = st.text_input("Nombre del Torneo:")
        col_m, col_r = st.columns(2)
        with col_m:
            meta_puntos = st.selectbox("Marcador de Meta:", [100, 200], index=1)
        with col_r:
            cant_rondas = st.selectbox("Cantidad de Rondas:", [5, 6, 7, 8, 9], index=1)

        if st.form_submit_button("Crear y Pasar a Inscripción", type="primary"):
            n_t = nombre_torneo.strip()
            if not n_t:
                st.warning("Debe escribir un nombre para el torneo.")
            elif n_t.lower() in [k.lower() for k in st.session_state.torneos.keys()]:
                st.error(f"Ya existe un torneo llamado '{n_t}'.")
            else:
                st.session_state.torneos[n_t] = {
                    "modalidad": mod,
                    "meta": meta_puntos,
                    "rondas": cant_rondas,
                    "atletas": [],
                    "retirados": [],
                    "ronda_actual": 1,
                    "amonestaciones": {},
                    "historial_byes": [],
                    "historial_parejas": [],
                    "resultados_rondas": {},
                    "estado_torneo": "inscribir_atletas",
                }
                guardar_estado_general(st.session_state.torneos)
                st.session_state.torneo_actual = n_t
                st.session_state.vista = "inscribir_atletas"
                st.rerun()

# -----------------------------------------------------------------------------
# 7. AGREGAR ATLETAS
# -----------------------------------------------------------------------------
elif st.session_state.vista == "inscribir_atletas":
    t_actual = st.session_state.torneo_actual
    datos_t = st.session_state.torneos[t_actual]

    st.title(f"{t_actual}")
    st.caption(f"Modalidad: {datos_t['modalidad']} | Meta: {datos_t['meta']} pts | Rondas: {datos_t['rondas']}")

    if st.button("⬅ Volver al Inicio"):
        st.session_state.vista = "puerta"
        st.rerun()

    st.markdown("### Inscripción de Atletas")

    with st.form("form_agregar_atleta", clear_on_submit=True):
        nuevo_atleta = st.text_input("Nombre del Atleta:")
        if st.form_submit_button("Agregar Atleta"):
            n_a = nuevo_atleta.strip()
            lista_actual = datos_t["atletas"]
            if not n_a:
                st.warning("Ingrese un nombre válido.")
            elif n_a.lower() in [x.lower() for x in lista_actual]:
                st.error(f"El atleta '{n_a}' ya está inscrito.")
            else:
                lista_actual.append(n_a)
                lista_actual.sort(key=lambda x: x.lower())
                guardar_estado_general(st.session_state.torneos)
                st.success(f"Atleta '{n_a}' agregado.")
                st.rerun()

    atletas = datos_t["atletas"]
    st.markdown(f"**Atletas Inscritos ({len(atletas)}):**")

    indices_a_eliminar = []
    for idx, atleta in enumerate(atletas):
        c1, c2 = st.columns([6, 1])
        c1.write(f"**{idx + 1}.** {atleta}")
        if c2.button("Eliminar", key=f"del_{idx}"):
            indices_a_eliminar.append(idx)

    if indices_a_eliminar:
        for idx in reversed(indices_a_eliminar):
            atletas.pop(idx)
        guardar_estado_general(st.session_state.torneos)
        st.rerun()

    st.markdown("---")
    if st.button("Comenzar el torneo", type="primary", use_container_width=True):
        if len(atletas) < 4:
            st.warning("Se requieren al menos 4 atletas inscritos para iniciar el torneo.")
        else:
            datos_t["estado_torneo"] = "rondas"
            datos_t["ronda_actual"] = 1
            guardar_estado_general(st.session_state.torneos)
            st.session_state.vista = "rondas"
            st.rerun()

# -----------------------------------------------------------------------------
# 8. RONDAS Y GENERACION CON CONTROL DE PAREJAS Y BYES
# -----------------------------------------------------------------------------
elif st.session_state.vista == "rondas":
    t_actual = st.session_state.torneo_actual
    datos_t = st.session_state.torneos[t_actual]
    
    if "resultados_rondas" not in datos_t:
        datos_t["resultados_rondas"] = {}
    if "historial_byes" not in datos_t:
        datos_t["historial_byes"] = []
    if "historial_parejas" not in datos_t:
        datos_t["historial_parejas"] = []
    if "retirados" not in datos_t:
        datos_t["retirados"] = []
    if "amonestaciones" not in datos_t:
        datos_t["amonestaciones"] = {}
    if "ronda_actual" not in datos_t:
        datos_t["ronda_actual"] = 1

    ronda = datos_t["ronda_actual"]

    st.title(f"{t_actual} ({datos_t['modalidad']})")
    st.subheader(f"Ronda {ronda} de {datos_t['rondas']}")

    col_ini, col_rank, col_ret, col_amon = st.columns([2, 2, 2, 2])

    with col_ini:
        if st.button("⬅ Menú Principal", use_container_width=True):
            st.session_state.vista = "puerta"
            st.rerun()

    with col_rank:
        if st.button("Ver Ranking", use_container_width=True):
            st.session_state.ver_ranking = not st.session_state.get("ver_ranking", False)

    with col_ret:
        if st.button("Retirados", use_container_width=True):
            st.session_state.ver_ret = not st.session_state.get("ver_ret", False)

    with col_amon:
        if st.button("Amonestaciones", use_container_width=True):
            st.session_state.ver_amon = not st.session_state.get("ver_amon", False)

    if st.session_state.get("ver_ranking", False):
        st.markdown("### Tabla de Posiciones Acumulada")
        st.dataframe(calcular_ranking(datos_t), use_container_width=True)

    if st.session_state.get("ver_ret", False):
        st.markdown("### Gestión de Atletas Retirados")
        j_ret_sel = st.selectbox("Seleccione Atleta:", datos_t["atletas"])
        col_ret_norm, col_ret_exp = st.columns(2)

        with col_ret_norm:
            if st.button("Retiro Normal (Fin de Ronda)", use_container_width=True):
                if j_ret_sel not in datos_t["retirados"]:
                    datos_t["retirados"].append(j_ret_sel)
                    guardar_estado_general(st.session_state.torneos)
                    st.success(f"{j_ret_sel} retirado respetando su puntaje.")
                    st.rerun()

        with col_ret_exp:
            if st.button("Expulsión (Forfeit 0-Meta)", use_container_width=True):
                if j_ret_sel not in datos_t["retirados"]:
                    datos_t["retirados"].append(j_ret_sel)
                    meta = datos_t["meta"]
                    r_str = str(ronda)
                    if r_str in datos_t["resultados_rondas"] and "mesas" in datos_t["resultados_rondas"][r_str]:
                        for m_key, d_m in datos_t["resultados_rondas"][r_str]["mesas"].items():
                            if j_ret_sel in d_m["pareja_A"]:
                                d_m["pts_A"] = 0
                                d_m["pts_B"] = meta
                            elif j_ret_sel in d_m["pareja_B"]:
                                d_m["pts_A"] = meta
                                d_m["pts_B"] = 0
                    guardar_estado_general(st.session_state.torneos)
                    st.error(f"{j_ret_sel} expulsado con marcador 0-{meta}.")
                    st.rerun()

    if st.session_state.get("ver_amon", False):
        st.markdown("### Registro de Amonestaciones")
        col_j_amon, col_pts_amon = st.columns(2)
        with col_j_amon:
            j_sel = st.selectbox("Seleccione Atleta:", datos_t["atletas"], key="sel_amon")
        with col_pts_amon:
            pts_penal = st.number_input("Puntos de Penalización:", min_value=0, value=0, step=10)

        if st.button("Aplicar Penalización", use_container_width=True):
            datos_t["amonestaciones"][j_sel] = pts_penal
            guardar_estado_general(st.session_state.torneos)
            st.success(f"Penalización de {j_sel} establecida en {pts_penal} puntos.")
            st.rerun()

    st.markdown("---")

    r_str = str(ronda)
    if r_str not in datos_t["resultados_rondas"]:
        datos_t["resultados_rondas"][r_str] = {}

    if "mesas" not in datos_t["resultados_rondas"][r_str]:
        ranking_actual = calcular_ranking(datos_t)
        activos = [d["nombre"] for d in ranking_actual if d["activo"]]

        # Selección estricta de Bye (evitando repetir si hay suficientes jugadores)
        jugadores_bye = []
        residuo = len(activos) % 4
        if residuo != 0:
            # Buscar primero candidatos que no hayan tenido bye
            candidatos_disponibles = [j for j in reversed(activos) if j not in datos_t["historial_byes"]]
            if len(candidatos_disponibles) < residuo:
                # Si se agotaron, reiniciar historial parcial de byes para permitir rotación equitativa
                datos_t["historial_byes"] = []
                candidatos_disponibles = list(reversed(activos))

            for candid in candidatos_disponibles:
                if len(jugadores_bye) < residuo:
                    jugadores_bye.append(candid)

            for jb in jugadores_bye:
                activos.remove(jb)
                if jb not in datos_t["historial_byes"]:
                    datos_t["historial_byes"].append(jb)

        num_mesas = len(activos) // 4
        mesas_generadas = {}

        # Algoritmo de formación de mesas con evitación de parejas repetidas
        parejas_historicas = set(tuple(sorted(p)) for p in datos_t["historial_parejas"])
