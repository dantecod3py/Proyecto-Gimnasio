from datetime import datetime
from database import conectar


def validar_fecha(fecha_texto):
    try:
        return datetime.strptime(fecha_texto, "%Y-%m-%d")
    except ValueError:
        return None


def registrar_suscripcion():
    print("\n------------- Registrar suscripción -------------")

    try:
        id_miembro = int(input("ID del Miembro: ").strip())
        if id_miembro <= 0:
            print("\nError: El ID debe ser positivo.")
            return
    except ValueError:
        print("\nError: El ID del miembro debe ser numérico.")
        return

    plan_cuota = input("Plan (Mensual/Trimestral/Anual): ").strip()
    cuota = input("Cuota: ").strip()
    fecha_inicio = input("Fecha de inicio (AAAA-MM-DD): ").strip()
    fecha_vencimiento = input("Fecha de vencimiento (AAAA-MM-DD): ").strip()
    estado = input("Estado (Activa/Vencida/Pendiente) [Activa]: ").strip() or "Activa"

    if not all([plan_cuota, cuota, fecha_inicio, fecha_vencimiento, estado]):
        print("\nError: Todos los campos son obligatorios.")
        return

    f_ini = validar_fecha(fecha_inicio)
    f_ven = validar_fecha(fecha_vencimiento)
    if not f_ini or not f_ven:
        print("\nError: Las fechas deben tener el formato AAAA-MM-DD.")
        return

    if f_ven < f_ini:
        print("\nError: La fecha de vencimiento no puede ser anterior a la de inicio.")
        return

    try:
        cuota = float(cuota.replace(",", "."))
        if cuota <= 0:
            print("\nError: La cuota debe ser mayor que cero.")
            return
    except ValueError:
        print("\nError: La cuota debe ser numérica.")
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
            INSERT INTO suscripciones (
                id_miembro, plan_cuota, cuota, fecha_inicio, fecha_vencimiento, estado
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (id_miembro, plan_cuota, cuota, fecha_inicio, fecha_vencimiento, estado))

        conexion.commit()
        print(f"\nSuscripción registrada correctamente para {miembro[0]} {miembro[1]}.")
        print("ID asignado:", cursor.lastrowid)

    except Exception as e:
        print("\nError al registrar la suscripción:", e)
    finally:
        conexion.close()


def listar_suscripcion():
    print("\n" + "-" * 15 + " Lista de suscripciones " + "-" * 15)

    conexion = conectar()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT
                s.id_suscripcion,
                m.nombre || ' ' || m.apellido AS cliente,
                s.plan_cuota,
                s.cuota,
                s.fecha_inicio,
                s.fecha_vencimiento,
                s.estado
            FROM suscripciones s
            INNER JOIN miembros m ON s.id_miembro = m.id_miembro
            ORDER BY s.id_suscripcion
        """)

        suscripciones = cursor.fetchall()
        if not suscripciones:
            print("\nNo existen suscripciones registradas.")
            return

        print("-" * 120)
        print(
            f"{'ID':<6}"
            f"{'MIEMBRO':<25}"
            f"{'PLAN':<18}"
            f"{'CUOTA':<13}"
            f"{'INICIO':<16}"
            f"{'VENCIMIENTO':<18}"
            f"{'ESTADO':<15}"
        )
        print("-" * 120)

        for s in suscripciones:
            print(
                f"{s[0]:<6}"
                f"{str(s[1]):<25}"
                f"{str(s[2]):<18}"
                f"{str(s[3]):<13}"
                f"{str(s[4]):<16}"
                f"{str(s[5]):<18}"
                f"{str(s[6]):<15}"
            )

        print("-" * 120)

    except Exception as e:
        print("\nError al consultar las suscripciones:", e)
    finally:
        conexion.close()


def buscar_suscripcion():
    print("\n" + "=" * 15 + " BUSCAR SUSCRIPCIÓN " + "=" * 15)

    dato = input("Ingrese nombre/cédula del miembro, plan, fecha o estado: ").strip()
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
                s.id_suscripcion,
                m.nombre || ' ' || m.apellido,
                s.plan_cuota,
                s.cuota,
                s.fecha_inicio,
                s.fecha_vencimiento,
                s.estado
            FROM suscripciones s
            INNER JOIN miembros m ON s.id_miembro = m.id_miembro
            WHERE m.nombre LIKE ?
               OR m.apellido LIKE ?
               OR m.cedula LIKE ?
               OR s.plan_cuota LIKE ?
               OR CAST(s.cuota AS TEXT) LIKE ?
               OR s.fecha_inicio LIKE ?
               OR s.fecha_vencimiento LIKE ?
               OR s.estado LIKE ?
            ORDER BY s.fecha_inicio DESC
        """, (texto, texto, texto, texto, texto, texto, texto, texto))

        suscripciones = cursor.fetchall()
        if not suscripciones:
            print("\nNo se encontraron suscripciones.")
            return

        print("\nSuscripciones encontradas:")
        print("-" * 60)
        for s in suscripciones:
            print(f"ID: {s[0]}")
            print(f"Miembro: {s[1]}")
            print(f"Plan: {s[2]}")
            print(f"Cuota: {s[3]}")
            print(f"Fecha de inicio: {s[4]}")
            print(f"Fecha de vencimiento: {s[5]}")
            print(f"Estado: {s[6]}")
            print("-" * 60)

    except Exception as e:
        print("\nError al buscar suscripciones:", e)
    finally:
        conexion.close()


def modificar_suscripcion():
    print("\n" + "=" * 15 + " MODIFICAR SUSCRIPCIÓN " + "=" * 15)

    try:
        id_suscripcion = int(input("Ingrese el ID de la suscripción: ").strip())
        if id_suscripcion <= 0:
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
            SELECT id_suscripcion, plan_cuota, cuota, fecha_inicio, fecha_vencimiento, estado
            FROM suscripciones
            WHERE id_suscripcion = ?
        """, (id_suscripcion,))

        suscripcion = cursor.fetchone()
        if not suscripcion:
            print("\nNo existe una suscripción con ese ID.")
            return

        print("\nDatos actuales:")
        print("Plan:", suscripcion[1])
        print("Cuota:", suscripcion[2])
        print("Fecha de inicio:", suscripcion[3])
        print("Fecha de vencimiento:", suscripcion[4])
        print("Estado:", suscripcion[5])

        print("\nIngrese los nuevos datos (Enter para conservar el actual):")

        plan_cuota = input(f"Nuevo plan [{suscripcion[1]}]: ").strip() or suscripcion[1]
        cuota_texto = input(f"Nueva cuota [{suscripcion[2]}]: ").strip()

        if cuota_texto:
            try:
                cuota = float(cuota_texto.replace(",", "."))
                if cuota <= 0:
                    print("\nLa cuota debe ser mayor que cero.")
                    return
            except ValueError:
                print("\nLa cuota debe ser numérica.")
                return
        else:
            cuota = suscripcion[2]

        fecha_inicio = input(f"Nueva fecha de inicio [{suscripcion[3]}]: ").strip() or suscripcion[3]
        fecha_vencimiento = input(f"Nueva fecha de vencimiento [{suscripcion[4]}]: ").strip() or suscripcion[4]

        f_ini = validar_fecha(fecha_inicio)
        f_ven = validar_fecha(fecha_vencimiento)
        if not f_ini or not f_ven or f_ven < f_ini:
            print("\nError: Fechas inválidas (use AAAA-MM-DD y verifique que el vencimiento no sea menor al inicio).")
            return

        estado = input(f"Nuevo estado [{suscripcion[5]}]: ").strip() or suscripcion[5]

        cursor.execute("""
            UPDATE suscripciones
            SET plan_cuota = ?, cuota = ?, fecha_inicio = ?, fecha_vencimiento = ?, estado = ?
            WHERE id_suscripcion = ?
        """, (plan_cuota, cuota, fecha_inicio, fecha_vencimiento, estado, id_suscripcion))

        conexion.commit()
        print("\nSuscripción modificada correctamente.")

    except Exception as e:
        print("\nError al modificar la suscripción:", e)
    finally:
        conexion.close()


def eliminar_suscripcion():
    print("\n" + "=" * 15 + " ELIMINAR SUSCRIPCIÓN " + "=" * 15)

    try:
        id_suscripcion = int(input("Ingrese el ID de la suscripción: ").strip())
        if id_suscripcion <= 0:
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
            SELECT s.plan_cuota, s.cuota, s.fecha_inicio, s.fecha_vencimiento, s.estado, m.nombre || ' ' || m.apellido
            FROM suscripciones s
            INNER JOIN miembros m ON s.id_miembro = m.id_miembro
            WHERE s.id_suscripcion = ?
        """, (id_suscripcion,))

        suscripcion = cursor.fetchone()
        if not suscripcion:
            print("\nNo existe una suscripción con ese ID.")
            return

        print("\nSuscripción encontrada:")
        print("Miembro:", suscripcion[5])
        print("Plan:", suscripcion[0])
        print("Cuota:", suscripcion[1])
        print("Fecha de inicio:", suscripcion[2])
        print("Fecha de vencimiento:", suscripcion[3])
        print("Estado:", suscripcion[4])

        confirmacion = input("\n¿Está seguro de eliminarla? (S/N): ").strip().upper()
        if confirmacion != "S":
            print("\nOperación cancelada.")
            return

        cursor.execute("DELETE FROM suscripciones WHERE id_suscripcion = ?", (id_suscripcion,))
        conexion.commit()
        print("\nSuscripción eliminada correctamente.")

    except Exception as e:
        print("\nNo se pudo eliminar la suscripción:", e)
    finally:
        conexion.close()
