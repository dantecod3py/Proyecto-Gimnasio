import getpass
from database import conectar


def iniciar_sesion():
    """Valida credenciales contra la tabla usuarios. Retorna el usuario autenticado o None."""
    print("\n" + "=" * 45)
    print("INICIO DE SESION - GIMNASIO".center(45))
    print("=" * 45)
    print("(Usuario por defecto: admin | Clave: 1234)")

    intentos = 3

    while intentos > 0:
        usuario = input("\nUsuario: ").strip()
        try:
            password = getpass.getpass("Contraseña: ").strip()
        except Exception:
            password = input("Contraseña: ").strip()

        if not usuario or not password:
            print("Debe ingresar usuario y contraseña.")
            continue

        conexion = conectar()
        if conexion is None:
            return None

        try:
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT id_usuario, usuario, rol
                FROM usuarios
                WHERE usuario = ? AND password = ?
            """, (usuario, password))

            cuenta = cursor.fetchone()

            if cuenta:
                print(f"\nBienvenido/a, {cuenta[1]} (Rol: {cuenta[2]}).")
                return cuenta
            else:
                intentos -= 1
                print(f"\nCredenciales incorrectas. Intentos restantes: {intentos}")

        except Exception as e:
            print(f"\nError durante el inicio de sesión: {e}")
            return None
        finally:
            conexion.close()

    print("\nDemasiados intentos fallidos. Cerrando sistema.")
    return None


def registrar_usuario():
    """Permite crear un nuevo usuario de acceso al sistema."""
    print("\n------------- Registrar Usuario del Sistema -------------")
    usuario = input("Nuevo nombre de usuario: ").strip()
    password = input("Contraseña: ").strip()
    rol = input("Rol (admin/operador) [operador]: ").strip().lower() or "operador"

    if not usuario or not password:
        print("\nError: Usuario y contraseña no pueden estar vacíos.")
        return

    if rol not in ("admin", "operador"):
        print("\nError: El rol debe ser 'admin' o 'operador'.")
        return

    conexion = conectar()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO usuarios (usuario, password, rol)
            VALUES (?, ?, ?)
        """, (usuario, password, rol))
        conexion.commit()
        print("\nUsuario registrado correctamente.")
    except Exception as e:
        print(f"\nError al registrar usuario (posible usuario duplicado): {e}")
    finally:
        conexion.close()
