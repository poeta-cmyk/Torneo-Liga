import streamlit as st

st.set_page_config(
    page_title="Torneo Liga - Franz Lameda", page_icon="🀁", layout="wide"
)

CLAVE_ACCESO = "POETA1479"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

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
# PUERTA PRINCIPAL
# -----------------------------------------------------------------------------
st.title("Torneo Liga")
st.markdown("*Sistema creado por Franz Lameda*")
st.markdown("### Seleccione una opción")

col1, col2 = st.columns(2)
with col1:
    if st.button("TORNEOS", use_container_width=True):
        st.session_state.vista = "torneos"
        st.rerun()
with col2:
    if st.button("NUEVO TORNEO", type="primary", use_container_width=True):
        st.session_state.vista = "nuevo_torneo"
        st.rerun()
