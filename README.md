# ¿De quién es la inflación?

App interactiva sobre la inflación que enfrentan los hogares de México según su ingreso y la entidad
donde viven, de julio de 2018 a septiembre de 2026. Calcula un índice de precios para cada tipo de hogar
y separa las diferencias en un efecto canasta (qué compran) y un efecto lugar (dónde viven).

Proyecto de Visualización de Datos, 2026. Oscar Daniel Hernández Romero y Kevin Mejía Rodríguez.

## Pestañas

- **Por ingreso:** inflación de cada decil de ingreso y la brecha entre el decil I y el X.
- **¿Por qué?:** la brecha repartida entre canasta y lugar, mes a mes y producto por producto.
- **Un experimento: refrescos y cigarros:** cuánto subieron los precios con el aumento del IEPS de enero de
  2026, comparados con productos que no cambiaron de impuesto y con los eneros anteriores, y cuánto le cuesta
  a cada decil de ingreso.
- **Del mayoreo a la canasta:** cuánto de un salto en el precio al mayoreo de frutas y verduras (Central de
  Abasto) llega al consumidor y a cada decil, y cuánto de la brecha entre deciles predice el mayoreo.
- **Por entidad:** mapa, comparación de las 32 entidades y su evolución.
- **Un experimento: la frontera:** qué pasó con los precios de Baja California cuando el IVA de la frontera
  norte bajó de 16 a 8 % en enero de 2019, por tipo de producto, por estado fronterizo y por nivel de ingreso.
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
Precios al mayoreo: SNIIM (Secretaría de Economía), Central de Abasto de la Ciudad de México.
La zona de la pestaña de la frontera es la del Decreto de estímulos fiscales región fronteriza norte
(Diario Oficial de la Federación, 31 de diciembre de 2018).
Las cuotas del IEPS de la pestaña de refrescos y cigarros son las del decreto que reforma la Ley del IEPS
(Diario Oficial de la Federación, 7 de noviembre de 2025) y del acuerdo de la SHCP del 22 de diciembre de 2025.
