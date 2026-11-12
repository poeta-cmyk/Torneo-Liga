import json
import os
import streamlit as st

st.set_page_config(
    page_title="Torneo Liga - Franz Lameda", page_icon="🀁", layout="wide"
)

ARCHIVO_ESTADO = "liga_estado.json"
CLAVE_ACCESO = "POETA1479"

# -----------------------------------------------------------------------------
# 1. AUTENTICACION
# -----------------------------------------------------------------------------
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
# 2. PERSISTENCIA DE DATOS
# -----------------------------------------------------------------------------
def cargar_estado():
    defecto = {
        "fase": "configuracion",
        "meta_puntos": 200,
        "jugadores": [],
        "jornadas": {}, # {"1": {"mesas": {...}, "resultados": {...}}}
        "jornada_actual": 1,
    }
    if os.path.exists(ARCHIVO_ESTADO):
        try:
            with open(ARCHIVO_ESTADO, "r", encoding="utf-8") as f:
                datos = json.load(f)
                for k, v in defecto.items():
                    if k not in datos:
                        datos[k] = v
                return datos
        except Exception:
            return defecto
    return defecto

def guardar_estado(estado):
    with open(ARCHIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=4)

estado = cargar_estado()

with st.sidebar:
    st.title("Opciones")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# -----------------------------------------------------------------------------
# 3. MOTOR DE CALCULO DE RANKING (JJ, JG, JP, Ave, P+, P-, DIF, Puntos)
# -----------------------------------------------------------------------------
def calcular_ranking_jornada(jornada_data):
    stats = {}
    rondas = jornada_data.get("rondas", {})
    
    for r_key, mesas in rondas.items():
        for m_key, datos in mesas.items():
            pA = datos.get("pareja_A", [])
            pB = datos.get("pareja_B", [])
            ptsA = datos.get("pts_A", 0)
            ptsB = datos.get("pts_B", 0)
            
            todos = pA + pB
            for j in todos:
                if j not in stats:
                    stats[j] = {"JJ": 0, "JG": 0, "JP": 0, "P+": 0, "P-": 0}
            
            for j in pA:
                stats[j]["JJ"] += 1
                stats[j]["P+"] += ptsA
                stats[j]["P-"] += ptsB
                if ptsA > ptsB:
                    stats[j]["JG"] += 1
                else:
                    stats[j]["JP"] += 1
                    
            for j in pB:
                stats[j]["JJ"] += 1
                stats[j]["P+"] += ptsB
                stats[j]["P-"] += ptsA
                if ptsB > ptsA:
                    stats[j]["JG"] += 1
                else:
                    stats[j]["JP"] += 1
                
    lista = []
    for j, d in stats.items():
        jj = d["JJ"]
        jg = d["JG"]
        jp = d["JP"]
        pp = d["P+"]
        pc = d["P-"]
        dif = pp - pc
        ave = round(pp / pc, 3) if pc > 0 else float(pp)
        puntos_liga = (jg * 2) - (jp * 1)
        
        lista.append({
            "nombre": j,
            "JJ": jj,
            "JG": jg,
            "JP": jp,
            "Ave": ave,
            "P+": pp,
            "P-": pc,
            "DIF": dif,
            "Puntos": puntos_liga
        })
        
    lista.sort(key=lambda x: (x["Puntos"], x["JG"], x["DIF"], x["P+"]), reverse=True)
    return lista

def calcular_ranking_general(estado):
    stats = {}
    for j_num, j_data in estado.get("jornadas", {}).items():
        rondas = j_data.get("rondas", {})
        for r_key, mesas in rondas.items():
            for m_key, datos in mesas.items():
                pA = datos.get("pareja_A", [])
                pB = datos.get("pareja_B", [])
                ptsA = datos.get("pts_A", 0)
                ptsB = datos.get("pts_B", 0)
                
                todos = pA + pB
                for j in todos:
                    if j not in stats:
                        stats[j] = {"JJ": 0, "JG": 0, "JP": 0, "P+": 0, "P-": 0}
                
                for j in pA:
                    stats[j]["JJ"] += 1
                    stats[j]["P+"] += ptsA
                    stats[j]["P-"] += ptsB
                    if ptsA > ptsB:
                        stats[j]["JG"] += 1
                    else:
                        stats[j]["JP"] += 1
                        
                for j in pB:
                    stats[j]["JJ"] += 1
                    stats[j]["P+"] += ptsB
                    stats[j]["P-"] += ptsA
                    if ptsB > ptsA:
                        stats[j]["JG"] += 1
                    else:
                        stats[j]["JP"] += 1
                    
    lista = []
    for j, d in stats.items():
        jj = d["JJ"]
        jg = d["JG"]
        jp = d["JP"]
        pp = d["P+"]
        pc = d["P-"]
        dif = pp - pc
        ave = round(pp / pc, 3) if pc > 0 else float(pp)
        puntos_liga = (jg * 2) - (jp * 1)
        
        lista.append({
            "nombre": j,
            "JJ": jj,
            "JG": jg,
            "JP": jp,
            "Ave": ave,
            "P+": pp,
            "P-": pc,
            "DIF": dif,
            "Puntos": puntos_liga
        })
        
    lista.sort(key=lambda x: (x["Puntos"], x["JG"], x["DIF"], x["P+"]), reverse=True)
    return lista

# -----------------------------------------------------------------------------
# 4. FASE DE CONFIGURACION E INSCRIPCION
# -----------------------------------------------------------------------------
if estado["fase"] == "configuracion":
    st.title("Torneo Liga - Inscripción de Atletas")
    st.markdown("*Sistema creado por Franz Lameda*")
    
    meta_sel = st.selectbox("Meta de Puntos por Partida:", [100, 200], index=1)
    estado["meta_puntos"] = meta_sel
    
    with st.form("form_atleta", clear_on_submit=True):
        nuevo = st.text_input("Nombre del Atleta:")
        if st.form_submit_button("Inscribir Atleta"):
            n = nuevo.strip()
            if n and n.upper() not in [x.upper() for x in estado["jugadores"]]:
                estado["jugadores"].append(n)
                guardar_estado(estado)
                st.success(f"Atleta {n} inscrito.")
                st.rerun()
                
    st.markdown(f"### Atletas Inscritos ({len(estado['jugadores'])})")
    for idx, jug in enumerate(estado["jugadores"]):
        col1, col2 = st.columns([6, 1])
        col1.write(f"**{idx + 1}.** {jug}")
        if col2.button("Eliminar", key=f"del_{idx}"):
            estado["jugadores"].pop(idx)
            guardar_estado(estado)
            st.rerun()
            
    if st.button("Iniciar Primera Jornada (6 Rondas)", type="primary", use_container_width=True):
        if len(estado["jugadores"]) < 4:
            st.warning("Se requieren al menos 4 atletas.")
        else:
            estado["fase"] = "liga"
            estado["jornada_actual"] = 1
            guardar_estado(estado)
            st.rerun()

# -----------------------------------------------------------------------------
# 5. FASE DE LIGA Y JORNADAS (6 RONDAS)
# -----------------------------------------------------------------------------
elif estado["fase"] == "liga":
    st.title("Torneo Liga - Desarrollo")
    st.markdown("*Sistema creado por Franz Lameda*")
    
    j_act = estado["jornada_actual"]
    st.subheader(f"Jornada Actual: #{j_act} (Modalidad: 6 Rondas)")
    
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        ver_sem = st.button("Ver Ranking Semanal", use_container_width=True)
    with col_v2:
        ver_gen = st.button("Ver Ranking General", use_container_width=True)
    with col_v3:
        nueva_jor = st.button("Avanzar a Siguiente Jornada", use_container_width=True)
        if nueva_jor:
            estado["jornada_actual"] += 1
            guardar_estado(estado)
            st.rerun()
            
    j_str = str(j_act)
    if j_str not in estado["jornadas"]:
        estado["jornadas"][j_str] = {"rondas": {}}
        jugs = list(estado["jugadores"])
        num_mesas = len(jugs) // 4
        
        # Generar estructura para las 6 rondas
        for r in range(1, 7):
            r_key = f"ronda_{r}"
            mesas_dict = {}
            for i in range(num_mesas):
                mesas_dict[f"mesa_{i+1}"] = {
                    "pareja_A": [jugs[i*4], jugs[i*4+2]],
                    "pareja_B": [jugs[i*4+1], jugs[i*4+3]],
                    "pts_A": 0,
                    "pts_B": 0
                }
            estado["jornadas"][j_str]["rondas"][r_key] = mesas_dict
        guardar_estado(estado)

    if ver_sem:
        st.markdown(f"### Ranking Semanal (Jornada {j_act})")
        rk_sem = calcular_ranking_jornada(estado["jornadas"][j_str])
        st.dataframe(rk_sem, use_container_width=True)
        
    if ver_gen:
        st.markdown("### Ranking General Acumulado")
        rk_gen = calcular_ranking_general(estado)
        st.dataframe(rk_gen, use_container_width=True)

    st.markdown("---")
    st.subheader(f"Carga de Resultados - Jornada {j_act} (6 Rondas)")
    
    rondas_dict = estado["jornadas"][j_str]["rondas"]
    ronda_sel = st.selectbox("Seleccione la Ronda a Cargar:", list(rondas_dict.keys()))
    
    if ronda_sel:
        mesas = rondas_dict[ronda_sel]
        for m_key, m_val in mesas.items():
            pA = m_val["pareja_A"]
            pB = m_val["pareja_B"]
            with st.expander(f"[{ronda_sel.upper()}] Mesa {m_key}: ({pA[0]} & {pA[1]}) vs ({pB[0]} & {pB[1]})", expanded=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    pa = st.number_input(f"Puntos Pareja A ({m_key})", 0, estado["meta_puntos"], int(m_val["pts_A"]), key=f"pa_{j_act}_{ronda_sel}_{m_key}")
                with col_b:
                    pb = st.number_input(f"Puntos Pareja B ({m_key})", 0, estado["meta_puntos"], int(m_val["pts_B"]), key=f"pb_{j_act}_{ronda_sel}_{m_key}")
                
                estado["jornadas"][j_str]["rondas"][ronda_sel][m_key]["pts_A"] = pa
                estado["jornadas"][j_str]["rondas"][ronda_sel][m_key]["pts_B"] = pb
                guardar_estado(estado)
