"""Dibujo de gráficos DENTRO de la interfaz (matplotlib embebido en Qt, nunca plt.show())."""
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QVBoxLayout

COLORES = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]


class Lienzo(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 3.5), tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)


def montar_lienzo(contenedor):
    """Crea un Lienzo dentro de un QWidget (placeholder del .ui) y lo devuelve."""
    lay = contenedor.layout()
    if lay is None:
        lay = QVBoxLayout(contenedor)
        lay.setContentsMargins(0, 0, 0, 0)
    lienzo = Lienzo(contenedor)
    lay.addWidget(lienzo)
    return lienzo


def _etiqueta_condicion(c):
    return f"Condición {c}"


# ----------------------------------------------------------------------
def dibujar_ecualizacion(lienzo, original, ecualizada, plano, indice):
    f = lienzo.fig
    f.clear()
    ax = f.subplots(2, 2)
    ax[0, 0].imshow(original, cmap="gray", aspect="equal")
    ax[0, 0].set_title("Original (uint8)", fontsize=9)
    ax[0, 1].imshow(ecualizada, cmap="gray", aspect="equal")
    ax[0, 1].set_title("Ecualizada", fontsize=9)
    for a in (ax[0, 0], ax[0, 1]):
        a.axis("off")
    ax[1, 0].hist(original.ravel(), bins=256, range=(0, 255), color="#555555")
    ax[1, 0].set_title("Histograma original", fontsize=9)
    ax[1, 1].hist(ecualizada.ravel(), bins=256, range=(0, 255), color="#1f77b4")
    ax[1, 1].set_title("Histograma ecualizado", fontsize=9)
    for a in (ax[1, 0], ax[1, 1]):
        a.set_xlabel("Nivel de gris (0-255)", fontsize=8)
        a.set_ylabel("Frecuencia (pixeles)", fontsize=8)
        a.tick_params(labelsize=7)
    f.suptitle(f"Ecualización - plano {plano}, corte {indice}", fontsize=10)
    lienzo.draw()


def dibujar_stem(lienzo, datos, canal):
    """datos: {condicion: (tiempo_ms, uV)} -> un subplot por condición, línea en t = 0 ms."""
    f = lienzo.fig
    f.clear()
    ejes = f.subplots(len(datos), 1, sharex=True, squeeze=False)[:, 0]
    for i, (ax, (cond, (t, y))) in enumerate(zip(ejes, datos.items())):
        ax.stem(t, y, linefmt=COLORES[i % 6], markerfmt=" ", basefmt="k-")
        ax.axvline(0, color="red", linestyle="--", linewidth=1.5, label="t = 0 ms")
        ax.set_title(f"Canal {canal} - {_etiqueta_condicion(cond)}", fontsize=9)
        ax.set_ylabel("Amplitud (µV)", fontsize=8)
        ax.legend(fontsize=7, loc="upper right")
        ax.tick_params(labelsize=7)
    ejes[-1].set_xlabel("Tiempo (ms)", fontsize=8)
    lienzo.draw()


def dibujar_histograma(lienzo, datos, canal):
    f = lienzo.fig
    f.clear()
    ejes = f.subplots(len(datos), 1, squeeze=False)[:, 0]
    for i, (ax, (cond, (_, y))) in enumerate(zip(ejes, datos.items())):
        ax.hist(y, bins=40, color=COLORES[i % 6], edgecolor="white")
        ax.set_title(f"Histograma canal {canal} - {_etiqueta_condicion(cond)}", fontsize=9)
        ax.set_xlabel("Amplitud (µV)", fontsize=8)
        ax.set_ylabel("Frecuencia (muestras)", fontsize=8)
        ax.tick_params(labelsize=7)
    lienzo.draw()


def dibujar_scatter(lienzo, datos, col_x, col_y):
    f = lienzo.fig
    f.clear()
    ax = f.subplots()
    for i, (cond, (x, y)) in enumerate(datos.items()):
        ax.scatter(x, y, s=6, alpha=0.5, color=COLORES[i % 6], label=_etiqueta_condicion(cond))
    ax.set_title(f"Dispersión: {col_y} vs {col_x}", fontsize=10)
    ax.set_xlabel(_con_unidad(col_x), fontsize=8)
    ax.set_ylabel(_con_unidad(col_y), fontsize=8)
    ax.legend(fontsize=7)
    ax.tick_params(labelsize=7)
    lienzo.draw()


def _con_unidad(col):
    if col == "time_ms":
        return "time_ms (ms)"
    if col in ("subject", "condition"):
        return col
    return f"{col} (µV)"


def dibujar_diferencia(lienzo, datos, canal_a, canal_b):
    f = lienzo.fig
    f.clear()
    ax = f.subplots()
    for i, (cond, (t, d)) in enumerate(datos.items()):
        ax.plot(t, d, color=COLORES[i % 6], linewidth=1, label=_etiqueta_condicion(cond))
    ax.axvline(0, color="k", linestyle="--", linewidth=1)
    ax.set_title(f"Diferencia interhemisférica: {canal_a} - {canal_b}", fontsize=10)
    ax.set_xlabel("Tiempo (ms)", fontsize=8)
    ax.set_ylabel("Diferencia de amplitud (µV)", fontsize=8)
    ax.legend(fontsize=7)
    ax.tick_params(labelsize=7)
    lienzo.draw()


# ----------------------------------------------------------------------
_TITULO_OP = {"suma": "Suma de los 4 canales", "resta": "Resta: C1 - C2 - C3 - C4",
              "multiplicacion": "Multiplicación de los 4 canales"}
_UNIDAD_OP = {"suma": "µV", "resta": "µV", "multiplicacion": "µV⁴"}


def dibujar_operacion(lienzo, tiempo, seg, resultados, nombres_canales):
    f = lienzo.fig
    f.clear()
    ax1, ax2 = f.subplots(2, 1, sharex=True)
    sep = np.ptp(seg) * 1.1 or 1.0
    for i in range(4):
        ax1.plot(tiempo, seg[i] + i * sep, color=COLORES[i], linewidth=1,
                 label=nombres_canales[i])
    ax1.set_title("Canales seleccionados (desplazados verticalmente)", fontsize=9)
    ax1.set_ylabel("Amplitud (µV) + desplazamiento", fontsize=8)
    ax1.legend(fontsize=7, ncol=4, loc="upper right")
    for j, (op, r) in enumerate(resultados.items()):
        ax2.plot(tiempo, r, color=COLORES[(j + 4) % 6], linewidth=1.2,
                 label=f"{op.capitalize()} ({_UNIDAD_OP[op]})")
    titulos = " / ".join(_TITULO_OP[o] for o in resultados)
    ax2.set_title(titulos, fontsize=9)
    ax2.set_xlabel("Tiempo (s)", fontsize=8)
    unidades = ", ".join(sorted({_UNIDAD_OP[o] for o in resultados}))
    ax2.set_ylabel(f"Amplitud ({unidades})", fontsize=8)
    ax2.legend(fontsize=7, loc="upper right")
    for a in (ax1, ax2):
        a.tick_params(labelsize=7)
    lienzo.draw()


def dibujar_boxplots(lienzo, media, desv, eje1, eje2):
    f = lienzo.fig
    f.clear()
    ax = f.subplots()
    ax.boxplot([media, desv], patch_artist=True,
               boxprops=dict(facecolor="#9ecae1"), medianprops=dict(color="red"))
    ax.set_xticks([1, 2])
    ax.set_xticklabels(["Promedio", "Desv. estándar"])
    ax.set_title(f"Distribución del promedio y la desviación estándar (ejes {eje1} y {eje2})",
                 fontsize=9)
    ax.set_ylabel("Amplitud (µV)", fontsize=8)
    ax.tick_params(labelsize=8)
    lienzo.draw()
