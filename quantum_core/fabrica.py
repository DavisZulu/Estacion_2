"""
fabrica.py
Decide que clase construir a partir del texto que trae el archivo de datos.

ORIGEN
------
Semana 3 (la funcion crear_transaccion) y Semana 3 Actividad 2 (el principio
OCP del taller de SOLID).

QUE CAMBIO RESPECTO A LAS ENTREGAS ANTERIORES
---------------------------------------------
En las Semanas 3 y 4 la fabrica era una cadena de if / elif:

    if tipo == "CREDITO":
        return TransaccionCredito(...)
    elif tipo == "DEBITO":
        ...

Funciona, pero incumple el principio abierto/cerrado (OCP): para admitir un
tipo nuevo hay que ENTRAR a modificar la funcion, que ya estaba probada.

Aqui la correspondencia entre el texto y la clase vive en un diccionario, el
REGISTRO DE TIPOS. Agregar un tipo nuevo es agregar una entrada, desde fuera y
sin tocar esta funcion:

    registrar_tipo("TRANSFERENCIA", TransaccionTransferencia)

Es el mismo razonamiento del taller de SOLID, donde agregar ReporteCSV no
obligo a modificar codigo_fuerte_srp.py.
"""

from quantum_core.modelo import (
    TransaccionCredito,
    TransaccionDebito,
    TransaccionEfectivo,
    TransaccionCripto,
    TransaccionBase,
)


# ============================================================================
# REGISTRO DE TIPOS: la tabla que reemplaza la cadena de if / elif
# ============================================================================
_REGISTRO = {
    "CREDITO": TransaccionCredito,
    "DEBITO": TransaccionDebito,
    "EFECTIVO": TransaccionEfectivo,
    "CRIPTO": TransaccionCripto,
}


def registrar_tipo(nombre, clase):
    """
    Agrega un tipo nuevo al registro sin modificar la fabrica.

    La clase debe heredar de TransaccionBase; de lo contrario no tendria el
    setter que valida el monto ni el metodo calcular_impacto(), y el resto del
    sistema fallaria mas adelante, cuando ya seria dificil saber por que.
    """
    if not issubclass(clase, TransaccionBase):
        raise TypeError("La clase registrada debe heredar de TransaccionBase.")

    _REGISTRO[nombre.upper()] = clase


def eliminar_tipo(nombre):
    """
    Quita un tipo del registro.

    Es la operacion simetrica de registrar_tipo(). Se usa sobre todo en las
    pruebas automaticas: como el registro es estado compartido de todo el
    paquete, una prueba que agrega un tipo debe dejarlo como estaba para no
    alterar el resultado de las siguientes.
    """
    _REGISTRO.pop(nombre.upper(), None)


def tipos_disponibles():
    """Devuelve la lista de tipos que el sistema sabe construir."""
    return sorted(_REGISTRO.keys())


def crear_transaccion(cliente_id, tipo, monto):
    """
    Devuelve el objeto especializado que corresponde al tipo recibido.

    Centralizar esta decision evita repartir condiciones por todo el programa.
    Un tipo no soportado genera un ValueError, que sera atrapado por el
    cargador igual que cualquier otro fallo de datos.

    Nota sobre el TypeError: esta funcion exige exactamente tres argumentos. Si
    una linea del archivo trae dos columnas (o cuatro), al desempaquetarla con
    el operador * la llamada queda mal armada y Python lanza TypeError antes de
    ejecutar una sola linea de este cuerpo.
    """
    # Normalizar permite aceptar CREDITO, Credito o credito de la misma forma.
    tipo = str(tipo).strip().upper()

    if tipo not in _REGISTRO:
        raise ValueError(f"tipo de transaccion desconocido: {tipo}")

    clase = _REGISTRO[tipo]

    return clase(cliente_id, tipo, monto)
