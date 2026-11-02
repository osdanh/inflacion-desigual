"""Gráficas de la app (Plotly). Cada función recibe datos ya filtrados y regresa una figura."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from datos import GEO, LUGAR, MESES, NOMBRE, ORDEN_GRUPOS, PAIS, ROMANOS, mes

# --- colores: el color sigue al papel que cumple en la gráfica
GUINDA, AZUL = "#8E1F38", "#1F6FA8"            # decil I / sube más;  decil X / sube menos
TINTA, TINTA2, TENUE = "#22262A", "#5B6168", "#9AA0A6"
GRIS_SERIE, REJILLA, EJE = "#CDD1D6", "#ECEEF0", "#C7CBD1"
SECUENCIAL = [[0, "#FBF0EC"], [0.17, "#F6D2C8"], [0.33, "#ECA999"], [0.5, "#DB7C6E"], [0.67, "#C1504C"],
              [0.83, "#9D2B38"], [1, "#6E1527"]]                      # magnitud: un solo tono, claro a oscuro
DIVERGENTE = [[0, "#1B5E91"], [0.25, "#7DAFD2"], [0.5, "#EBECEE"], [0.75, "#DE9096"], [1, "#8E1F38"]]
COLOR_GRUPO = {"Alimentos procesados": "#E69F00", "Frutas, verduras y pecuarios": "#009E73",
               "Energéticos y tarifas": "#56B4E9", "Mercancías no alimenticias": "#0072B2",
               "Servicios": "#CC79A7", LUGAR: "#3A3F45"}              # orden fijo; revisado para daltonismo
FUENTE = "Inter, 'Segoe UI', system-ui, -apple-system, Roboto, sans-serif"
CONFIG = {"displayModeBar": False, "responsive": True}
# contorno de una sola entidad, para resaltarla sin mandar otra vez todo el mapa
GEO_ENTIDAD = {r["properties"]["cve_ent"]: {"type": "FeatureCollection", "features": [r]} for r in GEO["features"]}


def html(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config=CONFIG)


def base(fig, alto, leyenda=True, derecha=12):
    fig.update_layout(
        height=alto, margin=dict(l=8, r=derecha, t=8 if not leyenda else 34, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FUENTE, size=13, color=TINTA2), showlegend=leyenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title=None, font=dict(size=12.5, color=TINTA2)),
        hoverlabel=dict(bgcolor="white", bordercolor=EJE, font=dict(family=FUENTE, size=12.5, color=TINTA)),
    )
    fig.update_xaxes(showgrid=False, linecolor=EJE, ticks="outside", tickcolor=EJE, ticklen=4, automargin=True)
    fig.update_yaxes(gridcolor=REJILLA, zeroline=False, automargin=True)
    return fig


def eje_tiempo(fig):
    fig.update_xaxes(tickformat="%Y", dtick="M12", hoverformat="%m/%Y")
    return fig


def rango_con_etiquetas(valores, margen=0.22):
    """Rango del eje para barras horizontales, con espacio a ambos lados para el número de cada barra."""
    bajo, alto = min(float(valores.min()), 0.0), max(float(valores.max()), 0.0)
    holgura = (alto - bajo) * margen
    return [bajo - holgura, alto + holgura]


def linea_cero(fig, horizontal=True):
    (fig.add_hline if horizontal else fig.add_vline)(0, line_color=TENUE, line_width=1)
    return fig


def etiquetas_finales(fig, puntos, sufijo=" %", separacion=0.055):
    """Etiqueta al final de cada línea; si dos quedan encimadas las separa. puntos: [(texto, x, y, color)]"""
    if not puntos:
        return fig
    ys = [p[2] for p in puntos]
    rango = fig.layout.yaxis.range or [min(fig_min(fig), min(ys)), max(fig_max(fig), max(ys))]
    paso = (rango[1] - rango[0]) * separacion
    orden = sorted(range(len(puntos)), key=lambda i: ys[i])
    pos = list(ys)
    for a, b in zip(orden, orden[1:]):
        if pos[b] - pos[a] < paso:
            centro = (pos[a] + pos[b]) / 2
            pos[a], pos[b] = centro - paso / 2, centro + paso / 2
    for (texto, x, y, color), yp in zip(puntos, pos):
        fig.add_annotation(x=x, y=yp, text=f"<b>{texto}</b> {y:.1f}{sufijo}", showarrow=False, xanchor="left",
                           xshift=8, font=dict(color=color, size=12.5), bgcolor="white", borderpad=1)
    return fig


def _valores_y(fig):
    ys = [np.asarray(t.y, dtype=float) for t in fig.data if getattr(t, "y", None) is not None]
    return np.concatenate([y[~np.isnan(y)] for y in ys])


def fig_min(fig):
    return float(_valores_y(fig).min())


def fig_max(fig):
    return float(_valores_y(fig).max())


# ------------------------------------------------------------------ por ingreso
def lineas_deciles(ancho):
    """ancho: fechas x deciles (0 = todos). Resalta el decil I y el X; los demás quedan en gris."""
    fig = go.Figure()
    for k, d in enumerate(range(2, 10)):
        fig.add_scatter(x=ancho.index, y=ancho[d], mode="lines", line=dict(color=GRIS_SERIE, width=1.1),
                        name="Deciles II a IX", legendgroup="otros", showlegend=k == 0, hoverinfo="skip")
    fig.add_scatter(x=ancho.index, y=ancho[0], mode="lines", line=dict(color=TINTA, width=1.6, dash="dot"),
                    name="Todos los hogares", hovertemplate="%{y:.1f} %")
    fig.add_scatter(x=ancho.index, y=ancho[10], mode="lines", line=dict(color=AZUL, width=2.4),
                    name="Decil X (mayor ingreso)", hovertemplate="%{y:.1f} %")
    fig.add_scatter(x=ancho.index, y=ancho[1], mode="lines", line=dict(color=GUINDA, width=2.4),
                    name="Decil I (menor ingreso)", hovertemplate="%{y:.1f} %")
    base(fig, 400, derecha=96)
    eje_tiempo(fig).update_layout(hovermode="x unified")
    fig.update_yaxes(ticksuffix=" %")
    fin = ancho.index[-1]
    return etiquetas_finales(fig, [("I", fin, ancho[1].iloc[-1], GUINDA), ("X", fin, ancho[10].iloc[-1], AZUL)])


def brecha_simple(brecha):
    """Brecha decil I menos decil X en el tiempo (serie): barras con el color según el signo."""
    fig = go.Figure(go.Bar(x=brecha.index, y=brecha, marker=dict(color=np.where(brecha >= 0, GUINDA, AZUL), line_width=0),
                           hovertemplate="%{y:+.2f} pp<extra></extra>"))
    base(fig, 250, leyenda=False)
    eje_tiempo(fig).update_layout(bargap=0.2)
    fig.update_yaxes(ticksuffix=" pp")
    return linea_cero(fig)


# ------------------------------------------------------------------ por qué
def brecha_tiempo(detalle, total):
    """Brecha de inflación anual mes a mes: canasta por grupo de componentes, más lugar, y la línea del total."""
    canasta = detalle.pivot_table(index="fin", columns="grupo", values="canasta", aggfunc="sum")
    lugar = detalle.groupby("fin")["lugar"].sum()
    fig = go.Figure()
    for g in ORDEN_GRUPOS:
        fig.add_bar(x=canasta.index, y=canasta[g], name=g, marker=dict(color=COLOR_GRUPO[g], line=dict(color="white", width=0.4)),
                    hovertemplate="%{y:+.2f} pp")
    fig.add_bar(x=lugar.index, y=lugar, name=LUGAR, marker=dict(color=COLOR_GRUPO[LUGAR], line=dict(color="white", width=0.4)),
                hovertemplate="%{y:+.2f} pp")
    fig.add_scatter(x=total.index, y=total, mode="lines", name="Brecha total", line=dict(color=TINTA, width=2),
                    hovertemplate="<b>%{y:+.2f} pp</b>")
    base(fig, 420)
    eje_tiempo(fig).update_layout(barmode="relative", bargap=0.12, hovermode="x unified",
                                  legend=dict(traceorder="normal"))
    fig.update_yaxes(ticksuffix=" pp")
    return linea_cero(fig)


def brecha_acumulada(detalle):
    """Un periodo acumulado: aporte de cada grupo de componentes (canasta) y del lugar."""
    canasta = detalle.groupby("grupo")["canasta"].sum().reindex(ORDEN_GRUPOS)
    valores = pd.concat([canasta, pd.Series({LUGAR: detalle["lugar"].sum()})])[::-1]
    fig = go.Figure(go.Bar(
        x=valores, y=valores.index, orientation="h", marker=dict(color=[COLOR_GRUPO[k] for k in valores.index], cornerradius=3),
        text=[f"{v:+.2f}" for v in valores], textposition="outside", textfont=dict(color=TINTA, size=12.5),
        cliponaxis=False, hovertemplate="%{y}: %{x:+.2f} pp<extra></extra>"))
    base(fig, 300, leyenda=False, derecha=40)
    fig.update_xaxes(ticksuffix=" pp", showgrid=True, gridcolor=REJILLA, showline=False, ticks="")
    fig.update_yaxes(showgrid=False, tickfont=dict(color=TINTA))
    fig.update_xaxes(range=rango_con_etiquetas(valores, 0.4))
    return linea_cero(fig, horizontal=False)


def productos(nodos, n=8):
    """Productos que más abren (positivo) y más cierran (negativo) la brecha por efecto canasta."""
    d = pd.concat([nodos.nlargest(n, "canasta"), nodos.nsmallest(n, "canasta")]).drop_duplicates("clave")
    d = d.sort_values("canasta")
    nombre = d["titulo"].str.slice(0, 36) + np.where(d["titulo"].str.len() > 36, "…", "")
    medio = (d["inflacion_a"] + d["inflacion_b"]) / 2
    fig = go.Figure(go.Bar(
        x=d["canasta"], y=nombre, orientation="h",
        marker=dict(color=np.where(d["canasta"] >= 0, GUINDA, AZUL), cornerradius=3),
        text=[f"{v:+.2f}" for v in d["canasta"]], textposition="outside", textfont=dict(color=TINTA, size=12),
        cliponaxis=False, customdata=np.column_stack([d["peso_a"], d["peso_b"], medio, d["titulo"]]),
        hovertemplate=("<b>%{customdata[3]}</b><br>Aporte a la brecha: %{x:+.2f} pp<br>Peso en el gasto: decil I "
                       "%{customdata[0]:.2f} %, decil X %{customdata[1]:.2f} %<br>Inflación del periodo: "
                       "%{customdata[2]:.1f} %<extra></extra>")))
    base(fig, 30 * len(d) + 40, leyenda=False, derecha=44)
    fig.update_xaxes(ticksuffix=" pp", showgrid=True, gridcolor=REJILLA, showline=False, ticks="")
    fig.update_yaxes(showgrid=False, tickfont=dict(color=TINTA, size=12.5))
    fig.update_xaxes(range=rango_con_etiquetas(d["canasta"], 0.2))
    return linea_cero(fig, horizontal=False)


# ------------------------------------------------------------------ por entidad
def _escala(divergente, rango):
    if divergente:
        tope = max(abs(rango[0]), abs(rango[1]))
        return dict(colorscale=DIVERGENTE, zmin=-tope, zmax=tope, zmid=0)
    return dict(colorscale=SECUENCIAL, zmin=rango[0], zmax=rango[1])


def mapa(valores, divergente, rango, seleccion, sufijo, titulo):
    """Mapa de entidades; valores: serie por cve_ent."""
    v = valores.drop(PAIS, errors="ignore")
    fig = go.Figure(go.Choropleth(
        geojson=GEO, featureidkey="properties.cve_ent", locations=v.index, z=v.to_numpy(),
        customdata=[NOMBRE[k] for k in v.index], marker=dict(line=dict(color="white", width=0.7)),
        hovertemplate="<b>%{customdata}</b><br>%{z:+.1f}" + sufijo + "<extra></extra>" if divergente
        else "<b>%{customdata}</b><br>%{z:.1f}" + sufijo + "<extra></extra>",
        colorbar=dict(orientation="h", thickness=10, len=0.42, x=0.03, xanchor="left", y=0.04, yanchor="bottom",
                      title=dict(text=titulo, side="top", font=dict(size=12, color=TINTA2)),
                      ticksuffix=sufijo, tickfont=dict(size=11.5, color=TINTA2), outlinewidth=0),
        **_escala(divergente, rango)))
    if seleccion in v.index:
        fig.add_choropleth(geojson=GEO_ENTIDAD[seleccion], featureidkey="properties.cve_ent", locations=[seleccion], z=[0],
                           colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
                           marker=dict(line=dict(color=TINTA, width=2.2)), hoverinfo="skip")
    fig.update_geos(visible=False, projection_type="mercator", lonaxis_range=[-117.4, -86.5],
                    lataxis_range=[14.3, 32.8], bgcolor="rgba(0,0,0,0)")
    fig.update_layout(height=450, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=FUENTE, size=13, color=TINTA2), dragmode=False,
                      hoverlabel=dict(bgcolor="white", bordercolor=EJE, font=dict(family=FUENTE, size=12.5, color=TINTA)))
    return fig


def ranking(valores, divergente, rango, seleccion, sufijo):
    """Las 32 entidades ordenadas; mismo color que el mapa."""
    v = valores.drop(PAIS, errors="ignore").sort_values()
    escala = _escala(divergente, rango)
    nombres = [f"<b>{NOMBRE[k]}</b>" if k == seleccion else NOMBRE[k] for k in v.index]
    formato = "{:+.1f}" if divergente else "{:.1f}"
    fig = go.Figure(go.Bar(
        x=v, y=nombres, orientation="h",
        marker=dict(color=v, colorscale=escala["colorscale"], cmin=escala["zmin"], cmax=escala["zmax"], cornerradius=2,
                    line=dict(color=TINTA, width=[1.8 if k == seleccion else 0 for k in v.index])),
        text=[formato.format(x) for x in v], textposition="outside", textfont=dict(size=11.5, color=TINTA2),
        cliponaxis=False, hovertemplate="%{y}: %{x:.1f}" + sufijo + "<extra></extra>"))
    base(fig, 18.5 * len(v) + 30, leyenda=False, derecha=36)
    fig.update_xaxes(visible=False, range=rango_con_etiquetas(v, 0.14))
    fig.update_yaxes(showgrid=False, tickfont=dict(size=11.5, color=TINTA2), ticks="")
    fig.update_layout(bargap=0.22)
    if divergente:
        linea_cero(fig, horizontal=False)
    elif PAIS in valores.index:
        fig.add_vline(valores[PAIS], line_color=TINTA, line_width=1, line_dash="dot")
        fig.add_annotation(x=valores[PAIS], y=1, yref="paper", yanchor="bottom", showarrow=False,
                           text=f"País {valores[PAIS]:.1f}{sufijo}", font=dict(size=11.5, color=TINTA))
        fig.update_layout(margin=dict(t=22))
    return fig


def series_entidades(ancho, seleccion, sufijo, con_cero):
    """Todas las entidades en gris, el país punteado y la entidad elegida resaltada."""
    fig = go.Figure()
    for k in ancho.columns:
        if k not in (PAIS, seleccion):
            fig.add_scatter(x=ancho.index, y=ancho[k], mode="lines", line=dict(color=GRIS_SERIE, width=0.9),
                            name="Otras entidades", legendgroup="otras", showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=[None], y=[None], mode="lines", line=dict(color=GRIS_SERIE, width=1.2), name="Otras entidades")
    puntos = []
    if PAIS in ancho.columns:
        fig.add_scatter(x=ancho.index, y=ancho[PAIS], mode="lines", line=dict(color=TINTA, width=1.6, dash="dot"),
                        name="País", hovertemplate="%{y:.1f}" + sufijo)
    if seleccion in ancho.columns:
        fig.add_scatter(x=ancho.index, y=ancho[seleccion], mode="lines", line=dict(color=GUINDA, width=2.4),
                        name=NOMBRE[seleccion], hovertemplate="%{y:.1f}" + sufijo)
        puntos.append((NOMBRE[seleccion], ancho.index[-1], ancho[seleccion].iloc[-1], GUINDA))
    base(fig, 320, derecha=150)
    eje_tiempo(fig).update_layout(hovermode="x unified")
    fig.update_yaxes(ticksuffix=sufijo)
    if con_cero:
        linea_cero(fig)
    return etiquetas_finales(fig, puntos, sufijo=sufijo)


# ------------------------------------------------------------------ tu inflación
def tu_inflacion(tuya, pais):
    fig = go.Figure()
    fig.add_scatter(x=pais.index, y=pais, mode="lines", line=dict(color=TINTA, width=1.6, dash="dot"),
                    name="Todos los hogares del país", hovertemplate="%{y:.1f} %")
    fig.add_scatter(x=tuya.index, y=tuya, mode="lines", line=dict(color=GUINDA, width=2.4),
                    name="Tu canasta", hovertemplate="%{y:.1f} %")
    base(fig, 360, derecha=110)
    eje_tiempo(fig).update_layout(hovermode="x unified")
    fig.update_yaxes(ticksuffix=" %")
    fin = tuya.index[-1]
    return etiquetas_finales(fig, [("Tú", fin, tuya.iloc[-1], GUINDA), ("País", fin, pais.loc[fin], TINTA)])


def aportes_rubro(aportes):
    """Aporte de cada rubro a tu inflación anual del último mes (puntos porcentuales)."""
    a = aportes.sort_values()
    fig = go.Figure(go.Bar(x=a, y=a.index, orientation="h", marker=dict(color=np.where(a >= 0, GUINDA, AZUL), cornerradius=3),
                           text=[f"{v:+.2f}" for v in a], textposition="outside", textfont=dict(color=TINTA, size=12.5),
                           cliponaxis=False, hovertemplate="%{y}: %{x:+.2f} pp<extra></extra>"))
    base(fig, 36 * len(a) + 30, leyenda=False, derecha=44)
    fig.update_xaxes(visible=False, range=rango_con_etiquetas(a, 0.12))
    fig.update_yaxes(showgrid=False, tickfont=dict(color=TINTA, size=12.5), ticks="")
    return fig


# ------------------------------------------------------------------ un experimento: la frontera
# El guinda es Baja California, la tratada. Los placebos (las entidades donde no pasó nada) van en gris.
FRANJA = "#E3E5E8"                                                    # donde caen nueve de cada diez placebos
NOMBRE_FRANJA = "Nueve de cada diez entidades sin la política"
COLOR_CLASE = {"con IVA": GUINDA, "sin IVA": AZUL, "todo": TINTA}     # el producto pagaba IVA o no
NOMBRE_CLASE = {"con IVA": "Con IVA: bajó de 16 a 8 %", "sin IVA": "Sin IVA: tasa 0 % o exento", "todo": "Todos los productos"}
COLOR_PAPEL = {"tratada": GUINDA, "parcial": "#C1504C", "fronteriza sin ciudad en la zona": TENUE}    # de más a menos dosis
NOMBRE_PAPEL = {"tratada": "Todas sus ciudades en la zona", "parcial": "Una ciudad en la zona",
                "fronteriza sin ciudad en la zona": "Ninguna ciudad en la zona"}
COLOR_TIPO = {"Bienes con IVA": "#0072B2", "Gasolinas": "#56B4E9", "Electricidad": "#E69F00", "Lo demás": TENUE}


def eje_meses(fig, fechas):
    """Eje de una ventana de pocos meses: una marca por trimestre, con el mes en español."""
    marcas = [f for f in fechas if f.month % 3 == 1]
    fig.update_xaxes(tickmode="array", tickvals=marcas, hoverformat="%m/%Y",
                     ticktext=[mes(f) if f.month == 1 or f == marcas[0] else MESES[f.month - 1] for f in marcas])
    return fig


def franja_en_leyenda(fig):
    fig.add_scatter(x=[None], y=[None], mode="markers", marker=dict(symbol="square", size=13, color=FRANJA), name=NOMBRE_FRANJA)
    return fig


def frontera_eventos(ancho, tratada, inicio, traslado=None):
    """ancho: meses x entidades, diferencia de precios en %. La tratada resaltada; cada una de las demás, en gris,
    es un placebo. `traslado` dibuja la referencia del recorte completo del IVA."""
    otras = [k for k in ancho.columns if k != tratada]
    fig = go.Figure()
    for k in otras:
        fig.add_scatter(x=ancho.index, y=ancho[k], mode="lines", line=dict(color=GRIS_SERIE, width=0.9),
                        showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=[None], y=[None], mode="lines", line=dict(color=GRIS_SERIE, width=1.2), name="Cada entidad sin la política")
    extremos = np.column_stack([ancho[otras].min(axis=1), ancho[otras].max(axis=1)])
    fig.add_scatter(x=ancho.index, y=ancho[tratada], mode="lines+markers", line=dict(color=GUINDA, width=2.4),
                    marker=dict(size=7, color=GUINDA, line=dict(color="white", width=1.5)), name=NOMBRE[tratada], customdata=extremos,
                    hovertemplate="<b>%{y:+.1f} %</b><br>Las demás: de %{customdata[0]:+.1f} a %{customdata[1]:+.1f} %<extra></extra>")
    base(fig, 410, derecha=24)
    eje_meses(fig, ancho.index).update_layout(hovermode="x unified")
    bajo = min(float(ancho.min().min()), traslado or 0.0)
    alto = max(float(ancho.max().max()), 0.0)
    fig.update_yaxes(ticksuffix=" %", range=[bajo - 0.08 * (alto - bajo), alto + 0.12 * (alto - bajo)])
    linea_cero(fig)
    vispera = f"{inicio - pd.Timedelta(days=15):%Y-%m-%d}"            # entre el último mes previo y el primero con el decreto
    fig.add_shape(type="line", xref="x", yref="paper", x0=vispera, x1=vispera, y0=0, y1=1, line=dict(color=TENUE, width=1, dash="dot"))
    fig.add_annotation(x=vispera, y=1, yref="paper", yanchor="top", xanchor="left", xshift=6, showarrow=False,
                       text=f"Enero de {inicio.year}: IVA de 16 a 8 %", font=dict(size=12, color=TINTA2))
    if traslado is not None:
        fig.add_hline(traslado, line_color=TENUE, line_width=1, line_dash="dot")
        fig.add_annotation(x=ancho.index[0], y=traslado, yshift=10, xanchor="left", showarrow=False, bgcolor="white", borderpad=1,
                           text=f"Recorte completo: {traslado:.1f} %", font=dict(size=12, color=TINTA2))
    ultimo = float(ancho[tratada].iloc[-1])                           # la etiqueta va del lado libre del último punto
    fig.add_annotation(x=ancho.index[-1], y=ultimo, xanchor="right", xshift=6, showarrow=False, bgcolor="white", borderpad=1,
                       yanchor="top" if ultimo < 0 else "bottom", yshift=-9 if ultimo < 0 else 9,
                       text=f"<b>{NOMBRE[tratada]}</b> {ultimo:+.1f} %", font=dict(color=GUINDA, size=12.5))
    return fig


def frontera_tipos(resumen, seleccion, traslado):
    """Efecto un año después por tipo de producto (resumen: uno por renglón, con clase, efecto y placebos). La barra
    es Baja California y la franja gris, donde cae el 90 % de los placebos; el tipo elegido lleva borde."""
    r = resumen.iloc[::-1]                                            # el primero queda arriba
    fig = go.Figure()
    fig.add_bar(x=r["placebo_p95"] - r["placebo_p05"], base=r["placebo_p05"], y=r["canasta"], orientation="h", width=0.7,
                marker=dict(color=FRANJA, cornerradius=3), name=NOMBRE_FRANJA, hoverinfo="skip")
    for clase, color in COLOR_CLASE.items():
        d = r[r["clase"] == clase]
        fig.add_bar(
            x=d["efecto"], y=d["canasta"], orientation="h", width=0.36, name=NOMBRE_CLASE[clase],
            marker=dict(color=color, cornerradius=3, line=dict(color=TINTA, width=[1.8 if k == seleccion else 0 for k in d["canasta"]])),
            text=[f"{v:+.1f}" for v in d["efecto"]], textposition="outside", textfont=dict(color=TINTA, size=12), cliponaxis=False,
            customdata=np.column_stack([d["placebo_min"], d["placebo_max"], d["rango"], d["valor_p"]]),
            hovertemplate=("<b>%{y}</b><br>Baja California: %{x:+.1f} %<br>Las 26 sin la política: de %{customdata[0]:+.1f} a "
                           "%{customdata[1]:+.1f} %<br>Lugar %{customdata[2]:.0f} de 27 (p = %{customdata[3]:.2f})<extra></extra>"))
    base(fig, 29 * len(r) + 84, derecha=20)
    fig.update_layout(barmode="overlay", legend=dict(traceorder="normal"))
    extremos = pd.concat([r["efecto"], r["placebo_p05"], r["placebo_p95"], pd.Series([traslado])])
    fig.update_xaxes(ticksuffix=" %", showgrid=True, gridcolor=REJILLA, showline=False, ticks="",
                     range=rango_con_etiquetas(extremos, 0.08))
    fig.update_yaxes(showgrid=False, tickfont=dict(color=TINTA, size=12.5), tickmode="array", tickvals=list(r["canasta"]),
                     ticktext=[f"<b>{k}</b>" if k == seleccion else k for k in r["canasta"]],
                     categoryorder="array", categoryarray=list(r["canasta"]), range=[-1.5, len(r) - 0.4])
    linea_cero(fig, horizontal=False)
    fig.add_vline(traslado, line_color=TENUE, line_width=1, line_dash="dot")
    fig.add_annotation(x=traslado, y=0, yref="paper", yanchor="bottom", xanchor="left", xshift=5, showarrow=False,
                       text=f"Recorte completo: {traslado:.1f} %", font=dict(size=11.5, color=TINTA2))     # en el renglón libre de abajo
    return fig


def frontera_estados(estados, franja):
    """Los estados fronterizos, de más a menos ciudades del INPC dentro de la zona. estados: entidad, papel, ciudades,
    en_la_zona, efecto y esperado (el efecto de la tratada por su dosis); franja: (p05, p95) de los placebos."""
    e = estados.iloc[::-1].reset_index(drop=True)
    e["etiqueta"] = (e["entidad"] + "<br>" + e["en_la_zona"].astype(str) + " de " + e["ciudades"].astype(str)
                     + np.where(e["ciudades"] == 1, " ciudad", " ciudades"))
    fig = go.Figure()
    for papel, color in COLOR_PAPEL.items():
        d = e[e["papel"] == papel]
        fig.add_bar(
            x=d["efecto"], y=d["etiqueta"], orientation="h", width=0.46, name=NOMBRE_PAPEL[papel], marker=dict(color=color, cornerradius=3),
            customdata=np.column_stack([d["entidad"], d["ciudades_inpc"], d["ciudades_en_la_zona"].replace("", "ninguna")]),
            hovertemplate=("<b>%{customdata[0]}</b>: %{x:+.1f} %<br>Ciudades del INPC: %{customdata[1]}<br>"
                           "Dentro de la zona: %{customdata[2]}<extra></extra>"))
    fig.add_scatter(x=e["esperado"], y=e["etiqueta"], mode="markers", name="Lo esperado por su parte dentro de la zona",
                    marker=dict(symbol="line-ns", size=17, line=dict(color=TINTA, width=2)),
                    hovertemplate="Esperado: %{x:+.1f} %<extra></extra>")
    franja_en_leyenda(fig)
    for r in e.itertuples():          # el valor va en una columna a la derecha: junto a la barra tropezaría con la marca
        fig.add_annotation(x=1, xref="paper", y=r.etiqueta, xanchor="left", xshift=8, showarrow=False,
                           text=f"<b>{r.efecto:+.1f} %</b>", font=dict(color=TINTA, size=12.5))
    base(fig, 56 * len(e) + 96, derecha=62)
    fig.update_layout(legend=dict(traceorder="normal"))
    fig.add_vrect(x0=franja[0], x1=franja[1], fillcolor=FRANJA, line_width=0, layer="below")
    extremos = pd.concat([e["efecto"], e["esperado"], pd.Series(franja)])
    fig.update_xaxes(ticksuffix=" %", showgrid=True, gridcolor=REJILLA, showline=False, ticks="",
                     range=rango_con_etiquetas(extremos, 0.06))
    fig.update_yaxes(showgrid=False, tickfont=dict(color=TINTA, size=12.5), categoryorder="array", categoryarray=list(e["etiqueta"]))
    return linea_cero(fig, horizontal=False)


def frontera_incidencia(aportes, total, participacion):
    """Efecto en el costo de la canasta por decil. aportes y participacion: deciles x tipos (puntos porcentuales y
    % del gasto); total: por decil, con efecto, placebos y hogares en la muestra."""
    fig = go.Figure()
    for t in aportes.columns:
        fig.add_bar(x=aportes.index, y=aportes[t], name=t, marker=dict(color=COLOR_TIPO[t], line=dict(color="white", width=1.5)),
                    customdata=participacion[t], hovertemplate="%{y:+.2f} pp (%{customdata:.0f} % de su gasto)")
    franja_en_leyenda(fig)
    piso = aportes.clip(upper=0).sum(axis=1)                          # donde termina la barra hacia abajo
    fig.add_scatter(x=aportes.index, y=piso, mode="text", text=[f"<b>{v:+.1f} %</b>" for v in total["efecto"]],
                    textposition="bottom center", textfont=dict(color=TINTA, size=12.5), cliponaxis=False, name="Total",
                    showlegend=False, customdata=np.column_stack([total["efecto"], total["placebo_min"], total["placebo_max"],
                                                                  total["hogares_muestra"]]),
                    hovertemplate=("<b>%{customdata[0]:+.2f} %</b><br>Entidades sin la política: de %{customdata[1]:+.2f} a "
                                   "%{customdata[2]:+.2f} %<br>%{customdata[3]:.0f} hogares en la muestra"))
    base(fig, 400)
    fig.update_layout(barmode="relative", bargap=0.42, hovermode="x unified", legend=dict(traceorder="normal"))
    franja = [float(total["placebo_p05"].min()), float(total["placebo_p95"].max())]
    fig.add_hrect(y0=franja[0], y1=franja[1], fillcolor=FRANJA, line_width=0, layer="below")
    bajo, alto = float(piso.min()), max(franja[1], float(aportes.clip(lower=0).sum(axis=1).max()))
    fig.update_yaxes(ticksuffix=" %", range=[bajo - 0.16 * (alto - bajo), alto + 0.06 * (alto - bajo)])
    fig.update_xaxes(type="category", title=dict(text="Decil de ingreso (I: el de menor ingreso)", font=dict(size=12.5, color=TINTA2)))
    return linea_cero(fig)


# ------------------------------------------------------------------ un experimento: refrescos y cigarros
# El guinda es el producto con el impuesto nuevo; cada línea gris, un producto de comparación tratado como si lo pagara.
COLOR_IMPUESTO = {"Bebidas": "#E69F00", "Cigarros": "#CC79A7"}                 # en la canasta de cada decil
COLOR_DIRECTO = {"Pagaron más impuesto": GUINDA, "Frutas, verduras y pecuarios": "#009E73", "Energéticos": "#56B4E9",
                 "Lo demás": TENUE}
NOMBRE_PLACEBO_PRODUCTO = "Cada producto sin impuesto nuevo, como si lo pagara"


def impuestos_eventos(tray, placebos, inicio, nombre, referencia=None):
    """tray: efecto por mes en % (diciembre de 2025 = 0); placebos: meses x productos de comparación, cada uno contra
    los demás. referencia: (valor, texto) de lo que subiría el precio si todo el impuesto llegara al consumidor."""
    fig = go.Figure()
    for k in placebos.columns:
        fig.add_scatter(x=placebos.index, y=placebos[k], mode="lines", line=dict(color=GRIS_SERIE, width=0.9),
                        showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=[None], y=[None], mode="lines", line=dict(color=GRIS_SERIE, width=1.2), name=NOMBRE_PLACEBO_PRODUCTO)
    extremos = np.column_stack([placebos.min(axis=1), placebos.max(axis=1)])
    fig.add_scatter(x=tray.index, y=tray, mode="lines+markers", line=dict(color=GUINDA, width=2.4),
                    marker=dict(size=7, color=GUINDA, line=dict(color="white", width=1.5)), name=nombre, customdata=extremos,
                    hovertemplate=("<b>%{y:+.1f} %</b><br>Sin impuesto nuevo: de %{customdata[0]:+.1f} a "
                                   "%{customdata[1]:+.1f} %<extra></extra>"))
    base(fig, 410, derecha=24)
    eje_meses(fig, tray.index).update_layout(hovermode="x unified")
    bajo = min(float(tray.min()), float(placebos.min().min()), 0.0)
    alto = max(float(tray.max()), float(placebos.max().max()), referencia[0] if referencia else 0.0)
    fig.update_yaxes(ticksuffix=" %", range=[bajo - 0.08 * (alto - bajo), alto + 0.14 * (alto - bajo)])
    linea_cero(fig)
    vispera = f"{inicio - pd.Timedelta(days=15):%Y-%m-%d}"            # entre diciembre y el primer mes con el impuesto
    fig.add_shape(type="line", xref="x", yref="paper", x0=vispera, x1=vispera, y0=0, y1=1, line=dict(color=TENUE, width=1, dash="dot"))
    fig.add_annotation(x=vispera, y=1, yref="paper", yanchor="top", xanchor="right", xshift=-6, showarrow=False,
                       text=f"Enero de {inicio.year}: sube el IEPS", font=dict(size=12, color=TINTA2))
    if referencia:
        fig.add_hline(referencia[0], line_color=TENUE, line_width=1, line_dash="dot")
        fig.add_annotation(x=tray.index[0], y=referencia[0], yshift=10, xanchor="left", showarrow=False, bgcolor="white",
                           borderpad=1, text=referencia[1], font=dict(size=12, color=TINTA2))
    ultimo = float(tray.iloc[-1])
    fig.add_annotation(x=tray.index[-1], y=ultimo, xanchor="right", xshift=6, yanchor="bottom", yshift=9, showarrow=False,
                       bgcolor="white", borderpad=1, text=f"<b>{nombre}</b> {ultimo:+.1f} %", font=dict(color=GUINDA, size=12.5))
    return fig


def impuestos_eneros(eneros, especial=None):
    """Cada enero contra lo normal, en %. eneros: por año, efecto, tipo (normal, fuera de los normales, tratado) y la
    franja donde caen nueve de cada diez productos de comparación ese mismo enero. especial: (año, texto) de otro enero
    en que el impuesto también cambió."""
    e = eneros.assign(x=eneros["anio"].astype(str))
    fig = go.Figure()
    fig.add_bar(x=e["x"], y=e["placebo_p95"] - e["placebo_p05"], base=e["placebo_p05"], width=0.78,
                marker=dict(color=FRANJA, cornerradius=3), name="9 de cada 10 productos sin impuesto nuevo", hoverinfo="skip")
    marcar = e["anio"] == (especial[0] if especial else None)
    anio = int(e.loc[e["tipo"] == "tratado", "anio"].iat[0])
    rayado = dict(color="white", line=dict(color=TENUE, width=1.2), pattern=dict(shape="/", fgcolor=TENUE, size=5, solidity=0.35))
    grupos = [("tratado", dict(color=GUINDA), f"{anio}: el impuesto nuevo"),
              ("normal", dict(color=TENUE), "Eneros normales (la referencia)"),
              ("fuera de los normales", rayado, "Fuera de la referencia")]
    for tipo, estilo, nombre in grupos:
        d = e[(e["tipo"] == tipo) & ~marcar]
        fig.add_bar(x=d["x"], y=d["efecto"], width=0.42, name=nombre, marker=dict(cornerradius=3, **estilo),
                    text=[f"{v:+.1f}" for v in d["efecto"]], textposition="outside", textfont=dict(color=TINTA, size=12),
                    cliponaxis=False, hovertemplate="%{x}: %{y:+.1f} %<extra></extra>")
    if especial:
        d = e[marcar]
        fig.add_bar(x=d["x"], y=d["efecto"], width=0.42, name=especial[1], marker=dict(color="#C1504C", cornerradius=3),
                    text=[f"{v:+.1f}" for v in d["efecto"]], textposition="outside", textfont=dict(color=TINTA, size=12),
                    cliponaxis=False, hovertemplate="%{x}: %{y:+.1f} %<extra></extra>")
    base(fig, 350)
    fig.update_layout(barmode="overlay", legend=dict(traceorder="normal"))
    bajo = min(float(e[["efecto", "placebo_p05"]].min().min()), 0.0)
    alto = max(float(e[["efecto", "placebo_p95"]].max().max()), 0.0)
    fig.update_yaxes(ticksuffix=" %", range=[bajo - 0.1 * (alto - bajo), alto + 0.16 * (alto - bajo)])
    fig.update_xaxes(type="category", title=dict(text="Enero contra diciembre, cada año", font=dict(size=12.5, color=TINTA2)))
    return linea_cero(fig)



def impuestos_incidencia(inc):
    """Por decil (I a X): aportes de las bebidas y los cigarros al costo de la canasta (pp), el total con su intervalo
    (5 a 95 % de los sorteos con el ruido de los placebos) y los pesos de más al mes por hogar."""
    fig = go.Figure()
    for nombre in COLOR_IMPUESTO:
        clave = nombre.lower()
        fig.add_bar(x=inc["nivel"], y=inc[f"aporte_{clave}"], name=nombre,
                    marker=dict(color=COLOR_IMPUESTO[nombre], line=dict(color="white", width=1.5)),
                    customdata=inc[f"participacion_{clave}"], hovertemplate=f"{nombre}: %{{y:.2f}} pp (%{{customdata:.1f}} % de su gasto)")
    fig.add_scatter(x=inc["nivel"], y=inc["efecto"], mode="markers", marker=dict(size=6, color=TINTA, symbol="line-ew",
                                                                                 line=dict(color=TINTA, width=0)),
                    error_y=dict(type="data", symmetric=False, array=inc["efecto_p95"] - inc["efecto"],
                                 arrayminus=inc["efecto"] - inc["efecto_p05"], color=TINTA2, thickness=1.3, width=5),
                    name="Intervalo", showlegend=False,
                    customdata=np.column_stack([inc["efecto_p05"], inc["efecto_p95"], inc["pesos_mes"]]),
                    hovertemplate=("<b>Total: %{y:.2f} %</b> (de %{customdata[0]:.2f} a %{customdata[1]:.2f})<br>"
                                   "%{customdata[2]:.0f} pesos más al mes por hogar<extra></extra>"))
    fig.add_scatter(x=inc["nivel"], y=inc["efecto_p95"], mode="text", text=[f"<b>{v:.2f} %</b>" for v in inc["efecto"]],
                    textposition="top center", textfont=dict(color=TINTA, size=12.5), cliponaxis=False, showlegend=False,
                    hoverinfo="skip")
    base(fig, 380)
    fig.update_layout(barmode="stack", bargap=0.42, hovermode="x unified", legend=dict(traceorder="normal"))
    fig.update_yaxes(ticksuffix=" %", range=[0, float(inc["efecto_p95"].max()) * 1.18])
    fig.update_xaxes(type="category", title=dict(text="Decil de ingreso (I: el de menor ingreso)", font=dict(size=12.5, color=TINTA2)))
    return fig


def impuestos_directo(directo):
    """Enero de 2026 contra un enero normal en el índice de los deciles I y X, repartido por tipo de producto (puntos
    porcentuales). El rombo es lo que marca el índice del decil; lo que no cuadra por la aproximación va en «Lo demás»."""
    filas = {"I": "Decil I", "X": "Decil X", "I menos X": "I menos X"}
    d = directo.set_index("decil").loc[list(filas)].copy()
    d["Frutas, verduras y pecuarios"] = d["Frutas y verduras"] + d["Pecuarios"]
    d["Lo demás"] = d["Lo demás"] + d["directo"] - d["suma"]
    y = [filas[k] for k in d.index][::-1]
    fig = go.Figure()
    for grupo, color in COLOR_DIRECTO.items():
        fig.add_bar(x=d[grupo].iloc[::-1], y=y, orientation="h", name=grupo, width=0.52,
                    marker=dict(color=color, line=dict(color="white", width=1)),
                    hovertemplate=f"{grupo}: %{{x:+.2f}} puntos<extra></extra>")
    fig.add_scatter(x=d["directo"].iloc[::-1], y=y, mode="markers", name="Lo que marca el índice del decil",
                    marker=dict(symbol="diamond", size=12, color=TINTA, line=dict(color="white", width=1.5)),
                    hovertemplate="Índice del decil: %{x:+.2f} puntos<extra></extra>")
    base(fig, 330)
    fig.update_layout(barmode="relative", legend=dict(traceorder="normal"))
    fig.update_xaxes(showgrid=True, gridcolor=REJILLA, showline=False, ticks="", zeroline=False,
                     title=dict(text="Puntos porcentuales", font=dict(size=12.5, color=TINTA2)))
    fig.update_yaxes(showgrid=False, tickfont=dict(color=TINTA, size=12.5), categoryorder="array", categoryarray=y)
    return linea_cero(fig, horizontal=False)
