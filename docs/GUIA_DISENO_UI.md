# Guía para diseñar los .ui en Qt Designer
> **Los `.ui` los deben hacer ustedes.** El enunciado dice que no se califica sin evidencia de `.ui` hechos por el grupo y que no se aceptan diseños hechos por IA. Este documento solo lista los *nombres de objeto* (`objectName`) que el código necesita; el diseño visual (colores, fuentes, logo, iconos, disposición) es suyo.
## Pasos
1. Abra Qt Designer (en Anaconda: `designer` o `pyqt5-tools designer`, según el .md de Teams).
2. Nuevo formulario con la plantilla **Main Window** (el widget raíz DEBE ser `QMainWindow`).
3. Arrastre los widgets de la tabla de cada ventana y cambie su **objectName** (panel *Property Editor* → `objectName`) por el nombre exacto indicado. Mayúsculas y minúsculas importan.
4. Personalice: *styleSheet*, fuentes, colores, iconos (`Resource`/rutas), imágenes de fondo, `windowTitle`.
5. Guarde con el nombre indicado dentro de `vista/ui/`.
6. Compruebe: `python tools/verificar_ui.py` (le dice qué falta). Luego `python main.py`.

No hay que escribir ninguna señal/slot en Designer: el controlador conecta todo por código.

## `ventana_bienvenida.ui`

Pantalla de bienvenida: logo, nombre de la app, mensaje y botón de inicio. Es la que más pueden decorar (imagen de fondo, fuente propia).

| objectName | Tipo de widget |
|---|---|
| `labelTitulo` | QLabel |
| `labelBienvenida` | QLabel |
| `btnIniciar` | QPushButton |

## `ventana_login.ui`

Dos campos de texto, botón y una etiqueta para errores. El campo de clave se oculta por código.

| objectName | Tipo de widget |
|---|---|
| `lineEditUsuario` | QLineEdit |
| `lineEditClave` | QLineEdit |
| `btnIngresar` | QPushButton |
| `labelEstado` | QLabel |

## `ventana_menu.ui`

Tercera ventana. Arriba los 4 datos del usuario; en el centro los botones de submenú (el texto lo pone el código según el rol; para señales solo se usan 2 y se ocultan los demás); abajo cerrar sesión.

| objectName | Tipo de widget |
|---|---|
| `labelId` | QLabel |
| `labelNombre` | QLabel |
| `labelRol` | QLabel |
| `labelFechaHora` | QLabel |
| `btnSubmenu1` | QPushButton |
| `btnSubmenu2` | QPushButton |
| `btnSubmenu3` | QPushButton |
| `btnSubmenu4` | QPushButton |
| `btnCerrarSesion` | QPushButton |

## `ventana_imagenes.ui`

Ventana principal de imágenes. Sugerencia: columna izquierda con carga de carpeta + tabla; arriba del centro los 3 radio buttons, el scrollbar horizontal y la etiqueta del corte; debajo un QTabWidget con EXACTAMENTE 4 pestañas en este orden: 0 Visor, 1 Rotación, 2 Ecualización, 3 Binarización. Cada QLabel de imagen conviene con tamaño mínimo ~400x400 y alineación centrada. 'widgetGraficoEcualizacion' es un QWidget vacío (el código le inserta la figura).

| objectName | Tipo de widget |
|---|---|
| `btnCargarCarpeta` | QPushButton |
| `labelCarpeta` | QLabel |
| `tableInfo` | QTableWidget |
| `radioTransversal` | QRadioButton |
| `radioCoronal` | QRadioButton |
| `radioSagital` | QRadioButton |
| `scrollCortes` | QScrollBar |
| `labelNumeroCorte` | QLabel |
| `tabWidget` | QTabWidget |
| `labelVisor` | QLabel |
| `dialAngulo` | QDial |
| `labelAngulo` | QLabel |
| `btnAplicarRotacion` | QPushButton |
| `btnRestablecerRotacion` | QPushButton |
| `labelRotada` | QLabel |
| `btnEcualizar` | QPushButton |
| `widgetGraficoEcualizacion` | QWidget |
| `dialUmbral` | QDial |
| `labelUmbral` | QLabel |
| `dialKernel` | QDial |
| `labelKernel` | QLabel |
| `comboBinarizacion` | QComboBox |
| `labelBinaria` | QLabel |
| `btnVolverMenu` | QPushButton |

## `ventana_senales_csv.ui`

Sugerencia: izquierda los controles (cargar, combos, 4 botones); derecha un QTabWidget con las 4 gráficas (Stem, Histograma, Scatter, Diferencia) y otra pestaña/zona con info + describe. Los 'widgetXXX' son QWidget vacíos donde el código inserta la gráfica.

| objectName | Tipo de widget |
|---|---|
| `btnCargarCSV` | QPushButton |
| `labelArchivo` | QLabel |
| `textInfo` | QPlainTextEdit |
| `tableDescribe` | QTableWidget |
| `comboCanal` | QComboBox |
| `comboX` | QComboBox |
| `comboY` | QComboBox |
| `comboCanalA` | QComboBox |
| `comboCanalB` | QComboBox |
| `btnGraficarStem` | QPushButton |
| `btnGraficarHist` | QPushButton |
| `btnGraficarScatter` | QPushButton |
| `btnGraficarDiferencia` | QPushButton |
| `widgetStem` | QWidget |
| `widgetHist` | QWidget |
| `widgetScatter` | QWidget |
| `widgetDiferencia` | QWidget |
| `btnVolverMenu` | QPushButton |

## `ventana_senales_mat.ui`

Sugerencia: bloque 'Archivo' (cargar, llaves, seleccionar, forma, frecuencia de muestreo), bloque 'Operación' (4 combos de canal, mín, máx, 3 checkboxes, botón, gráfica) y bloque 'Estadísticas' (2 combos de eje, botón, etiqueta, gráfica).

| objectName | Tipo de widget |
|---|---|
| `btnCargarMAT` | QPushButton |
| `labelArchivo` | QLabel |
| `comboLlaves` | QComboBox |
| `btnSeleccionarLlave` | QPushButton |
| `labelForma` | QLabel |
| `spinFs` | QSpinBox |
| `comboCanal1` | QComboBox |
| `comboCanal2` | QComboBox |
| `comboCanal3` | QComboBox |
| `comboCanal4` | QComboBox |
| `spinMin` | QSpinBox |
| `spinMax` | QSpinBox |
| `checkSuma` | QCheckBox |
| `checkResta` | QCheckBox |
| `checkMultiplicacion` | QCheckBox |
| `btnOperar` | QPushButton |
| `widgetOperacion` | QWidget |
| `comboEje1` | QComboBox |
| `comboEje2` | QComboBox |
| `btnEstadisticas` | QPushButton |
| `labelFormaResultado` | QLabel |
| `widgetBoxplot` | QWidget |
| `btnVolverMenu` | QPushButton |

## Consejos de diseño (para que se vea personalizado)

- Definan una paleta de 3-4 colores y úsenla en todas las ventanas (styleSheet de la ventana).
- Usen una fuente distinta a la de defecto (Property Editor → font) y el logo del grupo en bienvenida y login.
- Pongan layouts (grid/vertical/horizontal) en las ventanas para que se adapten al tamaño.
- Dejen el QLabel de imagen con `sizePolicy` Expanding y fondo oscuro; las imágenes médicas se ven mejor.
- Guarden sus capturas del Designer: son evidencia para la sustentación.
