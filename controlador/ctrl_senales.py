"""Controladores del módulo de señales (CSV y MAT)."""
import os

from config import FS_MAT_DEFECTO
from modelo.senales import ErrorNoArreglo, SenalesCSV, SenalesMAT
from vista import graficos


class ControladorCSV:
    def __init__(self, vista, bd, obtener_usuario):
        self.v, self.bd, self.obtener_usuario = vista, bd, obtener_usuario
        self.modelo = SenalesCSV()
        v = self.v
        v.btnCargarCSV.clicked.connect(self.cargar)
        v.btnGraficarStem.clicked.connect(self.graficar_stem)
        v.btnGraficarHist.clicked.connect(self.graficar_histograma)
        v.btnGraficarScatter.clicked.connect(self.graficar_scatter)
        v.btnGraficarDiferencia.clicked.connect(self.graficar_diferencia)

    def _hay_datos(self):
        if self.modelo.df is None:
            self.v.mostrar_aviso("Sin datos", "Primero cargue un archivo CSV.")
            return False
        return True

    def _log(self, tipo, parametros):
        u = self.obtener_usuario()
        self.bd.guardar_procesamiento(u["id"] if u else None, tipo, self.modelo.ruta,
                                      parametros, {"ok": True})

    def cargar(self):
        ruta = self.v.pedir_archivo()
        if not ruta:
            return
        try:
            self.modelo.cargar(ruta)
        except Exception as e:
            self.v.mostrar_error("No se pudo cargar el CSV", str(e))
            return
        self.v.mostrar_archivo(os.path.basename(ruta))
        self.v.mostrar_info(self.modelo.info_texto(), self.modelo.describe())
        self.v.poblar_combos(self.modelo.canales, self.modelo.columnas)
        self._log("carga_csv", {"filas": len(self.modelo.df)})
        self.v.mostrar_estado("CSV cargado.")

    def graficar_stem(self):
        if not self._hay_datos():
            return
        canal = self.v.comboCanal.currentText()
        graficos.dibujar_stem(self.v.lienzo_stem, self.modelo.por_condicion(canal), canal)
        self._log("stem", {"canal": canal})

    def graficar_histograma(self):
        if not self._hay_datos():
            return
        canal = self.v.comboCanal.currentText()
        graficos.dibujar_histograma(self.v.lienzo_hist, self.modelo.por_condicion(canal), canal)
        self._log("histograma", {"canal": canal})

    def graficar_scatter(self):
        if not self._hay_datos():
            return
        x, y = self.v.comboX.currentText(), self.v.comboY.currentText()
        graficos.dibujar_scatter(self.v.lienzo_scatter, self.modelo.scatter(x, y), x, y)
        self._log("scatter", {"x": x, "y": y})

    def graficar_diferencia(self):
        if not self._hay_datos():
            return
        a, b = self.v.comboCanalA.currentText(), self.v.comboCanalB.currentText()
        if a == b:
            self.v.mostrar_aviso("Canales iguales", "Elija dos canales distintos.")
            return
        graficos.dibujar_diferencia(self.v.lienzo_diferencia,
                                    self.modelo.diferencia_interhemisferica(a, b), a, b)
        self._log("diferencia_interhemisferica", {"a": a, "b": b})


class ControladorMAT:
    def __init__(self, vista, bd, obtener_usuario):
        self.v, self.bd, self.obtener_usuario = vista, bd, obtener_usuario
        self.modelo = SenalesMAT()
        self.v.spinFs.setValue(FS_MAT_DEFECTO)
        v = self.v
        v.btnCargarMAT.clicked.connect(self.cargar)
        v.btnSeleccionarLlave.clicked.connect(self.seleccionar_llave)
        v.btnOperar.clicked.connect(self.operar)
        v.btnEstadisticas.clicked.connect(self.estadisticas)

    def _log(self, tipo, parametros, resultado):
        u = self.obtener_usuario()
        self.bd.guardar_procesamiento(u["id"] if u else None, tipo, self.modelo.ruta,
                                      parametros, resultado)

    def _hay_arreglo(self):
        if self.modelo.arreglo is None:
            self.v.mostrar_aviso("Sin datos", "Cargue un .mat y seleccione la llave del arreglo.")
            return False
        return True

    def cargar(self):
        ruta = self.v.pedir_archivo()
        if not ruta:
            return
        try:
            llaves = self.modelo.cargar(ruta)
        except Exception as e:
            self.v.mostrar_error("No se pudo cargar el .mat", str(e))
            return
        self.v.mostrar_archivo(os.path.basename(ruta))
        self.v.poblar_llaves(llaves)
        self.v.mostrar_forma("Seleccione la llave y presione 'Seleccionar'.")
        self.v.mostrar_estado("Archivo .mat cargado.")

    def seleccionar_llave(self):
        llave = self.v.comboLlaves.currentText()
        try:
            forma = self.modelo.seleccionar_llave(llave)
        except ErrorNoArreglo as e:
            self.v.mostrar_error("Llave inválida", str(e))
            return
        total = forma[1] * forma[2]
        self.v.poblar_canales(forma[0], total)
        self.v.mostrar_forma(f"Forma 3D: {forma}  ->  2D: ({forma[0]}, {total})")
        self._log("seleccion_llave", {"llave": llave}, {"forma": forma})

    def operar(self):
        if not self._hay_arreglo():
            return
        canales = self.v.canales_seleccionados()
        try:
            tiempo, seg, res = self.modelo.operar(
                canales, self.v.spinMin.value(), self.v.spinMax.value(),
                self.v.operaciones_seleccionadas(), self.v.spinFs.value())
        except ValueError as e:
            self.v.mostrar_error("Parámetros inválidos", str(e))
            return
        nombres = [f"Canal {c}" for c in canales]
        graficos.dibujar_operacion(self.v.lienzo_operacion, tiempo, seg, res, nombres)
        self._log("operacion_canales",
                  {"canales": canales, "min": self.v.spinMin.value(),
                   "max": self.v.spinMax.value(), "ops": list(res)},
                  {"muestras": int(seg.shape[1])})

    def estadisticas(self):
        if not self._hay_arreglo():
            return
        e1, e2 = self.v.ejes_seleccionados()
        try:
            media, desv = self.modelo.estadisticas(e1, e2)
        except ValueError as e:
            self.v.mostrar_error("Ejes inválidos", str(e))
            return
        self.v.labelFormaResultado.setText(
            f"Forma del vector resultante (promedio y desviación): {media.shape}")
        graficos.dibujar_boxplots(self.v.lienzo_boxplot, media, desv, e1, e2)
        self._log("estadisticas_ejes", {"ejes": [e1, e2]}, {"forma": media.shape})
