from database import inicializar_bd
from login import iniciar_sesion, registrar_usuario

from miembros import (
    registrar_miembro,
    listar_miembros,
    buscar_miembro,
    modificar_miembro,
    eliminar_miembro
)

from pagos import (
    registrar_pago,
    listar_pago,
    buscar_pago,
    modificar_pago,
    eliminar_pago
)

from suscripciones import (
    registrar_suscripcion,
    listar_suscripcion,
    buscar_suscripcion,
    modificar_suscripcion,
    eliminar_suscripcion
)


def ejecutar_accion(funcion):
    try:
        funcion()
    except Exception as error:
        print(f"\nOcurrió un error: {error}")

    input("\nPresiona Enter para continuar...")


def mostrar_menu(titulo, opciones):
    print("\n" + "=" * 45)
    print(titulo.center(45))
    print("=" * 45)

    for numero, descripcion in opciones:
        print(f"{numero}. {descripcion}")

    print("=" * 45)


def menu_generico(titulo, acciones, texto_salir="Volver al menú anterior"):
    while True:
        opciones = [
            (numero, descripcion)
            for numero, descripcion, _ in acciones
        ]
        opciones.append((0, texto_salir))

        mostrar_menu(titulo, opciones)
        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        accion = next(
            (funcion for numero, _, funcion in acciones if str(numero) == opcion),
            None
        )

        if accion is None:
            print("\nOpción inválida.")
            input("Presiona Enter para continuar...")
            continue

        ejecutar_accion(accion)


def menu_miembros():
    acciones = [
        (1, "Registrar Miembro", registrar_miembro),
        (2, "Listar Miembros", listar_miembros),
        (3, "Buscar Miembro", buscar_miembro),
        (4, "Modificar Miembro", modificar_miembro),
        (5, "Eliminar Miembro", eliminar_miembro)
    ]
    menu_generico("GESTIÓN DE MIEMBROS", acciones)


def menu_pagos():
    acciones = [
        (1, "Registrar Pago", registrar_pago),
        (2, "Listar Pagos", listar_pago),
        (3, "Buscar Pago", buscar_pago),
        (4, "Modificar Pago", modificar_pago),
        (5, "Eliminar Pago", eliminar_pago)
    ]
    menu_generico("GESTIÓN DE PAGOS", acciones)


def menu_suscripciones():
    acciones = [
        (1, "Registrar Suscripción", registrar_suscripcion),
        (2, "Listar Suscripciones", listar_suscripcion),
        (3, "Buscar Suscripción", buscar_suscripcion),
        (4, "Modificar Suscripción", modificar_suscripcion),
        (5, "Eliminar Suscripción", eliminar_suscripcion)
    ]
    menu_generico("GESTIÓN DE SUSCRIPCIONES", acciones)


def menu_principal(usuario_actual):
    acciones = [
        (1, "Gestión de Miembros", menu_miembros),
        (2, "Gestión de Pagos", menu_pagos),
        (3, "Gestión de Suscripciones", menu_suscripciones)
    ]

    if usuario_actual[2] == "admin":
        acciones.append((4, "Registrar Nuevo Usuario (Admin)", registrar_usuario))

    menu_generico("SISTEMA DE GESTIÓN DE GIMNASIO", acciones, texto_salir="Cerrar sesión y salir")


if __name__ == "__main__":
    if inicializar_bd():
        usuario_autenticado = iniciar_sesion()
        if usuario_autenticado:
            menu_principal(usuario_autenticado)
    else:
        print("\nNo se pudo iniciar la base de datos. Verifique permisos de escritura.")
