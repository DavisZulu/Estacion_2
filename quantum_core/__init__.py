"""
quantum_core
Paquete del sistema de gestion de transacciones Quantum Core.

Cada modulo tiene una sola responsabilidad, siguiendo el principio SRP que se
estudio en la Semana 3:

    modelo        -> las clases de transaccion (encapsulamiento, herencia,
                     polimorfismo).
    fabrica       -> decide que clase construir a partir del texto del tipo.
    cargador      -> lee archivos planos tolerando registros corruptos.
    serializador  -> traduce objetos a JSON y de JSON a objetos.
    reportes      -> presenta los resultados en distintos formatos.

Las clases se escriben UNA sola vez, en modelo.py, y los demas modulos las
importan. Esa es la diferencia central entre esta entrega y los archivos
sueltos de cada semana, donde la misma jerarquia estaba repetida tres veces.
"""

from quantum_core.modelo import (
    TransaccionBase,
    TransaccionCredito,
    TransaccionDebito,
    TransaccionEfectivo,
    TransaccionCripto,
)
from quantum_core.fabrica import crear_transaccion, registrar_tipo, tipos_disponibles

__all__ = [
    "TransaccionBase",
    "TransaccionCredito",
    "TransaccionDebito",
    "TransaccionEfectivo",
    "TransaccionCripto",
    "crear_transaccion",
    "registrar_tipo",
    "tipos_disponibles",
]
