"""Capa de persistencia (SQLite). Solo el Modelo habla con la base de datos."""
import hashlib
import io
import json
import os
import secrets
import sqlite3
from datetime import datetime

import numpy as np

from config import DB_PATH, ROL_IMAGENES, ROL_SENALES

USUARIOS_INICIALES = [
    # (usuario, clave, nombre, rol)
    ("imagenes1", "img123", "Santiago Agudelo", ROL_IMAGENES),
    ("imagenes2", "img456", "Isabella Arrieta", ROL_IMAGENES),
    ("senales1", "sen123", "Isabela López", ROL_SENALES),
    ("senales2", "sen456", "Carlos Andrés Guerrero", ROL_SENALES),
]


def _hash(clave, sal):
    return hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal), 100_000).hex()


class BaseDatos:
    def __init__(self, ruta=DB_PATH):
        self.ruta = ruta
        self.conn = sqlite3.connect(ruta)
        self.conn.row_factory = sqlite3.Row
        self._crear_tablas()
        self._sembrar_usuarios()

    # ------------------------------------------------------------------
    def _crear_tablas(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            clave_hash TEXT NOT NULL,
            sal TEXT NOT NULL,
            nombre TEXT NOT NULL,
            rol TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sesiones(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            fecha_hora TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS estudios_dicom(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER REFERENCES usuarios(id),
            fecha_hora TEXT NOT NULL,
            carpeta TEXT,
            paciente TEXT,
            modalidad TEXT,
            filas INTEGER,
            columnas INTEGER,
            n_cortes INTEGER,
            voxel_alto_mm REAL,
            voxel_largo_mm REAL,
            voxel_ancho_mm REAL,
            forma_volumen TEXT,
            dtype TEXT,
            forma_matriz TEXT,
            matriz_pixeles BLOB
        );
        CREATE TABLE IF NOT EXISTS procesamientos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER REFERENCES usuarios(id),
            fecha_hora TEXT NOT NULL,
            tipo TEXT NOT NULL,
            archivo TEXT,
            parametros TEXT,
            resultado TEXT
        );
        """)
        self.conn.commit()

    def _sembrar_usuarios(self):
        if self.conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]:
            return
        for usuario, clave, nombre, rol in USUARIOS_INICIALES:
            sal = secrets.token_hex(16)
            self.conn.execute(
                "INSERT INTO usuarios(usuario, clave_hash, sal, nombre, rol) VALUES(?,?,?,?,?)",
                (usuario, _hash(clave, sal), sal, nombre, rol))
        self.conn.commit()

    # ------------------------------------------------------------------
    def validar_usuario(self, usuario, clave):
        """Devuelve dict con id, nombre, rol o None si las credenciales fallan."""
        fila = self.conn.execute("SELECT * FROM usuarios WHERE usuario=?",
                                 (usuario.strip(),)).fetchone()
        if fila is None:
            return None
        if not secrets.compare_digest(_hash(clave, fila["sal"]), fila["clave_hash"]):
            return None
        return {"id": fila["id"], "usuario": fila["usuario"],
                "nombre": fila["nombre"], "rol": fila["rol"]}

    def registrar_sesion(self, usuario_id):
        ahora = datetime.now()
        self.conn.execute("INSERT INTO sesiones(usuario_id, fecha_hora) VALUES(?,?)",
                          (usuario_id, ahora.isoformat(timespec="seconds")))
        self.conn.commit()
        return ahora

    # ------------------------------------------------------------------
    def guardar_estudio(self, usuario_id, info, matriz):
        """Guarda un registro con los metadatos DICOM y una matriz de pixeles (corte central)."""
        buf = io.BytesIO()
        np.save(buf, matriz)
        cur = self.conn.execute(
            """INSERT INTO estudios_dicom(usuario_id, fecha_hora, carpeta, paciente, modalidad,
               filas, columnas, n_cortes, voxel_alto_mm, voxel_largo_mm, voxel_ancho_mm,
               forma_volumen, dtype, forma_matriz, matriz_pixeles)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (usuario_id, datetime.now().isoformat(timespec="seconds"),
             info["carpeta"], info["paciente"], info["modalidad"], info["filas"],
             info["columnas"], info["n_cortes"], info["voxel_alto"], info["voxel_largo"],
             info["voxel_ancho"], str(info["forma_volumen"]), str(matriz.dtype),
             str(matriz.shape), buf.getvalue()))
        self.conn.commit()
        return cur.lastrowid

    def listar_estudios(self):
        return [dict(f) for f in self.conn.execute(
            "SELECT id, fecha_hora, paciente, modalidad, filas, columnas, n_cortes "
            "FROM estudios_dicom")]

    def cargar_matriz_estudio(self, estudio_id):
        fila = self.conn.execute("SELECT matriz_pixeles FROM estudios_dicom WHERE id=?",
                                 (estudio_id,)).fetchone()
        return np.load(io.BytesIO(fila["matriz_pixeles"])) if fila else None

    def guardar_procesamiento(self, usuario_id, tipo, archivo, parametros, resultado):
        self.conn.execute(
            "INSERT INTO procesamientos(usuario_id, fecha_hora, tipo, archivo, parametros, resultado)"
            " VALUES(?,?,?,?,?,?)",
            (usuario_id, datetime.now().isoformat(timespec="seconds"), tipo,
             os.path.basename(str(archivo or "")), json.dumps(parametros, default=str),
             json.dumps(resultado, default=str)))
        self.conn.commit()

    def cerrar(self):
        self.conn.close()