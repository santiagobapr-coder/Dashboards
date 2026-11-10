"""
Tablero interactivo de productos con Dash y Plotly
==================================================

Analiza precio, margen y unidades vendidas a partir de 05_productos.csv.
Reproduce las 5 gráficas del Shiny anterior:
    4.1  Dispersión            (precio vs. margen, color = categoría)
    4.3  Barras                (margen promedio por categoría)
    4.7  Caja                  (precio por categoría)
    4.11 Línea de tendencia    (regresión lineal precio -> margen, con banda de confianza)
    4.12 Barras horizontales   (unidades vendidas por producto)

Uso
---
    pip install dash plotly pandas numpy
    python dashboard_productos.py              # http://127.0.0.1:8050
    python dashboard_productos.py --puerto 8060
    python dashboard_productos.py --csv "otra/ruta/05_productos.csv"
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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


# ======================================================================================
# C. REGISTRO
# ======================================================================================
# (identificador, título de la pestaña, función)
PESTANAS = [
    ("g-dispersion", "4.1 Dispersión", grafico_dispersion),
    ("g-barras", "4.3 Barras", grafico_barras),
    ("g-caja", "4.7 Caja", grafico_caja),
    ("g-tendencia", "4.11 Tendencia", grafico_tendencia),
    ("g-horizontales", "4.12 Barras horizontales", None),     # depende además del control de orden y top
]


def filtrar(datos, categorias, productos, precio, margen, unidades_min):
    s = (datos["categoria"].isin(categorias or []) & datos["producto"].isin(productos or [])
         & datos["precio"].between(*precio) & datos["margen_pct"].between(*margen)
         & (datos["unidades"] >= unidades_min))
    return datos[s]


# ======================================================================================
# D. APLICACIÓN DASH
# ======================================================================================
def construir_aplicacion(datos):
    from dash import Dash, Input, Output, dcc, html

    app = Dash(__name__, title="Tablero de productos")
    p_min, p_max = int(datos["precio"].min()), int(datos["precio"].max())
    m_min, m_max = int(datos["margen_pct"].min()), int(datos["margen_pct"].max())
    u_max = int(datos["unidades"].max())
    productos = sorted(datos["producto"])

    tarjeta = {"background": "white", "border": "1px solid #E5E8E8", "borderRadius": "10px", "padding": "6px",
               "boxShadow": "0 1px 3px rgba(0,0,0,0.06)"}
    kpi_estilo = {"background": "white", "border": "1px solid #E5E8E8", "borderLeft": f"5px solid {COLOR_PRINCIPAL}",
                  "borderRadius": "10px", "padding": "10px 16px", "boxShadow": "0 1px 3px rgba(0,0,0,0.06)"}
    etiqueta = {"fontSize": "12px", "fontWeight": "bold", "color": "#34495E", "marginBottom": "4px"}
    pestana_estilo = {"padding": "10px", "fontWeight": "bold", "color": "#5D6D7E"}
    pestana_activa = {**pestana_estilo, "borderTop": f"3px solid {COLOR_SECUNDARIO}", "color": COLOR_PRINCIPAL}

    def tarjetas_kpi(d):
        return [html.Div([html.Div(t, style={"fontSize": "12px", "color": "#5D6D7E"}),
                          html.Div(v, style={"fontSize": "24px", "fontWeight": "bold", "color": "#1B2631"})],
                         style=kpi_estilo) for t, v in indicadores_clave(d)]

    def marcas(a, b, pasos=4):
        return {int(v): str(int(v)) for v in np.linspace(a, b, pasos)}

    filtros = html.Div([
        html.Div([html.Div("Categoría", style=etiqueta),
                  dcc.Checklist(id="f-categoria", options=CATEGORIAS, value=CATEGORIAS, inline=True,
                                labelStyle={"marginRight": "10px"})]),
        html.Div([html.Div("Producto", style=etiqueta),
                  dcc.Dropdown(id="f-producto", options=productos, value=productos, multi=True)],
                 style={"minWidth": "280px", "flex": "1"}),
        html.Div([html.Div("Precio ($)", style=etiqueta),
                  dcc.RangeSlider(id="f-precio", min=p_min, max=p_max, step=1, value=[p_min, p_max],
                                  marks=marcas(p_min, p_max), tooltip={"placement": "bottom"})],
                 style={"minWidth": "220px", "flex": "1"}),
        html.Div([html.Div("Margen (%)", style=etiqueta),
                  dcc.RangeSlider(id="f-margen", min=m_min, max=m_max, step=1, value=[m_min, m_max],
                                  marks=marcas(m_min, m_max), tooltip={"placement": "bottom"})],
                 style={"minWidth": "220px", "flex": "1"}),
        html.Div([html.Div("Unidades mínimas", style=etiqueta),
                  dcc.Slider(id="f-unidades", min=0, max=u_max, step=50, value=0,
                             marks={v: f"{v:,}" for v in range(0, u_max + 1, 1000)}, tooltip={"placement": "bottom"})],
                 style={"minWidth": "220px", "flex": "1"}),
    ], style={"display": "flex", "gap": "26px", "flexWrap": "wrap", "alignItems": "flex-start", "background": "white",
              "border": "1px solid #E5E8E8", "borderRadius": "10px", "padding": "12px 16px"})

    controles_horizontales = html.Div([
        html.Div([html.Div("Orden", style=etiqueta),
                  dcc.RadioItems(id="f-orden", options=[{"label": "Mayor a menor", "value": "desc"},
                                                        {"label": "Menor a mayor", "value": "asc"}],
                                 value="desc", inline=True, labelStyle={"marginRight": "12px"})]),
        html.Div([html.Div("Mostrar los N primeros", style=etiqueta),
                  dcc.Dropdown(id="f-top", options=[{"label": "Todos", "value": 0}] +
                               [{"label": f"Top {n}", "value": n} for n in (3, 5, 8)],
                               value=0, clearable=False, style={"width": "140px"})]),
    ], style={"display": "flex", "gap": "26px", "padding": "8px 12px"})

    pestanas = []
    for ident, titulo, _ in PESTANAS:
        grafico = dcc.Graph(id=ident, config={"displaylogo": False}, style={"height": "470px"})
        contenido = [controles_horizontales, grafico] if ident == "g-horizontales" else [grafico]
        pestanas.append(dcc.Tab(label=titulo, value=ident, style=pestana_estilo, selected_style=pestana_activa,
                                children=html.Div(contenido, style={**tarjeta, "marginTop": "10px"})))

    app.layout = html.Div([
        html.Div([html.H2("Análisis de productos · Precio, margen y unidades", style={"margin": "0", "color": "white"}),
                  html.Div("Explora cómo se relacionan el precio, el margen y las ventas por categoría y producto. "
                           "Todos los filtros actualizan los indicadores y las cinco gráficas.",
                           style={"color": "#E6F4F4", "fontSize": "13px", "marginTop": "4px"})],
                 style={"background": f"linear-gradient(90deg, {COLOR_PRINCIPAL}, #1F9A9E)", "padding": "16px 22px",
                        "borderRadius": "10px", "borderBottom": f"4px solid {COLOR_SECUNDARIO}"}),
        html.Div(filtros, style={"margin": "12px 0"}),
        html.Div(id="kpis", children=tarjetas_kpi(datos),
                 style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
                        "gap": "12px"}),
        dcc.Tabs(id="pestanas", value=PESTANAS[0][0], children=pestanas, style={"marginTop": "14px"}),
    ], style={"maxWidth": "1400px", "margin": "0 auto", "padding": "16px", "fontFamily": "Arial, sans-serif",
              "background": "#F4F6F7", "minHeight": "100vh"})

    salidas = [Output("kpis", "children")] + [Output(i, "figure") for i, _, _ in PESTANAS]

    @app.callback(salidas, Input("f-categoria", "value"), Input("f-producto", "value"), Input("f-precio", "value"),
                  Input("f-margen", "value"), Input("f-unidades", "value"), Input("f-orden", "value"),
                  Input("f-top", "value"))
    def actualizar(categorias, prods, precio, margen, unidades_min, orden, top):
        d = filtrar(datos, categorias, prods, precio, margen, unidades_min)
        if d.empty:
            return [tarjetas_kpi(d)] + [_figura_vacia() for _ in PESTANAS]
        figuras = [f(d) if f else grafico_barras_horizontales(d, orden, top) for _, _, f in PESTANAS]
        return [tarjetas_kpi(d)] + figuras

    app.actualizar = actualizar
    return app


# ======================================================================================
# PUNTO DE ENTRADA
# ======================================================================================
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Tablero de productos con Dash y Plotly")
    ap.add_argument("--puerto", type=int, default=8050)
    ap.add_argument("--csv", type=Path, default=RUTA_CSV)
    args = ap.parse_args()
    aplicacion = construir_aplicacion(cargar_datos(args.csv))
    aplicacion.run(debug=False, port=args.puerto)
