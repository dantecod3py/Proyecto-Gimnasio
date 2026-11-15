import sqlite3
from database import conectar


def registrar_miembro():
    print("\n------------- Registrar Miembro -------------")

    nombre = input("Nombre: ").strip()
    apellido = input("Apellido: ").strip()
    cedula = input("Cédula: ").strip()
    edad = input("Edad: ").strip()
    genero = input("Género: ").strip()
    contacto = input("Contacto: ").strip()

    if not nombre or not apellido or not cedula:
        print("\nError: Nombre, apellido y cédula son obligatorios.")
        return

    if edad:
        try:
            edad = int(edad)
            if edad <= 0:
                print("\nError: La edad debe ser mayor que cero.")
                return
        except ValueError:
            print("\nError: La edad debe ser numérica.")
            return
    else:
        edad = None

    conexion = conectar()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO miembros (nombre, apellido, cedula, edad, genero, contacto)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, apellido, cedula, edad, genero, contacto))

        conexion.commit()
        print("\nMiembro registrado correctamente.")
        print("ID asignado:", cursor.lastrowid)

    except sqlite3.IntegrityError:
        print("\nError: Ya existe un miembro registrado con esa cédula.")
    except Exception as e:
        print("\nError al registrar miembro:", e)
    finally:
        conexion.close()


def listar_miembros():
    print("\n" + "-" * 15 + " Lista de Miembros " + "-" * 15)

    conexion = conectar()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id_miembro, nombre, apellido, cedula, edad, genero, contacto
            FROM miembros
            ORDER BY id_miembro
        """)

        miembros = cursor.fetchall()

        if not miembros:
            print("\nNo existen miembros registrados.")
            return

        print("-" * 105)
        print(
            f"{'ID':<6}"
            f"{'NOMBRE':<18}"
            f"{'APELLIDO':<18}"
            f"{'CEDULA':<18}"
            f"{'EDAD':<8}"
            f"{'GENERO':<15}"
            f"{'CONTACTO':<20}"
        )
        print("-" * 105)

        for miembro in miembros:
            print(
                f"{str(miembro[0]):<6}"
                f"{str(miembro[1]):<18}"
                f"{str(miembro[2]):<18}"
                f"{str(miembro[3]):<18}"
                f"{str(miembro[4] or ''):<8}"
                f"{str(miembro[5] or ''):<15}"
                f"{str(miembro[6] or ''):<20}"
            )

        print("-" * 105)

    except Exception as e:
        print("\nError al consultar miembros:", e)
    finally:
        conexion.close()


def buscar_miembro():
    print("\n" + "=" * 15 + " BUSCAR MIEMBRO " + "=" * 15)

    dato = input("Ingrese nombre, apellido o cédula: ").strip()
    if not dato:
        print("\nDebe ingresar un dato para realizar la búsqueda.")
        return

    conexion = conectar()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        texto = f"%{dato}%"

        cursor.execute("""
            SELECT id_miembro, nombre, apellido, cedula, edad, genero, contacto
            FROM miembros
            WHERE nombre LIKE ?
               OR apellido LIKE ?
               OR cedula LIKE ?
            ORDER BY nombre
        """, (texto, texto, texto))

        miembros = cursor.fetchall()

        if not miembros:
            print("\nNo se encontraron miembros.")
            return

        print("\nMiembros encontrados:")
        print("-" * 50)
        for miembro in miembros:
            print(f"ID: {miembro[0]}")
            print(f"Nombre: {miembro[1]}")
            print(f"Apellido: {miembro[2]}")
            print(f"Cédula: {miembro[3]}")
            print(f"Edad: {miembro[4]}")
            print(f"Género: {miembro[5]}")
            print(f"Contacto: {miembro[6]}")
            print("-" * 50)

    except Exception as e:
        print("\nError al buscar miembro:", e)
    finally:
        conexion.close()


def modificar_miembro():
    print("\n" + "=" * 15 + " MODIFICAR MIEMBRO " + "=" * 15)

    try:
        id_miembro = int(input("Ingrese ID del miembro: ").strip())
        if id_miembro <= 0:
            print("\nEl ID debe ser un número positivo.")
            return
    except ValueError:
        print("\nEl ID debe ser numérico.")
        return

    conexion = conectar()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id_miembro, nombre, apellido, cedula, edad, genero, contacto
            FROM miembros
            WHERE id_miembro = ?
        """, (id_miembro,))

        miembro = cursor.fetchone()
        if not miembro:
            print("\nNo existe un miembro con ese ID.")
            return

        print("\nDatos actuales:")
        print("Nombre:", miembro[1])
        print("Apellido:", miembro[2])
        print("Cédula:", miembro[3])
        print("Edad:", miembro[4])
        print("Género:", miembro[5])
        print("Contacto:", miembro[6])

        print("\nIngrese los nuevos datos (Enter para conservar el actual):")

        nombre = input(f"Nuevo nombre [{miembro[1]}]: ").strip() or miembro[1]
        apellido = input(f"Nuevo apellido [{miembro[2]}]: ").strip() or miembro[2]
        cedula = input(f"Nueva cédula [{miembro[3]}]: ").strip() or miembro[3]
        edad_texto = input(f"Nueva edad [{miembro[4] or ''}]: ").strip()

        if edad_texto:
            try:
                edad = int(edad_texto)
                if edad <= 0:
                    print("\nLa edad debe ser mayor que cero.")
                    return
            except ValueError:
                print("\nLa edad debe ser numérica.")
                return
        else:
            edad = miembro[4]

        genero = input(f"Nuevo género [{miembro[5] or ''}]: ").strip() or miembro[5]
        contacto = input(f"Nuevo contacto [{miembro[6] or ''}]: ").strip() or miembro[6]

        cursor.execute("""
            UPDATE miembros
            SET nombre = ?, apellido = ?, cedula = ?, edad = ?, genero = ?, contacto = ?
            WHERE id_miembro = ?
        """, (nombre, apellido, cedula, edad, genero, contacto, id_miembro))

        conexion.commit()
        print("\nMiembro modificado correctamente.")

    except sqlite3.IntegrityError:
        print("\nError: Esa cédula ya pertenece a otro miembro.")
    except Exception as e:
        print("\nError al modificar miembro:", e)
    finally:
        conexion.close()


def eliminar_miembro():
    print("\n" + "=" * 15 + " ELIMINAR MIEMBRO " + "=" * 15)

    try:
        id_miembro = int(input("Ingrese ID del miembro: ").strip())
        if id_miembro <= 0:
            print("\nEl ID debe ser un número positivo.")
            return
    except ValueError:
        print("\nEl ID debe ser numérico.")
        return

    conexion = conectar()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT nombre, apellido, cedula
            FROM miembros
            WHERE id_miembro = ?
        """, (id_miembro,))

        miembro = cursor.fetchone()
        if not miembro:
            print("\nNo existe un miembro con ese ID.")
            return

        print("\nMiembro encontrado:")
        print("Nombre:", miembro[0])
        print("Apellido:", miembro[1])
        print("Cédula:", miembro[2])

        confirmacion = input("\n¿Está seguro de eliminarlo? Se borrarán sus pagos y suscripciones (S/N): ").strip().upper()
        if confirmacion != "S":
            print("\nOperación cancelada.")
            return

        cursor.execute("DELETE FROM miembros WHERE id_miembro = ?", (id_miembro,))
        conexion.commit()
        print("\nMiembro eliminado correctamente.")

    except Exception as e:
        print("\nNo se pudo eliminar el miembro:", e)
    finally:
        conexion.close()
