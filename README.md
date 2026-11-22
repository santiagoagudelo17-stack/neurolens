# NeuroLens — Visualización y análisis de datos biomédicos

Proyecto final · Informática II 2026-2 · Bioingeniería, Universidad de Antioquia
Arquitectura **MVC** · **PyQt5** (interfaces en Qt Designer, cargadas con `uic.loadUi`) · **SQLite**

Integrantes: _(nombres del grupo)_

## Instalación (Windows, Anaconda Prompt)
```
conda create -n neurolens python=3.11
conda activate neurolens
pip install -r requirements.txt
```
(Si el profesor indicó otra forma de instalar PyQt en los .md de Teams, úsenla.)

## Antes de ejecutar
1. Diseñen los `.ui` en Qt Designer siguiendo `docs/GUIA_DISENO_UI.md` y guárdenlos en `vista/ui/`.
2. `python tools/verificar_ui.py` → debe decir *"Todos los .ui cumplen el contrato"*.
3. Copien los datos del curso a `datos/` (opcional; la app pide la ruta con un diálogo).

## Ejecutar
```
python main.py
```
Usuarios de prueba (se crean solos en `neurolens.db`; las claves se guardan con hash PBKDF2):

| Usuario | Clave | Rol |
|---|---|---|
| imagenes1 | img123 | Usuario de imágenes |
| imagenes2 | img456 | Usuario de imágenes |
| senales1 | sen123 | Usuario de señales |
| senales2 | sen456 | Usuario de señales |

## Estructura
```
main.py                 punto de entrada
config.py               nombre de la app, rutas, constantes (frecuencia de muestreo .mat)
modelo/                 lógica y datos (sin Qt): base_datos, volumen_dicom, procesador_imagen, senales
vista/                  ventanas.py (clases que cargan los .ui), graficos.py, ui/*.ui
controlador/            app.py (flujo de ventanas), ctrl_imagenes.py, ctrl_senales.py
pruebas/                prueba integral automática (usa un andamio SOLO para tests)
tools/verificar_ui.py   comprueba los .ui contra el contrato
docs/                   diagrama de clases, guías, manual
```
El Modelo no importa PyQt; la Vista no contiene lógica de negocio; el Controlador conecta señales y coordina.

## Base de datos (SQLite)
`usuarios`, `sesiones` (id, nombre, rol, fecha-hora de ingreso), `estudios_dicom` (paciente, modalidad, filas, columnas, voxel alto/largo/ancho, matriz de pixeles), `procesamientos` (registro de cada análisis).

## Pruebas automáticas
```
set QT_QPA_PLATFORM=offscreen        (Windows; en Linux: export ...)
python pruebas/prueba_integral.py ruta\a\datos
```

## Correcciones respecto al Parcial 3
Orden de cortes por la normal del plano, separación real entre cortes (T2: 6 mm, no el grosor 5 mm), manejo de carpetas con varias series, soporte multiframe, visualización dentro de la interfaz (sin `plt.show()`).
