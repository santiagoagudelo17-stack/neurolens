"""SOLO PARA PRUEBAS AUTOMÁTICAS (sin pantalla). NO es un diseño de la aplicación.
Reemplaza uic.loadUi por un constructor que crea los widgets del contrato (objectName)
para poder probar controladores y modelos sin los .ui reales hechos en Qt Designer."""
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from vista import ventanas


def _clases_ventana():
    return {c.ARCHIVO_UI: c for c in vars(ventanas).values()
            if isinstance(c, type) and issubclass(c, ventanas.VentanaBase) and c.ARCHIVO_UI}


def instalar():
    clases = _clases_ventana()
    import os

    def falso_loadUi(ruta, base):
        contrato = clases[os.path.basename(ruta)].WIDGETS
        central = QWidget()
        lay = QVBoxLayout(central)
        base.setCentralWidget(central)
        for nombre, clase in contrato.items():
            w = getattr(QtWidgets, clase)()
            w.setObjectName(nombre)
            if clase == "QLabel":
                w.setMinimumSize(300, 300)
            if clase == "QWidget":
                w.setMinimumSize(400, 300)
            if clase == "QTabWidget":
                for i in range(4):
                    w.addTab(QWidget(), f"tab{i}")
            if clase == "QTableWidget":
                pass
            setattr(base, nombre, w)
            lay.addWidget(w)

    ventanas.uic.loadUi = falso_loadUi
    ventanas.os.path.isfile = lambda p: True  # los .ui reales no se necesitan en la prueba
