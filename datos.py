"""Datos de la app: se leen una vez al arrancar (carpeta datos, la arma construir_datos_app.py)."""
import json
from pathlib import Path

import pandas as pd

DATOS = Path(__file__).parent / "datos"
PAIS = "00"
PRINCIPAL = "enigh2022_calibrado"
BASE = pd.Timestamp(2018, 7, 1)
ENLACE = pd.Timestamp(2024, 7, 1)
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
                "octubre", "noviembre", "diciembre"]
ROMANOS = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

VARIANTES = {
    "enigh2022_calibrado": "Principal: ENIGH 2022 calibrada",
    "enigh2022": "ENIGH 2022 sin calibrar",
    "enigh2018_calibrado": "ENIGH 2018 calibrada",
    "enigh2018": "ENIGH 2018 sin calibrar",
    "encadenado": "Encadenada: 2018 y luego 2022",
}
# componentes de la inflación (INEGI) agrupados para las gráficas
GRUPO_COMPONENTE = {
    "Alimentos, bebidas y tabaco": "Alimentos procesados",
    "Frutas y verduras": "Frutas, verduras y pecuarios",
    "Pecuarios": "Frutas, verduras y pecuarios",
    "Energéticos": "Energéticos y tarifas",
    "Tarifas autorizadas por el gobierno": "Energéticos y tarifas",
    "Mercancías no alimenticias": "Mercancías no alimenticias",
    "Educación (colegiaturas)": "Servicios",
    "Vivienda": "Servicios",
    "Otros servicios": "Servicios",
    "Varios": "Servicios",
}
ORDEN_GRUPOS = ["Alimentos procesados", "Frutas, verduras y pecuarios", "Energéticos y tarifas",
                "Mercancías no alimenticias", "Servicios"]
LUGAR = "Lugar (dónde viven)"


def mes(f, largo=False):
    """'sep 2026' o 'septiembre de 2026'."""
    return f"{MESES_LARGOS[f.month - 1]} de {f.year}" if largo else f"{MESES[f.month - 1]} {f.year}"


def leer(nombre, **kw):
    return pd.read_csv(DATOS / nombre, encoding="utf-8-sig", **kw)


entidades = leer("entidades.csv", dtype=str)
NOMBRE = dict(zip(entidades["cve_ent"], entidades["entidad"])) | {PAIS: "País"}
ABREV = dict(zip(entidades["cve_ent"], entidades["abreviatura"])) | {PAIS: "País"}
rubros = leer("rubros.csv", dtype=str)
RUBRO = dict(zip(rubros["rubro"], rubros["titulo"]))

ind_dec = leer("indices_deciles.csv", dtype={"rubro": str}, parse_dates=["fecha"])
ind_ent = leer("indices_entidades.csv.gz", dtype={"cve_ent": str, "rubro": str}, parse_dates=["fecha"])
ind_ent["acumulada"] = ind_ent["indice"] - 100
ind_dec["acumulada"] = ind_dec["indice"] - 100

_fechas = {"parse_dates": ["inicio", "fin"]}
brecha_dec = leer("brecha_deciles.csv", **_fechas)
brecha_det = leer("brecha_deciles_detalle.csv", **_fechas)
brecha_det = brecha_det[brecha_det["clasificacion"] == "componente"].copy()
brecha_det["grupo"] = brecha_det["categoria"].map(GRUPO_COMPONENTE)
brecha_nodos = leer("brecha_deciles_nodos.csv", dtype={"clave": str, "rubro": str}, **_fechas)
brecha_ent = leer("brecha_entidades.csv", dtype={"cve_ent": str}, **_fechas)
canastas = leer("canastas.csv", dtype={"cve_ent": str, "rubro": str})
cortes = leer("cortes_ingreso.csv")

with open(DATOS / "entidades.geojson", encoding="utf-8") as _f:
    GEO = json.load(_f)

FECHAS = sorted(ind_dec["fecha"].unique())
FIN = pd.Timestamp(FECHAS[-1])
PRIMER_ANUAL = pd.Timestamp(FECHAS[12])
ACUMULADOS = {                     # periodos acumulados de la descomposición: etiqueta -> (inicio, fin)
    f"{mes(BASE)} a {mes(FIN)}": (BASE, FIN),
    f"{mes(BASE)} a {mes(ENLACE)}": (BASE, ENLACE),
    f"{mes(ENLACE)} a {mes(FIN)}": (ENLACE, FIN),
}

# tablas anchas para consultar rápido: (quintil, rubro) -> fechas x entidades
_ANCHAS = {}


def ancha(quintil, rubro, medida):
    """Fechas en renglones y entidades (más el país) en columnas, para un quintil, rubro y medida."""
    llave = (int(quintil), rubro, medida)
    if llave not in _ANCHAS:
        d = ind_ent[(ind_ent["quintil"] == int(quintil)) & (ind_ent["rubro"] == rubro)]
        _ANCHAS[llave] = d.pivot(index="fecha", columns="cve_ent", values=medida)
    return _ANCHAS[llave]


def a_mes(fecha):
    """Primer día del mes de una fecha del deslizador."""
    return pd.Timestamp(fecha.year, fecha.month, 1)


# --- un experimento: la frontera norte en enero de 2019 (tablas de construir_frontera.py)
FR_TRATADA = "02"                                  # Baja California: toda la entidad está en la zona
FR_FRONTERIZAS = ["02", "28", "08", "05", "26", "19"]
FR_INICIO = pd.Timestamp(2019, 1, 1)               # entra en vigor el decreto
FR_TRASLADO = 100 * (1.08 / 1.16 - 1)              # -6.9 %: el precio final si todo el recorte del IVA llega al consumidor
FR_PRINCIPAL = "mismos meses"                      # julio a diciembre de 2019 contra los mismos meses de 2018
FR_TIPOS = ["Bienes con IVA", "Gasolinas", "Electricidad", "Lo demás"]

fr_eventos = leer("frontera_eventos.csv", dtype={"cve_ent": str}, parse_dates=["fecha"])
fr_entidades = leer("frontera_entidades.csv", dtype={"cve_ent": str})
fr_resumen = leer("frontera_resumen.csv")
fr_estados = leer("frontera_estados.csv", dtype={"cve_ent": str}).fillna({"ciudades_en_la_zona": ""})
fr_incidencia = leer("frontera_incidencia.csv")
FR_CLASE = dict(zip(fr_resumen["canasta"], fr_resumen["clase"]))
FR_CON_MESES = list(dict.fromkeys(fr_eventos["canasta"]))      # la luz y el total no tienen trayectoria mensual comparable
_FR_ANCHAS = {}


def fr_ancha(canasta):
    """Meses en renglones y entidades en columnas: brecha de cada entidad contra las no fronterizas, en %."""
    if canasta not in _FR_ANCHAS:
        d = fr_eventos[fr_eventos["canasta"] == canasta]
        _FR_ANCHAS[canasta] = d.pivot(index="fecha", columns="cve_ent", values="brecha")
    return _FR_ANCHAS[canasta]


def fr_efectos(canasta, medida=FR_PRINCIPAL):
    """El efecto de una canasta para las 32 entidades (cada una contra las no fronterizas), en %."""
    d = fr_entidades[(fr_entidades["canasta"] == canasta) & (fr_entidades["medida"] == medida)]
    return d.set_index("cve_ent")["efecto"]
