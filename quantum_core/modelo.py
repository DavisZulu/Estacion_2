"""
modelo.py
Las clases del dominio: que es una transaccion y como se comporta.

ORIGEN
------
Semana 3, Actividad 1. Aqui viven los tres pilares de la POO que pide la
Estacion 2:

    Encapsulamiento -> el monto se guarda en el atributo protegido _monto y
                       solo se puede cambiar pasando por el setter, que valida.
    Herencia        -> las cuatro clases hijas reutilizan constructor, getter,
                       setter y metodos de consulta sin repetir una linea.
    Polimorfismo    -> las cuatro implementan calcular_impacto() de forma
                       distinta y quien las usa no necesita saber cual es cual.

RESPONSABILIDAD UNICA
---------------------
Este modulo no lee archivos, no escribe logs y no genera JSON. Solo sabe que
es una transaccion. Todo lo demas vive en los otros modulos del paquete.
"""


# ============================================================================
# 1. CLASE BASE: LO QUE COMPARTEN TODAS LAS TRANSACCIONES
# ============================================================================
class TransaccionBase:
    """
    Estructura comun de todas las transacciones, con el monto validado.

    En esta clase NO hay ningun try-except, y es intencional. El objeto solo
    sabe defenderse lanzando el error; decidir que se hace con ese error es
    trabajo de quien lo llama. Si se atrapara aqui dentro, la clase aceptaria
    datos malos en silencio y se perderia el blindaje.
    """

    def __init__(self, cliente_id, tipo, monto):
        """
        Inicializa una transaccion.

        La asignacion self.monto = monto no guarda el dato directamente: pasa
        por el setter, de modo que incluso el valor inicial queda validado.
        """
        self.cliente_id = cliente_id
        self.tipo = tipo
        self.monto = monto

    # ---- Encapsulamiento -------------------------------------------------
    # Getter: permite leer el monto con objeto.monto. El valor real vive en el
    # atributo protegido _monto, al que el resto del programa no llega directo.
    @property
    def monto(self):
        """Devuelve el monto protegido de la transaccion."""
        return self._monto

    @monto.setter
    def monto(self, nuevo_monto):
        """
        Valida y almacena un nuevo monto.

        De aqui salen DOS errores distintos, aunque los dos se llamen igual:

          1. float(nuevo_monto) lanza ValueError cuando el dato es un texto que
             no representa un numero, como "texto_invalido" o una cadena vacia.
             Es un fallo de CONVERSION.
          2. El raise lo lanzamos nosotros cuando el numero es negativo. El
             dato si es numerico; lo que falla es la REGLA DE NEGOCIO.
        """
        nuevo_monto = float(nuevo_monto)

        if nuevo_monto < 0:
            raise ValueError("el monto no puede ser negativo")

        # Se asigna a _monto para no volver a entrar al setter.
        self._monto = nuevo_monto

    # ---- Polimorfismo ----------------------------------------------------
    def calcular_impacto(self):
        """
        Obliga a cada clase hija a definir su propia formula.

        La clase base no tiene una regla general. Si una hija olvidara escribir
        su version, este error avisa con claridad que falta implementarla.
        """
        raise NotImplementedError(
            "Cada tipo de transaccion debe calcular su propio impacto."
        )

    # ---- Consulta --------------------------------------------------------
    def obtener_informacion(self):
        """Devuelve los datos principales en un texto facil de leer."""
        return (
            f"ID: {self.cliente_id:<6} | Tipo: {self.tipo:<10} | "
            f"Monto: ${self.monto:>14,.2f}"
        )

    def obtener_monto(self):
        """Devuelve el monto para operaciones como el calculo del total."""
        return self.monto

    def es_del_tipo(self, tipo_filtro):
        """Indica si la transaccion corresponde al tipo solicitado."""
        return self.tipo == tipo_filtro.upper()

    def __str__(self):
        """Representacion legible del objeto al imprimirlo."""
        return self.obtener_informacion()


# ============================================================================
# 2. CLASES HIJAS: HERENCIA Y POLIMORFISMO
# ============================================================================
# Todas reciben el constructor, el getter, el setter y los metodos de consulta
# de TransaccionBase. Cada una reescribe unicamente calcular_impacto(): esa
# respuesta distinta al mismo metodo es el polimorfismo.


class TransaccionCredito(TransaccionBase):
    """Credito: el impacto corresponde al 2 % del monto."""

    def calcular_impacto(self):
        return self.monto * 0.02


class TransaccionDebito(TransaccionBase):
    """Debito: comision fija de 1.500, sin importar el monto."""

    def calcular_impacto(self):
        return 1500.0


class TransaccionEfectivo(TransaccionBase):
    """Efectivo: el impacto corresponde al 1 % del monto."""

    def calcular_impacto(self):
        return self.monto * 0.01


class TransaccionCripto(TransaccionBase):
    """Cripto: el impacto corresponde al 3 % del monto."""

    def calcular_impacto(self):
        return self.monto * 0.03
