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
# 1. BASE DE DATOS PERSISTENTE
# -----------------------------------------------------------------------------
def cargar_base_torneos():
    if os.path.exists(ARCHIVO_ESTADO):
        try:
            with open(ARCHIVO_ESTADO, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def guardar_base_torneos(torneos):
    with open(ARCHIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(torneos, f, ensure_ascii=False, indent=4)


# -----------------------------------------------------------------------------
# 2. GENERACION DE PRIMERA RONDA (AL AZAR)
# -----------------------------------------------------------------------------
def crear_primera_ronda_azar(atletas):
    mezclados = list(atletas)
    random.shuffle(mezclados)

    residuo = len(mezclados) % 4
    byes = mezclados[:residuo] if residuo > 0 else []
    en_juego = mezclados[residuo:]

    mesas = {}
    num_mesas = len(en_juego) // 4
    for m_idx in range(num_mesas):
        base = 4 * m_idx
        mesas[f"mesa_{m_idx + 1}"] = {
            "pareja_A": [en_juego[base], en_juego[base + 2]],
            "pareja_B": [en_juego[base + 1], en_juego[base + 3]],
            "pts_A": 0,
            "pts_B": 0,
        }

    return mesas, byes


# -----------------------------------------------------------------------------
# 3. ESTADO DE SESION
# -----------------------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "vista" not in st.session_state:
    st.session_state.vista = "puerta"
if "torneos" not in st.session_state:
    st.session_state.torneos = cargar_base_torneos()
if "torneo_actual" not in st.session_state:
    st.session_state.torneo_actual = None
if "torneo_a_eliminar" not in st.session_state:
    st.session_state.torneo_a_eliminar = None


# -----------------------------------------------------------------------------
# 4. ACCESO POR CLAVE
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
# 5. MENU PRINCIPAL
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
            st.session_state.vista = "nuevo_torneo"
            st.rerun()


# -----------------------------------------------------------------------------
# 6. CREAR NUEVO TORNEO
# -----------------------------------------------------------------------------
elif st.session_state.vista == "nuevo_torneo":
    st.title("Nuevo Torneo")
    if st.button("⬅ Volver al Inicio"):
        st.session_state.vista = "puerta"
        st.rerun()

    with st.form("form_nuevo_torneo"):
        nombre_torneo = st.text_input("Nombre del Torneo:")
        col_m, col_r = st.columns(2)
        with col_m:
            meta_puntos = st.selectbox("Marcador de Meta:", [100, 200], index=1)
        with col_r:
            cant_rondas = st.selectbox("Cantidad de Rondas:", [6, 7, 8, 9], index=1)

        if st.form_submit_button("INICIAR TORNEO", type="primary"):
            n_t = nombre_torneo.strip()
            if not n_t:
                st.warning("Debe escribir un nombre para el torneo.")
            elif n_t.lower() in [k.lower() for k in st.session_state.torneos.keys()]:
                st.error(f"Ya existe un torneo llamado '{n_t}'.")
            else:
                st.session_state.torneos[n_t] = {
                    "nombre": n_t,
                    "meta": meta_puntos,
                    "rondas": cant_rondas,
                    "atletas": [],
                    "ronda_actual": 1,
                    "resultados_rondas": {},
                }
                guardar_base_torneos(st.session_state.torneos)
                st.session_state.torneo_actual = n_t
                st.session_state.vista = "inscribir_atletas"
                st.rerun()


# -----------------------------------------------------------------------------
# 7. INSCRIPCION DE ATLETAS (ORDEN ALFABETICO)
# -----------------------------------------------------------------------------
elif st.session_state.vista == "inscribir_atletas":
    t_actual = st.session_state.torneo_actual
    datos_t = st.session_state.torneos[t_actual]

    st.title(f"{t_actual}")
    st.caption(f"Meta: {datos_t['meta']} pts | Rondas: {datos_t['rondas']}")

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
                guardar_base_torneos(st.session_state.torneos)
                st.success(f"Atleta '{n_a}' agregado.")
                st.rerun()

    atletas = datos_t["atletas"]
    st.markdown(f"**Atletas Inscritos ({len(atletas)}):**")
    for idx, atleta in enumerate(atletas):
        st.write(f"**{idx + 1}.** {atleta}")

    if len(atletas) >= 4:
        st.markdown("---")
        if st.button("GENERAR PRIMERA RONDA", type="primary", use_container_width=True):
            mesas, byes = crear_primera_ronda_azar(atletas)
            datos_t["ronda_actual"] = 1
            datos_t["resultados_rondas"]["1"] = {
                "mesas": mesas,
                "byes": byes,
            }
            guardar_base_torneos(st.session_state.torneos)
            st.session_state.vista = "ronda_1"
            st.rerun()


# -----------------------------------------------------------------------------
# 8. PRIMERA RONDA CON ANOTADORES
# -----------------------------------------------------------------------------
elif st.session_state.vista == "ronda_1":
    t_actual = st.session_state.torneo_actual
    datos_t = st.session_state.torneos[t_actual]
    meta = datos_t["meta"]
    ronda_1 = datos_t.get("resultados_rondas", {}).get("1", {})
    mesas = ronda_1.get("mesas", {})
    byes = ronda_1.get("byes", [])

    st.title(f"{t_actual} — Ronda 1")
    st.caption(f"Meta: {meta} pts | Rondas: {datos_t['rondas']}")

    if st.button("⬅ Volver al Inicio"):
        st.session_state.vista = "puerta"
        st.rerun()

    st.markdown("### Mesas de Juego - Ronda 1")
    for m_key, m_data in mesas.items():
        num_mesa = m_key.split("_")[1]
        p_a = m_data["pareja_A"]
        p_b = m_data["pareja_B"]

        with st.container(border=True):
            st.markdown(
                f"**Mesa {num_mesa}:** {p_a[0]} y {p_a[1]}  vs  {p_b[0]} y {p_b[1]}"
            )
            col_a, col_b = st.columns(2)
            with col_a:
                pts_a = st.number_input(
                    f"Puntos Pareja A (Mesa {num_mesa})",
                    min_value=0,
                    max_value=meta,
                    value=int(m_data.get("pts_A", 0)),
                    key=f"r1_pts_A_{t_actual}_{m_key}",
                )
            with col_b:
                pts_b = st.number_input(
                    f"Puntos Pareja B (Mesa {num_mesa})",
                    min_value=0,
                    max_value=meta,
                    value=int(m_data.get("pts_B", 0)),
                    key=f"r1_pts_B_{t_actual}_{m_key}",
                )

            if m_data.get("pts_A") != pts_a or m_data.get("pts_B") != pts_b:
                m_data["pts_A"] = pts_a
                m_data["pts_B"] = pts_b
                guardar_base_torneos(st.session_state.torneos)

    if byes:
        st.markdown("### Descansos (Bye)")
        for jb in byes:
            st.info(f"Jugador libre (Bye): {jb}")


# -----------------------------------------------------------------------------
# 9. BASE DE DATOS DE TORNEOS GUARDADOS
# -----------------------------------------------------------------------------
elif st.session_state.vista == "lista_torneos":
    st.title("Torneos Guardados")
    if st.button("⬅ Volver al Inicio"):
        st.session_state.torneo_a_eliminar = None
        st.session_state.vista = "puerta"
        st.rerun()

    if not st.session_state.torneos:
        st.info("Aún no hay torneos registrados en la base de datos.")
    else:
        for nombre, info in list(st.session_state.torneos.items()):
            col_abrir, col_borrar = st.columns([4, 1])
            etiqueta = (
                f"📂 {nombre} — Meta: {info['meta']} pts | Rondas: {info['rondas']} | "
                f"Atletas: {len(info.get('atletas', []))}"
            )
            with col_abrir:
                if st.button(etiqueta, key=f"abrir_{nombre}", use_container_width=True):
                    st.session_state.torneo_actual = nombre
                    if "1" in info.get("resultados_rondas", {}):
                        st.session_state.vista = "ronda_1"
                    else:
                        st.session_state.vista = "inscribir_atletas"
                    st.rerun()
            with col_borrar:
                if st.button(
                    "🗑️ Eliminar",
                    key=f"req_del_{nombre}",
                    use_container_width=True,
                ):
                    st.session_state.torneo_a_eliminar = nombre
                    st.rerun()

        if st.session_state.torneo_a_eliminar:
            t_del = st.session_state.torneo_a_eliminar
            st.markdown("---")
            st.warning(
                f"Está a punto de eliminar permanentemente el torneo **'{t_del}'**."
            )
            clave_confirm = st.text_input(
                "Clave de autorización:", type="password", key="clave_borrar_torneo"
            )
            c_conf, c_canc = st.columns(2)
            with c_conf:
                if st.button(
                    "Confirmar Eliminación",
                    type="primary",
                    use_container_width=True,
                ):
                    if clave_confirm == CLAVE_ACCESO:
                        del st.session_state.torneos[t_del]
                        guardar_base_torneos(st.session_state.torneos)
                        if st.session_state.torneo_actual == t_del:
                            st.session_state.torneo_actual = None
                        st.session_state.torneo_a_eliminar = None
                        st.success(f"Torneo '{t_del}' eliminado.")
                        st.rerun()
                    else:
                        st.error("Clave incorrecta.")
            with c_canc:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.torneo_a_eliminar = None
                    st.rerun()
