"""
Tablero de productos en Streamlit
=================================
Analiza precio, margen y unidades vendidas a partir de 05_productos.csv.
Graficas (Plotly):
    4.1  Dispersion            (precio vs. margen, color = categoria)
    4.3  Barras                (margen promedio por categoria)
    4.7  Caja                  (precio por categoria)
    4.11 Linea de tendencia    (regresion lineal precio -> margen, con banda de confianza)
    4.12 Barras horizontales   (unidades vendidas por producto)

Uso
---
    pip install -r requirements.txt
    streamlit run streamlit_app.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ======================================================================================
# CONFIGURACIÓN
# ======================================================================================
COLOR_PRINCIPAL = "#187D80"
COLOR_SECUNDARIO = "#E8A33D"
COLOR_TERCIARIO = "#6C3483"
COLOR_ALERTA = "#C0392B"

CATEGORIAS = ["Tecnología", "Muebles", "Papelería"]
PALETA = {"Tecnología": COLOR_PRINCIPAL, "Muebles": COLOR_SECUNDARIO, "Papelería": COLOR_TERCIARIO}

RUTA_CSV = Path(__file__).resolve().parent / "05_productos.csv"


# ======================================================================================
# A. DATOS
# ======================================================================================
def cargar_datos(ruta=RUTA_CSV):
    datos = pd.read_csv(ruta, encoding="utf-8")
    datos["categoria"] = pd.Categorical(datos["categoria"], categories=CATEGORIAS, ordered=True)
    datos["ingresos"] = datos["precio"] * datos["unidades"]
    datos["utilidad"] = datos["ingresos"] * datos["margen_pct"] / 100
    return datos


# ======================================================================================
# B. GRÁFICOS
# ======================================================================================
def _estilo(figura, titulo, leyenda=True):
    figura.update_layout(
        template="plotly_white",
        title=dict(text=titulo, x=0.01, xanchor="left", font=dict(size=15)),
        margin=dict(l=50, r=20, t=55, b=45),
        font=dict(family="Arial, sans-serif", size=12),
        legend=dict(orientation="h", y=-0.2, x=0) if leyenda else None,
        showlegend=leyenda, legend_title_text="", autosize=True,
    )
    return figura


def _figura_vacia(mensaje="Sin datos para los filtros seleccionados"):
    figura = go.Figure()
    figura.add_annotation(text=mensaje, showarrow=False, font=dict(size=14, color="grey"))
    figura.update_xaxes(visible=False)
    figura.update_yaxes(visible=False)
    return _estilo(figura, "", leyenda=False)


def grafico_dispersion(d):
    """4.1 Dispersión: precio vs. margen."""
    f = px.scatter(d, x="precio", y="margen_pct", color="categoria", size="unidades", size_max=34,
                   hover_name="producto", opacity=0.75, color_discrete_map=PALETA,
                   category_orders={"categoria": CATEGORIAS},
                   labels={"precio": "Precio ($)", "margen_pct": "Margen (%)", "categoria": "Categoría",
                           "unidades": "Unidades"})
    f.update_traces(marker=dict(line=dict(width=1, color="white")))
    return _estilo(f, "Precio y margen por producto (tamaño = unidades)")


def grafico_barras(d):
    """4.3 Barras: margen promedio por categoría."""
    r = d.groupby("categoria", observed=True)["margen_pct"].mean().reset_index()
    f = px.bar(r, x="categoria", y="margen_pct", color="categoria", color_discrete_map=PALETA,
               text=r["margen_pct"].map("{:.1f}%".format),
               labels={"categoria": "Categoría", "margen_pct": "Margen promedio (%)"})
    f.update_traces(textposition="outside")
    f.update_yaxes(range=[0, max(r["margen_pct"].max() * 1.2, 10)])
    return _estilo(f, "Margen promedio por categoría", leyenda=False)


def grafico_caja(d):
    """4.7 Caja: distribución del precio por categoría."""
    f = px.box(d, x="categoria", y="precio", color="categoria", points="all", hover_name="producto",
               color_discrete_map=PALETA, category_orders={"categoria": CATEGORIAS},
               labels={"categoria": "Categoría", "precio": "Precio ($)"})
    return _estilo(f, "Distribución del precio por categoría", leyenda=False)


def grafico_tendencia(d):
    """4.11 Línea de tendencia lineal precio -> margen, con banda de confianza del 95 %."""
    if len(d) < 2 or d["precio"].nunique() < 2:
        return _figura_vacia("Se necesitan al menos 2 productos con precios distintos")
    x, y = d["precio"].to_numpy(float), d["margen_pct"].to_numpy(float)
    n = len(x)
    pendiente, intercepto = np.polyfit(x, y, 1)
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    cuadricula = np.linspace(x.min(), x.max(), 100)
    ajuste = intercepto + pendiente * cuadricula
    f = go.Figure()
    if n > 2:
        s = np.sqrt(((y - (intercepto + pendiente * x)) ** 2).sum() / (n - 2))
        sxx = ((x - x.mean()) ** 2).sum()
        error = s * np.sqrt(1 / n + (cuadricula - x.mean()) ** 2 / sxx)
        # valor crítico t(0.975, n-2); para n > 12 se aproxima con 2.0
        t = {3: 12.71, 4: 4.30, 5: 3.18, 6: 2.78, 7: 2.57, 8: 2.45, 9: 2.37, 10: 2.31, 11: 2.26,
             12: 2.23}.get(n, 2.0)
        f.add_scatter(x=np.r_[cuadricula, cuadricula[::-1]], y=np.r_[ajuste + t * error, (ajuste - t * error)[::-1]],
                      fill="toself", fillcolor="rgba(232,163,61,0.22)", line=dict(width=0), hoverinfo="skip",
                      name="IC 95 %")
    f.add_scatter(x=x, y=y, mode="markers", text=d["producto"], name="Productos",
                  marker=dict(size=11, color=COLOR_PRINCIPAL, opacity=0.8, line=dict(width=1, color="white")),
                  hovertemplate="%{text}<br>Precio: $%{x}<br>Margen: %{y}%<extra></extra>")
    f.add_scatter(x=cuadricula, y=ajuste, mode="lines", name=f"Tendencia (R² = {r2:.2f})",
                  line=dict(color=COLOR_ALERTA, width=3))
    f.update_xaxes(title_text="Precio ($)")
    f.update_yaxes(title_text="Margen (%)")
    return _estilo(f, f"Tendencia lineal: cada $100 de precio cambia el margen {pendiente * 100:+.1f} pp")


def grafico_barras_horizontales(d, orden="desc", top=None):
    """4.12 Barras horizontales: unidades por producto."""
    r = d.sort_values("unidades", ascending=(orden == "desc"))   # en horizontal, lo último queda arriba
    if top:
        r = r.tail(top)
    f = px.bar(r, x="unidades", y="producto", orientation="h", color="categoria", color_discrete_map=PALETA,
               text="unidades", labels={"unidades": "Unidades vendidas", "producto": "", "categoria": "Categoría"},
               category_orders={"categoria": CATEGORIAS})
    f.update_traces(texttemplate="%{text:,}", textposition="outside")
    f.update_yaxes(categoryorder="array", categoryarray=list(r["producto"]))
    f.update_xaxes(range=[0, r["unidades"].max() * 1.15])
    return _estilo(f, "Unidades vendidas por producto")


def indicadores_clave(d):
    if d.empty:
        return [("Productos", "0"), ("Unidades vendidas", "—"), ("Ingresos estimados", "—"),
                ("Utilidad estimada", "—"), ("Margen ponderado", "—")]
    margen_pond = d["utilidad"].sum() / d["ingresos"].sum() * 100
    return [
        ("Productos", f"{len(d)}"),
        ("Unidades vendidas", f"{d['unidades'].sum():,.0f}"),
        ("Ingresos estimados", f"${d['ingresos'].sum():,.0f}"),
        ("Utilidad estimada", f"${d['utilidad'].sum():,.0f}"),
        ("Margen ponderado", f"{margen_pond:.1f} %"),
    ]


def filtrar(datos, categorias, productos, precio, margen, unidades_min):
    s = (datos["categoria"].isin(categorias or []) & datos["producto"].isin(productos or [])
         & datos["precio"].between(*precio) & datos["margen_pct"].between(*margen)
         & (datos["unidades"] >= unidades_min))
    return datos[s]


# ======================================================================================
# APLICACION STREAMLIT
# ======================================================================================
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
