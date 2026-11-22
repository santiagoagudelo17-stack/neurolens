"""Verifica que los .ui que ustedes diseñaron en Qt Designer tengan los widgets
(objectName y tipo) que el Controlador espera.   Uso:  python tools/verificar_ui.py"""
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import UI_DIR
from vista import ventanas

clases = [c for c in vars(ventanas).values()
          if isinstance(c, type) and issubclass(c, ventanas.VentanaBase) and c.ARCHIVO_UI]
hay_error = False
for cls in clases:
    ruta = os.path.join(UI_DIR, cls.ARCHIVO_UI)
    print(f"\n== {cls.ARCHIVO_UI}")
    if not os.path.isfile(ruta):
        print("   [FALTA EL ARCHIVO] créelo en Qt Designer y guárdelo en vista/ui/")
        hay_error = True
        continue
    raiz = ET.parse(ruta).getroot().find("widget")
    if raiz.get("class") != "QMainWindow":
        print(f"   [ERROR] el widget raíz debe ser QMainWindow (es {raiz.get('class')}). "
              "Cree el formulario con la plantilla 'Main Window'.")
        hay_error = True
    encontrados = {w.get("name"): w.get("class") for w in raiz.iter("widget")}
    for nombre, clase in cls.WIDGETS.items():
        real = encontrados.get(nombre)
        if real is None:
            print(f"   [FALTA] {nombre} ({clase})")
            hay_error = True
        elif real != clase:
            print(f"   [TIPO]  {nombre}: debe ser {clase} y es {real}")
            hay_error = True
    if not hay_error:
        pass
print("\n" + ("Hay problemas: corrija los marcados." if hay_error else "Todos los .ui cumplen el contrato."))
sys.exit(1 if hay_error else 0)
