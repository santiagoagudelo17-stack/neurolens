"""Punto de entrada de NeuroLens.  Ejecutar:  python main.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Qt5Agg")

from PyQt5.QtWidgets import QApplication, QMessageBox

from config import APP_NOMBRE
from controlador.app import ControladorApp
from vista.ventanas import UiIncompleta


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NOMBRE)
    try:
        controlador = ControladorApp()
    except UiIncompleta as e:
        QMessageBox.critical(None, "Faltan archivos de diseño (.ui)", str(e))
        return 1
    controlador.iniciar()
    codigo = app.exec_()
    controlador.cerrar()
    return codigo


if __name__ == "__main__":
    sys.exit(main())
