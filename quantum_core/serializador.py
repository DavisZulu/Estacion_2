"""
serializador.py
Traduce los objetos a JSON y el JSON de vuelta a objetos.

ORIGEN
------
Semana 4, Actividad 2.

EL PROBLEMA QUE SE RESUELVE
---------------------------
Los objetos viven en la MEMORIA de Python: existen mientras el programa corre y
desaparecen cuando termina. Para guardarlos en disco, meterlos en una base de
datos o enviarlos por internet hay que convertirlos a un formato de texto que
cualquier sistema entienda. Ese formato universal es JSON.

EL VIAJE COMPLETO, EN DOS ESCALAS
---------------------------------
    Objeto Python  ->  Diccionario  ->  Texto JSON      (serializar)
    Texto JSON     ->  Diccionario  ->  Objeto Python   (deserializar)

La escala del medio, el DICCIONARIO, no es opcional: el modulo json no sabe
traducir un objeto de una clase propia del proyecto, pero si sabe traducir un
diccionario.

QUE SE PIERDE Y QUE SE RECUPERA
-------------------------------
Al serializar se pierden los METODOS: el JSON guarda unicamente los DATOS. Al
deserializar los metodos vuelven, porque se los devuelve la clase en el momento
de llamar al constructor. El objeto que resulta no es el original: es una copia
nueva con los mismos datos.

El JSON tampoco guarda A QUE CLASE pertenecia el objeto. Lo unico que viaja es
el dato "tipo". Es la fabrica la que lee ese texto en el destino y decide si
construye un credito, un debito, un efectivo o una cripto.

MANEJO DE ERRORES
-----------------
    Origen del fallo                        Excepcion
    ----------------------------------------------------------------
    Texto JSON mal formado                  json.JSONDecodeError
    Falta una clave en el registro          se valida y se lanza ValueError
    Tipo de transaccion desconocido         ValueError (lo lanza la fabrica)
    Monto que no es un numero               ValueError (lo lanza el setter)
    Monto negativo                          ValueError (lo lanza el setter)
    El archivo JSON no existe               FileNotFoundError

Los fallos tecnicos se traducen a un ValueError con un mensaje del dominio,
porque quien llama necesita saber QUE dato esta mal, no en que linea del modulo
json ocurrio.

DETALLE QUE CONVIENE NO OLVIDAR
-------------------------------
json.dumps() NO devuelve un diccionario: devuelve un str. Y json.loads() NO
devuelve un objeto: devuelve un diccionario. El ultimo tramo hasta el objeto es
siempre manual. La "s" de dumps y loads es de string, no es un plural.
"""

import json
import os

from quantum_core.cargador import obtener_registro
from quantum_core.fabrica import crear_transaccion


# Las tres claves que debe traer todo registro serializado.
CLAVES_OBLIGATORIAS = ("cliente_id", "tipo", "monto")


# ============================================================================
# 1. DE OBJETO A JSON (serializar)
# ============================================================================
def objeto_a_diccionario(transaccion):
    """
    Convierte un objeto en el diccionario que el modulo json si sabe traducir.

    Se guardan solo los datos. El impacto se incluye como valor calculado,
    porque es informacion util para quien reciba el archivo y no se puede
    recalcular sin conocer la clase de origen.
    """
    return {
        "cliente_id": transaccion.cliente_id,
        "tipo": transaccion.tipo,
        "monto": transaccion.obtener_monto(),
        "impacto": transaccion.calcular_impacto(),
    }


def objeto_a_json(transaccion):
    """Devuelve el objeto convertido en texto JSON."""
    return json.dumps(
        objeto_a_diccionario(transaccion), indent=4, ensure_ascii=False
    )


def guardar_transacciones(lista_transacciones, nombre_archivo):
    """
    Escribe la lista completa de objetos en un archivo JSON.

    Devuelve la cantidad de registros escritos. La carpeta de destino se crea
    si no existe, porque .gitignore excluye la carpeta de salidas y en un clon
    recien descargado del repositorio no estaria.
    """
    registro = obtener_registro()

    carpeta = os.path.dirname(nombre_archivo)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

    como_lista = [objeto_a_diccionario(t) for t in lista_transacciones]

    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        json.dump(como_lista, archivo, indent=4, ensure_ascii=False)

    registro.info(
        f"Serializacion completada: {len(como_lista)} registros escritos "
        f"en {nombre_archivo}"
    )

    return len(como_lista)


# ============================================================================
# 2. DE JSON A OBJETO (deserializar)
# ============================================================================
def diccionario_a_objeto(como_dict):
    """
    Reconstruye el objeto a partir de un diccionario.

    Antes de llamar a la fabrica se comprueba que esten las tres claves
    obligatorias. Sin esa validacion, un registro incompleto produciria un
    KeyError, que no le dice a nadie cual fue el dato que falto.
    """
    if not isinstance(como_dict, dict):
        raise ValueError("el registro serializado no es un objeto JSON valido")

    faltantes = [c for c in CLAVES_OBLIGATORIAS if c not in como_dict]

    if faltantes:
        raise ValueError(
            "al registro le faltan las claves: " + ", ".join(faltantes)
        )

    # La fabrica decide la clase a partir del texto "tipo"; el setter de la
    # clase valida el monto. La validacion no se repite aqui.
    return crear_transaccion(
        como_dict["cliente_id"], como_dict["tipo"], como_dict["monto"]
    )


def json_a_objeto(texto_json):
    """
    Convierte un texto JSON en un objeto.

    El JSONDecodeError se traduce a ValueError para que quien llama maneje un
    solo tipo de fallo de datos, sin tener que conocer el modulo json.
    """
    try:
        como_dict = json.loads(texto_json)
    except json.JSONDecodeError as error:
        raise ValueError(f"el texto JSON esta mal formado: {error.msg}")

    return diccionario_a_objeto(como_dict)


def cargar_transacciones_json(nombre_archivo):
    """
    Lee un archivo JSON y devuelve la lista de objetos reconstruidos.

    Aplica la misma estrategia de recuperacion del cargador de texto plano: un
    registro malo se descarta con su motivo en el log y el proceso continua.
    Devuelve la lista de objetos y la cantidad de registros descartados.
    """
    registro = obtener_registro()

    try:
        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            contenido = json.load(archivo)
    except FileNotFoundError:
        registro.error(f"No se encontro el archivo JSON: {nombre_archivo}")
        raise
    except json.JSONDecodeError as error:
        registro.error(
            f"El archivo {nombre_archivo} no contiene JSON valido: {error.msg}"
        )
        raise ValueError(f"el archivo JSON esta mal formado: {error.msg}")

    if not isinstance(contenido, list):
        raise ValueError("el archivo JSON deberia contener una lista de registros")

    objetos = []
    descartados = 0

    for posicion, como_dict in enumerate(contenido, start=1):
        try:
            objetos.append(diccionario_a_objeto(como_dict))
        except ValueError as error:
            descartados += 1
            registro.warning(
                f"[Registro {posicion:>2}] descartado al deserializar: {error}"
            )

    registro.info(
        f"Deserializacion de {nombre_archivo}: {len(objetos)} objetos "
        f"reconstruidos, {descartados} descartados"
    )

    return objetos, descartados
