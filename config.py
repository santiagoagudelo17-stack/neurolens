"""Configuración central de NeuroLens (nombre, rutas y constantes)."""
import os

APP_NOMBRE = "NeuroLens"
APP_LEMA = "Visualización y análisis de datos biomédicos"

RAIZ = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(RAIZ, "vista", "ui")
RESULTADOS_DIR = os.path.join(RAIZ, "resultados")
DB_PATH = os.path.join(RAIZ, "neurolens.db")

ROL_IMAGENES = "imagenes"
ROL_SENALES = "senales"
ROLES_NOMBRE = {
    ROL_IMAGENES: "Usuario de imágenes",
    ROL_SENALES: "Usuario de señales",
}

# Columnas del CSV que NO son canales EEG
COLUMNAS_NO_CANAL = ("subject", "condition", "time_ms")

# Frecuencia de muestreo por defecto para los .mat (Hz).
# AJUSTAR con el valor del Parcial 2 (el usuario puede cambiarla en la interfaz).
FS_MAT_DEFECTO = 250
