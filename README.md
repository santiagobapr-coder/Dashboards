# Dashboards

## Tarea Streamlit - Clase 4: Tablero de productos

Tablero interactivo en **Streamlit** (graficas con Plotly) que analiza **precio, margen y unidades vendidas** por producto y categoria.

Carpeta: [`Tarea Streamlit - Clase 4`](./Tarea%20Streamlit%20-%20Clase%204)

### Contenido del tablero

- Filtros (barra lateral): categoria, producto, rango de precio, rango de margen y unidades minimas.
- Indicadores: productos, unidades, ingresos, utilidad y margen ponderado.
- 5 graficas: dispersion precio vs. margen, margen promedio por categoria, caja de precios, linea de tendencia con banda de confianza y barras horizontales de unidades.

### Como ejecutarlo

```bash
cd "Tarea Streamlit - Clase 4"
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Se abre automaticamente en http://localhost:8501.

### Archivos

- `streamlit_app.py`: aplicacion Streamlit (archivo principal).
- `dashboard_productos.py`: datos y funciones de graficas (tambien incluye una version anterior en Dash).
- `05_productos.csv`: datos.
