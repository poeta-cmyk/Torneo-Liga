import json
import os
import random
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
# 2. PERSISTENCIA Y REINICIO FORZADO DESDE CERO
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("Opciones")
    if st.button("🔄 Borrar Todo y Reiniciar", type="primary"):
        if os.path.exists(ARCHIVO_ESTADO):
            os.remove(ARCHIVO_ESTADO)
        st.session_state.clear()
        st.rerun()
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

def cargar_estado():
    defecto = {
        "fase": "configuracion",
        "meta_puntos": 200,
        "jugadores": [],
        "jornadas": {},
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

# -----------------------------------------------------------------------------
# 3. MOTOR DE CALCULO
# -----------------------------------------------------------------------------
def calcular_ranking_jornada(jornada_data):
    stats = {}
    rondas = jornada_data.get("rondas", {})
    meta = jornada_data.get("meta_puntos", 200)
    
    for r_key, contenido in rondas.items():
        for m_key, datos in contenido.get("mesas", {}).items():
            pA, pB = datos.get("pareja_A", []), datos.get("pareja_B", [])
            ptsA, ptsB = datos.get("pts_A", 0), datos.get("pts_B", 0)
            for j in pA + pB:
                if j not in stats: stats[j] = {"JJ": 0, "JG": 0, "JP": 0, "P+": 0, "P-": 0}
            if pA and pB:
                for j in pA:
                    stats[j]["JJ"] += 1; stats[j]["P+"] += ptsA; stats[j]["P-"] += ptsB
                    if ptsA > ptsB: stats[j]["JG"] += 1
                    else: stats[j]["JP"] += 1
                for j in pB:
                    stats[j]["JJ"] += 1; stats[j]["P+"] += ptsB; stats[j]["P-"] += ptsA
                    if ptsB > ptsA: stats[j]["JG"] += 1
                    else: stats[j]["JP"] += 1
                        
        for j in contenido.get("bye", []):
            if j not in stats: stats[j] = {"JJ": 0, "JG": 0, "JP": 0, "P+": 0, "P-": 0}
            stats[j]["JJ"] += 1; stats[j]["JG"] += 1; stats[j]["P+"] += meta; stats[j]["P-"] += meta // 2
                
    lista = []
    for j, d in stats.items():
        pp, pc = d["P+"], d["P-"]
        dif = pp - pc
        ave = round(pp / pc, 3) if pc > 0 else float(pp)
        puntos_liga = (d["JG"] * 2) - (d["JP"] * 1)
        lista.append({"nombre": j, "JJ": d["JJ"], "JG": d["JG"], "JP": d["JP"], "Ave": ave, "P+": pp, "P-": pc, "DIF": dif, "Puntos": puntos_liga})
        
    lista.sort(key=lambda x: (x["Puntos"], x["JG"], x["DIF"], x["P+"]), reverse=True)
    return lista

def calcular_ranking_general(estado):
    stats = {}
    for j_num, j_data in estado.get("jornadas", {}).items():
        meta = j_data.get("meta_puntos", 200)
        for r_key, contenido in j_data.get("rondas", {}).items():
            for m_key, datos in contenido.get("mesas", {}).items():
                pA, pB = datos.get("pareja_A", []), datos.get("pareja_B", [])
                ptsA, ptsB = datos.get("pts_A", 0), datos.get("pts_B", 0)
                for j in pA + pB:
                    if j not in stats: stats[j] = {"JJ": 0, "JG": 0, "JP": 0, "P+": 0, "P-": 0}
                if pA and pB:
                    for j in pA:
                        stats[j]["JJ"] += 1; stats[j]["P+"] += ptsA; stats[j]["P-"] += ptsB
                        if ptsA > ptsB: stats[j]["JG"] += 1
                        else: stats[j]["JP"] += 1
                    for j in pB:
                        stats[j]["JJ"] += 1; stats[j]["P+"] += ptsB; stats[j]["P-"] += ptsA
                        if ptsB > ptsA: stats[j]["JG"] += 1
                        else: stats[j]["JP"] += 1
            for j in contenido.get("bye", []):
                if j not in stats: stats[j] = {"JJ": 0, "JG": 0, "JP": 0, "P+": 0, "P-": 0}
                stats[j]["JJ"] += 1; stats[j]["JG"] += 1; stats[j]["P+"] += meta; stats[j]["P-"] += meta // 2
                
    lista = []
    for j, d in stats.items():
        pp, pc = d["P+"], d["P-"]
        dif = pp - pc
        ave = round(pp / pc, 3) if pc > 0 else float(pp)
        puntos_liga = (d["JG"] * 2) - (d["JP"] * 1)
        lista.append({"nombre": j, "JJ": d["JJ"], "JG": d["JG"], "JP": d["JP"], "Ave": ave, "P+": pp, "P-": pc, "DIF": dif, "Puntos": puntos_liga})
        
    lista.sort(key=lambda x: (x["Puntos"], x["JG"], x["DIF"], x["P+"]), reverse=True)
    return lista

# -----------------------------------------------------------------------------
# 4. CONFIGURACION E INSCRIPCION ALFABETICA Y SIN DUPLICADOS
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
            if n:
                if n.lower() in [x.lower() for x in estado["jugadores"]]:
                    st.error(f"El atleta '{n}' ya está inscrito.")
                else:
                    estado["jugadores"].append(n)
                    estado["jugadores"].sort(key=lambda x: x.lower())
                    guardar_estado(estado)
                    st.success(f"Atleta {n} inscrito.")
                    st.rerun()
            else:
                st.warning("Ingrese un nombre válido.")
                
    st.markdown(f"### Atletas Inscritos ({len(estado['jugadores'])})")
    for idx, jug in enumerate(estado["jugadores"]):
        col1, col2 = st.columns([6, 1])
        col1.write(f"**{idx + 1}.** {jug}")
        if col2.button("Eliminar", key=f"del_{idx}"):
            estado["jugadores"].pop(idx)
            guardar_estado(estado)
            st.rerun()
            
    if st.button("Iniciar Primera Jornada", type="primary", use_container_width=True):
        if len(estado["jugadores"]) < 4:
            st.warning("Se requieren al menos 4 atletas.")
        else:
            estado["fase"] = "liga"
            estado["jornada_actual"] = 1
            guardar_estado(estado)
            st.rerun()

# -----------------------------------------------------------------------------
# 5. DESARROLLO DE LIGA (6 RONDAS AL AZAR POR JORNADA)
# -----------------------------------------------------------------------------
elif estado["fase"] == "liga":
    st.title("Torneo Liga - Desarrollo")
    st.markdown("*Sistema creado por Franz Lameda*")
    
    j_act = estado["jornada_actual"]
    st.subheader(f"Jornada Actual: #{j_act}")
    
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        ver_sem = st.button("Ver Ranking Semanal", use_container_width=True)
    with col_v2:
        ver_gen = st.button("Ver Ranking General", use_container_width=True)
    with col_v3:
        if st.button("Avanzar a Siguiente Jornada", use_container_width=True):
            estado["jornada_actual"] += 1
            guardar_estado(estado)
            st.rerun()
            
    j_str = str(j_act)
    if j_str not in estado["jornadas"]:
        estado["jornadas"][j_str] = {"meta_puntos": estado["meta_puntos"], "rondas": {}}
        jugs = list(estado["jugadores"])
        
        for r in range(1, 7):
            r_key = f"ronda_{r}"
            lista_azar = list(jugs)
            random.shuffle(lista_azar)
            bye_list = []
            
            if len(lista_azar) % 4 != 0 and len(lista_azar) >= 4:
                sobrantes = len(lista_azar) % 4
                for _ in range(sobrantes):
                    bye_list.append(lista_azar.pop())
            
            mesas_dict = {}
            num_mesas = len(lista_azar) // 4
            for i in range(num_mesas):
                mesas_dict[f"mesa_{i+1}"] = {
                    "pareja_A": [lista_azar[i*4], lista_azar[i*4+2]],
                    "pareja_B": [lista_azar[i*4+1], lista_azar[i*4+3]],
                    "pts_A": 0,
                    "pts_B": 0
                }
            estado["jornadas"][j_str]["rondas"][r_key] = {"mesas": mesas_dict, "bye": bye_list}
        guardar_estado(estado)

    jornada_actual_dict = estado["jornadas"][j_str]

    if ver_sem:
        st.markdown(f"### Ranking Semanal (Jornada {j_act})")
        st.dataframe(calcular_ranking_jornada(jornada_actual_dict), use_container_width=True)
        
    if ver_gen:
        st.markdown("### Ranking General Acumulado")
        st.dataframe(calcular_ranking_general(estado), use_container_width=True)

    st.markdown("---")
    st.subheader(f"Carga de Resultados - Jornada {j_act} (6 Rondas)")
    meta_actual = jornada_actual_dict.get("meta_puntos", 200)
    
    for r_key, contenido in jornada_actual_dict["rondas"].items():
        mesas = contenido.get("mesas", {})
        bye_arr = contenido.get("bye", [])
        
        titulo = f"📌 {r_key.upper().replace('_', ' ')}"
        if bye_arr: titulo += f" | Descansa (BYE): {', '.join(bye_arr)}"
        
        with st.expander(titulo, expanded=(r_key == "ronda_1")):
            if bye_arr:
                st.info(f"Atletas en BYE (Ganan {meta_actual} a {meta_actual//2}): **{', '.join(bye_arr)}**")
                
            for m_key, m_val in mesas.items():
                pA, pB = m_val["pareja_A"], m_val["pareja_B"]
                col_m, col_a, col_b = st.columns([2, 1, 1])
                with col_m:
                    st.markdown(f"**Mesa {m_key.split('_')[1]}**<br>({pA[0]} & {pA[1]}) vs ({pB[0]} & {pB[1]})", unsafe_allow_html=True)
                with col_a:
                    pa = st.number_input(f"Pts A ({r_key}_{m_key})", 0, meta_actual, int(m_val["pts_A"]), key=f"pa_{j_act}_{r_key}_{m_key}")
                with col_b:
                    pb = st.number_input(f"Pts B ({r_key}_{m_key})", 0, meta_actual, int(m_val["pts_B"]), key=f"pb_{j_act}_{r_key}_{m_key}")
                
                estado["jornadas"][j_str]["rondas"][r_key]["mesas"][m_key]["pts_A"] = pa
                estado["jornadas"][j_str]["rondas"][r_key]["mesas"][m_key]["pts_B"] = pb
                guardar_estado(estado)
