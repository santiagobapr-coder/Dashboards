"""
Tablero de productos en Streamlit
=================================
Reutiliza los datos y las 5 graficas de dashboard_productos.py (Plotly).

    pip install -r requirements.txt
    streamlit run streamlit_app.py
"""

import streamlit as st

from dashboard_productos import (CATEGORIAS, RUTA_CSV, cargar_datos, filtrar,
                                 grafico_barras, grafico_barras_horizontales, grafico_caja,
                                 grafico_dispersion, grafico_tendencia, indicadores_clave,
                                 _figura_vacia)

st.set_page_config(page_title="Tablero de productos", page_icon="📊", layout="wide")


@st.cache_data
def datos_base():
    return cargar_datos(RUTA_CSV)


datos = datos_base()

st.title("Análisis de productos · Precio, margen y unidades")
st.caption("Explora cómo se relacionan el precio, el margen y las ventas por categoría y producto. "
           "Los filtros de la barra lateral actualizan los indicadores y las cinco gráficas.")

# ---- Filtros -------------------------------------------------------------------------
with st.sidebar:
    st.header("Filtros")
    categorias = st.multiselect("Categoría", CATEGORIAS, default=CATEGORIAS)
    productos = st.multiselect("Producto", sorted(datos["producto"]), default=sorted(datos["producto"]))
    p_min, p_max = int(datos["precio"].min()), int(datos["precio"].max())
    m_min, m_max = int(datos["margen_pct"].min()), int(datos["margen_pct"].max())
    precio = st.slider("Precio ($)", p_min, p_max, (p_min, p_max))
    margen = st.slider("Margen (%)", m_min, m_max, (m_min, m_max))
    unidades_min = st.slider("Unidades mínimas", 0, int(datos["unidades"].max()), 0, step=50)

d = filtrar(datos, categorias, productos, precio, margen, unidades_min)

# ---- Indicadores ---------------------------------------------------------------------
for col, (titulo, valor) in zip(st.columns(5), indicadores_clave(d)):
    col.metric(titulo, valor)

# ---- Gráficas ------------------------------------------------------------------------
if d.empty:
    st.plotly_chart(_figura_vacia(), width='stretch')
else:
    pestanas = st.tabs(["4.1 Dispersión", "4.3 Barras", "4.7 Caja", "4.11 Tendencia", "4.12 Barras horizontales"])
    with pestanas[0]:
        st.plotly_chart(grafico_dispersion(d), width='stretch')
    with pestanas[1]:
        st.plotly_chart(grafico_barras(d), width='stretch')
    with pestanas[2]:
        st.plotly_chart(grafico_caja(d), width='stretch')
    with pestanas[3]:
        st.plotly_chart(grafico_tendencia(d), width='stretch')
    with pestanas[4]:
        c1, c2 = st.columns(2)
        orden = c1.radio("Orden", ["desc", "asc"], format_func=lambda v: "Mayor a menor" if v == "desc" else "Menor a mayor",
                         horizontal=True)
        top = c2.selectbox("Mostrar", [0, 3, 5, 8], format_func=lambda n: "Todos" if n == 0 else f"Top {n}")
        st.plotly_chart(grafico_barras_horizontales(d, orden, top), width='stretch')

with st.expander("Ver datos"):
    st.dataframe(d, width='stretch', hide_index=True)
