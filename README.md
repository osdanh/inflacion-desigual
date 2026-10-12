# ¿De quién es la inflación?

App interactiva sobre la inflación que enfrentan los hogares de México según su ingreso y la entidad
donde viven, de julio de 2018 a septiembre de 2026. Calcula un índice de precios para cada tipo de hogar
y separa las diferencias en un efecto canasta (qué compran) y un efecto lugar (dónde viven).

Proyecto de Visualización de Datos, 2026. Oscar Daniel Hernández Romero y Kevin Mejía Rodríguez.

## Pestañas

- **Por ingreso:** inflación de cada decil de ingreso y la brecha entre el decil I y el X.
- **¿Por qué?:** la brecha repartida entre canasta y lugar, mes a mes y producto por producto.
- **Por entidad:** mapa, comparación de las 32 entidades y su evolución.
- **Tu inflación:** la inflación de una canasta propia, con los precios de la entidad elegida.
- **Método:** datos, cálculo y advertencias.

## Correrla en una computadora

```
pip install -r requirements.txt
python -m shiny run app.py
```

## Archivos

- `app.py`: interfaz y servidor (Shiny para Python).
- `figuras.py`: gráficas de Plotly.
- `datos.py`: lectura de las tablas de `datos/`.
- `datos/`: tablas ya calculadas (índices, descomposición, canastas y mapa).
- `www/`: hoja de estilos y Plotly.

## Fuentes

Cálculos propios con datos de INEGI: Índice Nacional de Precios al Consumidor por entidad federativa y
genérico, Encuesta Nacional de Ingresos y Gastos de los Hogares 2018 y 2022, y Marco Geoestadístico.
