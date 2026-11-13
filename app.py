import streamlit as st

st.set_page_config(
    page_title="Torneo Liga - Franz Lameda", page_icon="🀁", layout="wide"
)

CLAVE_ACCESO = "POETA1479"

# -----------------------------------------------------------------------------
# 1. INICIALIZACION DE MEMORIA
# -----------------------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "vista" not in st.session_state:
    st.session_state.vista = "puerta"
if "torneos" not in st.session_state:
    st.session_state.torneos = {}
if "torneo_actual" not in st.session_state:
    st.session_state.torneo_actual = None
if "modalidad_temp" not in st.session_state:
    st.session_state.modalidad_temp = None
if "torneo_a_eliminar" not in st.session_state:
    st.session_state.torneo_a_eliminar = None

# -----------------------------------------------------------------------------
# 2. PANTALLA DE CLAVE
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
# 3. PUERTA PRINCIPAL (TORNEOS vs NUEVO TORNEO)
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
# 4. ELEGIR MODALIDAD (RELAMPAGO vs DE LIGA)
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
# 5. CONFIGURAR TORNEO (NOMBRE, META Y RONDAS)
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
                }
                st.session_state.torneo_actual = n_t
                st.session_state.vista = "inscribir_atletas"
                st.rerun()

# -----------------------------------------------------------------------------
# 6. AGREGAR ATLETAS AL TORNEO
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
                st.success(f"Atleta '{n_a}' agregado.")
                st.rerun()

    atletas = datos_t["atletas"]
    st.markdown(f"**Atletas Inscritos ({len(atletas)}):**")
    for idx, atleta in enumerate(atletas):
        c1, c2 = st.columns([6, 1])
        c1.write(f"**{idx + 1}.** {atleta}")
        if c2.button("Eliminar", key=f"del_{idx}"):
            atletas.pop(idx)
            st.rerun()

# -----------------------------------------------------------------------------
# 7. LISTA DE TORNEOS GUARDADOS (CON ELIMINACION PROTEGIDA POR CLAVE)
# -----------------------------------------------------------------------------
elif st.session_state.vista == "lista_torneos":
    st.title("Torneos Guardados")
    if st.button("⬅ Volver al Inicio"):
        st.session_state.torneo_a_eliminar = None
        st.session_state.vista = "puerta"
        st.rerun()

    if not st.session_state.torneos:
        st.info("Aún no hay torneos creados.")
    else:
        for nombre, info in list(st.session_state.torneos.items()):
            col_abrir, col_borrar = st.columns([4, 1])
            etiqueta = f"📂 {nombre} ({info['modalidad']} - {info['meta']} pts - {info['rondas']} rondas)"
            with col_abrir:
                if st.button(etiqueta, key=f"abrir_{nombre}", use_container_width=True):
                    st.session_state.torneo_actual = nombre
                    st.session_state.vista = "inscribir_atletas"
                    st.rerun()
            with col_borrar:
                if st.button("🗑️ Eliminar Torneo", key=f"req_del_{nombre}", use_container_width=True):
                    st.session_state.torneo_a_eliminar = nombre
                    st.rerun()

        if st.session_state.torneo_a_eliminar:
            t_del = st.session_state.torneo_a_eliminar
            st.markdown("---")
            st.warning(f"⚠️ **AVISO DE SEGURIDAD:** Está a punto de eliminar permanentemente el torneo **'{t_del}'**. Introduzca su clave para proceder.")
            clave_confirm = st.text_input("Clave de autorización:", type="password", key="clave_borrar_torneo")
            
            c_conf, c_canc = st.columns(2)
            with c_conf:
                if st.button("Confirmar Eliminación", type="primary", use_container_width=True):
                    if clave_confirm == CLAVE_ACCESO:
                        del st.session_state.torneos[t_del]
                        if st.session_state.torneo_actual == t_del:
                            st.session_state.torneo_actual = None
                        st.session_state.torneo_a_eliminar = None
                        st.success(f"Torneo '{t_del}' eliminado correctamente.")
                        st.rerun()
                    else:
                        st.error("Clave incorrecta. No se eliminó el torneo.")
            with c_canc:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.torneo_a_eliminar = None
                    st.rerun()
