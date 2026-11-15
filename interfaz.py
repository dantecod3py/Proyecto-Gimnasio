"""Interfaz gráfica del Sistema de Gestión de Gimnasio (customtkinter + SQLite).

Instalar:  py -m pip install customtkinter
Ejecutar:  py interfaz.py
"""
import re
import sqlite3
from datetime import datetime, timedelta
from tkinter import ttk, messagebox
from types import SimpleNamespace

import customtkinter as ctk

from database import conectar, inicializar_bd

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

PLANES = ["Mensual", "Trimestral", "Anual"]
ESTADOS = ["Activa", "Vencida", "Pendiente"]
METODOS = ["Efectivo", "Transferencia", "Tarjeta"]
ROLES = ["operador", "admin"]
FECHA = "%Y-%m-%d"
MAX_INTENTOS = 3
FONDO, MENU, PRIMARIO = "#F4F6F9", "#172B4D", "#087E8B"
VERDE, ROJO, NARANJA = "#198754", "#DC3545", "#F39C12"
BOTONES = {"verde": (VERDE, "#146C43"), "azul": (PRIMARIO, "#06616B"), "rojo": (ROJO, "#A52834"),
           "gris": ("#6C757D", "#565E64"), "naranja": (NARANJA, "#C77C00")}


# ---------------------------------------------------------- utilidades
def formato_gs(valor):
    """150000 -> 'G. 150.000' (los guaraníes no llevan decimales)."""
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return "G. 0"
    if valor.is_integer():
        return "G. " + f"{int(valor):,}".replace(",", ".")
    return "G. " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def leer_monto(texto):
    """Acepta 150000, 150.000, 150000,50 o 150000.50. Lanza ValueError."""
    t = texto.strip().replace(" ", "")
    t = t.replace(".", "").replace(",", ".") if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", t) \
        else t.replace(",", ".")
    valor = float(t)
    if valor <= 0:
        raise ValueError
    return valor


def leer_fecha(texto):
    return datetime.strptime(texto.strip(), FECHA).strftime(FECHA)


def hoy():
    return datetime.now().strftime(FECHA)


def plural(n, singular, plural_):
    return f"{n} {singular if n == 1 else plural_}"


def fijar_combo(combo, valor, base):
    """Selecciona 'valor'; si no está entre las opciones (dato cargado a mano) lo agrega."""
    valores = list(base) + ([valor] if valor and valor not in base else [])
    combo.configure(values=valores)
    combo.set(valor or (base[0] if base else ""))


def _db(sql, params, escribir):
    con = conectar()
    if con is None:
        raise RuntimeError("No se pudo conectar con la base de datos.")
    try:
        cur = con.cursor()
        cur.execute(sql, params)
        if not escribir:
            return cur.fetchall()
        con.commit()
        return cur.lastrowid, cur.rowcount
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def consultar(sql, params=()):
    return _db(sql, params, False)


def ejecutar(sql, params=()):
    """INSERT/UPDATE/DELETE. Devuelve (último id, filas afectadas)."""
    return _db(sql, params, True)


# ------------------------------------------------- reportes (JOIN)
REPORTES = {
    "Pagos por miembro": (
        "SELECT m.nombre, m.apellido, m.cedula, p.monto, p.fecha_pago, p.metodo "
        "FROM miembros m JOIN pagos p ON m.id_miembro = p.id_miembro ORDER BY p.fecha_pago DESC",
        [("nombre", "Nombre", 140), ("apellido", "Apellido", 140), ("cedula", "Cédula", 120),
         ("monto", "Monto", 130, "gs"), ("fecha", "Fecha de pago", 130), ("metodo", "Método", 130)]),
    "Suscripciones activas": (
        "SELECT m.nombre, m.apellido, s.plan_cuota, s.cuota, s.fecha_inicio, s.fecha_vencimiento, "
        "s.estado FROM miembros m JOIN suscripciones s ON m.id_miembro = s.id_miembro "
        "WHERE s.estado = 'Activa'",
        [("nombre", "Nombre", 120), ("apellido", "Apellido", 120), ("plan", "Plan", 160),
         ("cuota", "Cuota", 120, "gs"), ("inicio", "Inicio", 110), ("venc", "Vencimiento", 110),
         ("estado", "Estado", 90)]),
    "Miembro, suscripción y pagos": (
        "SELECT m.id_miembro, m.nombre || ' ' || m.apellido AS miembro, s.plan_cuota, "
        "s.estado AS estado_suscripcion, p.monto, p.fecha_pago FROM miembros m "
        "LEFT JOIN suscripciones s ON m.id_miembro = s.id_miembro "
        "LEFT JOIN pagos p ON m.id_miembro = p.id_miembro ORDER BY m.id_miembro",
        [("id", "ID", 50), ("miembro", "Miembro", 200), ("plan", "Plan", 170),
         ("estado", "Estado suscripción", 140), ("monto", "Monto", 130, "gs"),
         ("fecha", "Fecha de pago", 130)]),
}


# ------------------------------------------------ módulos CRUD
# Cada módulo se describe con datos; Aplicacion.mostrar_modulo construye todo.
#   campos: (columna_bd, etiqueta, tipo, fila, columna[, extra[, ancho]])
#   tipos : txt (obligatorio) | opt (opcional) | int | monto | fecha | clave
#           combo | edit (combo editable) | miembro (combo de miembros)
#   extra : combo/edit -> opciones | int/monto -> (título, mensaje) de error
#           fecha -> "hoy" para que arranque con la fecha actual
def _confirma_miembro(app, id_):
    n_s = consultar("SELECT COUNT(*) FROM suscripciones WHERE id_miembro = ?", (id_,))[0][0]
    n_p = consultar("SELECT COUNT(*) FROM pagos WHERE id_miembro = ?", (id_,))[0][0]
    return ("¿Estás seguro de eliminar el miembro seleccionado?\n\n"
            f"También se eliminarán sus {n_s} suscripción(es) y {n_p} pago(s).\n"
            "Esta operación no se puede deshacer.")


def _confirma_usuario(app, id_):
    if id_ == app.usuario[0]:
        return app.aviso("No permitido", "No podés eliminar tu propio usuario mientras tenés "
                                         "la sesión abierta.")
    fila = consultar("SELECT usuario, rol FROM usuarios WHERE id_usuario = ?", (id_,))
    admins = consultar("SELECT COUNT(*) FROM usuarios WHERE rol = 'admin'")[0][0]
    if not fila:
        return None
    if fila[0][1] == "admin" and admins <= 1:
        return app.aviso("No permitido", "No se puede eliminar el único administrador.")
    return f"¿Eliminar el usuario «{fila[0][0]}»?"


ERR_CUOTA = ("Cuota inválida", "La cuota debe ser un número mayor que cero.")
ERR_MONTO = ("Monto inválido", "El monto debe ser un número mayor que cero.")
ERR_EDAD = ("Edad inválida", "La edad debe ser un número entero mayor que cero.")

MODULOS = {
    "miembros": dict(
        menu="Miembros", titulo="GESTIÓN DE MIEMBROS", form="DATOS DEL MIEMBRO",
        sing="miembro", plur="miembros", tabla="miembros", pk="id_miembro",
        oblig="Nombre, apellido y cédula son obligatorios.",
        campos=[("nombre", "Nombre", "txt", 1, 0), ("apellido", "Apellido", "txt", 1, 1),
                ("cedula", "Cédula", "txt", 2, 0), ("edad", "Edad (opcional)", "int", 2, 1, ERR_EDAD),
                ("genero", "Género (opcional)", "opt", 3, 0),
                ("contacto", "Contacto (opcional)", "opt", 3, 1)],
        cols=[("id", "ID", 50), ("nombre", "Nombre", 140), ("apellido", "Apellido", 140),
              ("cedula", "Cédula", 110), ("edad", "Edad", 60), ("genero", "Género", 110),
              ("contacto", "Contacto", 140)],
        busq="Buscar por nombre, apellido o cédula...",
        sql="SELECT id_miembro, nombre, apellido, cedula, edad, genero, contacto FROM miembros "
            "WHERE nombre LIKE ? OR apellido LIKE ? OR cedula LIKE ? ORDER BY id_miembro",
        dup=("Cédula repetida", "Ya existe un miembro registrado con esa cédula.",
             "Esa cédula ya pertenece a otro miembro."),
        confirma=_confirma_miembro,
        ask_mod="¿Deseás guardar los cambios del miembro seleccionado?",
        ok_mod="Los datos del miembro fueron actualizados."),
    "suscripciones": dict(
        menu="Suscripciones", titulo="GESTIÓN DE SUSCRIPCIONES", form="DATOS DE LA SUSCRIPCIÓN",
        sing="suscripción", plur="suscripciones", f=True, tabla="suscripciones", pk="id_suscripcion",
        oblig="El plan y el estado son obligatorios.",
        msg_miembro="Seleccioná un miembro. Si no hay, registralo primero.",
        campos=[("id_miembro", "Miembro", "miembro", 1, 0),
                ("plan_cuota", "Plan (elegí o escribí otro)", "edit", 1, 1, PLANES),
                ("cuota", "Cuota (G.)", "monto", 2, 0, ERR_CUOTA),
                ("estado", "Estado", "combo", 2, 1, ESTADOS),
                ("fecha_inicio", "Fecha de inicio (AAAA-MM-DD)", "fecha", 3, 0, "hoy"),
                ("fecha_vencimiento", "Fecha de vencimiento (AAAA-MM-DD)", "fecha", 3, 1)],
        cols=[("id", "ID", 50), ("miembro", "Miembro", 190), ("plan", "Plan", 120),
              ("cuota", "Cuota", 110, "gs"), ("inicio", "Inicio", 100),
              ("venc", "Vencimiento", 110), ("estado", "Estado", 90)],
        busq="Buscar por miembro, plan o estado...",
        sql="SELECT s.id_suscripcion, m.nombre || ' ' || m.apellido, s.plan_cuota, s.cuota, "
            "s.fecha_inicio, s.fecha_vencimiento, s.estado FROM suscripciones s "
            "INNER JOIN miembros m ON m.id_miembro = s.id_miembro "
            "WHERE m.nombre LIKE ? OR m.apellido LIKE ? OR m.cedula LIKE ? OR s.plan_cuota LIKE ? "
            "OR s.estado LIKE ? ORDER BY s.id_suscripcion DESC",
        tag=6, tags={"Activa": VERDE, "Vencida": ROJO, "Pendiente": NARANJA},
        check=lambda d: ("Fechas inválidas", "La fecha de vencimiento no puede ser anterior "
                                             "a la de inicio.")
        if d["fecha_vencimiento"] < d["fecha_inicio"] else None),
    "pagos": dict(
        menu="Pagos", titulo="GESTIÓN DE PAGOS", form="DATOS DEL PAGO",
        sing="pago", plur="pagos", tabla="pagos", pk="pago_id",
        msg_miembro="Seleccioná el miembro que realiza el pago.",
        campos=[("id_miembro", "Miembro", "miembro", 1, 0),
                ("monto", "Monto (G.)", "monto", 1, 1, ERR_MONTO),
                ("fecha_pago", "Fecha de pago (AAAA-MM-DD)", "fecha", 2, 0, "hoy"),
                ("metodo", "Método de pago", "combo", 2, 1, METODOS)],
        cols=[("id", "ID", 50), ("miembro", "Miembro", 220), ("monto", "Monto", 140, "gs"),
              ("fecha", "Fecha de pago", 130), ("metodo", "Método", 140)],
        busq="Buscar por miembro, monto, método o fecha...",
        sql="SELECT p.pago_id, m.nombre || ' ' || m.apellido, p.monto, p.fecha_pago, p.metodo "
            "FROM pagos p INNER JOIN miembros m ON m.id_miembro = p.id_miembro "
            "WHERE m.nombre LIKE ? OR m.apellido LIKE ? OR m.cedula LIKE ? "
            "OR CAST(p.monto AS TEXT) LIKE ? OR p.metodo LIKE ? OR p.fecha_pago LIKE ? "
            "ORDER BY p.fecha_pago DESC, p.pago_id DESC",
        total=lambda filas: f"Recaudado: {formato_gs(sum(f[2] for f in filas))}  |  "
                            + plural(len(filas), "pago", "pagos"),
        ok_reg=lambda i, d: ("Pago registrado", f"Pago N° {i} registrado.\n\nMonto: "
                             f"{formato_gs(d['monto'])}\nFecha: {d['fecha_pago']}\nMétodo: {d['metodo']}")),
    "usuarios": dict(
        menu="Usuarios", titulo="USUARIOS DEL SISTEMA", form="NUEVO USUARIO", admin=True,
        sing="usuario", plur="usuarios", tabla="usuarios", pk="id_usuario", sin_mod=True,
        rellenar=False, oblig="Usuario y contraseña no pueden estar vacíos.",
        campos=[("usuario", "Nombre de usuario", "txt", 1, 0), ("password", "Contraseña", "clave", 1, 1),
                ("rol", "Rol", "combo", 2, 0, ROLES, 220)],
        cols=[("id", "ID", 60), ("usuario", "Usuario", 280), ("rol", "Rol", 180)],
        sql="SELECT id_usuario, usuario, rol FROM usuarios ORDER BY id_usuario",
        dup=("Usuario repetido", "Ya existe un usuario con ese nombre."),
        confirma=_confirma_usuario,
        ok_reg=lambda i, d: ("Registro exitoso", "Usuario registrado correctamente.")),
}
for _c in MODULOS.values():   # concordancia de género para los mensajes (el/la, un/una...)
    _f = _c.get("f", False)
    _c.update(un="una" if _f else "un", el="la" if _f else "el", o="a" if _f else "o",
              de="de la" if _f else "del", los="las" if _f else "los")


def campos(c):
    """Completa cada campo con extra=None y ancho=380 cuando no los trae."""
    return [(*f, *(None, 380)[len(f) - 5:]) for f in c["campos"]]


# ---------------------------------------------------- aplicación
class Aplicacion(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("SISTEMA DE GESTIÓN DE GIMNASIO")
        ancho, alto = min(1250, self.winfo_screenwidth() - 40), min(780, self.winfo_screenheight() - 90)
        self.geometry(f"{ancho}x{alto}")
        self.minsize(min(1100, ancho), min(650, alto))
        self.usuario, self.intentos = None, MAX_INTENTOS    # usuario = (id, nombre, rol)
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Treeview", background="white", foreground="#333333", rowheight=32,
                         fieldbackground="white", font=("Arial", 10))
        estilo.configure("Treeview.Heading", background=MENU, foreground="white",
                         font=("Arial", 10, "bold"), padding=8)
        estilo.map("Treeview", background=[("selected", PRIMARIO)], foreground=[("selected", "white")])
        self.mostrar_login()

    # ------------------------------------------------ estructura
    def limpiar_ventana(self):
        for w in self.winfo_children():
            w.destroy()

    def limpiar_contenido(self):
        for w in self.contenido.winfo_children():
            w.destroy()

    def crear_interfaz(self):
        menu = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=MENU)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)
        ctk.CTkLabel(menu, text="GESTIÓN DE\nGIMNASIO", font=("Arial", 22, "bold"),
                     text_color="white").pack(pady=(30, 6))
        ctk.CTkLabel(menu, text=f"{self.usuario[1]}  ({self.usuario[2]})", font=("Arial", 12),
                     text_color="#9FB3C8").pack(pady=(0, 22))
        opciones = ([("Inicio", self.mostrar_inicio)]
                    + [(MODULOS[k]["menu"], lambda k=k: self.mostrar_modulo(k))
                       for k in ("miembros", "suscripciones", "pagos")]
                    + [("Consultas", self.mostrar_consultas)])
        if self.usuario[2] == "admin":
            opciones.append(("Usuarios", lambda: self.mostrar_modulo("usuarios")))
        for texto, cmd in opciones:
            ctk.CTkButton(menu, text=texto, height=42, corner_radius=8, anchor="w",
                          fg_color="transparent", hover_color="#29466E", text_color="white",
                          font=("Arial", 14), command=cmd).pack(fill="x", padx=15, pady=4)
        for texto, color, hover, cmd, pady in (("Cerrar sistema", "#B02A37", "#842029", self.destroy, (6, 25)),
                                               ("Cerrar sesión", "#29466E", "#365A8A", self.cerrar_sesion, 6)):
            ctk.CTkButton(menu, text=texto, height=42, fg_color=color, hover_color=hover,
                          text_color="white", command=cmd).pack(side="bottom", fill="x", padx=15, pady=pady)
        self.contenido = ctk.CTkFrame(self, fg_color=FONDO, corner_radius=0)
        self.contenido.pack(side="right", fill="both", expand=True)

    # ------------------------------------------------------ login
    def mostrar_login(self):
        self.limpiar_ventana()
        self.usuario, self.intentos = None, MAX_INTENTOS
        self.configure(fg_color=MENU)
        t = ctk.CTkFrame(self, fg_color="white", corner_radius=16, width=440, height=470)
        t.place(relx=0.5, rely=0.5, anchor="center")
        t.pack_propagate(False)
        ctk.CTkLabel(t, text="INICIO DE SESIÓN", font=("Arial", 26, "bold"),
                     text_color=MENU).pack(pady=(40, 4))
        ctk.CTkLabel(t, text="Sistema de gestión de gimnasio", font=("Arial", 14),
                     text_color="#666666").pack(pady=(0, 24))
        entradas = []
        for texto, show, pady in (("Usuario", "", (3, 12)), ("Contraseña", "*", (3, 6))):
            ctk.CTkLabel(t, text=texto, font=("Arial", 13, "bold"),
                         text_color="#333333").pack(anchor="w", padx=45)
            e = ctk.CTkEntry(t, width=350, height=40, placeholder_text=texto, show=show)
            e.pack(pady=pady)
            e.bind("<Return>", lambda ev: self.iniciar_sesion())
            entradas.append(e)
        self.e_user, self.e_clave = entradas
        self.aviso_login = ctk.CTkLabel(t, text="", font=("Arial", 12), text_color=ROJO)
        self.aviso_login.pack(pady=(2, 8))
        ctk.CTkButton(t, text="Ingresar", width=350, height=44, fg_color=PRIMARIO, hover_color="#06616B",
                      font=("Arial", 15, "bold"), command=self.iniciar_sesion).pack()
        ctk.CTkLabel(t, text="Usuario por defecto: admin  |  Clave: 1234", font=("Arial", 11),
                     text_color="#888888").pack(pady=(16, 0))
        self.e_user.focus_set()

    def iniciar_sesion(self):
        usuario, clave = self.e_user.get().strip(), self.e_clave.get().strip()
        if not usuario or not clave:
            return self.aviso_login.configure(text="Debe ingresar usuario y contraseña.")
        try:
            cuenta = consultar("SELECT id_usuario, usuario, rol FROM usuarios "
                               "WHERE usuario = ? AND password = ?", (usuario, clave))
        except Exception as e:
            return self.error("Error", "No se pudo validar el inicio de sesión:", e)
        if cuenta:
            self.usuario = cuenta[0]
            self.configure(fg_color=FONDO)
            self.limpiar_ventana()
            self.crear_interfaz()
            return self.mostrar_inicio()
        self.intentos -= 1
        self.e_clave.delete(0, "end")
        if self.intentos <= 0:
            messagebox.showerror("Acceso denegado", "Demasiados intentos fallidos. Se cerrará el sistema.")
            return self.destroy()
        self.aviso_login.configure(text=f"Credenciales incorrectas. Intentos restantes: {self.intentos}")

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión", "¿Querés cerrar la sesión actual?"):
            self.mostrar_login()

    # ------------------------------------------ ayudantes de interfaz
    @staticmethod
    def aviso(titulo, mensaje):
        messagebox.showwarning(titulo, mensaje)

    @staticmethod
    def error(titulo, mensaje, error):
        messagebox.showerror(titulo, f"{mensaje}\n{error}")

    def encabezado(self, texto):
        """Título de la sección. Devuelve la etiqueta de la derecha (totales)."""
        fila = ctk.CTkFrame(self.contenido, fg_color="transparent")
        fila.pack(fill="x", padx=25, pady=(20, 10))
        ctk.CTkLabel(fila, text=texto, font=("Arial", 26, "bold"), text_color=MENU).pack(side="left")
        etiqueta = ctk.CTkLabel(fila, text="", font=("Arial", 14, "bold"), text_color=PRIMARIO)
        etiqueta.pack(side="right")
        return etiqueta

    def tarjeta(self):
        return ctk.CTkFrame(self.contenido, fg_color="white", corner_radius=12)

    @staticmethod
    def subtitulo(padre, texto):
        return ctk.CTkLabel(padre, text=texto, font=("Arial", 17, "bold"), text_color=MENU)

    @staticmethod
    def campo(padre, titulo, fila, col, ancho=380, valores=None, editable=False):
        """Etiqueta + entrada (o combo si se pasan 'valores') en una grilla de 2 filas por campo."""
        ctk.CTkLabel(padre, text=titulo, font=("Arial", 13, "bold"), text_color="#333333").grid(
            row=fila * 2, column=col, sticky="w", padx=20, pady=(5, 3))
        w = (ctk.CTkEntry(padre, width=ancho, height=38, placeholder_text=titulo) if valores is None
             else ctk.CTkComboBox(padre, width=ancho, height=38, values=valores,
                                  state="normal" if editable else "readonly"))
        w.grid(row=fila * 2 + 1, column=col, sticky="w", padx=20, pady=(0, 5))
        return w

    @staticmethod
    def fila_botones(padre, acciones):
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        for texto, estilo, cmd in acciones:
            ctk.CTkButton(marco, text=texto, width=115, height=38, fg_color=BOTONES[estilo][0],
                          hover_color=BOTONES[estilo][1], command=cmd).pack(side="left", padx=5)
        return marco

    def barra_busqueda(self, placeholder, comando):
        marco = ctk.CTkFrame(self.contenido, fg_color="transparent")
        marco.pack(fill="x", padx=25, pady=(15, 5))
        entrada = ctk.CTkEntry(marco, placeholder_text=placeholder, width=400, height=38)
        entrada.pack(side="left", padx=(0, 10))
        entrada.bind("<KeyRelease>", lambda e: comando())

        def mostrar_todos():
            entrada.delete(0, "end")
            comando()

        ctk.CTkButton(marco, text="Buscar", width=100, height=38, fg_color=PRIMARIO,
                      hover_color="#06616B", command=comando).pack(side="left", padx=5)
        ctk.CTkButton(marco, text="Mostrar todos", width=120, height=38, fg_color="#6C757D",
                      hover_color="#565E64", command=mostrar_todos).pack(side="left", padx=5)
        return entrada

    @staticmethod
    def crear_tabla(padre, columnas):
        """columnas: lista de (id, título, ancho[, 'gs'])."""
        tabla = ttk.Treeview(padre, columns=[c[0] for c in columnas], show="headings")
        for col in columnas:
            tabla.heading(col[0], text=col[1])
            tabla.column(col[0], width=col[2], anchor="center")
        scroll = ttk.Scrollbar(padre, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y", padx=(0, 10), pady=10)
        tabla.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        return tabla

    @staticmethod
    def fila_visible(fila, columnas):
        """None -> vacío y formato de guaraníes en las columnas 'gs'."""
        return tuple("" if v is None else formato_gs(v) if len(columnas[i]) > 3 else v
                     for i, v in enumerate(fila))

    @staticmethod
    def escribir(entrada, valor=""):
        entrada.delete(0, "end")
        if valor is not None:
            entrada.insert(0, str(valor))

    def cargar_combo_miembros(self, combo):
        """Llena el combo con los miembros y devuelve {etiqueta: id}."""
        try:
            filas = consultar("SELECT id_miembro, nombre, apellido, cedula FROM miembros "
                              "ORDER BY nombre, apellido")
        except Exception as e:
            self.error("Error", "No se pudieron cargar los miembros:", e)
            filas = []
        mapa = {f"{f[0]} - {f[1]} {f[2]} (C.I. {f[3]})": f[0] for f in filas}
        valores = list(mapa) or ["Sin miembros registrados"]
        combo.configure(values=valores)
        combo.set(valores[0])
        return mapa

    # ------------------------------------------------------ inicio
    def mostrar_inicio(self):
        self.limpiar_contenido()
        for texto, fuente, color, pady in (("Panel principal", ("Arial", 28, "bold"), MENU, (35, 10)),
                                           (f"Bienvenido/a, {self.usuario[1]}", ("Arial", 15), "#666666", (0, 25))):
            ctk.CTkLabel(self.contenido, text=texto, font=fuente, text_color=color).pack(
                anchor="w", padx=35, pady=pady)
        miembros = activas = por_vencer = 0
        recaudado = 0.0
        try:
            limite = (datetime.now() + timedelta(days=7)).strftime(FECHA)
            miembros = consultar("SELECT COUNT(*) FROM miembros")[0][0]
            activas = consultar("SELECT COUNT(*) FROM suscripciones WHERE estado = 'Activa'")[0][0]
            por_vencer = consultar("SELECT COUNT(*) FROM suscripciones WHERE estado = 'Activa' "
                                   "AND fecha_vencimiento BETWEEN ? AND ?", (hoy(), limite))[0][0]
            recaudado = consultar("SELECT COALESCE(SUM(monto), 0) FROM pagos")[0][0]
        except Exception as e:
            self.error("Error", "No se pudieron cargar los datos del panel:", e)
        fila = ctk.CTkFrame(self.contenido, fg_color="transparent")
        fila.pack(fill="x", padx=25, pady=15)
        for titulo, sub, color in (("MIEMBROS", plural(miembros, "registrado", "registrados"), PRIMARIO),
                                   ("SUSCRIPCIONES", plural(activas, "activa", "activas"), VERDE),
                                   ("POR VENCER", f"{por_vencer} en los próximos 7 días", NARANJA),
                                   ("PAGOS", f"{formato_gs(recaudado)} recaudados", "#6F42C1")):
            t = ctk.CTkFrame(fila, fg_color="white", corner_radius=12, border_width=1, border_color="#E1E5EA")
            t.pack(side="left", fill="both", expand=True, padx=8, pady=8)
            ctk.CTkLabel(t, text=titulo, font=("Arial", 19, "bold"), text_color=color).pack(pady=(25, 8))
            ctk.CTkLabel(t, text=sub, font=("Arial", 13), text_color="#666666").pack(pady=(0, 25), padx=10)
        ctk.CTkLabel(self.contenido, text="Bienvenido al sistema de gimnasio", font=("Arial", 20, "bold"),
                     text_color=MENU).pack(pady=60)

    # ------------------- módulos CRUD (miembros, suscripciones, pagos, usuarios)
    def mostrar_modulo(self, nombre):
        c = MODULOS[nombre]
        if c.get("admin") and (self.usuario is None or self.usuario[2] != "admin"):
            return self.aviso("Acceso restringido", "Solo un administrador puede gestionar usuarios.")
        self.limpiar_contenido()
        m = SimpleNamespace(c=c, w={}, mapa={}, sel=None)   # estado del módulo abierto
        m.total = self.encabezado(c["titulo"])
        form = self.tarjeta()
        form.pack(fill="x", padx=25, pady=10)
        self.subtitulo(form, c["form"]).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))
        for k, etiqueta, tipo, fila, col, extra, ancho in campos(c):
            vals = [""] if tipo == "miembro" else extra if tipo in ("combo", "edit") else None
            w = m.w[k] = self.campo(form, etiqueta, fila, col, ancho, vals, tipo == "edit")
            if tipo == "clave":
                w.configure(show="*")
            if tipo == "miembro":
                m.mapa = self.cargar_combo_miembros(w)
        acciones = [("Registrar", "verde", self.registrar), ("Modificar", "azul", self.modificar),
                    ("Eliminar", "rojo", self.eliminar), ("Limpiar", "gris", self.limpiar)]
        if c.get("sin_mod"):
            del acciones[1]
        self.fila_botones(form, [(t, e, lambda f=f: f(m)) for t, e, f in acciones]).grid(
            row=8, column=0, columnspan=2, sticky="e", padx=20, pady=(10, 20))
        m.busq = self.barra_busqueda(c["busq"], lambda: self.listar(m)) if "busq" in c else None
        marco = self.tarjeta()
        marco.pack(fill="both", expand=True, padx=25, pady=(5 if m.busq else 15, 20))
        m.tabla = self.crear_tabla(marco, c["cols"])
        for etiqueta, color in c.get("tags", {}).items():
            m.tabla.tag_configure(etiqueta, foreground=color)
        m.tabla.bind("<<TreeviewSelect>>", lambda e: self.seleccionar(m))
        self.limpiar(m)
        self.listar(m)

    def listar(self, m):
        c = m.c
        for item in m.tabla.get_children():
            m.tabla.delete(item)
        try:
            p = f"%{m.busq.get().strip()}%" if m.busq else ""
            filas = consultar(c["sql"], (p,) * c["sql"].count("?"))
            for f in filas:
                m.tabla.insert("", "end", values=self.fila_visible(f, c["cols"]),
                               tags=(f[c["tag"]],) if "tag" in c else ())
            m.total.configure(text=c["total"](filas) if "total" in c
                              else "Total: " + plural(len(filas), c["sing"], c["plur"]))
        except Exception as e:
            self.error("Error", f"No se pudieron listar {c['los']} {c['plur']}:", e)

    def leer(self, m):
        """Valida el formulario. Devuelve {columna: valor} o None (tras avisar al usuario)."""
        c, d = m.c, {}
        n_fechas = sum(f[2] == "fecha" for f in campos(c))
        for k, _, tipo, _, _, extra, _ in campos(c):
            w = m.w[k]
            v = w.get().strip()
            if tipo == "miembro":
                v = m.mapa.get(w.get())
                if not v:
                    return self.aviso("Miembro requerido", c["msg_miembro"])
            elif tipo in ("txt", "clave", "combo", "edit") and not v:
                return self.aviso("Datos incompletos", c["oblig"])
            try:
                if tipo in ("opt", "int"):
                    v = v or None
                if tipo == "int" and v:
                    v = int(v)
                    if not 0 < v <= 120:
                        raise ValueError
                elif tipo == "monto":
                    v = leer_monto(v)
                elif tipo == "fecha":
                    v = leer_fecha(v)
            except ValueError:
                return self.aviso(*(("Fechas inválidas" if n_fechas > 1 else "Fecha inválida",
                                     "Usá el formato AAAA-MM-DD\nEjemplo: 2026-06-01")
                                    if tipo == "fecha" else extra))
            d[k] = v
        if "check" in c and (problema := c["check"](d)):
            return self.aviso(*problema)
        return d

    def fallo(self, c, accion, e, dup=None):
        """Error de base de datos; si es un dato repetido y el módulo lo prevé, avisa con su mensaje."""
        if dup and isinstance(e, sqlite3.IntegrityError) and "dup" in c:
            self.aviso(c["dup"][0], c["dup"][dup])
        else:
            self.error("Error", f"No se pudo {accion} {c['el']} {c['sing']}:", e)

    def registrar(self, m):
        c, d = m.c, self.leer(m)
        if d is None:
            return
        try:
            nuevo_id, _ = ejecutar(f"INSERT INTO {c['tabla']} ({', '.join(d)}) "
                                   f"VALUES ({', '.join('?' * len(d))})", tuple(d.values()))
            titulo, texto = c["ok_reg"](nuevo_id, d) if "ok_reg" in c else (
                "Registro exitoso", f"{c['sing'].capitalize()} registrad{c['o']} con ID {nuevo_id}.")
            messagebox.showinfo(titulo, texto)
            self.limpiar(m)
            self.listar(m)
        except Exception as e:
            self.fallo(c, "registrar", e, 1)

    def seleccionar(self, m):
        sel = m.tabla.selection()
        if not sel:
            return
        m.sel = int(m.tabla.item(sel[0], "values")[0])
        if not m.c.get("rellenar", True):
            return
        try:
            cs = campos(m.c)
            fila = consultar(f"SELECT {', '.join(f[0] for f in cs)} FROM {m.c['tabla']} "
                             f"WHERE {m.c['pk']} = ?", (m.sel,))
            for (k, _, tipo, _, _, extra, _), v in zip(cs, fila[0] if fila else ()):
                w = m.w[k]
                if tipo == "miembro":
                    etiqueta = next((e for e, i in m.mapa.items() if i == v), None)
                    if etiqueta:
                        w.set(etiqueta)
                elif tipo in ("combo", "edit"):
                    fijar_combo(w, v, extra)
                else:
                    self.escribir(w, int(v) if tipo == "monto" and float(v).is_integer() else v)
        except Exception as e:
            self.error("Error", "No se pudieron cargar los datos:", e)

    def modificar(self, m):
        c = m.c
        if m.sel is None:
            return self.aviso(f"Seleccionar {c['sing']}", f"Primero seleccioná {c['un']} {c['sing']} de la tabla.")
        d = self.leer(m)
        if d is None or not messagebox.askyesno(
                "Confirmar modificación",
                c.get("ask_mod", f"¿Deseás guardar los cambios {c['de']} {c['sing']}?")):
            return
        try:
            _, filas = ejecutar(f"UPDATE {c['tabla']} SET {', '.join(k + '=?' for k in d)} "
                                f"WHERE {c['pk']}=?", (*d.values(), m.sel))
            if filas:
                messagebox.showinfo("Modificación exitosa", c.get(
                    "ok_mod", f"{c['el'].capitalize()} {c['sing']} fue modificad{c['o']} correctamente."))
            else:
                self.aviso("Aviso", f"No se encontró {c['el']} {c['sing']}.")
            self.limpiar(m)
            self.listar(m)
        except Exception as e:
            self.fallo(c, "modificar", e, 2)

    def eliminar(self, m):
        c = m.c
        if m.sel is None:
            return self.aviso(f"Seleccionar {c['sing']}", f"Primero seleccioná {c['un']} {c['sing']} de la tabla.")
        try:
            texto = c["confirma"](self, m.sel) if "confirma" in c else (
                f"¿Estás seguro de eliminar {c['el']} {c['sing']} seleccionad{c['o']}?\n\n"
                "Esta operación no se puede deshacer.")
        except Exception as e:
            return self.error("Error", f"No se pudo comprobar {c['el']} {c['sing']}:", e)
        if texto is None or not messagebox.askyesno(f"Eliminar {c['sing']}", texto):
            return
        try:
            ejecutar(f"DELETE FROM {c['tabla']} WHERE {c['pk']} = ?", (m.sel,))
            messagebox.showinfo("Eliminación exitosa", f"{c['el'].capitalize()} {c['sing']} fue eliminad{c['o']}.")
            self.limpiar(m)
            self.listar(m)
        except Exception as e:
            self.fallo(c, "eliminar", e)

    def limpiar(self, m):
        for k, _, tipo, _, _, extra, _ in campos(m.c):
            if tipo in ("combo", "edit"):
                fijar_combo(m.w[k], None, extra)
            elif tipo != "miembro":
                self.escribir(m.w[k], hoy() if tipo == "fecha" and extra == "hoy" else "")
        m.sel = None
        for item in m.tabla.selection():
            m.tabla.selection_remove(item)

    # ------------------------------------------- consultas combinadas
    def mostrar_consultas(self):
        self.limpiar_contenido()
        self.total_consulta = self.encabezado("CONSULTAS COMBINADAS")
        barra = self.tarjeta()
        barra.pack(fill="x", padx=25, pady=10)
        self.subtitulo(barra, "SELECCIONAR REPORTE").pack(anchor="w", padx=20, pady=(15, 8))
        fila = ctk.CTkFrame(barra, fg_color="transparent")
        fila.pack(fill="x", padx=20, pady=(0, 15))
        for nombre in REPORTES:
            ctk.CTkButton(fila, text=nombre, height=38, fg_color=PRIMARIO, hover_color="#06616B",
                          command=lambda n=nombre: self.ejecutar_reporte(n)).pack(side="left", padx=(0, 10))
        self.lbl_reporte = ctk.CTkLabel(self.contenido, text="Elegí un reporte para verlo.",
                                        font=("Arial", 16, "bold"), text_color=MENU)
        self.lbl_reporte.pack(anchor="w", padx=30, pady=(5, 0))
        self.marco_reporte = self.tarjeta()
        self.marco_reporte.pack(fill="both", expand=True, padx=25, pady=(5, 20))

    def ejecutar_reporte(self, nombre):
        sql, columnas = REPORTES[nombre]
        for w in self.marco_reporte.winfo_children():
            w.destroy()
        tabla = self.crear_tabla(self.marco_reporte, columnas)
        self.lbl_reporte.configure(text=nombre.upper())
        try:
            filas = consultar(sql)
            for f in filas:
                tabla.insert("", "end", values=self.fila_visible(f, columnas))
            self.total_consulta.configure(text=f"Total: {len(filas)} registros")
            if not filas:
                messagebox.showinfo("Sin resultados", "No hay registros para este reporte por ahora.")
        except Exception as e:
            self.error("Error", "No se pudo ejecutar el reporte:", e)


if __name__ == "__main__":
    if inicializar_bd():   # crea tablas y el usuario admin si no existen
        Aplicacion().mainloop()
    else:
        print("\nNo se pudo iniciar la base de datos. Verifique permisos de escritura.")