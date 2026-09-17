"""
test_integracion.py
Pruebas automaticas del sistema Quantum Core.

POR QUE HAY PRUEBAS EN ESTA ENTREGA
-----------------------------------
El enunciado no las pide, pero son la forma profesional de demostrar que lo que
el informe afirma es cierto. Cada prueba de este archivo verifica una de las
afirmaciones de la entrega:

    El encapsulamiento impide guardar un monto negativo.
    El polimorfismo hace que cada clase calcule su impacto de otra forma.
    La fabrica queda abierta a extension (OCP) gracias al registro de tipos.
    La carga tolerante a fallos procesa 38 registros y descarta 12.
    La serializacion conserva el monto y recupera la clase original.

Ejecucion desde la raiz del proyecto:

    python3 -m unittest discover -s pruebas -t .
"""

import os
import tempfile
import unittest

from quantum_core.modelo import (
    TransaccionBase,
    TransaccionCredito,
    TransaccionDebito,
    TransaccionEfectivo,
    TransaccionCripto,
)
from quantum_core.fabrica import (
    crear_transaccion,
    registrar_tipo,
    eliminar_tipo,
    tipos_disponibles,
)
from quantum_core.cargador import (
    configurar_registro,
    cargar_transacciones,
    calcular_monto_total,
)
from quantum_core.serializador import (
    guardar_transacciones,
    cargar_transacciones_json,
    json_a_objeto,
    objeto_a_json,
)


ARCHIVO_CORRUPTO = os.path.join("datos", "transacciones_corruptas.txt")


class PruebaEncapsulamiento(unittest.TestCase):
    """El monto solo se puede guardar pasando por el setter que valida."""

    def test_monto_negativo_es_rechazado(self):
        with self.assertRaises(ValueError):
            TransaccionCredito("T001", "CREDITO", -1)

    def test_monto_no_numerico_es_rechazado(self):
        with self.assertRaises(ValueError):
            TransaccionCredito("T002", "CREDITO", "texto_invalido")

    def test_el_monto_se_guarda_como_numero(self):
        transaccion = TransaccionCredito("T003", "CREDITO", "500000")
        self.assertEqual(transaccion.monto, 500000.0)
        self.assertIsInstance(transaccion.monto, float)

    def test_el_setter_tambien_protege_una_asignacion_posterior(self):
        transaccion = TransaccionDebito("T004", "DEBITO", 1000)
        with self.assertRaises(ValueError):
            transaccion.monto = -50


class PruebaPolimorfismo(unittest.TestCase):
    """La misma llamada produce un resultado distinto en cada clase."""

    def test_cada_clase_calcula_su_propio_impacto(self):
        monto = 100000
        esperado = {
            TransaccionCredito: 2000.0,   # 2 %
            TransaccionDebito: 1500.0,    # comision fija
            TransaccionEfectivo: 1000.0,  # 1 %
            TransaccionCripto: 3000.0,    # 3 %
        }

        for clase, valor in esperado.items():
            with self.subTest(clase=clase.__name__):
                objeto = clase("T005", "X", monto)
                self.assertAlmostEqual(objeto.calcular_impacto(), valor, places=2)

    def test_la_clase_base_no_define_una_formula(self):
        base = TransaccionBase("T006", "BASE", 1000)
        with self.assertRaises(NotImplementedError):
            base.calcular_impacto()


class PruebaFabrica(unittest.TestCase):
    """El registro de tipos deja la fabrica abierta a extension."""

    def test_construye_la_clase_que_corresponde(self):
        self.assertIsInstance(
            crear_transaccion("T007", "cripto", 1000), TransaccionCripto
        )

    def test_un_tipo_desconocido_lanza_value_error(self):
        with self.assertRaises(ValueError):
            crear_transaccion("T008", "CHEQUE", 1000)

    def test_se_puede_agregar_un_tipo_sin_modificar_la_fabrica(self):
        class TransaccionTransferencia(TransaccionBase):
            def calcular_impacto(self):
                return 2500.0

        registrar_tipo("TRANSFERENCIA", TransaccionTransferencia)

        # El registro es estado compartido por todo el paquete: si esta prueba
        # dejara el tipo puesto, la carga del archivo corrupto aceptaria la
        # linea C019,TRANSFERENCIA,540000 y las cifras de las otras pruebas
        # cambiarian. addCleanup garantiza que se retire al terminar.
        self.addCleanup(eliminar_tipo, "TRANSFERENCIA")

        self.assertIn("TRANSFERENCIA", tipos_disponibles())
        nueva = crear_transaccion("T009", "TRANSFERENCIA", 1000)
        self.assertEqual(nueva.calcular_impacto(), 2500.0)

    def test_no_se_admite_una_clase_ajena_a_la_jerarquia(self):
        class Impostora:
            pass

        with self.assertRaises(TypeError):
            registrar_tipo("IMPOSTORA", Impostora)


class PruebaToleranciaAFallos(unittest.TestCase):
    """La carga descarta lo corrupto y continua con el resto."""

    @classmethod
    def setUpClass(cls):
        # El log se manda a un archivo temporal para no ensuciar salidas/.
        cls.temporal = tempfile.NamedTemporaryFile(suffix=".log", delete=False)
        cls.temporal.close()
        configurar_registro(cls.temporal.name)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.temporal.name)

    def test_conteo_de_validas_y_descartadas(self):
        validas, fallos = cargar_transacciones(ARCHIVO_CORRUPTO)

        self.assertEqual(len(validas), 38)
        self.assertEqual(fallos["ValueError"], 8)
        self.assertEqual(fallos["TypeError"], 4)

    def test_un_archivo_inexistente_detiene_el_proceso(self):
        with self.assertRaises(FileNotFoundError):
            cargar_transacciones(os.path.join("datos", "no_existe.txt"))


class PruebaSerializacion(unittest.TestCase):
    """El viaje objeto -> JSON -> objeto no deforma los datos."""

    @classmethod
    def setUpClass(cls):
        cls.temporal = tempfile.NamedTemporaryFile(suffix=".log", delete=False)
        cls.temporal.close()
        configurar_registro(cls.temporal.name)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.temporal.name)

    def test_el_monto_total_sobrevive_al_viaje(self):
        originales, _ = cargar_transacciones(ARCHIVO_CORRUPTO)

        with tempfile.TemporaryDirectory() as carpeta:
            destino = os.path.join(carpeta, "transacciones.json")
            guardar_transacciones(originales, destino)
            recuperadas, descartados = cargar_transacciones_json(destino)

        self.assertEqual(descartados, 0)
        self.assertEqual(len(recuperadas), len(originales))
        self.assertAlmostEqual(
            calcular_monto_total(recuperadas),
            calcular_monto_total(originales),
            places=2,
        )

    def test_la_clase_se_recupera_desde_el_texto_del_tipo(self):
        original = TransaccionCripto("T010", "CRIPTO", 1000)
        recuperada = json_a_objeto(objeto_a_json(original))

        self.assertIsInstance(recuperada, TransaccionCripto)
        self.assertEqual(recuperada.monto, original.monto)
        # No es el mismo objeto: es una copia nueva con los mismos datos.
        self.assertIsNot(recuperada, original)

    def test_un_registro_incompleto_se_reporta_con_la_clave_que_falta(self):
        with self.assertRaises(ValueError) as contexto:
            json_a_objeto('{"cliente_id": "T011", "tipo": "CREDITO"}')

        self.assertIn("monto", str(contexto.exception))

    def test_un_texto_json_mal_formado_se_traduce_a_value_error(self):
        with self.assertRaises(ValueError):
            json_a_objeto("{esto no es json}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
