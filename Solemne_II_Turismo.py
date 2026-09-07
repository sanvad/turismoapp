# ==========================================================
# SOLEMNE II
# Analisis de datos de turismo en Chile
# Autor: ______________________________
# Asignatura: _________________________
# ==========================================================

import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# ----------------------------------------------------------
# Configuracion de la pagina
# ----------------------------------------------------------

st.set_page_config(
    page_title="Turismo en Chile",
    page_icon="🇨🇱",
    layout="wide"
)


# ----------------------------------------------------------
# Datos de la API
# ----------------------------------------------------------

# Recurso de alojamientos turisticos de SERNATUR
RESOURCE_ID = "85f6d5c5-6ae6-4d99-b20d-9d88d04c7b64"

URL = "https://datos.gob.cl/api/3/action/datastore_search"


# ----------------------------------------------------------
# Funcion para obtener los datos
# ----------------------------------------------------------

@st.cache_data(ttl=3600)
def obtener_datos():

    todos_los_datos = []
    offset = 0
    cantidad = 1000

    while True:

        parametros = {
            "resource_id": RESOURCE_ID,
            "limit": cantidad,
            "offset": offset
        }

        try:
            respuesta = requests.get(
                URL,
                params=parametros,
                timeout=30
            )

            respuesta.raise_for_status()

        except requests.exceptions.RequestException as error:
            raise Exception("No se pudo conectar con la API: " + str(error))

        datos = respuesta.json()

        if datos["success"] == False:
            raise Exception("La API no pudo entregar los datos.")

        registros = datos["result"]["records"]

        if len(registros) == 0:
            break

        todos_los_datos.extend(registros)

        total = datos["result"].get("total", len(todos_los_datos))

        offset = offset + cantidad

        if offset >= total:
            break

    df = pd.DataFrame(todos_los_datos)

    # La API puede entregar un identificador interno.
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])

    # Quitar espacios innecesarios en las columnas de texto.
    for columna in df.columns:
        if df[columna].dtype == "object":
            df[columna] = df[columna].astype(str).str.strip()

    return df


# ----------------------------------------------------------
# Funciones auxiliares
# ----------------------------------------------------------

def buscar_columna(df, palabras):

    for columna in df.columns:

        nombre = str(columna).lower()

        for palabra in palabras:
            if palabra.lower() in nombre:
                return columna

    return None


def crear_grafico(datos, titulo, nombre_eje):

    fig, ax = plt.subplots(figsize=(10, 5))

    datos.plot(kind="bar", ax=ax)

    ax.set_title(titulo)
    ax.set_xlabel(nombre_eje)
    ax.set_ylabel("Cantidad")
    ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()

    return fig


# ----------------------------------------------------------
# Titulo
# ----------------------------------------------------------

st.title("🇨🇱 Turismo en Chile")
st.subheader("Analisis de alojamientos turisticos")

st.write(
    """
    Esta aplicacion permite explorar informacion de establecimientos
    de alojamiento turistico registrados en Chile.

    Los datos son obtenidos directamente desde el Portal de Datos
    Abiertos del Gobierno de Chile mediante una API REST.
    """
)


# ----------------------------------------------------------
# Consulta de la API
# ----------------------------------------------------------

try:

    with st.spinner("Obteniendo datos desde la API..."):
        df = obtener_datos()

except Exception as error:

    st.error(str(error))
    st.stop()


# ----------------------------------------------------------
# Identificar algunas columnas importantes
# ----------------------------------------------------------

columna_region = buscar_columna(
    df,
    ["region", "región"]
)

columna_comuna = buscar_columna(
    df,
    ["comuna"]
)

columna_tipo = buscar_columna(
    df,
    ["tipo de alojamiento", "tipo alojamiento", "tipo"]
)

columna_categoria = buscar_columna(
    df,
    ["categoria", "categoría", "clasificacion", "clasificación"]
)


# ----------------------------------------------------------
# Resumen general
# ----------------------------------------------------------

st.header("📊 Resumen general")

total_registros = len(df)

if columna_region is not None:
    cantidad_regiones = df[columna_region].nunique()
else:
    cantidad_regiones = 0

if columna_comuna is not None:
    cantidad_comunas = df[columna_comuna].nunique()
else:
    cantidad_comunas = 0

if columna_tipo is not None:
    cantidad_tipos = df[columna_tipo].nunique()
else:
    cantidad_tipos = 0


a, b, c, d = st.columns(4)

a.metric("Establecimientos", total_registros)
b.metric("Regiones", cantidad_regiones)
c.metric("Comunas", cantidad_comunas)
d.metric("Tipos de alojamiento", cantidad_tipos)


# ----------------------------------------------------------
# Filtros
# ----------------------------------------------------------

st.header("🔎 Filtros")

datos_filtrados = df.copy()


if columna_region is not None:

    regiones = sorted(
        datos_filtrados[columna_region]
        .dropna()
        .astype(str)
        .unique()
    )

    region_elegida = st.selectbox(
        "Seleccione una región",
        ["Todas"] + list(regiones)
    )

    if region_elegida != "Todas":

        datos_filtrados = datos_filtrados[
            datos_filtrados[columna_region].astype(str)
            == region_elegida
        ]


if columna_comuna is not None:

    comunas = sorted(
        datos_filtrados[columna_comuna]
        .dropna()
        .astype(str)
        .unique()
    )

    comuna_elegida = st.selectbox(
        "Seleccione una comuna",
        ["Todas"] + list(comunas)
    )

    if comuna_elegida != "Todas":

        datos_filtrados = datos_filtrados[
            datos_filtrados[columna_comuna].astype(str)
            == comuna_elegida
        ]


if columna_tipo is not None:

    tipos = sorted(
        datos_filtrados[columna_tipo]
        .dropna()
        .astype(str)
        .unique()
    )

    tipo_elegido = st.selectbox(
        "Seleccione un tipo de alojamiento",
        ["Todos"] + list(tipos)
    )

    if tipo_elegido != "Todos":

        datos_filtrados = datos_filtrados[
            datos_filtrados[columna_tipo].astype(str)
            == tipo_elegido
        ]


st.write(
    "Cantidad de registros después de aplicar los filtros:",
    len(datos_filtrados)
)


# ----------------------------------------------------------
# Tabla de datos
# ----------------------------------------------------------

st.subheader("Datos seleccionados")

st.dataframe(
    datos_filtrados,
    use_container_width=True,
    height=350
)


# ----------------------------------------------------------
# Analisis por region
# ----------------------------------------------------------

if columna_region is not None:

    st.header("🗺️ Alojamientos por región")

    cantidad_region = (
        datos_filtrados[columna_region]
        .dropna()
        .value_counts()
        .head(20)
    )

    if len(cantidad_region) > 0:

        grafico = crear_grafico(
            cantidad_region,
            "Cantidad de alojamientos por región",
            "Región"
        )

        st.pyplot(grafico)

        region_mayor = cantidad_region.index[0]
        cantidad_mayor = cantidad_region.iloc[0]

        st.write(
            f"La región que presenta la mayor cantidad de registros "
            f"en la selección actual es **{region_mayor}**, "
            f"con **{cantidad_mayor} establecimientos**."
        )


# ----------------------------------------------------------
# Analisis por comuna
# ----------------------------------------------------------

if columna_comuna is not None:

    st.header("🏙️ Alojamientos por comuna")

    cantidad_comuna = (
        datos_filtrados[columna_comuna]
        .dropna()
        .value_counts()
        .head(15)
    )

    if len(cantidad_comuna) > 0:

        grafico = crear_grafico(
            cantidad_comuna,
            "Comunas con mayor cantidad de alojamientos",
            "Comuna"
        )

        st.pyplot(grafico)

        st.dataframe(
            cantidad_comuna.rename(
                "Cantidad de establecimientos"
            ).to_frame(),
            use_container_width=True
        )


# ----------------------------------------------------------
# Analisis por tipo de alojamiento
# ----------------------------------------------------------

if columna_tipo is not None:

    st.header("🏨 Tipos de alojamiento")

    cantidad_tipo = (
        datos_filtrados[columna_tipo]
        .dropna()
        .value_counts()
        .head(15)
    )

    if len(cantidad_tipo) > 0:

        izquierda, derecha = st.columns(2)

        with izquierda:

            grafico = crear_grafico(
                cantidad_tipo,
                "Distribución por tipo de alojamiento",
                "Tipo"
            )

            st.pyplot(grafico)

        with derecha:

            st.dataframe(
                cantidad_tipo.rename(
                    "Cantidad"
                ).to_frame(),
                use_container_width=True
            )


# ----------------------------------------------------------
# Analisis por categoria
# ----------------------------------------------------------

if columna_categoria is not None:

    st.header("⭐ Categorías")

    cantidad_categoria = (
        datos_filtrados[columna_categoria]
        .dropna()
        .value_counts()
        .head(15)
    )

    if len(cantidad_categoria) > 0:

        grafico = crear_grafico(
            cantidad_categoria,
            "Distribución de establecimientos por categoría",
            "Categoría"
        )

        st.pyplot(grafico)


# ----------------------------------------------------------
# Estadisticas
# ----------------------------------------------------------

st.header("📈 Estadísticas")

columnas_numericas = datos_filtrados.select_dtypes(
    include="number"
).columns.tolist()

if len(columnas_numericas) > 0:

    st.write(
        "A continuación se muestran estadísticas descriptivas "
        "de las variables numéricas disponibles."
    )

    estadisticas = datos_filtrados[
        columnas_numericas
    ].describe().T

    estadisticas = estadisticas.round(2)

    st.dataframe(
        estadisticas,
        use_container_width=True
    )

else:

    st.info(
        "El conjunto de datos no contiene variables numéricas "
        "que puedan analizarse directamente."
    )


# ----------------------------------------------------------
# Descargar datos
# ----------------------------------------------------------

st.header("⬇️ Descargar información")

archivo_csv = datos_filtrados.to_csv(
    index=False,
    encoding="utf-8-sig"
)

st.download_button(
    "Descargar datos filtrados",
    archivo_csv,
    "turismo_chile_filtrado.csv",
    "text/csv"
)


# ----------------------------------------------------------
# Metodologia
# ----------------------------------------------------------

st.header("📚 Metodología")

st.write(
    """
    Para realizar este proyecto se utilizó una API REST pública
    disponible en el Portal de Datos Abiertos del Gobierno de Chile.

    Primero se realiza una solicitud GET utilizando la biblioteca
    requests. La respuesta se obtiene en formato JSON y posteriormente
    se transforma en un DataFrame utilizando pandas.

    Después se aplican filtros y conteos para analizar la distribución
    de los establecimientos según región, comuna, tipo y categoría.

    Finalmente, los resultados se presentan mediante gráficos
    desarrollados con matplotlib y una interfaz interactiva creada
    con Streamlit.
    """
)


# ----------------------------------------------------------
# Conclusiones
# ----------------------------------------------------------

st.header("💡 Conclusiones")

st.write(
    """
    A partir de los datos analizados es posible observar que los
    establecimientos de alojamiento turístico no se distribuyen de
    manera uniforme entre las distintas regiones y comunas.

    La utilización de filtros permite realizar comparaciones más
    específicas y observar cómo cambia la información cuando se
    selecciona una zona determinada.

    Los gráficos ayudan a identificar rápidamente las regiones,
    comunas y tipos de alojamiento que presentan una mayor cantidad
    de registros.

    Los resultados corresponden exclusivamente al conjunto de datos
    utilizado, por lo que deben interpretarse considerando el período
    y las características de la fuente original.
    """
)


# ----------------------------------------------------------
# Fuente
# ----------------------------------------------------------

st.divider()

st.caption(
    "Fuente: Portal de Datos Abiertos del Gobierno de Chile - SERNATUR"
)

st.caption(
    "Consulta realizada mediante API REST utilizando requests y GET."
)

st.caption(
    "Resource ID: " + RESOURCE_ID
)
st.caption(
    "David Sandoval Bahamonde
    david@queilen.cl" 
)
