import streamlit as st
from datetime import date
from snowflake.snowpark.functions import col

# Estilos visuales
st.markdown("""
    <style>
        .titulo {
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 20px;
        }
        .subtitulo {
            font-size: 20px;
            color: #34495e;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .stButton button {
            background-color: #2980b9;
            color: white;
            font-weight: bold;
        }
        .stButton button:hover {
            background-color: #1f5f8b;
        }
    </style>
""", unsafe_allow_html=True)

cnx = st.connection('snowflake')
session = cnx.session()

# Funciones auxiliares
def get_opciones(tabla, columna):
    df = session.table(tabla).select(columna).to_pandas()
    opciones = df[columna].dropna().unique().tolist()
    return ["-- Selecciona una opción --"] + sorted(opciones)

def obtener_pais_cve(nombre_pais):
    df_pais = session.table("ID_PAISES").filter(f"PAIS_NOMBRE = '{nombre_pais}'").select("PAIS_CVE").to_pandas()
    if not df_pais.empty:
        return df_pais["PAIS_CVE"].iloc[0][1:]
    return None

def obtener_estado_cve(nombre_estado):
    df_estado = session.table("ID_ESTADOS").filter(f"ESTADO_NOMBRE = '{nombre_estado}'").select("ESTADO_CVE").to_pandas()
    return df_estado["ESTADO_CVE"].iloc[0] if not df_estado.empty else None

def get_paises_con_agencias():
    agencias = session.table("ID_AGENCIAS").select(col("PAIS_COD")).distinct()
    paises = session.table("ID_PAISES").select(col("PAIS_CVE"), col("PAIS_NOMBRE"))
    paises_validos = paises.join(agencias, paises["PAIS_CVE"] == agencias["PAIS_COD"]).select("PAIS_NOMBRE")
    df_paises = paises_validos.to_pandas()
    opciones = df_paises["PAIS_NOMBRE"].dropna().unique().tolist()
    return ["-- Selecciona una opción --"] + sorted(opciones)

def get_estados_con_agencias(pais_cve):
    agencias = session.table("ID_AGENCIAS").select("ESTADO_CVE").distinct()
    estados = session.table("ID_ESTADOS").filter(col("PAIS_CVE") == pais_cve).select("ESTADO_CVE", "ESTADO_NOMBRE")
    estados_validos = estados.join(agencias, estados["ESTADO_CVE"] == agencias["ESTADO_CVE"]).select("ESTADO_NOMBRE")
    df_estados = estados_validos.to_pandas()
    opciones = df_estados["ESTADO_NOMBRE"].dropna().unique().tolist()
    return ["Sin Estado Disponible"] if not opciones else ["-- Selecciona una opción --"] + sorted(opciones)

def get_ciudades_con_agencias(estado_cve):
    agencias = session.table("ID_AGENCIAS").filter(col("ESTADO_CVE") == estado_cve).select("CIUDAD_NOMBRE").distinct()
    df_ciudades = agencias.to_pandas()
    opciones = df_ciudades["CIUDAD_NOMBRE"].dropna().unique().tolist()
    return ["Sin Ciudad de Agencia"] if not opciones else ["-- Selecciona una opción --"] + sorted(opciones)

def get_agencias_por_ciudad(estado_cve, ciudad_nombre):
    df_agencias = session.table("ID_AGENCIAS") \
        .filter(f"ESTADO_CVE = '{estado_cve}' AND CIUDAD_NOMBRE = '{ciudad_nombre}'") \
        .select("AGENCIA_NOMBRE").to_pandas()
    agencias = df_agencias["AGENCIA_NOMBRE"].dropna().unique().tolist()
    return ["Sin Agencia Disponible"] if not agencias else ["-- Selecciona una opción --"] + sorted(agencias)

# Opciones fijas
paises = get_paises_con_agencias()
canales = get_opciones("ID_CANALES", "CANAL_NOMBRE")
paquetes = get_opciones("ID_PAQUETE", "PAQUETE_NOMBRE")
tipos_habitacion = get_opciones("ID_HABITACION", "TIPO_HABITACION_NOMBRE")

# Interfaz principal
st.markdown('<div class="titulo">Sistema de Reservaciones</div>', unsafe_allow_html=True)
name_on_order = st.text_input("👤 Ingresa tu nombre para comenzar", key="nombre_usuario")

if name_on_order:
    st.markdown(f"**¡Gracias, {name_on_order}! Completa tu reservación:**")
    st.divider()

    st.markdown('<div class="subtitulo">📍 Ubicación</div>', unsafe_allow_html=True)
    nombre_pais = st.selectbox("Selecciona el país", paises)
    nombre_estado = "-- Selecciona una opción --"
    ciudad_agencia = "-- Selecciona una opción --"
    agencia_nombre = "-- Selecciona una opción --"
    estado_cve = None
    pais_cve = None
    ciudades, agencias = [], []

    if nombre_pais != "-- Selecciona una opción --":
        pais_cve = obtener_pais_cve(nombre_pais)
        estados = get_estados_con_agencias(pais_cve)
        nombre_estado = st.selectbox("Selecciona el estado", estados)
        estados_disponibles = estados != ["Sin Estado Disponible"]

        if nombre_estado == "Sin Estado Disponible":
            ciudad_agencia = st.selectbox("Selecciona ciudad de agencia", ["Sin Ciudad de Agencia"])
            agencia_nombre = st.selectbox("Selecciona la agencia", ["Sin Agencia Disponible"])
        elif nombre_estado != "-- Selecciona una opción --":
            estado_cve = obtener_estado_cve(nombre_estado)
            ciudades = get_ciudades_con_agencias(estado_cve)
            ciudad_agencia = st.selectbox("Selecciona ciudad de agencia", ciudades)

            if ciudad_agencia not in ["-- Selecciona una opción --", "Sin Ciudad de Agencia"]:
                agencias = get_agencias_por_ciudad(estado_cve, ciudad_agencia)
                agencia_nombre = st.selectbox("Selecciona la agencia", agencias)
            else:
                agencia_nombre = st.selectbox("Selecciona la agencia", ["Sin Agencia Disponible"])
    else:
        st.info("Selecciona un país para comenzar.")

    st.divider()
    st.markdown('<div class="subtitulo">🛏️ Habitación</div>', unsafe_allow_html=True)
    nombre_canal = st.selectbox("Selecciona el canal de venta", canales)
    nombre_paquete = st.selectbox("Selecciona el paquete", paquetes)
    tipo_habitacion = st.selectbox("Selecciona el tipo de habitación", tipos_habitacion)

    st.markdown('<div class="subtitulo">👨‍👩‍👧 Historial</div>', unsafe_allow_html=True)
    respuesta_antecedente = st.radio("¿Has hecho una reservación antes?", options=["-- Selecciona una opción --", "Sí", "No"])

    hist_menores = hist_adultos = hist_total_habitaciones = "-- Selecciona una opción --"
    opciones_menores = ["-- Selecciona una opción --"] + [str(i) for i in range(0, 11)]
    opciones_adultos = ["-- Selecciona una opción --"] + [str(i) for i in range(0, 11)]
    opciones_habitaciones = ["-- Selecciona una opción --"] + [str(i) for i in range(1, 7)]

    if respuesta_antecedente in ["Sí", "No"]:
        menores_sel = st.selectbox("Menores en la habitación", opciones_menores)
        adultos_sel = st.selectbox("Adultos en la habitación", opciones_adultos)
        habitaciones_sel = st.selectbox("Número de habitaciones", opciones_habitaciones)
        hist_menores = f"{menores_sel}-0" if respuesta_antecedente == "Sí" else f"0-{menores_sel}"
        hist_adultos = f"{adultos_sel}-0" if respuesta_antecedente == "Sí" else f"0-{adultos_sel}"
        hist_total_habitaciones = f"{habitaciones_sel}-0" if respuesta_antecedente == "Sí" else f"0-{habitaciones_sel}"

    st.divider()
    st.markdown('<div class="subtitulo">📅 Fechas</div>', unsafe_allow_html=True)
    date_range = st.date_input("Selecciona el rango de fechas", value=(date.today(), date.today()), min_value=date.today())

    errores = {}
    if st.button("✅ Confirmar reserva"):
        if nombre_pais == "-- Selecciona una opción --":
            errores["pais"] = "Selecciona un país válido."
        if estados_disponibles and nombre_estado in ["-- Selecciona una opción --", "Sin Estado Disponible"]:
            errores["estado"] = "Selecciona un estado válido."
        if ciudad_agencia in ["-- Selecciona una opción --"] or (ciudad_agencia == "Sin Ciudad de Agencia" and "Sin Ciudad de Agencia" not in ciudades):
            errores["ciudad"] = "Selecciona una ciudad válida."
        if agencia_nombre in ["-- Selecciona una opción --"] or (agencia_nombre == "Sin Agencia Disponible" and "Sin Agencia Disponible" not in agencias):
            errores["agencia"] = "Selecciona una agencia válida."
        if nombre_canal == "-- Selecciona una opción --":
            errores["canal"] = "Selecciona un canal de venta."
        if nombre_paquete == "-- Selecciona una opción --":
            errores["paquete"] = "Selecciona un paquete."
        if tipo_habitacion == "-- Selecciona una opción --":
            errores["habitacion"] = "Selecciona un tipo de habitación."
        if respuesta_antecedente == "-- Selecciona una opción --":
            errores["reservacion"] = "Selecciona si has hecho reservaciones antes."
        if menores_sel == "-- Selecciona una opción --":
            errores["menores"] = "Selecciona número de menores."
        if habitaciones_sel == "-- Selecciona una opción --":
            errores["habitaciones"] = "Selecciona número de habitaciones."
        if not isinstance(date_range, tuple) or len(date_range) != 2 or date_range[1] <= date_range[0]:
            errores["fechas"] = "Selecciona un rango de fechas válido."

        if errores:
            for mensaje in errores.values():
                st.warning("⚠️ " + mensaje)
        else:
            fecha_ingreso, fecha_salida = date_range
            numero_dias = (fecha_salida - fecha_ingreso).days + 1
            numero_noches = numero_dias - 1
            fecha_reservacion = date.today()

            insert_stmt = f"""
                INSERT INTO ALMACENAMIENTO_DE_RESERVAS 
                (nombre_pais, nombre_estado, ciudad_agencia, nombre_agencia, nombre_on_order,
                 fecha_ingreso, fecha_salida, numero_noches, numero_dias, fecha_reservacion,
                 nombre_canal, nombre_paquete, nombre_tipo_habitacion, hist_menores, hist_adultos, hist_total_habitaciones)
                VALUES 
                ('{nombre_pais}', '{nombre_estado}', '{ciudad_agencia}', '{agencia_nombre}', '{name_on_order}',
                 '{fecha_ingreso}', '{fecha_salida}', {numero_noches}, {numero_dias}, '{fecha_reservacion}',
                 '{nombre_canal}', '{nombre_paquete}', '{tipo_habitacion}', '{hist_menores}', '{hist_adultos}', '{hist_total_habitaciones}')
            """
            try:
                session.sql(insert_stmt).collect()
                st.success("✅ ¡Reservación registrada con éxito!")
            except Exception as e:
                st.error(f"🚫 Error al guardar la reserva: {e}")
else:
    st.info("✍️ Ingresa tu nombre para comenzar.")

