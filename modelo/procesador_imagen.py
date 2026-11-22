"""Procesamiento de cortes: planos anatómicos, ecualización, binarización y rotación.
No dibuja nada (la visualización es responsabilidad de la Vista)."""
import os

import cv2
import numpy as np

PLANOS = ("transversal", "coronal", "sagital")

TIPOS_BINARIZACION = {
    "Binary": cv2.THRESH_BINARY,
    "Binary_inv": cv2.THRESH_BINARY_INV,
    "Trunc": cv2.THRESH_TRUNC,
    "ToZero": cv2.THRESH_TOZERO,
    "ToZero_inv": cv2.THRESH_TOZERO_INV,
    "Otsu": cv2.THRESH_BINARY + cv2.THRESH_OTSU,
}


def a_uint8(matriz):
    """Normaliza cualquier matriz a uint8 (0-255)."""
    m = matriz.astype(np.float32)
    return cv2.normalize(m, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)


class ProcesadorImagen:
    def __init__(self, volumen_dicom):
        self.vol = volumen_dicom

    # ------------------------------------------------------------------
    def maximo_indice(self, plano):
        n, filas, cols = self.vol.volumen_actual().shape
        return {"transversal": n, "coronal": filas, "sagital": cols}[plano] - 1

    def obtener_corte(self, plano, indice):
        """Corte crudo (sin normalizar) del plano pedido, con el aspect ya corregido."""
        v = self.vol.volumen_actual()
        indice = int(np.clip(indice, 0, self.maximo_indice(plano)))
        if plano == "transversal":
            return v[indice]
        corte = v[:, indice, :] if plano == "coronal" else v[:, :, indice]
        # En coronal/sagital el eje vertical son los cortes: cada fila mide 'ancho' mm
        # y cada columna mide 'voxel_escalado[0]' mm -> se estira el alto por esa razón.
        aspect = self.vol.voxel_ancho / self.vol.voxel_escalado[0]
        nuevo_alto = max(1, int(round(corte.shape[0] * aspect)))
        return cv2.resize(corte.astype(np.float32), (corte.shape[1], nuevo_alto),
                          interpolation=cv2.INTER_LINEAR)

    def corte_uint8(self, plano, indice):
        return a_uint8(self.obtener_corte(plano, indice))

    # ------------------------------------------------------------------
    @staticmethod
    def rotar_corte(corte_u8, grados):
        h, w = corte_u8.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), grados, 1.0)
        return cv2.warpAffine(corte_u8, M, (w, h))

    @staticmethod
    def ecualizar(corte_u8):
        return cv2.equalizeHist(corte_u8)

    @staticmethod
    def binarizar(corte_u8, umbral, tam_kernel, tipo):
        """Umbraliza según 'tipo' y aplica apertura morfológica con kernel tam x tam."""
        flag = TIPOS_BINARIZACION[tipo]
        _, bin_img = cv2.threshold(corte_u8, int(umbral), 255, flag)
        k = int(tam_kernel)
        if k > 1:
            kernel = np.ones((k, k), np.uint8)
            bin_img = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel)
        return bin_img

    # ------------------------------------------------------------------
    @staticmethod
    def guardar_png(ruta, imagen):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        cv2.imwrite(ruta, imagen)
