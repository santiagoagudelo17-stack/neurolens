"""Modelo de señales biomédicas: CSV (ERP) y MAT (matrices 3D). Sin dependencia de Qt."""
import io

import numpy as np
import pandas as pd
import scipy.io as sio

from config import COLUMNAS_NO_CANAL


class ErrorNoArreglo(Exception):
    """La llave elegida del .mat no corresponde a un arreglo numérico."""


# ======================================================================
class SenalesCSV:
    def __init__(self):
        self.ruta = None
        self.df = None

    def cargar(self, ruta):
        df = pd.read_csv(ruta)
        faltan = [c for c in ("condition", "time_ms") if c not in df.columns]
        if faltan:
            raise ValueError(f"El CSV no tiene las columnas requeridas: {', '.join(faltan)}")
        self.ruta, self.df = ruta, df
        return df

    @property
    def canales(self):
        return [c for c in self.df.columns if c not in COLUMNAS_NO_CANAL]

    @property
    def columnas(self):
        return list(self.df.columns)

    @property
    def condiciones(self):
        return sorted(self.df["condition"].unique())

    def info_texto(self):
        buf = io.StringIO()
        self.df.info(buf=buf)
        return buf.getvalue()

    def describe(self):
        return self.df.describe().round(4)

    # --- datos listos para graficar --------------------------------------
    def por_condicion(self, canal):
        """{condicion: (tiempo_ms, amplitud_uV)} para un canal."""
        return {c: (g["time_ms"].to_numpy(), g[canal].to_numpy())
                for c, g in self.df.groupby("condition")}

    def scatter(self, col_x, col_y):
        """{condicion: (x, y)} para dos columnas cualquiera."""
        return {c: (g[col_x].to_numpy(), g[col_y].to_numpy())
                for c, g in self.df.groupby("condition")}

    def diferencia_interhemisferica(self, canal_a, canal_b):
        """{condicion: (tiempo_ms, canal_a - canal_b)}"""
        return {c: (g["time_ms"].to_numpy(), (g[canal_a] - g[canal_b]).to_numpy())
                for c, g in self.df.groupby("condition")}


# ======================================================================
OPERACIONES = ("suma", "resta", "multiplicacion")


class SenalesMAT:
    def __init__(self):
        self.ruta = None
        self.contenido = {}
        self.llave = None
        self.arreglo = None  # matriz 3D sin modificar (canales, tiempos, ensayos)

    def cargar(self, ruta):
        crudo = sio.loadmat(ruta)
        # Se validan las variables reales (las que no empiezan con "__"), pero en el
        # QComboBox se ofrecen TODAS las llaves, para que "No es un arreglo" pueda salir.
        if not any(not k.startswith("__") for k in crudo):
            raise ValueError("El archivo .mat no contiene variables.")
        self.contenido = dict(crudo)
        self.ruta, self.llave, self.arreglo = ruta, None, None
        return list(self.contenido.keys())

    def seleccionar_llave(self, llave):
        valor = self.contenido.get(llave)
        if (not isinstance(valor, np.ndarray) or not np.issubdtype(valor.dtype, np.number)
                or valor.ndim < 2):
            raise ErrorNoArreglo("No es un arreglo, vuelva a intentarlo")
        if valor.ndim != 3:
            raise ErrorNoArreglo(
                f"Se esperaba una matriz 3D (canales, tiempos, ensayos) y la forma es {valor.shape}")
        self.llave, self.arreglo = llave, valor.astype(np.float64)
        return self.arreglo.shape

    # --- reshape 3D -> 2D ------------------------------------------------
    def a_2d(self):
        """(canales, tiempos, ensayos) -> (canales, tiempos*ensayos): ensayos concatenados."""
        c = self.arreglo.shape[0]
        return self.arreglo.reshape(c, -1, order="F")

    def operar(self, canales, p_min, p_max, operaciones, fs):
        """Aplica suma/resta/multiplicación a 4 canales entre p_min y p_max (muestras).
        Devuelve (tiempo_s, matriz_4xN, {operacion: resultado})."""
        if len(canales) != 4:
            raise ValueError("Se requieren exactamente 4 canales.")
        if not operaciones:
            raise ValueError("Seleccione al menos una operación.")
        m = self.a_2d()
        n_canales, total = m.shape
        if any(c < 0 or c >= n_canales for c in canales):
            raise ValueError(f"Los canales deben estar entre 0 y {n_canales - 1}.")
        if p_min < 0 or p_max > total or p_min >= p_max:
            raise ValueError(f"Rango inválido: debe cumplirse 0 <= mín < máx <= {total}.")
        seg = m[list(canales), p_min:p_max]
        tiempo = np.arange(p_min, p_max) / float(fs)
        res = {}
        for op in operaciones:
            if op == "suma":
                res[op] = seg.sum(axis=0)
            elif op == "resta":
                res[op] = seg[0] - seg[1] - seg[2] - seg[3]
            elif op == "multiplicacion":
                res[op] = seg.prod(axis=0)
            else:
                raise ValueError(f"Operación desconocida: {op}")
        return tiempo, seg, res

    def estadisticas(self, eje1, eje2):
        """Promedio y desviación estándar sobre dos ejes de la matriz 3D original."""
        if eje1 == eje2:
            raise ValueError("Elija dos ejes distintos.")
        ejes = (eje1, eje2)
        media = self.arreglo.mean(axis=ejes)
        desv = self.arreglo.std(axis=ejes)
        return media, desv