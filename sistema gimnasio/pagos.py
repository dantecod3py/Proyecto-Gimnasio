from datetime import datetime
from database import conectar


def validar_fecha(fecha_texto):
    try:
        datetime.strptime(fecha_texto, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def registrar_pago():
    print("\n------------- Registrar Pago -------------")

    try:
        id_miembro = int(input("ID del Miembro: ").strip())
        if id_miembro <= 0:
            print("\nError: El ID debe ser positivo.")
            return
    except ValueError:
        print("\nError: El ID del miembro debe ser numérico.")
        return

    monto = input("Monto: ").strip()
    fecha_pago = input("Fecha de pago (AAAA-MM-DD): ").strip()
    metodo = input("Método (Efectivo/Transferencia/Tarjeta): ").strip()

    if not monto or not fecha_pago or not metodo:
        print("\nError: Todos los campos son obligatorios.")
        return

    if not validar_fecha(fecha_pago):
        print("\nError: Formato de fecha inválido. Use AAAA-MM-DD.")
        return

    try:
        monto = float(monto.replace(",", "."))
        if monto <= 0:
            print("\nError: El monto debe ser mayor que cero.")
            return
    except ValueError:
        print("\nError: El monto debe ser numérico.")
        return

    conexion = conectar()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()

        cursor.execute("SELECT nombre, apellido FROM miembros WHERE id_miembro = ?", (id_miembro,))
        miembro = cursor.fetchone()
        if not miembro:
            print(f"\nError: No existe ningún miembro con ID {id_miembro}.")
            return

        cursor.execute("""
            INSERT INTO pagos (id_miembro, monto, fecha_pago, metodo)
            VALUES (?, ?, ?, ?)
        """, (id_miembro, monto, fecha_pago, metodo))

        conexion.commit()
        print(f"\nPago registrado correctamente para {miembro[0]} {miembro[1]}.")
        print("ID de pago asignado:", cursor.lastrowid)

    except Exception as e:
        print("\nError al registrar el pago:", e)
    finally:
        conexion.close()


def listar_pago():
    print("\n" + "-" * 15 + " Lista de Pagos " + "-" * 15)

    conexion = conectar()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT
                p.pago_id,
                m.nombre || ' ' || m.apellido AS cliente,
                p.monto,
                p.fecha_pago,
                p.metodo
            FROM pagos p
            INNER JOIN miembros m ON p.id_miembro = m.id_miembro
            ORDER BY p.pago_id
        """)

        pagos = cursor.fetchall()
        if not pagos:
            print("\nNo existen pagos registrados.")
            return

        print("-" * 95)
        print(
            f"{'ID':<8}"
            f"{'MIEMBRO':<28}"
            f"{'MONTO':<15}"
            f"{'FECHA PAGO':<18}"
            f"{'METODO':<20}"
        )
        print("-" * 95)

        for pago in pagos:
            print(
                f"{pago[0]:<8}"
                f"{str(pago[1]):<28}"
                f"{str(pago[2]):<15}"
                f"{str(pago[3]):<18}"
                f"{str(pago[4]):<20}"
            )

        print("-" * 95)

    except Exception as e:
        print("\nError al consultar los pagos:", e)
    finally:
        conexion.close()


def buscar_pago():
    print("\n" + "=" * 15 + " BUSCAR PAGO " + "=" * 15)

    dato = input("Ingrese nombre/cédula del miembro, monto, fecha o método: ").strip()
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
            SELECT
                p.pago_id,
                m.nombre || ' ' || m.apellido,
                p.monto,
                p.fecha_pago,
                p.metodo
            FROM pagos p
            INNER JOIN miembros m ON p.id_miembro = m.id_miembro
            WHERE m.nombre LIKE ?
               OR m.apellido LIKE ?
               OR m.cedula LIKE ?
               OR CAST(p.monto AS TEXT) LIKE ?
               OR p.fecha_pago LIKE ?
               OR p.metodo LIKE ?
            ORDER BY p.fecha_pago DESC
        """, (texto, texto, texto, texto, texto, texto))

        pagos = cursor.fetchall()
        if not pagos:
            print("\nNo se encontraron pagos.")
            return

        print("\nPagos encontrados:")
        print("-" * 50)
        for pago in pagos:
            print(f"ID Pago: {pago[0]}")
            print(f"Miembro: {pago[1]}")
            print(f"Monto: {pago[2]}")
            print(f"Fecha de pago: {pago[3]}")
            print(f"Método: {pago[4]}")
            print("-" * 50)

    except Exception as e:
        print("\nError al buscar pagos:", e)
    finally:
        conexion.close()


def modificar_pago():
    print("\n" + "=" * 15 + " MODIFICAR PAGO " + "=" * 15)

    try:
        pago_id = int(input("Ingrese ID del pago: ").strip())
        if pago_id <= 0:
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
            SELECT pago_id, monto, fecha_pago, metodo
            FROM pagos
            WHERE pago_id = ?
        """, (pago_id,))

        pago = cursor.fetchone()
        if not pago:
            print("\nNo existe un pago con ese ID.")
            return

        print("\nDatos actuales:")
        print("Monto:", pago[1])
        print("Fecha de pago:", pago[2])
        print("Método:", pago[3])

        print("\nIngrese los nuevos datos (Enter para conservar el actual):")

        monto_texto = input(f"Nuevo monto [{pago[1]}]: ").strip()
        if monto_texto:
            try:
                monto = float(monto_texto.replace(",", "."))
                if monto <= 0:
                    print("\nEl monto debe ser mayor que cero.")
                    return
            except ValueError:
                print("\nEl monto debe ser numérico.")
                return
        else:
            monto = pago[1]

        fecha_pago = input(f"Nueva fecha de pago [{pago[2]}]: ").strip() or pago[2]
        if not validar_fecha(fecha_pago):
            print("\nError: Formato de fecha inválido. Use AAAA-MM-DD.")
            return

        metodo = input(f"Nuevo método [{pago[3]}]: ").strip() or pago[3]

        cursor.execute("""
            UPDATE pagos
            SET monto = ?, fecha_pago = ?, metodo = ?
            WHERE pago_id = ?
        """, (monto, fecha_pago, metodo, pago_id))

        conexion.commit()
        print("\nPago modificado correctamente.")

    except Exception as e:
        print("\nError al modificar el pago:", e)
    finally:
        conexion.close()


def eliminar_pago():
    print("\n" + "=" * 15 + " ELIMINAR PAGO " + "=" * 15)

    try:
        pago_id = int(input("Ingrese ID del pago: ").strip())
        if pago_id <= 0:
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
            SELECT p.pago_id, m.nombre || ' ' || m.apellido, p.monto, p.fecha_pago, p.metodo
            FROM pagos p
            INNER JOIN miembros m ON p.id_miembro = m.id_miembro
            WHERE p.pago_id = ?
        """, (pago_id,))

        pago = cursor.fetchone()
        if not pago:
            print("\nNo existe un pago con ese ID.")
            return

        print("\nPago encontrado:")
        print("ID:", pago[0])
        print("Miembro:", pago[1])
        print("Monto:", pago[2])
        print("Fecha de pago:", pago[3])
        print("Método:", pago[4])

        confirmacion = input("\n¿Está seguro de eliminarlo? (S/N): ").strip().upper()
        if confirmacion != "S":
            print("\nOperación cancelada.")
            return

        cursor.execute("DELETE FROM pagos WHERE pago_id = ?", (pago_id,))
        conexion.commit()
        print("\nPago eliminado correctamente.")

    except Exception as e:
        print("\nNo se pudo eliminar el pago:", e)
    finally:
        conexion.close()
