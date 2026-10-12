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
    panel_ingreso, panel_porque, panel_entidad, panel_tu, panel_metodo,
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
