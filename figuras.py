"""Gráficas de la app (Plotly). Cada función recibe datos ya filtrados y regresa una figura."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from datos import GEO, LUGAR, NOMBRE, ORDEN_GRUPOS, PAIS, ROMANOS, mes

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
