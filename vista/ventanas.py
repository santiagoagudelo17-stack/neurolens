"""VISTA: una clase por ventana. Cada una carga su archivo .ui (hecho en Qt Designer)
con uic.loadUi. Aquí NO hay lógica de negocio: solo se leen/escriben widgets.

Cada clase declara en WIDGETS los objectName (y su tipo) que el Controlador espera
encontrar en el .ui. Si falta alguno se lanza UiIncompleta con un mensaje claro."""
import os

import numpy as np
from PyQt5 import QtWidgets
from vista.utils_ui import cargar_ui_compatible
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem

from config import APP_LEMA, APP_NOMBRE, UI_DIR
from vista import graficos


class UiIncompleta(Exception):
    pass


class VentanaBase(QMainWindow):
    ARCHIVO_UI = ""
    WIDGETS = {}  # objectName -> nombre de clase Qt

    def __init__(self):
        super().__init__()
        ruta = os.path.join(UI_DIR, self.ARCHIVO_UI)
        if not os.path.isfile(ruta):
            raise UiIncompleta(f"Falta el archivo de diseño: {ruta}\n"
                               "Créelo en Qt Designer (ver docs/GUIA_DISENO_UI.md).")
        cargar_ui_compatible(ruta, self)
        self._validar_widgets()

    def _validar_widgets(self):
        problemas = []
        for nombre, clase in self.WIDGETS.items():
            w = getattr(self, nombre, None)
            if w is None:
                problemas.append(f"  - falta '{nombre}' ({clase})")
            elif not isinstance(w, getattr(QtWidgets, clase)):
                problemas.append(f"  - '{nombre}' debe ser {clase} y es {type(w).__name__}")
        if problemas:
            raise UiIncompleta(f"{self.ARCHIVO_UI} no cumple el contrato:\n" + "\n".join(problemas))

    # utilidades comunes ------------------------------------------------
    def mostrar_error(self, titulo, mensaje):
        QMessageBox.critical(self, titulo, mensaje)

    def mostrar_aviso(self, titulo, mensaje):
        QMessageBox.information(self, titulo, mensaje)

    def mostrar_estado(self, texto):
        self.statusBar().showMessage(texto, 8000)

    @staticmethod
    def poner_imagen(label, imagen):
        """Muestra una matriz numpy uint8 (gris HxW o RGB HxWx3) en un QLabel respetando el aspect."""
        img = np.ascontiguousarray(imagen)
        if img.ndim == 2:
            qimg = QImage(img.data, img.shape[1], img.shape[0], img.shape[1],
                          QImage.Format_Grayscale8)
        else:
            qimg = QImage(img.data, img.shape[1], img.shape[0], img.shape[1] * 3,
                          QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg.copy())
        destino = label.size()
        if destino.width() < 50 or destino.height() < 50:
            destino = pix.size()
        label.setAlignment(Qt.AlignCenter)
        label.setPixmap(pix.scaled(destino, Qt.KeepAspectRatio, Qt.SmoothTransformation))


# ======================================================================
class VentanaBienvenida(VentanaBase):
    ARCHIVO_UI = "ventana_bienvenida.ui"
    WIDGETS = {"labelTitulo": "QLabel", "labelBienvenida": "QLabel",
               "btnIniciar": "QPushButton"}

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NOMBRE)
        self.labelTitulo.setText(APP_NOMBRE)
        self.labelBienvenida.setText(f"¡Bienvenido a {APP_NOMBRE}!\n{APP_LEMA}")


class VentanaLogin(VentanaBase):
    ARCHIVO_UI = "ventana_login.ui"
    WIDGETS = {"lineEditUsuario": "QLineEdit", "lineEditClave": "QLineEdit",
               "btnIngresar": "QPushButton", "labelEstado": "QLabel"}

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NOMBRE} - Inicio de sesión")
        self.lineEditClave.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lineEditUsuario.returnPressed.connect(self.lineEditClave.setFocus)
        self.lineEditClave.returnPressed.connect(self.btnIngresar.click)

    def credenciales(self):
        return self.lineEditUsuario.text(), self.lineEditClave.text()

    def mostrar_mensaje(self, texto):
        self.labelEstado.setText(texto)

    def limpiar(self):
        self.lineEditClave.clear()
        self.labelEstado.clear()
        self.lineEditUsuario.setFocus()


class VentanaMenu(VentanaBase):
    """Tercera ventana: datos del usuario y submenús según su rol."""
    ARCHIVO_UI = "ventana_menu.ui"
    WIDGETS = {"labelId": "QLabel", "labelNombre": "QLabel", "labelRol": "QLabel",
               "labelFechaHora": "QLabel",
               "btnSubmenu1": "QPushButton", "btnSubmenu2": "QPushButton",
               "btnSubmenu3": "QPushButton", "btnSubmenu4": "QPushButton",
               "btnCerrarSesion": "QPushButton"}

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NOMBRE} - Menú")

    @property
    def botones_submenu(self):
        return [self.btnSubmenu1, self.btnSubmenu2, self.btnSubmenu3, self.btnSubmenu4]

    def mostrar_usuario(self, usuario, rol_texto, fecha):
        self.labelId.setText(f"ID: {usuario['id']}")
        self.labelNombre.setText(f"Nombre: {usuario['nombre']}")
        self.labelRol.setText(f"Rol: {rol_texto}")
        self.labelFechaHora.setText(
            f"Ingreso: {fecha.strftime('%d/%m/%Y')}  {fecha.strftime('%H:%M:%S')}")

    def configurar_submenus(self, textos):
        for i, b in enumerate(self.botones_submenu):
            if i < len(textos):
                b.setText(textos[i])
                b.setVisible(True)
            else:
                b.setVisible(False)


# ======================================================================
class VentanaImagenes(VentanaBase):
    ARCHIVO_UI = "ventana_imagenes.ui"
    redimensionada = pyqtSignal()
    WIDGETS = {
        "btnCargarCarpeta": "QPushButton", "labelCarpeta": "QLabel",
        "tableInfo": "QTableWidget",
        "radioTransversal": "QRadioButton", "radioCoronal": "QRadioButton",
        "radioSagital": "QRadioButton",
        "scrollCortes": "QScrollBar", "labelNumeroCorte": "QLabel",
        "tabWidget": "QTabWidget", "labelVisor": "QLabel",
        "dialAngulo": "QDial", "labelAngulo": "QLabel",
        "btnAplicarRotacion": "QPushButton", "btnRestablecerRotacion": "QPushButton",
        "labelRotada": "QLabel",
        "btnEcualizar": "QPushButton", "widgetGraficoEcualizacion": "QWidget",
        "dialUmbral": "QDial", "labelUmbral": "QLabel",
        "dialKernel": "QDial", "labelKernel": "QLabel",
        "comboBinarizacion": "QComboBox", "labelBinaria": "QLabel",
        "btnVolverMenu": "QPushButton",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NOMBRE} - Imágenes médicas")
        self.radioTransversal.setChecked(True)
        self.scrollCortes.setOrientation(Qt.Horizontal)
        self.scrollCortes.setEnabled(False)
        self.dialAngulo.setRange(-180, 180)
        self.dialAngulo.setValue(0)
        self.dialAngulo.setWrapping(False)
        self.dialUmbral.setRange(0, 255)
        self.dialUmbral.setValue(127)
        self.dialKernel.setRange(1, 21)
        self.dialKernel.setValue(1)
        self.tableInfo.setColumnCount(2)
        self.tableInfo.setHorizontalHeaderLabels(["Campo", "Valor"])
        self.tableInfo.horizontalHeader().setStretchLastSection(True)
        self.tableInfo.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.lienzo_ecualizacion = graficos.montar_lienzo(self.widgetGraficoEcualizacion)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.redimensionada.emit()

    # --- lectura de controles ---------------------------------------
    def pedir_carpeta(self):
        return QtWidgets.QFileDialog.getExistingDirectory(self, "Seleccione la carpeta DICOM")

    def plano_actual(self):
        if self.radioCoronal.isChecked():
            return "coronal"
        if self.radioSagital.isChecked():
            return "sagital"
        return "transversal"

    def llenar_tipos_binarizacion(self, tipos):
        self.comboBinarizacion.clear()
        self.comboBinarizacion.addItems(list(tipos))

    # --- escritura --------------------------------------------------
    def mostrar_tabla(self, filas):
        self.tableInfo.setRowCount(len(filas))
        for i, (campo, valor) in enumerate(filas):
            self.tableInfo.setItem(i, 0, QTableWidgetItem(str(campo)))
            self.tableInfo.setItem(i, 1, QTableWidgetItem(str(valor)))
        self.tableInfo.resizeColumnToContents(0)

    def configurar_scroll(self, maximo, valor):
        self.scrollCortes.blockSignals(True)
        self.scrollCortes.setEnabled(True)
        self.scrollCortes.setRange(0, maximo)
        self.scrollCortes.setValue(valor)
        self.scrollCortes.blockSignals(False)

    def mostrar_numero_corte(self, indice, maximo):
        self.labelNumeroCorte.setText(f"Corte {indice} / {maximo}")

    def mostrar_angulo(self, grados):
        self.labelAngulo.setText(f"Ángulo: {grados}°")

    def mostrar_umbral(self, v):
        self.labelUmbral.setText(f"Umbral: {v}")

    def mostrar_kernel(self, k):
        self.labelKernel.setText(f"Kernel: {k} x {k}")

    def seleccionar_pestana(self, i):
        self.tabWidget.setCurrentIndex(i)

    def poner_imagen(self, etiqueta, matriz):
        alto, ancho = matriz.shape
        imagen = QImage(
            matriz.data,
            ancho,
            alto,
            ancho,
            QImage.Format_Grayscale8
        )
        pixmap = QPixmap.fromImage(imagen)
        etiqueta.setPixmap(pixmap)

    def mostrar_aviso(self, titulo, mensaje):
        QMessageBox.warning(self, titulo, mensaje)

    def mostrar_error(self, titulo, mensaje):
        QMessageBox.critical(self, titulo, mensaje)

    def mostrar_estado(self, mensaje):
        self.statusBar().showMessage(mensaje, 5000)

class VentanaSenalesCSV(VentanaBase):
    ARCHIVO_UI = "ventana_senales_csv.ui"
    WIDGETS = {
        "btnCargarCSV": "QPushButton", "labelArchivo": "QLabel",
        "textInfo": "QPlainTextEdit", "tableDescribe": "QTableWidget",
        "comboCanal": "QComboBox", "comboX": "QComboBox", "comboY": "QComboBox",
        "comboCanalA": "QComboBox", "comboCanalB": "QComboBox",
        "btnGraficarStem": "QPushButton", "btnGraficarHist": "QPushButton",
        "btnGraficarScatter": "QPushButton", "btnGraficarDiferencia": "QPushButton",
        "widgetStem": "QWidget", "widgetHist": "QWidget",
        "widgetScatter": "QWidget", "widgetDiferencia": "QWidget",
        "btnVolverMenu": "QPushButton",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NOMBRE} - Señales CSV")
        self.tableDescribe.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.textInfo.setReadOnly(True)
        self.lienzo_stem = graficos.montar_lienzo(self.widgetStem)
        self.lienzo_hist = graficos.montar_lienzo(self.widgetHist)
        self.lienzo_scatter = graficos.montar_lienzo(self.widgetScatter)
        self.lienzo_diferencia = graficos.montar_lienzo(self.widgetDiferencia)

    def pedir_archivo(self):
        ruta, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Seleccione un archivo CSV", "", "CSV (*.csv)")
        return ruta

    def mostrar_archivo(self, nombre):
        self.labelArchivo.setText(nombre)

    def poblar_combos(self, canales, columnas):
        for combo, items in ((self.comboCanal, canales), (self.comboCanalA, canales),
                             (self.comboCanalB, canales), (self.comboX, columnas),
                             (self.comboY, columnas)):
            combo.clear()
            combo.addItems(list(items))
        if len(canales) > 1:
            self.comboCanalB.setCurrentIndex(1)
        if len(columnas) > 1:
            self.comboY.setCurrentIndex(1)

    def mostrar_info(self, texto_info, df_describe):
        self.textInfo.setPlainText(texto_info)
        d = df_describe
        self.tableDescribe.setRowCount(len(d.index))
        self.tableDescribe.setColumnCount(len(d.columns))
        self.tableDescribe.setHorizontalHeaderLabels([str(c) for c in d.columns])
        self.tableDescribe.setVerticalHeaderLabels([str(i) for i in d.index])
        for i in range(len(d.index)):
            for j in range(len(d.columns)):
                self.tableDescribe.setItem(i, j, QTableWidgetItem(str(d.iat[i, j])))


class VentanaSenalesMAT(VentanaBase):
    ARCHIVO_UI = "ventana_senales_mat.ui"
    WIDGETS = {
        "btnCargarMAT": "QPushButton", "labelArchivo": "QLabel",
        "comboLlaves": "QComboBox", "btnSeleccionarLlave": "QPushButton",
        "labelForma": "QLabel", "spinFs": "QSpinBox",
        "comboCanal1": "QComboBox", "comboCanal2": "QComboBox",
        "comboCanal3": "QComboBox", "comboCanal4": "QComboBox",
        "spinMin": "QSpinBox", "spinMax": "QSpinBox",
        "checkSuma": "QCheckBox", "checkResta": "QCheckBox",
        "checkMultiplicacion": "QCheckBox",
        "btnOperar": "QPushButton", "widgetOperacion": "QWidget",
        "comboEje1": "QComboBox", "comboEje2": "QComboBox",
        "btnEstadisticas": "QPushButton", "labelFormaResultado": "QLabel",
        "widgetBoxplot": "QWidget", "btnVolverMenu": "QPushButton",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NOMBRE} - Señales MAT")
        self.lienzo_operacion = graficos.montar_lienzo(self.widgetOperacion)
        self.lienzo_boxplot = graficos.montar_lienzo(self.widgetBoxplot)
        self.btnSeleccionarLlave.setEnabled(False)
        for combo in (self.comboEje1, self.comboEje2):
            combo.clear()
            combo.addItems(["0", "1", "2"])
        self.comboEje2.setCurrentIndex(1)
        self.spinFs.setRange(1, 100000)

    @property
    def combos_canales(self):
        return [self.comboCanal1, self.comboCanal2, self.comboCanal3, self.comboCanal4]

    def pedir_archivo(self):
        ruta, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Seleccione un archivo MAT", "", "MAT (*.mat)")
        return ruta

    def mostrar_archivo(self, nombre):
        self.labelArchivo.setText(nombre)

    def poblar_llaves(self, llaves):
        self.comboLlaves.clear()
        self.comboLlaves.addItems(list(llaves))
        self.btnSeleccionarLlave.setEnabled(True)

    def poblar_canales(self, n_canales, n_muestras_total):
        for i, combo in enumerate(self.combos_canales):
            combo.clear()
            combo.addItems([f"Canal {k}" for k in range(n_canales)])
            combo.setCurrentIndex(min(i, n_canales - 1))
        self.spinMin.setRange(0, n_muestras_total - 1)
        self.spinMax.setRange(1, n_muestras_total)
        self.spinMin.setValue(0)
        self.spinMax.setValue(min(625, n_muestras_total))

    def mostrar_forma(self, texto):
        self.labelForma.setText(texto)

    def operaciones_seleccionadas(self):
        ops = []
        if self.checkSuma.isChecked():
            ops.append("suma")
        if self.checkResta.isChecked():
            ops.append("resta")
        if self.checkMultiplicacion.isChecked():
            ops.append("multiplicacion")
        return ops

    def canales_seleccionados(self):
        return [c.currentIndex() for c in self.combos_canales]

    def ejes_seleccionados(self):
        return self.comboEje1.currentIndex(), self.comboEje2.currentIndex()
