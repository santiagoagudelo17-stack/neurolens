"""Modelo de un estudio DICOM: lectura, escalado x2 y reconstrucción 3D.

Mejoras respecto al Parcial 3:
  * Los cortes se ordenan proyectando ImagePositionPatient sobre la normal del plano
    (no solo con la coordenada Z), así funciona también con cortes oblicuos.
  * La separación real entre cortes (eje Z del voxel) se calcula a partir de las
    posiciones; SliceThickness es solo el último recurso (en T2 el grosor es 5 mm
    pero la separación real es 6 mm).
  * Si la carpeta mezcla varias series, se usa la serie más grande y se avisa.
  * Soporta DICOM multiframe (incluso RGB, se convierte a gris).
"""
import os
from collections import defaultdict

import cv2
import numpy as np
import pydicom


class VolumenDicom:
    def __init__(self, carpeta):
        self.carpeta = carpeta
        # --- información del dataset ---
        self.nombre_paciente = None
        self.id_paciente = None
        self.modalidad = None
        self.filas = None
        self.columnas = None
        self.n_cortes = 0
        self.voxel_alto = None      # mm (espaciado entre filas)
        self.voxel_largo = None     # mm (espaciado entre columnas)
        self.voxel_ancho = None     # mm (separación entre cortes)
        self.grosor_corte = None    # SliceThickness del header
        self.voxel_escalado = None  # (alto, largo, ancho) después del x2
        self.advertencias = []
        # --- datos ---
        self.datasets = []
        self.matrices_pixeles = []  # matrices originales de cada corte
        self.volumen = None         # volumen 3D con cada corte escalado x2 (n, 2H, 2W)
        self.volumen_corregido = None
        self.cargar_carpeta()

    # ------------------------------------------------------------------
    def cargar_carpeta(self):
        if not os.path.isdir(self.carpeta):
            raise FileNotFoundError(f"No existe la carpeta: {self.carpeta}")

        archivos = []
        for raiz, _, nombres in os.walk(self.carpeta):
            for nombre in sorted(nombres):
                ruta = os.path.join(raiz, nombre)
                try:
                    ds = pydicom.dcmread(ruta)
                except Exception:
                    continue
                if "PixelData" in ds:
                    archivos.append(ds)
        if not archivos:
            raise ValueError("No se encontraron archivos DICOM con pixeles en la carpeta.")

        primero = archivos[0]
        if int(getattr(primero, "NumberOfFrames", 1) or 1) > 1 or len(archivos) == 1:
            self._cargar_multiframe(primero)
        else:
            self._cargar_cortes(archivos)
        self._escalar_y_reconstruir()

    # ------------------------------------------------------------------
    def _cargar_cortes(self, archivos):
        # una sola serie
        series = defaultdict(list)
        for ds in archivos:
            series[str(getattr(ds, "SeriesInstanceUID", "?"))].append(ds)
        if len(series) > 1:
            grande = max(series.values(), key=len)
            self.advertencias.append(
                f"La carpeta contiene {len(series)} series; se usó la de {len(grande)} cortes.")
            archivos = grande
        else:
            archivos = next(iter(series.values()))

        posiciones = self._posiciones(archivos)
        if posiciones is not None:
            orden = np.argsort(posiciones)
            archivos = [archivos[i] for i in orden]
            posiciones = np.asarray(posiciones)[orden]
        else:
            archivos.sort(key=lambda d: int(getattr(d, "InstanceNumber", 0)))
        self.datasets = archivos

        p = archivos[0]
        self._info_basica(p)
        ps = [float(v) for v in getattr(p, "PixelSpacing", [1.0, 1.0])]
        self.voxel_alto, self.voxel_largo = ps[0], ps[1]
        self.grosor_corte = float(getattr(p, "SliceThickness", 0) or 0) or None

        ancho = None
        if posiciones is not None and len(posiciones) > 1:
            d = np.abs(np.diff(posiciones))
            d = d[d > 1e-6]
            if d.size:
                ancho = round(float(np.median(d)), 6)
        if ancho is None and getattr(p, "SpacingBetweenSlices", None):
            ancho = abs(float(p.SpacingBetweenSlices))
        if ancho is None:
            ancho = self.grosor_corte or 1.0
            self.advertencias.append("No se pudo calcular la separación entre cortes; "
                                     "se usó SliceThickness.")
        self.voxel_ancho = ancho

        self.matrices_pixeles = [self._a_gris(d.pixel_array) for d in archivos]

    def _cargar_multiframe(self, ds):
        self.datasets = [ds]
        self._info_basica(ds)
        arr = ds.pixel_array
        if arr.ndim == 2:
            arr = arr[None]
        if arr.ndim == 4:  # frames, filas, cols, canales (RGB)
            arr = arr.mean(axis=-1).astype(np.uint8)
        self.matrices_pixeles = [arr[i] for i in range(arr.shape[0])]
        ps = None
        sf = ds.get("SharedFunctionalGroupsSequence")
        if sf and sf[0].get("PixelMeasuresSequence"):
            pm = sf[0].PixelMeasuresSequence[0]
            ps = [float(v) for v in pm.PixelSpacing]
            self.grosor_corte = float(pm.get("SliceThickness", 0) or 0) or None
        elif "PixelSpacing" in ds:
            ps = [float(v) for v in ds.PixelSpacing]
        if ps is None:
            ps = [1.0, 1.0]
            self.advertencias.append("El archivo no trae PixelSpacing; se asumió 1 mm.")
        self.voxel_alto, self.voxel_largo = ps
        self.voxel_ancho = self.grosor_corte or 1.0

    def _info_basica(self, ds):
        self.nombre_paciente = str(getattr(ds, "PatientName", "Desconocido")) or "Desconocido"
        self.id_paciente = str(getattr(ds, "PatientID", ""))
        self.modalidad = str(getattr(ds, "Modality", "Desconocida"))

    @staticmethod
    def _a_gris(matriz):
        if matriz.ndim == 3:
            matriz = matriz.mean(axis=-1).astype(np.uint8)
        return matriz

    @staticmethod
    def _posiciones(archivos):
        try:
            iop = np.array(archivos[0].ImageOrientationPatient, dtype=float)
            normal = np.cross(iop[:3], iop[3:])
            return [float(np.dot(normal, np.array(d.ImagePositionPatient, dtype=float)))
                    for d in archivos]
        except Exception:
            return None

    # ------------------------------------------------------------------
    def _escalar_y_reconstruir(self):
        self.filas, self.columnas = self.matrices_pixeles[0].shape
        self.n_cortes = len(self.matrices_pixeles)
        escalados = [cv2.resize(m, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
                     for m in self.matrices_pixeles]
        self.volumen = np.stack(escalados, axis=0)
        self.voxel_escalado = (self.voxel_alto / 2, self.voxel_largo / 2, self.voxel_ancho)

    # ------------------------------------------------------------------
    def corregirAngulo(self, grados):
        """Rota todos los cortes transversales 'grados' alrededor del centro de la imagen."""
        if self.volumen is None:
            raise ValueError("Primero debe construirse el volumen 3D")
        _, filas, cols = self.volumen.shape
        M = cv2.getRotationMatrix2D((cols / 2, filas / 2), grados, 1.0)
        self.volumen_corregido = np.stack(
            [cv2.warpAffine(c, M, (cols, filas)) for c in self.volumen], axis=0)

    def restablecer(self):
        self.volumen_corregido = None

    def volumen_actual(self):
        return self.volumen_corregido if self.volumen_corregido is not None else self.volumen

    # ------------------------------------------------------------------
    def info_tabla(self):
        """Pares (campo, valor) para mostrar en el QTableWidget."""
        a, l, w = self.voxel_alto, self.voxel_largo, self.voxel_ancho
        ea, el, ew = self.voxel_escalado
        n, fa, ca = self.volumen.shape
        filas = [
            ("Paciente", self.nombre_paciente),
            ("ID paciente", self.id_paciente),
            ("Modalidad (Modality)", self.modalidad),
            ("Filas (original)", self.filas),
            ("Columnas (original)", self.columnas),
            ("Número de cortes", self.n_cortes),
            ("Voxel original alto x largo x ancho (mm)", f"{a:.4f} x {l:.4f} x {w:.4f}"),
            ("Tamaño nuevo de cada corte (x2)", f"{fa} x {ca}"),
            ("Voxel nuevo alto x largo x ancho (mm)", f"{ea:.4f} x {el:.4f} x {ew:.4f}"),
            ("Forma del volumen 3D (cortes, filas, cols)", f"{n} x {fa} x {ca}"),
            ("Tipo de dato de pixel", str(self.matrices_pixeles[0].dtype)),
        ]
        for adv in self.advertencias:
            filas.append(("Advertencia", adv))
        return filas

    def info_registro(self):
        """Diccionario listo para guardar en la base de datos."""
        return {
            "carpeta": self.carpeta, "paciente": self.nombre_paciente,
            "modalidad": self.modalidad, "filas": self.filas, "columnas": self.columnas,
            "n_cortes": self.n_cortes, "voxel_alto": self.voxel_alto,
            "voxel_largo": self.voxel_largo, "voxel_ancho": self.voxel_ancho,
            "forma_volumen": tuple(self.volumen.shape),
        }

    def matriz_representativa(self):
        """Matriz de pixeles del corte central (se guarda en la BD)."""
        return self.matrices_pixeles[len(self.matrices_pixeles) // 2]
