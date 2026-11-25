"""Utilidades para cargar archivos .ui en PyQt5."""
import re
from io import StringIO

from PyQt5 import uic


def cargar_ui_compatible(ruta, widget):
    """Carga un .ui guardado con Qt Designer de Qt 6 en PyQt5.

    El Designer de Qt 6 escribe los enums con un formato que el uic de PyQt5
    no reconoce (por ejemplo Qt::AlignmentFlag::AlignCenter). Esta función
    corrige el texto en memoria y luego lo carga; el archivo .ui no se modifica.
    """
    with open(ruta, "r", encoding="utf-8") as f:
        contenido = f.read()

    # Qt::AlignmentFlag::AlignCenter -> Qt::AlignCenter
    contenido = re.sub(r"\b([A-Za-z]+)::[A-Za-z]+::([A-Za-z]+)", r"\1::\2", contenido)

    # Quitar espacios y saltos de línea dentro de <set>...</set>
    contenido = re.sub(
        r"<set>(.*?)</set>",
        lambda m: "<set>" + re.sub(r"\s+", "", m.group(1)) + "</set>",
        contenido,
        flags=re.DOTALL,
    )

    uic.loadUi(StringIO(contenido), widget)