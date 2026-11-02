"""
¿De quién es la inflación?  Inflación por tipo de hogar y por entidad, México, 2018-2026.

App de Shiny para Python con gráficas de Plotly. Los datos vienen de la carpeta datos (la arma
construir_datos_app.py, en la carpeta de arriba).

Para verla en esta computadora, desde la carpeta app:
    python -m shiny run app.py
"""
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from shiny import App, reactive, render, ui

import datos as D
import figuras as F

AQUI = Path(__file__).parent
RUBROS8 = [str(i) for i in range(1, 9)]
MEDIDAS = {"inflacion_anual": "Inflación anual", "acumulada": "Acumulada desde julio de 2018"}
QUE = {"inflacion": "Inflación de los hogares", "brecha": "Diferencia contra el país",
       "canasta": "Efecto canasta", "lugar": "Efecto lugar"}
COMPARACIONES = {"1-10": "Decil I contra decil X"} | {f"{d}-0": f"Decil {D.ROMANOS[d]} contra todos los hogares"
                                                      for d in range(1, 11)}
ENTIDADES = dict(zip(D.entidades["cve_ent"], D.entidades["entidad"]))
ENT_INICIAL, QUINTIL_INICIAL = "09", 3


def opciones_quintil():
    tope = D.cortes.set_index("decil")["ingreso_mensual_max"]
    c = [round(tope[d], -2) for d in (2, 4, 6, 8)]
    return {1: f"Hasta ${c[0]:,.0f} al mes (quintil I)", 2: f"${c[0]:,.0f} a ${c[1]:,.0f} (quintil II)",
            3: f"${c[1]:,.0f} a ${c[2]:,.0f} (quintil III)", 4: f"${c[2]:,.0f} a ${c[3]:,.0f} (quintil IV)",
            5: f"Más de ${c[3]:,.0f} (quintil V)"}


def canasta(ent, quintil):
    c = D.canastas[(D.canastas["cve_ent"] == ent) & (D.canastas["quintil"] == int(quintil))]
    return c.set_index("rubro")["participacion"].reindex(RUBROS8)


def opciones_frontera():
    """Tipos de producto con trayectoria mensual, agrupados por si pagaban IVA."""
    grupos = {"con IVA": "Con IVA: bajó de 16 a 8 %", "sin IVA": "Sin IVA: tasa 0 % o exento", "comparación": "Comparación"}
    return {titulo: {k: k for k in D.FR_CON_MESES if D.FR_CLASE[k] == clase} for clase, titulo in grupos.items()}


def opciones_impuestos():
    """Productos y canastas del experimento de los impuestos, con las comprobaciones aparte."""
    return {grupo: {k: k for k in canastas} for grupo, canastas in D.IM_GRUPOS.items()}


def opciones_mayoreo():
    """El promedio de las frutas y verduras y cada producto, del que más pesa en el INPC al que menos."""
    return {D.MY_PROMEDIO: D.MY_PROMEDIO, "Cada producto (del que más pesa al que menos)": {g: g for g in D.MY_PRODUCTOS}}


def cuando(h):
    return "el mismo mes" if h == 0 else "al mes siguiente" if h == 1 else f"a los {h} meses"


def tarjeta(etiqueta, valor, nota="", clase=""):
    return ui.div(ui.div(etiqueta, class_="tj-etiqueta"), ui.div(valor, class_=f"tj-valor {clase}"),
                  ui.div(nota, class_="tj-nota"), class_="tarjeta")


def grafica(titulo, salida, nota=None):
    return ui.card(ui.card_header(titulo), ui.output_ui(salida),
                   ui.p(nota, class_="nota-grafica") if nota else None)


def pct(v, signo=False):
    return f"{v:+.1f} %" if signo else f"{v:.1f} %"


def pp(v):
    return f"{v:+.1f} pp"


# ============================================================================ interfaz
panel_ingreso = ui.nav_panel(
    "Por ingreso",
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("dec_rubro", "Rubro", D.RUBRO),
            ui.input_radio_buttons("dec_medida", "Medida", MEDIDAS),
            ui.input_select("dec_variante", "Ponderadores", D.VARIANTES),
            ui.p("Los deciles ordenan a los hogares del país por su ingreso: el I es el 10 % con menos "
                 "ingreso y el X el 10 % con más.", class_="ayuda"),
            width=320),
        ui.output_ui("dec_tarjetas"),
        grafica("Inflación por decil de ingreso", "dec_lineas"),
        grafica("La brecha: decil I menos decil X", "dec_brecha",
                "Arriba de cero, la inflación del decil I es mayor que la del decil X."),
    ))

panel_porque = ui.nav_panel(
    "¿Por qué?",
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("pq_comp", "Comparación", COMPARACIONES),
            ui.input_select("pq_periodo", "Periodo acumulado", list(D.ACUMULADOS)),
            ui.p(ui.tags.b("Canasta: "), "los dos grupos compran cosas distintas, y unas suben más que otras.",
                 class_="ayuda"),
            ui.p(ui.tags.b("Lugar: "), "el mismo producto sube distinto en las entidades donde vive cada grupo.",
                 class_="ayuda"),
            ui.p("La suma de los dos efectos es exactamente la brecha.", class_="ayuda"),
            width=320),
        ui.output_ui("pq_tarjetas"),
        grafica("Brecha de inflación anual, mes a mes", "pq_tiempo",
                "Cada barra reparte la brecha del mes entre los componentes de la canasta y el lugar; la línea es el total."),
        ui.layout_columns(
            grafica("Qué explica la brecha acumulada", "pq_acumulada"),
            grafica("Productos que más abren y más cierran la brecha", "pq_productos"),
            col_widths=(5, 7)),
    ))

panel_impuestos = ui.nav_panel(
    "Refrescos y cigarros",
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("im_producto", "Producto", opciones_impuestos()),
            ui.p(ui.tags.b("Qué pasó: "), "desde el 1 de enero de 2026 el IEPS de las bebidas con azúcar pasó de 1.65 a 3.08 "
                 "pesos por litro (las que solo llevan edulcorante pagan ahora 1.50) y el de los cigarros, de 160 a 200 % más "
                 "una cuota mayor por cigarro.", class_="ayuda"),
            ui.p(ui.tags.b("Cómo se mide: "), f"el precio de cada producto contra el de {D.IM_COMPARACION} alimentos y bebidas "
                 "que no cambiaron de impuesto, en la misma entidad y el mismo mes, y el enero de 2026 contra los eneros de "
                 "2021 a 2025, cuando la cuota solo se actualizó con la inflación.", class_="ayuda"),
            ui.p(ui.tags.b("Qué tan seguro: "), "la cuenta se repite con cada producto de comparación como si hubiera pagado "
                 "el impuesto, y con cada enero anterior.", class_="ayuda"),
            ui.p(ui.tags.b("Por qué producto por producto: "), "dentro de una ciudad todos los hogares pagan el mismo precio; "
                 "el impuesto llega distinto a cada decil solo por lo que compra.", class_="ayuda"),
            width=320),
        ui.output_ui("im_tarjetas"),
        ui.card(ui.card_header(ui.output_text("im_titulo")), ui.output_ui("im_eventos"), ui.output_ui("im_nota_eventos")),
        ui.card(ui.card_header("Cuánto subió el costo de la canasta de cada decil"), ui.output_ui("im_incidencia"),
                ui.output_ui("im_nota_incidencia")),
        ui.layout_columns(
            ui.card(ui.card_header(ui.output_text("im_titulo_eneros")), ui.output_ui("im_eneros"), ui.output_ui("im_nota_eneros")),
            ui.card(ui.card_header("¿Y si se compara el índice de cada decil?"), ui.output_ui("im_directo"),
                    ui.output_ui("im_nota_directo")),
            col_widths=(6, 6)),
    ))

panel_mayoreo = ui.nav_panel(
    "Del mayoreo a la canasta",
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("my_producto", "Producto", opciones_mayoreo()),
            ui.input_slider("my_h", "Meses después del salto", min=0, max=D.MY_H, value=1, step=1, ticks=False),
            ui.p(ui.tags.b("Qué se mide: "), "cuánto de un aumento del precio al mayoreo en la Central de Abasto de la Ciudad "
                 f"de México (SNIIM) llega al precio que pagan los hogares (INPC), mes a mes, en {D.MY_GENERICOS} frutas y "
                 "verduras.", class_="ayuda"),
            ui.p(ui.tags.b("Cómo: "), "proyecciones locales: el cambio del precio al consumidor varios meses después contra el "
                 "salto al mayoreo del mismo producto, quitando la temporada de cada producto y lo que mueve a todos a la vez "
                 "(inflación general, tipo de cambio). Como comprobación, la sequía de los estados de donde viene cada producto "
                 "sirve de instrumento (Monitor de Sequía, Conagua).", class_="ayuda"),
            ui.p(ui.tags.b("Por qué importa: "), "las frutas y verduras pesan más en el gasto del decil I, y lo que más compra "
                 "(jitomate, cebolla, papa, chile) es lo que más rápido pasa del mayoreo a la tienda.", class_="ayuda"),
            width=320),
        ui.output_ui("my_tarjetas"),
        ui.layout_columns(
            ui.card(ui.card_header(ui.output_text("my_titulo")), ui.output_ui("my_traslado"), ui.output_ui("my_nota_traslado")),
            ui.card(ui.card_header(ui.output_text("my_titulo_deciles")), ui.output_ui("my_deciles"),
                    ui.output_ui("my_nota_deciles")),
            col_widths=(6, 6)),
        ui.card(ui.card_header("La brecha de inflación anual entre el decil I y el X, y lo que predice el mayoreo"),
                ui.output_ui("my_historia"), ui.output_ui("my_nota_historia")),
        ui.card(ui.card_header("¿Y la sequía? Qué pasa con los precios cuando aumenta en los estados que surten a la Central de Abasto"),
                ui.output_ui("my_sequia"), ui.output_ui("my_nota_sequia")),
        ui.card(ui.card_header(ui.output_text("my_titulo_productos")), ui.output_ui("my_productos"),
                ui.p("Cada punto es una fruta o verdura; su tamaño, su peso en el INPC. A la derecha, las que pesan más en el gasto "
                     "del decil I que en el del X; arriba, las que más trasladan del mayoreo al consumidor en el mes elegido. El "
                     "jitomate y la cebolla están arriba a la derecha: por eso los saltos de la Central de Abasto pegan más al "
                     "decil I.", class_="nota-grafica")),
    ))

panel_entidad = ui.nav_panel(
    "Por entidad",
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("ent_que", "Qué mostrar", QUE),
            ui.input_radio_buttons("ent_periodo", "Periodo", {"anual": "Anual (12 meses)",
                                                              "acumulada": "Acumulada desde julio de 2018"}),
            ui.input_slider("ent_mes", "Mes", min=date(2019, 7, 1), max=date(D.FIN.year, D.FIN.month, 1),
                            value=date(D.FIN.year, D.FIN.month, 1), step=31, time_format="%m/%Y", ticks=False,
                            animate=ui.AnimationOptions(interval=1200, loop=False)),
            ui.panel_conditional(
                "input.ent_que === 'inflacion'",
                ui.input_select("ent_quintil", "Hogares", {0: "Todos", 1: "Quintil I (menor ingreso)", 2: "Quintil II",
                                                           3: "Quintil III", 4: "Quintil IV",
                                                           5: "Quintil V (mayor ingreso)"}),
                ui.input_select("ent_rubro", "Rubro", D.RUBRO)),
            ui.input_select("ent_sel", "Resaltar entidad", ENTIDADES, selected="20"),
            ui.output_ui("ent_ayuda"),
            width=320),
        ui.output_ui("ent_tarjetas"),
        ui.layout_columns(
            ui.card(ui.card_header(ui.output_text("ent_titulo")), ui.output_ui("ent_mapa")),
            ui.card(ui.card_header("Las 32 entidades"), ui.output_ui("ent_ranking")),
            col_widths=(7, 5)),
        grafica("En el tiempo (inflación anual)", "ent_series"),
    ))

panel_frontera = ui.nav_panel(
    "Un experimento: la frontera",
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("fr_tipo", "Tipo de producto", opciones_frontera()),
            ui.p(ui.tags.b("Qué pasó: "), "el 1 de enero de 2019, en 43 municipios de la frontera norte el IVA bajó de 16 a "
                 "8 %, el ISR de las empresas se redujo un tercio y el salario mínimo se duplicó. Baja California entera "
                 "quedó dentro.", class_="ayuda"),
            ui.p(ui.tags.b("Cómo se mide: "), "los precios de Baja California contra los de las 26 entidades que no tocan "
                 "la frontera, antes y después. Si todo el recorte llegara al consumidor, un precio con IVA bajaría "
                 f"{-D.FR_TRASLADO:.1f} %.", class_="ayuda"),
            ui.p(ui.tags.b("Qué tan seguro: "), "solo hay una entidad tratada completa. La prueba es repetir la cuenta con "
                 "cada una de las otras 26, donde no hubo política, y ver si alguna se mueve tanto como Baja California.",
                 class_="ayuda"),
            ui.p("Es el efecto del paquete entero, no solo del IVA.", class_="ayuda"),
            width=320),
        ui.output_ui("fr_tarjetas"),
        ui.card(ui.card_header(ui.output_text("fr_titulo")), ui.output_ui("fr_eventos"),
                ui.p("Diferencia de precios contra el promedio de las 26 entidades no fronterizas; diciembre de 2018 es el punto "
                     "de partida. Cada línea gris es una de esas 26 comparada con las otras 25: lo que se mueve la cuenta "
                     "donde no hubo política.", class_="nota-grafica")),
        ui.layout_columns(
            grafica("Un año después, por tipo de producto", "fr_tipos",
                    "Julio a diciembre de 2019 contra los mismos meses de 2018, para que la temporada no cuente (la tarifa de "
                    "luz cambia en verano). La barra con borde es el tipo elegido."),
            ui.card(ui.card_header(ui.output_text("fr_titulo_estados")), ui.output_ui("fr_estados"), ui.output_ui("fr_nota_estados")),
            col_widths=(7, 5)),
        ui.card(ui.card_header("Cuánto bajó el costo de la canasta de los hogares de Baja California"),
                ui.output_ui("fr_incidencia"), ui.output_ui("fr_nota_incidencia")),
    ))

panel_tu = ui.nav_panel(
    "Tu inflación",
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("tu_ent", "¿Dónde vives?", ENTIDADES, selected=ENT_INICIAL),
            ui.input_select("tu_quintil", "Ingreso mensual de tu hogar", opciones_quintil(), selected=QUINTIL_INICIAL),
            ui.p("Ingreso en pesos de 2022 (ENIGH).", class_="ayuda"),
            ui.tags.hr(),
            ui.tags.b("Tu canasta: % de tu gasto"),
            *[ui.input_slider(f"tu_r{r}", D.RUBRO[r], min=0, max=70, step=1, post=" %",
                              value=round(float(canasta(ENT_INICIAL, QUINTIL_INICIAL)[r]))) for r in RUBROS8],
            ui.output_ui("tu_suma"),
            ui.input_action_button("tu_reset", "Restablecer la canasta de mi grupo", class_="btn-sm btn-outline-secondary"),
            width=330),
        ui.output_ui("tu_tarjetas"),
        grafica("Tu inflación anual contra la del país", "tu_lineas",
                "Tu canasta se valúa con los precios de tu entidad; dentro de cada rubro se usa la mezcla de productos "
                "de los hogares de tu entidad y nivel de ingreso."),
        grafica("De dónde viene tu inflación del último año", "tu_aportes",
                "Aporte de cada rubro, en puntos porcentuales; suman tu inflación anual."),
    ))

METODO = """
### Qué muestra

La inflación no es la misma para todos los hogares: depende de **qué compran** y de **dónde viven**.
Esta app calcula un índice de precios para cada tipo de hogar (por decil de ingreso, por entidad y por
quintil dentro de cada entidad) de julio de 2018 a septiembre de 2026, y separa las diferencias en un
efecto canasta y un efecto lugar.

### Datos

- **Precios:** Índice Nacional de Precios al Consumidor (INEGI), índices mensuales por entidad federativa
  y por genérico (292 productos y servicios), base segunda quincena de julio de 2018 = 100.
- **Canastas:** Encuesta Nacional de Ingresos y Gastos de los Hogares (ENIGH, INEGI) 2022 y 2018: gasto
  monetario de cada hogar por producto, más el alquiler estimado de la vivienda propia.
- **Mapa:** Marco Geoestadístico de INEGI (diciembre de 2025), simplificado.
- **Impuestos:** decreto que reforma la Ley del IEPS (Diario Oficial de la Federación, 7 de noviembre de 2025) y
  acuerdo de la SHCP con las cuotas de 2026 (22 de diciembre de 2025).
- **Mayoreo:** Sistema Nacional de Información e Integración de Mercados (SNIIM, Secretaría de Economía), precios
  diarios de frutas y hortalizas en la Central de Abasto de la Ciudad de México, de 2012 a septiembre de 2026.

### Cómo se calcula

1. Cada clave de gasto de la ENIGH se asigna a un genérico del INPC (o al nivel más cercano cuando no hay
   uno propio). El 91 % del gasto queda en un genérico específico.
2. El gasto se **calibra**: el peso nacional de cada uno de los 76 conceptos del INPC es el oficial, y la
   ENIGH solo decide cómo se reparte entre hogares. Esto corrige, por ejemplo, que la encuesta subreporta
   alcohol y tabaco.
3. El índice de un grupo de hogares es el promedio de los índices de precios de su entidad, ponderado con
   la participación de cada producto en su gasto. Con todos los hogares juntos el resultado reproduce el
   INPC oficial (45.5 % contra 45.6 % de julio de 2018 a agosto de 2026).

### Canasta y lugar

La diferencia de inflación entre dos grupos se parte de forma exacta en dos:

- **Canasta:** compran productos distintos, y unos suben más que otros.
- **Lugar:** el mismo producto sube distinto en las entidades donde vive cada grupo.

### Un experimento: refrescos y cigarros

Lo anterior describe; las pestañas de experimentos buscan efectos. Desde el 1 de enero de 2026, el IEPS de las
bebidas saborizadas con azúcares añadidos pasó de 1.6451 a 3.0818 pesos por litro, las que solo llevan
edulcorantes empezaron a pagar 1.50, y el de los cigarros subió de 160 a 200 % más una cuota por cigarro de
0.6445 a 0.8516 pesos. Dentro de una ciudad todos los hogares pagan el mismo precio por producto, así que el
impuesto solo puede llegar distinto a cada decil por lo que compra: primero se mide cuánto subió cada precio y
después se reparte con la canasta de cada decil.

- **Comparación:** con y = 100 × log del índice de precios de la entidad, el producto y el mes, se toma el cambio
  de cada mes contra diciembre del año anterior. Primero se le resta el de 58 alimentos y bebidas que no
  cambiaron de impuesto (en la misma entidad y mes), y después lo normal de esa diferencia en los eneros de 2021
  a 2025. Es una triple diferencia (producto × año × mes), igual al coeficiente de una regresión con efectos
  fijos de entidad × mes. No hace falta un instrumento: el impuesto es el choque, y lo que se mide es su efecto
  directo en los precios.
- **Eneros normales:** cada enero las cuotas se actualizan con la inflación y muchos precios se ajustan; eso se
  quita comparando con los eneros de 2021 a 2025. Quedan fuera 2019 (el IVA de la frontera bajó a 8 %, y los
  refrescos y cigarros pagan IVA y casi ningún alimento) y 2020 (la cuota de los cigarros saltó de 0.35 a 0.4944
  pesos; el cálculo lo detecta: +4.3 %).
- **Placebos:** con un solo enero tratado no hay un error estándar confiable. La prueba es repetir la cuenta con
  cada producto de comparación como si hubiera pagado el impuesto (y con canastas al azar de ellos), y con cada
  enero anterior.
- **Traslado:** si todo el impuesto llega al consumidor, el litro de refresco sube 1.16 × (3.0818 − 1.6451 ×
  1.036) pesos respecto a un enero normal: 8.6 % del precio por litro, que sale de la ENIGH (gasto entre litros).
  En los cigarros, con cajetillas de 60 a 100 pesos, 17 a 19 %.
- **Hogares:** el efecto de cada producto se pondera con su peso en la canasta de cada decil (ENIGH 2022
  calibrada, a precios de diciembre de 2025). El intervalo sale de sumarle a cada efecto el ruido de los placebos.
- **Por qué no comparar directamente el índice de cada decil:** ese índice junta el impuesto con todo lo que pasó
  ese mes. En enero de 2026 los pecuarios bajaron más en la canasta del decil I y tapan parte del efecto.
- **Límites:** los refrescos subieron cerca de 0.8 % en diciembre de 2025, antes del impuesto (anticipación); los
  cigarros ya venían subiendo más que lo normal desde julio de 2025 y, sin esa tendencia, su efecto baja de 14.5 a
  9.7 %. El azúcar subió en diciembre, pero los dulces y panes, que llevan mucha azúcar y no pagan la cuota, no se
  movieron. La incidencia no cuenta que los hogares compren menos por el impuesto, y el precio por litro de la
  ENIGH mezcla presentaciones distintas a las que sigue el INPC.

Con el impuesto de 2014 (un peso por litro), los precios de los refrescos subieron un poco más que el impuesto
(Colchero y otros, 2015, *PLoS ONE*).

### Del mayoreo a la canasta

La brecha entre el decil I y el X sube y baja sobre todo con las frutas y verduras. Esta pestaña mide de dónde
vienen esos saltos: cuánto de un aumento del precio al mayoreo en la Central de Abasto llega al precio al
consumidor, en cuántos meses y a qué decil.

- **Índices:** cada producto del SNIIM (producto, calidad, presentación y origen) se asigna a uno de 30 genéricos
  de frutas y verduras del INPC (falta el frijol, que no está en esa sección del SNIIM). Su cambio mensual se
  promedia dentro del genérico y se encadena. Al consumidor se usa el índice nacional de cada genérico. En el
  archivo del SNIIM faltan junio de 2020 y enero de 2021.
- **Proyecciones locales (Jordà, 2005):** para cada horizonte h de 0 a 12 meses, el cambio del precio al
  consumidor de t − 1 a t + h se regresa contra el cambio al mayoreo en t, con tres rezagos de ambos, efectos
  fijos de producto × mes del año (la temporada) y de mes (lo que mueve a todos a la vez: inflación general, tipo
  de cambio, demanda). El coeficiente se identifica con los choques propios de cada producto, que en perecederos
  vienen sobre todo de la oferta (clima, plagas, cosechas). Se pondera con el INPC y los errores son de Driscoll y
  Kraay (1998), robustos a correlación entre productos y entre meses.
- **Por decil:** un salto de 10 % al mayoreo de todas las frutas y verduras sube la canasta de cada decil en
  10 × suma de (peso del producto en su gasto × su traslado). La comprobación directa es una proyección local de
  la brecha entre los deciles I y X contra el índice de mayoreo (errores de Newey y West).
- **Historia:** con el traslado de cada producto (rezagos distribuidos de 0 a 2 meses), el cambio anual al mayoreo
  predice el cambio anual al consumidor; con las canastas de los deciles, eso da la parte de la brecha que viene
  de la Central de Abasto.
- **Sequía:** del Monitor de Sequía de México (Conagua, base de municipios, quincenal) sale un índice de 0 a 5 por
  estado y mes. Cada producto se expone a la sequía de los estados de donde llegaba a la Central de Abasto en ese
  mes del año entre 2012 y 2017 (un instrumento de participaciones fijas). Se usa de dos formas: la respuesta de
  los precios a la sequía (forma reducida) y el traslado con la sequía como instrumento del salto al mayoreo.
- **Límites:** la sequía es un instrumento débil (F de 9 a 12) y su efecto inmediato es bajar el precio, no subirlo;
  el índice no pondera por superficie sembrada ni distingue el riego. El mayoreo es solo el de la Ciudad de
  México, los pecuarios no están y el traslado de la historia se estima con los mismos datos.

### Un experimento: la frontera norte

La pestaña de la frontera mide otro efecto: el 1 de enero de 2019 entró en vigor el
Decreto de estímulos fiscales región fronteriza norte (Diario Oficial de la Federación, 31 de diciembre de
2018) en 43 municipios de seis estados. El IVA bajó de 16 a 8 % y el ISR de las empresas de la zona, un
tercio; el mismo día su salario mínimo se duplicó. Baja California entera está en la zona, y con ella las
dos ciudades donde el INPC levanta sus precios (Tijuana y Mexicali).

- **Comparación:** los precios de Baja California contra los de las 26 entidades que no tocan la frontera,
  producto por producto, de julio de 2018 a diciembre de 2019 (diferencias en diferencias). Un recorte que
  llega completo al consumidor baja el precio 6.9 % (1.08 / 1.16).
- **Con IVA y sin IVA:** los 292 genéricos se clasificaron con la Ley del IVA. Los alimentos y las medicinas
  pagan tasa 0 %, y las rentas, las colegiaturas y el transporte público están exentos: ahí no debía pasar
  nada, y sirven de segunda comparación (triple diferencia).
- **Placebos:** con una sola entidad tratada no hay un error estándar confiable. La prueba es repetir la
  cuenta con cada una de las 26 entidades de comparación como si fuera la tratada; el valor p más chico
  posible es 1 entre 27 (0.04).
- **Dosis:** en Tamaulipas, Chihuahua y Coahuila solo una de las ciudades del INPC está en la zona, y en
  Sonora y Nuevo León ninguna. Lo que pesa la ciudad tratada en el índice del estado se mide con la
  electricidad, cuya tarifa regulada pasa el recorte íntegro.
- **Hogares:** la canasta de cada decil de Baja California (ENIGH 2018) se valúa con sus precios y con los
  de cada entidad de comparación.
- **Límites:** es el efecto del paquete entero (IVA, ISR, salario mínimo y estímulo a la gasolina), medido
  solo en precios y solo en 2019; seis meses previos es poco para descartar tendencias distintas; la
  telefonía, los seguros y las computadoras tienen un precio nacional en el INPC y no pueden mostrar nada.
  Después de 2019 la diferencia en las mercancías se redujo; en 2020 coincidieron la depreciación del peso
  y las restricciones al cruce de la frontera, y con estos datos no se puede saber cuánto del traslado fue
  duradero.

El efecto promedio de este paquete sobre la inflación ya fue estudiado, entre otros, por Campos-Vázquez y
Esquivel (2020, *Economics Letters*) y por Calderón, Cortés, Pérez Pérez y Salcedo (2023, *Labour Economics*).

### Advertencias

- Dentro de una misma entidad y producto, todos los hogares enfrentan el mismo índice: las diferencias de
  calidad, marca o tienda no se ven.
- INEGI advierte que los índices desagregados por entidad y genérico solo tienen valor informativo.
- Los quintiles y deciles son nacionales y se definen con el ingreso corriente del hogar.
- En «Ponderadores» se pueden ver las variantes de cálculo; el tamaño de la brecha cambia, pero no su
  signo ni el momento en que se revierte.

### Autores

Oscar Daniel Hernández Romero y Kevin Mejía Rodríguez. Proyecto de Visualización de Datos, 2026.
Cálculos propios con datos de INEGI.
"""

panel_metodo = ui.nav_panel("Método", ui.div(ui.markdown(METODO), class_="metodo"))

app_ui = ui.page_navbar(
    panel_ingreso, panel_porque, panel_impuestos, panel_mayoreo, panel_entidad, panel_frontera, panel_tu, panel_metodo,
    title="¿De quién es la inflación?",
    id="pestana",
    header=ui.head_content(ui.tags.script(src="plotly.min.js"), ui.include_css(AQUI / "www" / "estilos.css")),
    footer=ui.div("Fuente: cálculos propios con datos de INEGI (INPC por entidad y genérico, ENIGH 2018 y 2022, "
                  "Marco Geoestadístico). Julio de 2018 a " + D.mes(D.FIN, largo=True) + ".", class_="pie"),
    fillable=False,
    navbar_options=ui.navbar_options(bg="#FFFFFF", theme="light"),
    lang="es",
)


# ============================================================================ servidor
def server(input, output, session):
    # ------------------------------------------------------------ por ingreso
    @reactive.calc
    def dec_ancho():
        d = D.ind_dec[(D.ind_dec["variante"] == input.dec_variante()) & (D.ind_dec["rubro"] == input.dec_rubro())]
        return d.pivot(index="fecha", columns="decil", values=input.dec_medida()).dropna()

    @render.ui
    def dec_tarjetas():
        a = dec_ancho()
        f, u = a.index[-1], a.iloc[-1]
        nota = f"{MEDIDAS[input.dec_medida()].lower()}, {D.mes(f)}"
        return ui.div(tarjeta("Decil I (menor ingreso)", pct(u[1]), nota, "guinda"),
                      tarjeta("Decil X (mayor ingreso)", pct(u[10]), nota, "azul"),
                      tarjeta("Todos los hogares", pct(u[0]), nota),
                      tarjeta("Brecha: I menos X", pp(u[1] - u[10]), "puntos porcentuales"), class_="tarjetas")

    @render.ui
    def dec_lineas():
        return ui.HTML(F.html(F.lineas_deciles(dec_ancho())))

    @render.ui
    def dec_brecha():
        a = dec_ancho()
        return ui.HTML(F.html(F.brecha_simple(a[1] - a[10])))

    # ------------------------------------------------------------ por qué
    @reactive.calc
    def pq():
        a, b = (int(x) for x in input.pq_comp().split("-"))
        tot = D.brecha_dec[(D.brecha_dec["grupo_a"] == a) & (D.brecha_dec["grupo_b"] == b)]
        det = D.brecha_det[(D.brecha_det["grupo_a"] == a) & (D.brecha_det["grupo_b"] == b)]
        inicio, fin = D.ACUMULADOS[input.pq_periodo()]
        es = lambda d: d[(d["periodo"] == "acumulada") & (d["inicio"] == inicio) & (d["fin"] == fin)]
        return {"a": a, "b": b, "tot": tot, "det": det, "tot_acum": es(tot).iloc[0], "det_acum": es(det),
                "inicio": inicio, "fin": fin}

    @render.ui
    def pq_tarjetas():
        p = pq()
        t = p["tot_acum"]
        nombre_b = "Todos los hogares" if p["b"] == 0 else f"Decil {D.ROMANOS[p['b']]}"
        return ui.div(tarjeta(f"Decil {D.ROMANOS[p['a']]}", pct(t["inflacion_a"]), "inflación acumulada", "guinda"),
                      tarjeta(nombre_b, pct(t["inflacion_b"]), "inflación acumulada", "azul"),
                      tarjeta("Brecha", pp(t["brecha"]), "puntos porcentuales"),
                      tarjeta("Por la canasta", pp(t["canasta"]), "compran cosas distintas"),
                      tarjeta("Por el lugar", pp(t["lugar"]), "viven en entidades distintas"), class_="tarjetas")

    @render.ui
    def pq_tiempo():
        p = pq()
        anual = p["det"][p["det"]["periodo"] == "anual"]
        total = p["tot"][p["tot"]["periodo"] == "anual"].set_index("fin")["brecha"]
        return ui.HTML(F.html(F.brecha_tiempo(anual, total)))

    @render.ui
    def pq_acumulada():
        return ui.HTML(F.html(F.brecha_acumulada(pq()["det_acum"])))

    @render.ui
    def pq_productos():
        p = pq()
        if (p["a"], p["b"]) != (1, 10):
            return ui.p("El detalle por producto está calculado para la comparación del decil I contra el decil X.",
                        class_="ayuda")
        n = D.brecha_nodos[(D.brecha_nodos["inicio"] == p["inicio"]) & (D.brecha_nodos["fin"] == p["fin"])]
        return ui.HTML(F.html(F.productos(n)))

    # ------------------------------------------------------------ por entidad
    @reactive.calc
    def ent():
        que, periodo, f = input.ent_que(), input.ent_periodo(), D.a_mes(input.ent_mes())
        if que == "inflacion":
            medida = "inflacion_anual" if periodo == "anual" else "acumulada"
            ancho = D.ancha(input.ent_quintil(), input.ent_rubro(), medida).dropna()
            f = min(max(f, ancho.index[0]), ancho.index[-1])
            serie = ancho.loc[f]
            estados = serie.drop(D.PAIS)
            rango = [float(estados.min()), float(estados.max())]
            anual = D.ancha(input.ent_quintil(), input.ent_rubro(), "inflacion_anual").dropna()
            titulo = f"{MEDIDAS[medida]}, {D.mes(f)}" if periodo == "anual" else f"Inflación acumulada, {D.mes(D.BASE)} a {D.mes(f)}"
            return {"serie": serie, "anual": anual, "fecha": f, "divergente": False, "rango": rango, "sufijo": " %",
                    "titulo": titulo, "barra": "Inflación"}
        e = D.brecha_ent
        anual = e[e["periodo"] == "anual"].pivot(index="fin", columns="cve_ent", values=que)
        if periodo == "anual":
            f = min(max(f, anual.index[0]), anual.index[-1])
            serie = anual.loc[f]
            tope = float(serie.abs().max())
            titulo = f"{QUE[que]}, inflación anual a {D.mes(f)}"
        else:
            serie = e[(e["periodo"] == "acumulada") & (e["inicio"] == D.BASE) & (e["fin"] == D.FIN)].set_index("cve_ent")[que]
            f, tope = D.FIN, float(serie.abs().max())
            titulo = f"{QUE[que]}, inflación acumulada de {D.mes(D.BASE)} a {D.mes(D.FIN)}"
        return {"serie": serie, "anual": anual, "fecha": f, "divergente": True, "rango": [-tope, tope], "sufijo": " pp",
                "titulo": titulo, "barra": QUE[que]}

    @render.text
    def ent_titulo():
        return ent()["titulo"]

    @render.ui
    def ent_ayuda():
        textos = {
            "inflacion": "Inflación de los hogares que viven en cada entidad, con su propia canasta y los precios de su entidad.",
            "brecha": "Inflación de los hogares de la entidad menos la de todos los hogares del país.",
            "canasta": "Parte de la diferencia contra el país que se debe a que en la entidad se compra una canasta distinta.",
            "lugar": "Parte de la diferencia contra el país que se debe a que los mismos productos subieron distinto en la entidad.",
        }
        extra = "" if input.ent_que() == "inflacion" or input.ent_periodo() == "anual" else \
            " El acumulado de estos efectos se calcula para todo el periodo; el deslizador no lo cambia."
        return ui.p(textos[input.ent_que()] + extra, class_="ayuda")

    @render.ui
    def ent_tarjetas():
        x = ent()
        s = x["serie"].drop(D.PAIS, errors="ignore")
        fmt = (lambda v: f"{v:+.1f}{x['sufijo']}") if x["divergente"] else (lambda v: f"{v:.1f}{x['sufijo']}")
        sel = input.ent_sel()
        t = [tarjeta("La más alta", fmt(s.max()), D.NOMBRE[s.idxmax()], "guinda"),
             tarjeta("La más baja", fmt(s.min()), D.NOMBRE[s.idxmin()], "azul"),
             tarjeta(D.NOMBRE[sel], fmt(s[sel]), f"lugar {int(s.rank(ascending=False)[sel])} de 32")]
        if D.PAIS in x["serie"].index:
            t.insert(2, tarjeta("País", fmt(x["serie"][D.PAIS]), "todas las entidades"))
        else:
            t.insert(2, tarjeta("Distancia entre extremos", f"{s.max() - s.min():.1f} pp", "la más alta menos la más baja"))
        return ui.div(*t, class_="tarjetas")

    @render.ui
    def ent_mapa():
        x = ent()
        return ui.HTML(F.html(F.mapa(x["serie"], x["divergente"], x["rango"], input.ent_sel(), x["sufijo"], x["barra"])))

    @render.ui
    def ent_ranking():
        x = ent()
        return ui.HTML(F.html(F.ranking(x["serie"], x["divergente"], x["rango"], input.ent_sel(), x["sufijo"])))

    @render.ui
    def ent_series():
        x = ent()
        return ui.HTML(F.html(F.series_entidades(x["anual"], input.ent_sel(), x["sufijo"], x["divergente"])))

    # ------------------------------------------------------------ un experimento: la frontera
    @reactive.calc
    def fr():
        k = input.fr_tipo()
        return {"canasta": k, "clase": D.FR_CLASE[k], "medidas": D.fr_resumen[D.fr_resumen["canasta"] == k].set_index("medida")}

    @render.ui
    def fr_tarjetas():
        x = fr()
        m = x["medidas"]
        uno = m.loc[D.FR_PRINCIPAL]
        if x["clase"] == "sin IVA":
            tercera = tarjeta("IVA de estos productos", "Sin cambio", "tasa 0 % o exentos: aquí no debía pasar nada")
        elif pd.isna(uno["traslado"]):
            tercera = tarjeta("Recorte completo del IVA", pct(D.FR_TRASLADO, True),
                              "aquí se suma el estímulo al IEPS de la franja" if x["canasta"] == "Gasolinas"
                              else "lo que bajaría un precio con IVA")
        else:
            tercera = tarjeta("Llegó al precio", f"{100 * uno['traslado']:.0f} %",
                              f"del recorte del IVA, que completo sería {D.FR_TRASLADO:.1f} %")
        lugar = int(uno["rango"])
        distinto = "ninguna de las 26 sin la política bajó tanto" if lugar == 1 else \
            "ninguna de las 26 sin la política subió tanto" if lugar == 27 else "no se distingue de las 26 sin la política"
        return ui.div(tarjeta("Un año después", pct(uno["efecto"], True), "jul-dic de 2019 contra jul-dic de 2018", "guinda"),
                      tarjeta("A los tres meses", pct(m.loc["mar-2019", "efecto"], True), "marzo de 2019 contra diciembre de 2018"),
                      tercera,
                      tarjeta("Lugar entre 27 entidades", f"{lugar}", f"{distinto} (p = {uno['valor_p']:.2f})"), class_="tarjetas")

    @render.text
    def fr_titulo():
        return f"{fr()['canasta']}: Baja California contra las entidades que no tocan la frontera"

    @render.ui
    def fr_eventos():
        x = fr()
        a = D.fr_ancha(x["canasta"])
        a = a[[c for c in a.columns if c == D.FR_TRATADA or c not in D.FR_FRONTERIZAS]]
        con_referencia = x["clase"] == "con IVA" or x["clase"] == "comparación"
        return ui.HTML(F.html(F.frontera_eventos(a, D.FR_TRATADA, D.FR_INICIO, D.FR_TRASLADO if con_referencia else None)))

    @render.ui
    def fr_tipos():
        r = D.fr_resumen[(D.fr_resumen["medida"] == D.FR_PRINCIPAL) & (D.fr_resumen["clase"] != "comparación")]
        return ui.HTML(F.html(F.frontera_tipos(r, fr()["canasta"], D.FR_TRASLADO)))

    @reactive.calc
    def fr_frontera():
        efecto = D.fr_efectos(fr()["canasta"])
        e = D.fr_estados.assign(efecto=lambda d: d["cve_ent"].map(efecto))
        e["esperado"] = e["dosis"] * efecto[D.FR_TRATADA]
        placebos = efecto.drop(D.FR_FRONTERIZAS)
        return e, (float(placebos.quantile(0.05)), float(placebos.quantile(0.95)))

    @render.text
    def fr_titulo_estados():
        return f"{fr()['canasta']}: los seis estados de la frontera"

    @render.ui
    def fr_estados():
        return ui.HTML(F.html(F.frontera_estados(*fr_frontera())))

    @render.ui
    def fr_nota_estados():
        e, _ = fr_frontera()
        parciales = e[e["papel"] == "parcial"]
        return ui.p("Ciudades donde el INPC levanta precios en cada estado y cuántas están en la zona del decreto. La marca "
                    "negra es el efecto de Baja California por el peso de la ciudad tratada en el índice del estado ("
                    + ", ".join(f"{r.entidad} {r.dosis:.2f}" for r in parciales.itertuples())
                    + "), medido con la electricidad, cuya tarifa es regulada y pasa el recorte íntegro.", class_="nota-grafica")

    @reactive.calc
    def fr_deciles():
        d = D.fr_incidencia[D.fr_incidencia["corte"] == "decil"]
        partes = d[d["tipo"] != "Total"]
        orden = list(dict.fromkeys(d["nivel"]))
        ancho = lambda columna: partes.pivot(index="nivel", columns="tipo", values=columna).loc[orden, D.FR_TIPOS]
        return ancho("efecto"), d[d["tipo"] == "Total"].set_index("nivel").loc[orden], ancho("participacion")

    @render.ui
    def fr_incidencia():
        return ui.HTML(F.html(F.frontera_incidencia(*fr_deciles())))

    @render.ui
    def fr_nota_incidencia():
        _, total, _ = fr_deciles()
        t = D.fr_incidencia[D.fr_incidencia["tipo"] == "Total"].set_index("nivel")
        dif = t.loc["Decil X menos decil I"]
        return ui.p(f"Julio a diciembre de 2019 contra los mismos meses de 2018. Canasta de la ENIGH 2018 de los hogares de Baja "
                    f"California en cada decil nacional de ingreso (de {total['hogares_muestra'].min():.0f} a "
                    f"{total['hogares_muestra'].max():.0f} hogares en la muestra), valuada con sus precios y con los de cada "
                    f"entidad sin la política. Todos los hogares juntos: {t.loc['todos', 'efecto']:+.1f} %. La diferencia entre "
                    f"el decil X y el I ({dif['efecto']:+.1f} puntos) viene de la gasolina y no se distingue de lo que pasa en "
                    f"las entidades sin la política (p = {dif['valor_p']:.2f}). No cuenta lo que el salario mínimo hizo con los "
                    "ingresos.", class_="nota-grafica")

    # ------------------------------------------------------------ un experimento: refrescos y cigarros
    @reactive.calc
    def im():
        k = input.im_producto()
        return {"canasta": k, "medidas": D.im_resumen[D.im_resumen["canasta"] == k].set_index("medida"),
                "comprobacion": k in D.IM_COMPROBACIONES, "esperado": D.im_esperado(k)}

    @render.ui
    def im_tarjetas():
        x = im()
        m = x["medidas"]
        uno = m.loc[D.IM_PRINCIPAL]
        t = x["esperado"]
        if x["comprobacion"]:
            tercera = tarjeta("Impuesto de este producto", "Sin cambio", "si se mueve, no es por la cuota nueva")
        elif t is not None:
            completo = (t["esperado_min"] + t["esperado_max"]) / 2
            rango = (f"{t['esperado_min']:.0f} a {t['esperado_max']:.0f} %" if t["esperado_max"] - t["esperado_min"] > 0.5
                     else f"{completo:.1f} %")
            tercera = tarjeta("Llegó al precio", f"{100 * uno['efecto'] / completo:.0f} %",
                              f"del impuesto completo, que subiría el precio {rango}")
        else:
            tercera = tarjeta("Sin impuesto nuevo", f"{uno['placebo_p05']:+.1f} a {uno['placebo_p95']:+.1f} %",
                              "donde caen nueve de cada diez productos de comparación")
        n = int(uno["n_placebos"])
        if n == D.IM_COMPARACION:                                     # un producto: lugar entre los de comparación
            lugar = int(uno["lugar"])
            texto = ("ninguno sin impuesto nuevo subió tanto" if lugar == 1
                     else f"{lugar - 1} sin impuesto nuevo subieron más")
            cuarta = tarjeta(f"Lugar entre {n + 1} productos", f"{lugar}", f"{texto} (p = {uno['valor_p']:.2f})")
        else:                                                         # canasta: contra canastas al azar
            p = uno["valor_p"]
            cuarta = tarjeta("Contra canastas al azar", "p < 0.001" if p < 0.001 else f"p = {p:.2f}",
                             f"{n:,} canastas de productos sin impuesto nuevo, con los mismos pesos")
        return ui.div(tarjeta("En 2026", pct(uno["efecto"], True), "enero a septiembre, contra un enero normal", "guinda"),
                      tarjeta("En septiembre", pct(m.loc["sep-2026", "efecto"], True), "contra diciembre de 2025"),
                      tercera, cuarta, class_="tarjetas")

    @render.text
    def im_titulo():
        return f"{im()['canasta']}: precio contra {D.IM_COMPARACION} alimentos y bebidas sin impuesto nuevo"

    @render.ui
    def im_eventos():
        x = im()
        t, referencia = x["esperado"], None
        if t is not None:
            v = (t["esperado_min"] + t["esperado_max"]) / 2
            referencia = (v, f"Si todo el impuesto llegara al precio: {v:+.1f} %")
        return ui.HTML(F.html(F.impuestos_eventos(D.im_trayectoria(x["canasta"]), D.im_placebos_ancha, D.IM_INICIO,
                                                  x["canasta"], referencia)))

    @render.ui
    def im_nota_eventos():
        k = im()["canasta"]
        m = im()["medidas"]
        texto = ("Diferencia contra los productos de comparación, después de quitar lo que el producto se mueve en un enero "
                 "normal; diciembre de 2025 es el punto de partida. Cada línea gris es un producto de comparación contra los "
                 "demás: lo que se mueve la cuenta donde no hubo impuesto nuevo.")
        extra = {
            "Refrescos": f" En diciembre, antes del impuesto, ya subieron {m.loc['dic-2025', 'efecto']:.1f} % más que lo normal "
                         f"(anticipación); contando desde noviembre, el efecto es {m.loc['ene-sep 2026 contra nov-2025', 'efecto']:+.1f} %.",
            "Cigarros": f" Desde julio de 2025 ya subían más que lo normal; si esa tendencia hubiera seguido, el efecto sería "
                        f"{m.loc['ene-sep 2026 sin tendencia previa', 'efecto']:+.1f} % en lugar de {m.loc[D.IM_PRINCIPAL, 'efecto']:+.1f} %.",
            "Azúcar (no paga)": " El azúcar no paga la cuota y subió en diciembre de 2025, antes del impuesto. Los dulces y panes, "
                                "que llevan mucha azúcar, no se movieron: el salto de los refrescos no parece venir del costo del azúcar.",
            "Concentrados para refrescos": " Pagan por cada litro de bebida que rinden: en un sobre barato, la cuota pesa mucho.",
        }
        return ui.p(texto + extra.get(k, ""), class_="nota-grafica")

    @render.ui
    def im_incidencia():
        inc = D.im_incidencia.set_index("nivel").loc[D.ROMANOS[1:]].reset_index()
        return ui.HTML(F.html(F.impuestos_incidencia(inc)))

    @render.ui
    def im_nota_incidencia():
        t = D.im_incidencia.set_index("nivel")
        g = t.loc["Decil I menos decil X"]
        return ui.p(f"Efecto promedio de enero a septiembre de 2026 de las bebidas y los cigarros con impuesto nuevo en el costo de "
                    f"la canasta de cada decil (ENIGH 2022 calibrada, a precios de diciembre de 2025). Todos los hogares: "
                    f"{t.loc['Todos', 'efecto']:+.2f} %. Como parte de su gasto, el decil I paga {g['razon']:.1f} veces lo del X "
                    f"({g['efecto']:+.2f} puntos de diferencia; de {g['efecto_p05']:.2f} a {g['efecto_p95']:.2f} con el ruido de los "
                    f"placebos). En pesos es al revés: {t.loc['I', 'pesos_mes']:.0f} pesos más al mes por hogar en el decil I y "
                    f"{t.loc['X', 'pesos_mes']:.0f} en el X. La diferencia entre deciles viene de los refrescos; los cigarros pesan "
                    f"parecido en todos. El litro de refresco cuesta casi lo mismo en todos los deciles ({t.loc['I', 'precio_litro']:.1f} "
                    f"pesos en el I y {t.loc['X', 'precio_litro']:.1f} en el X), así que una cuota por litro no agrega desigualdad "
                    "por ese lado. No cuenta que los hogares compren menos por el impuesto.", class_="nota-grafica")

    @render.text
    def im_titulo_eneros():
        return f"{im()['canasta']}: cada enero contra lo normal"

    @render.ui
    def im_eneros():
        k = im()["canasta"]
        e = D.im_eneros[D.im_eneros["canasta"] == k].dropna(subset=["efecto"])
        especial = (2020, "2020: subió la cuota del cigarro") if k in ("Cigarros", "Bebidas y cigarros") else None
        return ui.HTML(F.html(F.impuestos_eneros(e, especial)))

    @render.ui
    def im_nota_eneros():
        texto = ("El mismo cálculo con cada enero desde 2019, como si en él hubiera entrado el impuesto. La referencia son los "
                 "eneros de 2021 a 2025; quedan fuera 2019, por el IVA de la frontera, y 2020, porque la cuota de los cigarros "
                 "saltó de 0.35 a 0.49 pesos (y el cálculo lo detecta).")
        if im()["canasta"] == "Bebidas energéticas":
            texto += " Las bebidas energéticas entraron al INPC en 2024: solo tienen el enero de 2025 para comparar."
        return ui.p(texto, class_="nota-grafica")

    @render.ui
    def im_directo():
        return ui.HTML(F.html(F.impuestos_directo(D.im_directo)))

    @render.ui
    def im_nota_directo():
        d = D.im_directo.set_index("decil").loc["I menos X"]
        return ui.p(f"Enero de 2026 contra los eneros de 2021 a 2025 en el índice de cada decil (el rombo), repartido por tipo "
                    f"de producto. El índice del decil junta el impuesto con todo lo que pasó ese enero: comparado así, el decil "
                    f"I contra el X da {d['directo']:+.2f} puntos, cuando el impuesto aporta {d['Pagaron más impuesto']:+.2f}; los "
                    "pecuarios bajaron más en la canasta del decil I y tapan parte del efecto. Por eso el efecto se mide producto "
                    "por producto y después se reparte con la canasta de cada decil.", class_="nota-grafica")

    # ------------------------------------------------------------ del mayoreo a la canasta
    @reactive.calc
    def my():
        k, h = input.my_producto(), int(input.my_h())
        return {"producto": k, "h": h, "curva": D.my_curva(k), "promedio": D.my_curva(D.MY_PROMEDIO),
                "deciles": D.my_deciles[D.my_deciles["h"] == h].set_index("decil").loc[D.ROMANOS[1:]].reset_index()}

    @render.ui
    def my_tarjetas():
        x = my()
        c, h = x["curva"], x["h"]
        d = x["deciles"].set_index("decil")["respuesta_por_producto"]
        sujeto = "en promedio" if x["producto"] == D.MY_PROMEDIO else x["producto"]
        return ui.div(
            tarjeta("El mismo mes", f"{c.loc[0, 'b']:.0f} %", f"del salto al mayoreo llega al consumidor ({sujeto})"),
            tarjeta(cuando(h).capitalize(), f"{c.loc[h, 'b']:.0f} %", f"intervalo de {c.loc[h, 'bajo']:.0f} a {c.loc[h, 'alto']:.0f} %"),
            tarjeta("Decil I contra decil X", f"{d['I'] / d['X']:.1f} veces",
                    f"un salto de 10 % al mayoreo sube su canasta {d['I']:.2f} y {d['X']:.2f} % {cuando(h)}", "guinda"),
            tarjeta("Lo que explica el mayoreo", f"{D.MY_AJUSTE:.2f}",
                    "correlación con lo que las frutas y verduras pusieron en la brecha I menos X"),
            class_="tarjetas")

    @render.text
    def my_titulo():
        return f"{my()['producto']}: cuánto del salto al mayoreo llega al consumidor"

    @render.ui
    def my_traslado():
        x = my()
        es_promedio = x["producto"] == D.MY_PROMEDIO
        return ui.HTML(F.html(F.mayoreo_traslado(x["curva"], x["h"], x["producto"], None if es_promedio else x["promedio"],
                                                 D.my_vi[D.my_vi["h"] <= 2] if es_promedio else None)))

    @render.ui
    def my_nota_traslado():
        t = D.my_traslado.set_index("h")
        texto = (f"Proyecciones locales con {D.MY_GENERICOS} frutas y verduras, de noviembre de 2018 a septiembre de 2026, "
                 "ponderadas con el INPC; el intervalo usa errores de Driscoll y Kraay. La curva baja después del primer mes "
                 f"porque los saltos al mayoreo se revierten: a los seis meses el propio mayoreo conserva "
                 f"{100 * t.loc[6, 'mayoreo_propio']:.0f} % del salto. Si se quedara arriba, al consumidor llegaría "
                 f"{100 * t.loc[D.MY_H, 'rezagos_distribuidos']:.0f} % (rezagos distribuidos).")
        if my()["producto"] != D.MY_PROMEDIO:
            texto += " Cada producto tiene su propia curva en la misma regresión; la línea punteada es el promedio."
        else:
            v = D.my_vi.set_index("h")
            texto += (f" Los rombos (meses 0 a 2; después el intervalo es demasiado ancho) usan la sequía de los estados de "
                      f"origen como instrumento (F de la primera etapa de "
                      f"{v['F'].min():.0f} a {v['F'].max():.0f}): {100 * v.loc[0, 'b_vi']:.0f} % el mismo mes y "
                      f"{100 * v.loc[1, 'b_vi']:.0f} % al siguiente, al menos lo mismo que sin instrumento; no es la tienda "
                      "jalando al mayoreo.")
        return ui.p(texto, class_="nota-grafica")

    @render.text
    def my_titulo_deciles():
        return f"Un salto de 10 % al mayoreo de todas las frutas y verduras, {cuando(my()['h'])}"

    @render.ui
    def my_deciles():
        return ui.HTML(F.html(F.mayoreo_deciles(my()["deciles"], "respuesta_por_producto", "ee_por_producto")))

    @render.ui
    def my_nota_deciles():
        x = my()
        d = x["deciles"].set_index("decil")
        b = D.my_brecha[(D.my_brecha["serie"] == "Decil I menos decil X") & (D.my_brecha["h"] == x["h"])].iloc[0]
        suma = d.loc["I", "respuesta_por_producto"] - d.loc["X", "respuesta_por_producto"]
        return ui.p(f"Efecto en el costo de la canasta, con el traslado de cada producto y su peso en el gasto de cada decil "
                    f"(ENIGH 2022 calibrada, a precios de septiembre de 2026): estas frutas y verduras son "
                    f"{d.loc['I', 'participacion']:.1f} % del gasto del decil I y {d.loc['X', 'participacion']:.1f} % del X. "
                    f"Comprobación directa: la brecha entre el decil I y el X sube {b['b']:.2f} puntos {cuando(x['h'])} de un "
                    f"salto de 10 % en el índice de mayoreo (proyección local de la brecha; producto por producto da {suma:.2f}). "
                    "La directa da más porque el índice de mayoreo se mueve junto con otros alimentos.", class_="nota-grafica")

    @render.ui
    def my_historia():
        return ui.HTML(F.html(F.mayoreo_historia(D.my_historia)))

    @render.ui
    def my_nota_historia():
        return ui.p("Diferencia entre la inflación anual del decil I y la del X (gris); la parte que pusieron estas frutas y "
                    "verduras con sus precios al consumidor (verde), y la que predice el mayoreo con el traslado de cada "
                    f"producto (punteada). Correlación entre estas dos: {D.MY_AJUSTE:.2f}. La subida de 2024 y la caída de 2025 "
                    "vienen de la Central de Abasto; los saltos de la brecha en 2020 y en 2022 a 2023 vienen de otros productos. "
                    "El traslado se estima con los mismos datos.", class_="nota-grafica")

    @render.ui
    def my_sequia():
        return ui.HTML(F.html(F.mayoreo_sequia(D.my_sequia, D.MY_H_SEQUIA)))

    @render.ui
    def my_nota_sequia():
        s = D.my_sequia.set_index(["serie", "h"])["b"]
        a = D.my_sequia_anual.set_index(["serie", "rezago"])
        return ui.p("Respuesta a un punto más de sequía (índice de 0 a 5, promedio de los municipios) en los estados de donde "
                    "suele venir cada producto, según el SNIIM de 2012 a 2017; entre mayo de 2023 y mayo de 2024 esa exposición "
                    f"subió 1.6 puntos. En los dos primeros meses el mayoreo baja {abs(s[('mayoreo', 0)]):.0f} a "
                    f"{abs(s[('mayoreo', 1)]):.0f} % y el consumidor {abs(s[('consumidor', 0)]):.0f} a "
                    f"{abs(s[('consumidor', 1)]):.0f} %. Una explicación posible: con sequía se cosecha y se vende antes, y no "
                    "hay lluvias que dañen lo sembrado. En cambios anuales, un año después el mayoreo sube "
                    f"{a.loc[('mayoreo', 12), 'b']:.0f} % (quizá porque se siembra menos), pero mes a mes eso no es estable. "
                    "La sequía no explica los saltos de precio como un choque inmediato; los de 2024 tendrían que venir de "
                    "otra cosa (calor, lluvias, lo que se dejó de sembrar), que con estos datos no se puede separar.",
                    class_="nota-grafica")

    @render.text
    def my_titulo_productos():
        return f"Lo que más compra el decil I es lo que más traslada ({cuando(my()['h'])})"

    @render.ui
    def my_productos():
        x = my()
        t = D.my_traslado_prod[D.my_traslado_prod["h"] == x["h"]].set_index("generico")["b"]
        p = D.my_productos.assign(dif=lambda d: d["peso_decil_I"] - d["peso_decil_X"],
                                  traslado=lambda d: 100 * d["generico"].map(t))
        return ui.HTML(F.html(F.mayoreo_productos(p, x["producto"])))

    # ------------------------------------------------------------ tu inflación
    @reactive.effect
    @reactive.event(input.tu_ent, input.tu_quintil, input.tu_reset)
    def _restablecer():
        c = canasta(input.tu_ent(), input.tu_quintil())
        for r in RUBROS8:
            ui.update_slider(f"tu_r{r}", value=round(float(c[r])))

    @reactive.calc
    def tu():
        w = np.array([input[f"tu_r{r}"]() for r in RUBROS8], float)
        suma = w.sum()
        w = w / suma if suma > 0 else canasta(input.tu_ent(), input.tu_quintil()).to_numpy() / 100
        d = D.ind_ent[(D.ind_ent["cve_ent"] == input.tu_ent()) & (D.ind_ent["quintil"] == int(input.tu_quintil()))
                      & D.ind_ent["rubro"].isin(RUBROS8)]
        d = d.pivot(index="fecha", columns="rubro", values="indice")[RUBROS8]
        indice = (d * w).sum(axis=1)
        anual = (100 * indice.pct_change(12)).dropna()
        aportes = pd.Series(100 * w * (d.iloc[-1] - d.iloc[-13]).to_numpy() / indice.iloc[-13],
                            index=[D.RUBRO[r] for r in RUBROS8])
        pais = D.ancha(0, "0", "inflacion_anual")[D.PAIS].dropna()
        return {"suma": suma, "indice": indice, "anual": anual, "aportes": aportes, "pais": pais,
                "pais_acum": D.ancha(0, "0", "acumulada")[D.PAIS].iloc[-1]}

    @render.ui
    def tu_suma():
        s = tu()["suma"]
        clase = "ayuda" if abs(s - 100) <= 1 else "ayuda aviso"
        return ui.p(f"Suma: {s:.0f} %. " + ("" if abs(s - 100) <= 1 else "Se reescala a 100 % para el cálculo."),
                    class_=clase)

    @render.ui
    def tu_tarjetas():
        x = tu()
        f = x["anual"].index[-1]
        tuya, pais = x["anual"].iloc[-1], x["pais"].loc[f]
        return ui.div(tarjeta("Tu inflación anual", pct(tuya), D.mes(f), "guinda"),
                      tarjeta("La del país", pct(pais), "todos los hogares"),
                      tarjeta("Diferencia", pp(tuya - pais), "tú menos el país"),
                      tarjeta("Tu acumulada", pct(x["indice"].iloc[-1] - 100), f"desde {D.mes(D.BASE)}; país {x['pais_acum']:.1f} %"),
                      class_="tarjetas")

    @render.ui
    def tu_lineas():
        x = tu()
        return ui.HTML(F.html(F.tu_inflacion(x["anual"], x["pais"])))

    @render.ui
    def tu_aportes():
        return ui.HTML(F.html(F.aportes_rubro(tu()["aportes"])))


app = App(app_ui, server, static_assets=AQUI / "www")
