"""Controlador principal: flujo Bienvenida -> Login -> Menú -> módulos."""
from config import ROL_IMAGENES, ROL_SENALES, ROLES_NOMBRE
from controlador.ctrl_imagenes import ControladorImagenes
from controlador.ctrl_senales import ControladorCSV, ControladorMAT
from modelo.base_datos import BaseDatos
from vista.ventanas import (VentanaBienvenida, VentanaImagenes, VentanaLogin,
                            VentanaMenu, VentanaSenalesCSV, VentanaSenalesMAT)

SUBMENUS = {
    ROL_IMAGENES: ["Cargar y visualizar DICOM", "Corregir ángulo",
                   "Ecualizar un corte", "Binarizar / umbralizar"],
    ROL_SENALES: ["Señales CSV (ERP)", "Señales MAT (matrices 3D)"],
}


class ControladorApp:
    def __init__(self, ruta_bd=None):
        self.bd = BaseDatos(ruta_bd) if ruta_bd else BaseDatos()
        self.usuario = None

        self.v_bienvenida = VentanaBienvenida()
        self.v_login = VentanaLogin()
        self.v_menu = VentanaMenu()
        self.v_imagenes = VentanaImagenes()
        self.v_csv = VentanaSenalesCSV()
        self.v_mat = VentanaSenalesMAT()

        obtener = lambda: self.usuario
        self.c_imagenes = ControladorImagenes(self.v_imagenes, self.bd, obtener)
        self.c_csv = ControladorCSV(self.v_csv, self.bd, obtener)
        self.c_mat = ControladorMAT(self.v_mat, self.bd, obtener)

        self.v_bienvenida.btnIniciar.clicked.connect(self.ir_a_login)
        self.v_login.btnIngresar.clicked.connect(self.ingresar)
        for i, boton in enumerate(self.v_menu.botones_submenu):
            boton.clicked.connect(lambda _=False, n=i: self.abrir_submenu(n))
        self.v_menu.btnCerrarSesion.clicked.connect(self.cerrar_sesion)
        for ventana in (self.v_imagenes, self.v_csv, self.v_mat):
            ventana.btnVolverMenu.clicked.connect(lambda _=False, w=ventana: self.volver_al_menu(w))

    # ------------------------------------------------------------------
    def iniciar(self):
        self.v_bienvenida.show()

    def ir_a_login(self):
        self.v_bienvenida.hide()
        self.v_login.limpiar()
        self.v_login.show()

    def ingresar(self):
        usuario, clave = self.v_login.credenciales()
        if not usuario.strip() or not clave:
            self.v_login.mostrar_mensaje("Escriba usuario y contraseña.")
            return
        datos = self.bd.validar_usuario(usuario, clave)
        if datos is None:
            self.v_login.mostrar_mensaje("Usuario o contraseña incorrectos.")
            return
        self.usuario = datos
        fecha = self.bd.registrar_sesion(datos["id"])
        self.v_menu.mostrar_usuario(datos, ROLES_NOMBRE[datos["rol"]], fecha)
        self.v_menu.configurar_submenus(SUBMENUS[datos["rol"]])
        self.v_login.hide()
        self.v_menu.show()

    def abrir_submenu(self, n):
        rol = self.usuario["rol"]
        if rol == ROL_IMAGENES:
            self.v_imagenes.seleccionar_pestana(n)
            self.v_imagenes.show()
            self.v_imagenes.raise_()
        elif rol == ROL_SENALES:
            ventana = self.v_csv if n == 0 else self.v_mat
            ventana.show()
            ventana.raise_()

    def volver_al_menu(self, ventana):
        ventana.hide()
        self.v_menu.show()
        self.v_menu.raise_()

    def cerrar_sesion(self):
        for v in (self.v_imagenes, self.v_csv, self.v_mat, self.v_menu):
            v.hide()
        self.usuario = None
        self.v_login.limpiar()
        self.v_login.show()

    def cerrar(self):
        self.bd.cerrar()
