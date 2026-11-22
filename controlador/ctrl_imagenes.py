"""Controlador del módulo de imágenes: conecta VentanaImagenes con VolumenDicom/ProcesadorImagen."""
import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from config import RESULTADOS_DIR
from modelo.procesador_imagen import TIPOS_BINARIZACION, ProcesadorImagen
from modelo.volumen_dicom import VolumenDicom
from vista import graficos

# Orden de las pestañas del QTabWidget en el .ui
PESTANA_VISOR, PESTANA_ROTACION, PESTANA_ECUALIZACION, PESTANA_BINARIZACION = 0, 1, 2, 3


class ControladorImagenes:
    def __init__(self, vista, bd, obtener_usuario):
        self.v = vista
        self.bd = bd
        self.obtener_usuario = obtener_usuario
        self.vol = None
        self.proc = None
        self.estudio_id = None

        v = self.v
        v.llenar_tipos_binarizacion(TIPOS_BINARIZACION.keys())
        v.mostrar_angulo(v.dialAngulo.value())
        v.mostrar_umbral(v.dialUmbral.value())
        v.mostrar_kernel(self._kernel())

        v.btnCargarCarpeta.clicked.connect(self.cargar_carpeta)
        for r in (v.radioTransversal, v.radioCoronal, v.radioSagital):
            r.toggled.connect(self._plano_cambiado)
        v.scrollCortes.valueChanged.connect(self.refrescar)
        v.tabWidget.currentChanged.connect(self.refrescar)
        v.redimensionada.connect(self.refrescar)
        v.dialAngulo.valueChanged.connect(self._angulo_cambiado)
        v.btnAplicarRotacion.clicked.connect(self.aplicar_rotacion)
        v.btnRestablecerRotacion.clicked.connect(self.restablecer_rotacion)
        v.btnEcualizar.clicked.connect(self.ecualizar)
        v.dialUmbral.valueChanged.connect(self._binarizacion_cambiada)
        v.dialKernel.valueChanged.connect(self._binarizacion_cambiada)
        v.comboBinarizacion.currentIndexChanged.connect(self._binarizacion_cambiada)

    # ------------------------------------------------------------------
    def _kernel(self):
        return self.v.dialKernel.value() | 1  # siempre impar

    def _hay_volumen(self, avisar=True):
        if self.vol is None:
            if avisar:
                self.v.mostrar_aviso("Sin datos", "Primero cargue una carpeta DICOM.")
            return False
        return True

    # ------------------------------------------------------------------
    def cargar_carpeta(self):
        carpeta = self.v.pedir_carpeta()
        if not carpeta:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            vol = VolumenDicom(carpeta)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.v.mostrar_error("No se pudo cargar", str(e))
            return
        QApplication.restoreOverrideCursor()
        self.vol = vol
        self.proc = ProcesadorImagen(vol)
        usuario = self.obtener_usuario()
        self.estudio_id = self.bd.guardar_estudio(
            usuario["id"] if usuario else None, vol.info_registro(), vol.matriz_representativa())

        self.v.labelCarpeta.setText(carpeta)
        self.v.mostrar_tabla(vol.info_tabla())
        self.v.dialAngulo.setValue(0)
        plano = self.v.plano_actual()
        maximo = self.proc.maximo_indice(plano)
        self.v.configurar_scroll(maximo, maximo // 2)
        self.refrescar()
        self.v.mostrar_estado(f"Estudio cargado y guardado en la base de datos (id {self.estudio_id}).")
        for adv in vol.advertencias:
            self.v.mostrar_aviso("Advertencia", adv)

    def _plano_cambiado(self, marcado):
        if not marcado or not self._hay_volumen(avisar=False):
            return
        maximo = self.proc.maximo_indice(self.v.plano_actual())
        self.v.configurar_scroll(maximo, maximo // 2)
        self.refrescar()

    # ------------------------------------------------------------------
    def _corte_actual(self):
        plano = self.v.plano_actual()
        indice = self.v.scrollCortes.value()
        return plano, indice, self.proc.corte_uint8(plano, indice)

    def refrescar(self, *_):
        if not self._hay_volumen(avisar=False):
            return
        plano, indice, u8 = self._corte_actual()
        maximo = self.proc.maximo_indice(plano)
        self.v.mostrar_numero_corte(indice, maximo)
        tab = self.v.tabWidget.currentIndex()
        if tab == PESTANA_VISOR:
            self.v.poner_imagen(self.v.labelVisor, u8)
        elif tab == PESTANA_ROTACION:
            self.v.poner_imagen(self.v.labelRotada,
                                self.proc.rotar_corte(u8, self.v.dialAngulo.value()))
        elif tab == PESTANA_BINARIZACION:
            self._mostrar_binaria(u8)

    # --- rotación ------------------------------------------------------
    def _angulo_cambiado(self, valor):
        self.v.mostrar_angulo(valor)
        if self._hay_volumen(avisar=False) and self.v.tabWidget.currentIndex() == PESTANA_ROTACION:
            _, _, u8 = self._corte_actual()
            self.v.poner_imagen(self.v.labelRotada, self.proc.rotar_corte(u8, valor))

    def aplicar_rotacion(self):
        if not self._hay_volumen():
            return
        grados = self.v.dialAngulo.value()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.vol.corregirAngulo(grados)
        finally:
            QApplication.restoreOverrideCursor()
        u = self.obtener_usuario()
        self.bd.guardar_procesamiento(u["id"] if u else None, "correccion_angulo",
                                      self.vol.carpeta, {"grados": grados}, {"ok": True})
        self.v.dialAngulo.blockSignals(True)
        self.v.dialAngulo.setValue(0)
        self.v.dialAngulo.blockSignals(False)
        self.v.mostrar_angulo(0)
        self.refrescar()
        self.v.mostrar_estado(f"Volumen rotado {grados}° y guardado como volumen corregido.")

    def restablecer_rotacion(self):
        if not self._hay_volumen():
            return
        self.vol.restablecer()
        self.v.dialAngulo.setValue(0)
        self.refrescar()
        self.v.mostrar_estado("Se restauró el volumen original.")

    # --- ecualización --------------------------------------------------
    def ecualizar(self):
        if not self._hay_volumen():
            return
        plano, indice, u8 = self._corte_actual()
        eq = self.proc.ecualizar(u8)
        graficos.dibujar_ecualizacion(self.v.lienzo_ecualizacion, u8, eq, plano, indice)
        base = os.path.join(RESULTADOS_DIR, f"ecualizacion_{plano}_{indice}")
        self.proc.guardar_png(base + "_imagen.png", eq)
        self.v.lienzo_ecualizacion.fig.savefig(base + "_grafico.png", dpi=120)
        u = self.obtener_usuario()
        self.bd.guardar_procesamiento(u["id"] if u else None, "ecualizacion", self.vol.carpeta,
                                      {"plano": plano, "corte": indice}, {"archivo": base})
        self.v.mostrar_estado(f"Ecualización lista. Guardada en {RESULTADOS_DIR}")

    # --- binarización --------------------------------------------------
    def _mostrar_binaria(self, u8):
        umbral = self.v.dialUmbral.value()
        k = self._kernel()
        tipo = self.v.comboBinarizacion.currentText()
        self.v.poner_imagen(self.v.labelBinaria, self.proc.binarizar(u8, umbral, k, tipo))

    def _binarizacion_cambiada(self, *_):
        self.v.mostrar_umbral(self.v.dialUmbral.value())
        self.v.mostrar_kernel(self._kernel())
        if self._hay_volumen(avisar=False) and self.v.tabWidget.currentIndex() == PESTANA_BINARIZACION:
            _, _, u8 = self._corte_actual()
            self._mostrar_binaria(u8)
