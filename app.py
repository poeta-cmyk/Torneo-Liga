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
# 2. PERSISTENCIA DE DATOS
# -----------------------------------------------------------------------------
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
    
    for r_key, contenido in rondas.items():
        mesas = contenido.get("mesas", {})
        for m_key, datos in mesas.items():
            pA = datos.get("pareja_A", [])
            pB = datos.get("pareja_B", [])
            ptsA = datos.get("pts_A", 0)
            ptsB = datos.get("pts_B", 0)
            
            todos = pA + pB
            for j in todos:
                if j not in stats:
                    stats[j] = {"JJ": 0, "JG": 0, "JP": 0, "P+": 0, "P-": 0}
            
            if pA and pB:
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
                        
        # Procesar BYE si existe en la ronda
        bye_list = contenido.get("bye", [])
        for j in bye_list:
            if j not in stats:
                stats[j] = {"JJ": 0, "JG": 0, "JP": 0, "P+": 0, "P-": 0}
            meta = jornada_data.get("meta_puntos", 200)
            pts_fav = meta
            pts_con = meta // 2
            stats[j]["JJ"] += 1
            stats[j]["JG"] += 1
            stats[j]["P+"] += pts_fav
            stats[j]["P-"] += pts_con
                
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
        meta = j_data.get("meta_puntos", 200)
        for r_key, contenido in rondas.items():
            mesas = contenido.get("mesas", {})
            for m_key, datos in mesas.items():
                pA = datos.get("pareja_A", [])
                pB = datos.get("pareja_B", [])
                ptsA = datos.get("pts_A", 0)
                ptsB = datos.get("pts_B", 0)
                
                todos = pA + pB
                for j in todos:
                    if j not in stats:
                        stats[j] = {"JJ": 0, "JG": 0, "JP": 0, "P+": 0, "P-": 0}
                
                if pA and pB:
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
                            
            bye_list = contenido.get("bye", [])
            for j in bye_list:
                if j not in stats:
                    stats[j] = {"JJ": 0, "JG": 0, "JP": 0, "P+": 0, "P-": 0}
                pts_fav = meta
                pts_con = meta // 2
                stats[j]["JJ"] += 1
                stats[j]["JG"] += 1
                stats[j]["P+"] += pts_fav
                stats[j]["P-"] += pts_con
                    
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
                estado["jugadores"].sort(key=lambda x: x.lower())
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
# 5. FASE DE LIGA (SISTEMA SUIZO Y RESTRICCIONES)
# -----------------------------------------------------------------------------
elif estado["fase"] == "liga":
    st.title("Torneo Liga - Desarrollo")
    st.markdown("*Sistema creado por Franz Lameda*")
    
    j_act = estado["jornada_actual"]
    st.subheader(f"Jornada Actual: #{j_act} (Modalidad: 6 Rondas - Sistema Suizo)")
    
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
        estado["jornadas"][j_str] = {"meta_puntos": estado["meta_puntos"], "rondas": {}}
    
    jornada_actual_dict = estado["jornadas"][j_str]
    rondas_dict = jornada_actual_dict["rondas"]
    
    jugs = list(estado["jugadores"])
    
    # Generar las 6 rondas aplicando Sistema Suizo y restricciones de no repetición absoluta
    for r in range(1, 7):
        r_key = f"ronda_{r}"
        if r_key not in rondas_dict:
            mesas_dict = {}
            bye_list = []
            
            if r == 1:
                # Ronda 1: Orden inicial
                lista_activa = list(jugs)
                random.shuffle(lista_activa) # O por orden de lista
                
                # Manejar imparidad en ronda 1 si aplica
                if len(lista_activa) % 4 != 0 and len(lista_activa) >= 4:
                    # Sacar jugadores para BYE si sobra gente que no completa mesa de 4
                    sobrantes = len(lista_activa) % 4
                    for _ in range(sobrantes):
                        bye_list.append(lista_activa.pop())
                
                num_mesas = len(lista_activa) // 4
                for i in range(num_mesas):
                    mesas_dict[f"mesa_{i+1}"] = {
                        "pareja_A": [lista_activa[i*4], lista_activa[i*4+2]],
                        "pareja_B": [lista_activa[i*4+1], lista_activa[i*4+3]],
                        "pts_A": 0,
                        "pts_B": 0
                    }
            else:
                # Rondas 2 a 6: Sistema Suizo basado en ranking parcial de la jornada
                # Recopilar historial previo de esta misma jornada para evitar repeticiones
                historial_parejas = set()
                historial_enfrentamientos = set()
                historial_byes = set()
                
                for prev_r in range(1, r):
                    prev_key = f"ronda_{prev_r}"
                    if prev_key in rondas_dict:
                        for m_d in rondas_dict[prev_key].get("mesas", {}).values():
                            pA = tuple(sorted(m_d.get("pareja_A", [])))
                            pB = tuple(sorted(m_d.get("pareja_B", [])))
                            if len(pA) == 2: historial_parejas.add(pA)
                            if len(pB) == 2: historial_parejas.add(pB)
                            # Registrar enfrentamientos de parejas o jugadores
                            historial_enfrentamientos.add((pA, pB))
                            historial_enfrentamientos.add((pB, pA))
                        for b_j in rondas_dict[prev_key].get("bye", []):
                            historial_byes.add(b_j)
                
                # Obtener ranking parcial de la jornada para ordenar por puntos
                rk_parcial = calcular_ranking_jornada(jornada_actual_dict)
                orden_suizo = [x["nombre"] for x in rk_parcial if x["nombre"] in jugs]
                # Asegurar que entren todos por si acaso
                for j in jugs:
                    if j not in orden_suizo:
                        orden_suizo.append(j)
                
                # Asignar BYE a quien no haya tenido BYE y esté más abajo (o rotando)
                if len(orden_suizo) % 4 != 0:
                    # Buscar candidato que no haya estado en historial_byes
                    candidato_bye = None
                    for j in reversed(orden_suizo):
                        if j not in historial_byes:
                            candidato_bye = j
                            break
                    if not candidato_bye and orden_suizo:
                        candidato_bye = orden_suizo[-1]
                    
                    if candidato_bye:
                        bye_list.append(candidato_bye)
                        orden_suizo.remove(candidato_bye)
                
                # Emparejar mesas de 4 intentando respetar el orden suizo y evitando repetir parejas/rivales
                # Algoritmo heurístico estricto de no repetición
                disponibles = list(orden_suizo)
                num_mesas = len(disponibles) // 4
                mesa_idx = 1
                
                while len(disponibles) >= 4 and mesa_idx <= num_mesas:
                    # Tomar al líder disponible
                    p1 = disponibles.pop(0)
                    # Buscar pareja ideal para p1 que no haya jugado antes con él
                    p2 = None
                    for idx_c, c in enumerate(disponibles):
                        par_candidata = tuple(sorted([p1, c]))
                        if par_candidata not in historial_parejas:
                            p2 = c
                            disponibles.pop(idx_c)
                            break
                    if not p2:
                        p2 = disponibles.pop(0)
                        
                    # Buscar rivales (pareja B) que no hayan jugado contra (p1, p2)
                    p3, p4 = None, None
                    encontrado_rivales = False
                    for i in range(len(disponibles)):
                        for j in range(i + 1, len(disponibles)):
                            cand3 = disponibles[i]
                            cand4 = disponibles[j]
                            par_rival = tuple(sorted([cand3, cand4]))
                            enf1 = (tuple(sorted([p1, p2])), par_rival)
                            if par_rival not in historial_parejas and enf1 not in historial_enfrentamientos:
                                p3 = cand3
                                p4 = cand4
                                encontrado_rivales = True
                                break
                        if encontrado_rivales:
                            break
                            
                    if not p3 or not p4:
                        p3 = disponibles.pop(0)
                        p4 = disponibles.pop(0)
                    else:
                        disponibles.remove(p3)
                        disponibles.remove(p4)
                        
                    mesas_dict[f"mesa_{mesa_idx}"] = {
                        "pareja_A": [p1, p2],
                        "pareja_B": [p3, p4],
                        "pts_A": 0,
                        "pts_B": 0
                    }
                    mesa_idx += 1
            
            rondas_dict[r_key] = {"mesas": mesas_dict, "bye": bye_list}
            guardar_estado(estado)

    if ver_sem:
        st.markdown(f"### Ranking Semanal (Jornada {j_act})")
        rk_sem = calcular_ranking_jornada(jornada_actual_dict)
        st.dataframe(rk_sem, use_container_width=True)
        
    if ver_gen:
        st.markdown("### Ranking General Acumulado")
        rk_gen = calcular_ranking_general(estado)
        st.dataframe(rk_gen, use_container_width=True)

    st.markdown("---")
    st.subheader(f"Carga de Resultados - Jornada {j_act} (Las 6 Rondas - Sistema Suizo)")
    
    meta_actual = jornada_actual_dict.get("meta_puntos", 200)
    
    for r_key, contenido in rondas_dict.items():
        mesas = contenido.get("mesas", {})
        bye_arr = contenido.get("bye", [])
        
        titulo_ronda = f"📌 {r_key.upper().replace('_', ' ')}"
        if bye_arr:
            titulo_ronda += f" | Descansa (BYE): {', '.join(bye_arr)}"
            
        with st.expander(titulo_ronda, expanded=(r_key == "ronda_1")):
            if bye_arr:
                st.info(f"Atletas en BYE automático en esta ronda (Ganan {meta_actual} a {meta_actual//2}): **{', '.join(bye_arr)}**")
                
            for m_key, m_val in mesas.items():
                pA = m_val["pareja_A"]
                pB = m_val["pareja_B"]
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
