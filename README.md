# Dashboards

## Tarea Streamlit - Clase 4: Tablero de productos

Tablero interactivo (Dash + Plotly) que analiza **precio, margen y unidades vendidas** por producto y categoria.

Carpeta: [`Tarea Streamlit - Clase 4`](./Tarea%20Streamlit%20-%20Clase%204)

### Contenido del tablero

- Filtros: categoria, producto, rango de precio, rango de margen y unidades minimas.
- Indicadores: productos, unidades, ingresos, utilidad y margen ponderado.
- 5 graficas: dispersion precio vs. margen, margen promedio por categoria, caja de precios, linea de tendencia con banda de confianza y barras horizontales de unidades.

### Como ejecutarlo

```bash
cd "Tarea Streamlit - Clase 4"
pip install -r requirements.txt
python dashboard_productos.py
```

Luego abrir http://127.0.0.1:8050 en el navegador.
