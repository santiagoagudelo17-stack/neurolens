"""Prueba integral sin pantalla con los datos reales del curso.
Uso:  QT_QPA_PLATFORM=offscreen python pruebas/prueba_integral.py <carpeta_datos>"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib
matplotlib.use("Qt5Agg")
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

from pruebas import andamio_ui
andamio_ui.instalar()

import config
config.RESULTADOS_DIR = tempfile.mkdtemp()
import controlador.ctrl_imagenes as ci
ci.RESULTADOS_DIR = config.RESULTADOS_DIR
from controlador.app import ControladorApp

DATOS = sys.argv[1]
app = QApplication([])
# silenciar cuadros modales
mensajes = []
for nombre in ("critical", "information", "warning"):
    setattr(QMessageBox, nombre, staticmethod(lambda *a, _n=nombre, **k: mensajes.append((_n, a[1:3]))))

ctrl = ControladorApp(os.path.join(config.RESULTADOS_DIR, "test.db"))
ok = lambda c, t: print(("OK   " if c else "FALLA"), t) or (None if c else sys.exit(1))

# ---- login ----
ctrl.iniciar()
ctrl.v_bienvenida.btnIniciar.click()
ctrl.v_login.lineEditUsuario.setText("imagenes1"); ctrl.v_login.lineEditClave.setText("mala")
ctrl.v_login.btnIngresar.click()
ok("incorrectos" in ctrl.v_login.labelEstado.text(), "login rechaza clave mala")
ctrl.v_login.lineEditClave.setText("img123"); ctrl.v_login.btnIngresar.click()
ok(ctrl.usuario and ctrl.usuario["rol"] == "imagenes", "login imagenes ok")
ok("ID:" in ctrl.v_menu.labelId.text() and "Ingreso" in ctrl.v_menu.labelFechaHora.text(), "menú muestra id/fecha")

# ---- imágenes ----
vi = ctrl.v_imagenes
for carpeta in ["imagenes/PPMI/3832", "imagenes/Sarcoma/img1", "imagenes/T2"]:
    QFileDialog.getExistingDirectory = staticmethod(lambda *a, c=carpeta: os.path.join(DATOS, c))
    t = time.time()
    vi.btnCargarCarpeta.click()
    v = ctrl.c_imagenes.vol
    ok(v is not None, f"carga {carpeta} ({time.time()-t:.1f}s) forma={v.volumen.shape} voxel={v.voxel_escalado}")
    for plano, radio in (("transversal", vi.radioTransversal), ("coronal", vi.radioCoronal), ("sagital", vi.radioSagital)):
        radio.setChecked(True)
        ok(vi.plano_actual() == plano, f"  plano {plano}, scroll max={vi.scrollCortes.maximum()}")
        vi.scrollCortes.setValue(vi.scrollCortes.maximum() // 3)
        vi.tabWidget.setCurrentIndex(0)
        ok(vi.labelVisor.pixmap() is not None, "  visor muestra corte; " + vi.labelNumeroCorte.text())
        vi.tabWidget.setCurrentIndex(1); vi.dialAngulo.setValue(15)
        ok(vi.labelRotada.pixmap() is not None, "  rotación en vivo")
        vi.dialAngulo.setValue(0)
        vi.tabWidget.setCurrentIndex(2); vi.btnEcualizar.click()
        vi.tabWidget.setCurrentIndex(3)
        for tipo in ("Binary", "Binary_inv", "Trunc", "ToZero", "ToZero_inv", "Otsu"):
            vi.comboBinarizacion.setCurrentText(tipo); vi.dialUmbral.setValue(100); vi.dialKernel.setValue(5)
        ok(vi.labelBinaria.pixmap() is not None, "  binarización con 6 tipos")
    vi.radioTransversal.setChecked(True)
    vi.dialAngulo.setValue(20); vi.btnAplicarRotacion.click()
    ok(v.volumen_corregido is not None, "  corregirAngulo aplicado al volumen")
    vi.btnRestablecerRotacion.click()
    ok(v.volumen_corregido is None, "  restablecer")
    ok(vi.tableInfo.rowCount() >= 10, f"  tabla con {vi.tableInfo.rowCount()} filas")

# multiframe
QFileDialog.getExistingDirectory = staticmethod(lambda *a: os.path.join(DATOS, "imagenes/series"))
vi.btnCargarCarpeta.click()
ok(ctrl.c_imagenes.vol is not None, "carpeta 'series' (multiframe RGB) carga")

filas = ctrl.bd.listar_estudios()
ok(len(filas) >= 4, f"BD tiene {len(filas)} estudios DICOM guardados")
ok(ctrl.bd.cargar_matriz_estudio(filas[0]["id"]).ndim == 2, "matriz de pixeles recuperable de BD")
print("  archivos generados:", sorted(os.listdir(config.RESULTADOS_DIR))[:4], "...")

# ---- señales ----
ctrl.cerrar_sesion()
ctrl.v_login.lineEditUsuario.setText("senales1"); ctrl.v_login.lineEditClave.setText("sen123")
ctrl.v_login.btnIngresar.click()
ok(ctrl.usuario["rol"] == "senales", "login señales")
vc = ctrl.v_csv
for f in ("ERP_01", "ERP_02", "ERP_03"):
    vc.pedir_archivo = lambda f=f: os.path.join(DATOS, f"senales_csv/{f}.csv")
    vc.btnCargarCSV.click()
    ok(vc.tableDescribe.rowCount() == 8 and "entries" in vc.textInfo.toPlainText(), f"{f}: info + describe")
    for b in (vc.btnGraficarStem, vc.btnGraficarHist, vc.btnGraficarScatter, vc.btnGraficarDiferencia):
        vc.comboCanalA.setCurrentIndex(0); vc.comboCanalB.setCurrentIndex(1)
        b.click()
ok(not [m for m in mensajes if m[0] == "critical"], "CSV sin errores")
vc.comboCanalA.setCurrentIndex(0); vc.comboCanalB.setCurrentIndex(0)
n = len(mensajes); vc.btnGraficarDiferencia.click()
ok(len(mensajes) == n + 1, "diferencia con canales iguales avisa")

vm = ctrl.v_mat
for f in ("Visual", "Sound", "Sensitive"):
    vm.pedir_archivo = lambda f=f: os.path.join(DATOS, f"senales_mat/{f}_Cue.mat")
    vm.btnCargarMAT.click()
    ok(vm.comboLlaves.count() >= 1, f"{f}_Cue.mat llaves: {[vm.comboLlaves.itemText(i) for i in range(vm.comboLlaves.count())]}")
    vm.comboLlaves.setCurrentText(f); vm.btnSeleccionarLlave.click()
    ok(vm.labelForma.text().startswith("Forma 3D"), "  " + vm.labelForma.text())
    vm.comboCanal1.setCurrentIndex(0); vm.comboCanal2.setCurrentIndex(5); vm.comboCanal3.setCurrentIndex(10); vm.comboCanal4.setCurrentIndex(20)
    vm.spinMin.setValue(0); vm.spinMax.setValue(1250)
    vm.checkSuma.setChecked(True); vm.checkResta.setChecked(True); vm.checkMultiplicacion.setChecked(True)
    vm.btnOperar.click()
    vm.comboEje1.setCurrentIndex(0); vm.comboEje2.setCurrentIndex(1); vm.btnEstadisticas.click()
    ok("(189,)" in vm.labelFormaResultado.text() or "(175,)" in vm.labelFormaResultado.text() or "(209,)" in vm.labelFormaResultado.text(), "  " + vm.labelFormaResultado.text())
    vm.comboEje2.setCurrentIndex(0); n = len(mensajes); vm.btnEstadisticas.click()
    ok(len(mensajes) == n + 1, "  ejes iguales avisa")
    vm.comboEje2.setCurrentIndex(2)
# llave no arreglo
ctrl.c_mat.modelo.contenido["texto"] = "hola"
vm.comboLlaves.addItem("texto"); vm.comboLlaves.setCurrentText("texto")
n = len(mensajes); vm.btnSeleccionarLlave.click()
ok(mensajes[-1][1][1] == "No es un arreglo, vuelva a intentarlo", "mensaje 'No es un arreglo, vuelva a intentarlo'")
print("\nTODAS LAS PRUEBAS PASARON")