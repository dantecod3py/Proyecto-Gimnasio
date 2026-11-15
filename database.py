import sqlite3
from pathlib import Path

BASE_DATOS = Path(__file__).resolve().parent / "db_gym.db"


def conectar():
    """Abre la conexión con la base de datos SQLite y activa claves foráneas."""
    try:
        conexion = sqlite3.connect(str(BASE_DATOS))
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion
    except sqlite3.Error as e:
        print(f"\nError al conectar con SQLite: {e}")
        return None


def inicializar_bd():
    """Crea las tablas del sistema si no existen e inserta el usuario admin inicial."""
    conexion = conectar()
    if conexion is None:
        return False

    try:
        cursor = conexion.cursor()

        # Tabla de usuarios para el Login
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                rol TEXT DEFAULT 'operador'
            )
        """)

        # Tabla de miembros
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS miembros (
                id_miembro INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                cedula TEXT NOT NULL UNIQUE,
                edad INTEGER,
                genero TEXT,
                contacto TEXT
            )
        """)

        # Tabla de suscripciones (vinculada a miembros)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suscripciones (
                id_suscripcion INTEGER PRIMARY KEY AUTOINCREMENT,
                id_miembro INTEGER NOT NULL,
                plan_cuota TEXT NOT NULL,
                cuota REAL NOT NULL,
                fecha_inicio TEXT NOT NULL,
                fecha_vencimiento TEXT NOT NULL,
                estado TEXT NOT NULL,
                FOREIGN KEY (id_miembro) REFERENCES miembros(id_miembro) ON DELETE CASCADE
            )
        """)

        # Tabla de pagos (vinculada a miembros)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagos (
                pago_id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_miembro INTEGER NOT NULL,
                monto REAL NOT NULL,
                fecha_pago TEXT NOT NULL,
                metodo TEXT NOT NULL,
                FOREIGN KEY (id_miembro) REFERENCES miembros(id_miembro) ON DELETE CASCADE
            )
        """)

        # Usuario por defecto: admin / 1234
        cursor.execute("""
            INSERT OR IGNORE INTO usuarios (usuario, password, rol)
            VALUES ('admin', '1234', 'admin')
        """)

        conexion.commit()
        return True

    except sqlite3.Error as e:
        print(f"\nError al inicializar la base de datos: {e}")
        return False
    finally:
        conexion.close()
