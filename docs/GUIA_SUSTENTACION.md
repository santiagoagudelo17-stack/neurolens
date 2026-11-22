# Preguntas probables en la sustentación (y qué responder)

**¿Dónde está MVC?** Modelo = `modelo/` (no importa Qt). Vista = `vista/` (cada clase carga su .ui y solo lee/escribe widgets). Controlador = `controlador/` (conecta señales de la vista con métodos del modelo).

**¿Cómo cargan los .ui?** `uic.loadUi(ruta, self)` en `VentanaBase`. Cada ventana declara sus `objectName` esperados y se valida al abrir.

**¿Cómo reconstruyen el 3D?** Cada corte se escala x2 con `cv2.resize` y se apilan con `np.stack` → (cortes, 2H, 2W). Coronal = `vol[:, i, :]`, sagital = `vol[:, :, i]`.

**¿Qué es el aspect y cómo lo corrigen?** En coronal/sagital el eje vertical son los cortes y cada uno mide `voxel_ancho` mm mientras un pixel mide `voxel_largo/2` mm; se reescala el alto por `voxel_ancho / (pixel_spacing/2)`.

**¿Por qué en T2 usan 6 mm y no 5?** Porque la separación real entre cortes (calculada con ImagePositionPatient) es 6 mm; el SliceThickness (5 mm) es el grosor, no el paso.

**¿Cómo funciona la rotación?** `cv2.getRotationMatrix2D(centro, grados, 1)` + `cv2.warpAffine`. El QDial rota en vivo el corte visible; "Aplicar" rota todo el volumen (`corregirAngulo`).

**Ecualización:** se normaliza a uint8 (`cv2.normalize`) y se aplica `cv2.equalizeHist`; redistribuye los niveles de gris para aumentar contraste.

**Binarización:** `cv2.threshold` con el tipo del QComboBox (Binary, Binary_inv, Trunc, ToZero, ToZero_inv, Otsu) y apertura morfológica con kernel k×k (k impar) elegido con un QDial.

**.mat 3D→2D:** `(64, 625, N)` → `(64, 625·N)` con `reshape(..., order="F")`, que concatena los ensayos en orden. El eje de tiempo es muestra/fs (fs editable; **confirmen la del Parcial 2**).

**Estadísticas por ejes:** `np.mean/np.std(axis=(a,b))` sobre la matriz 3D original; el vector resultante tiene la longitud del eje restante.

**Diferencia interhemisférica:** canal A − canal B (por ejemplo C3 − C4) por condición.

**¿Cómo protegen las contraseñas?** Hash PBKDF2-SHA256 con sal por usuario.

**¿Qué guardan en la BD?** Metadatos DICOM + matriz de pixeles (corte central) por estudio, sesiones y un registro de cada procesamiento.

> Prepárense para explicar cualquier línea: la IA está permitida, pero la sustentación evalúa que entiendan lo entregado.
