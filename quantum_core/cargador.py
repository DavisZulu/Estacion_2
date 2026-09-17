"""
cargador.py
Lectura de archivos planos que no se detiene ante un registro corrupto.

ORIGEN
------
Semana 4, Actividad 1.

EL PROBLEMA QUE SE RESUELVE
---------------------------
En la Semana 3 la clase quedo blindada: el setter lanza ValueError cuando el
monto es invalido. Eso esta bien, pero si nadie atrapa ese error el programa
completo se detiene en el primer registro corrupto. Al leer 50 registros, si el
numero 3 esta malo, se pierden los 47 que venian despues.

Aqui el sistema gana la capacidad de RECUPERARSE: cuando una linea falla se
deja constancia del fallo en el log y el proceso CONTINUA con la siguiente.

POR QUE EL try VA DENTRO DEL BUCLE
----------------------------------
Asi cada linea queda protegida por separado y una linea mala no arrastra a las
que vienen detras. Si el try envolviera todo el bucle, el primer fallo seguiria
interrumpiendo la lectura del resto del archivo.

QUE SE REGISTRA Y CON QUE NIVEL
-------------------------------
    warning -> un registro malo que se aparta. El sistema NO esta fallando:
               detecta el dato, lo descarta y sigue.
    error   -> una condicion que impide continuar, como un archivo inexistente.
               Ahi no hay nada que recuperar.

print() se reserva para los resultados del negocio; logging, para el rastro
auditable de la carga.
"""

import logging
import os
import sys

from quantum_core.fabrica import crear_transaccion


# Ruta por omision del archivo de auditoria que genera el programa.
ARCHIVO_LOG = os.path.join("salidas", "errores_carga.log")

# Nombre unico del registro, para que todos los modulos escriban en el mismo.
NOMBRE_REGISTRO = "quantum_core"


# ============================================================================
# 1. CONFIGURACION DEL REGISTRO DE ERRORES (LOGGING)
# ============================================================================
def configurar_registro(archivo_log=ARCHIVO_LOG):
    """
    Deja listo el registro de errores con dos destinos simultaneos.

    Destino 1: el archivo de auditoria, con fecha y hora en cada linea.
    Destino 2: la consola, para no perder la vista en vivo de lo que ocurre.

    Devuelve el objeto logger que usaran los demas modulos.
    """
    registro = logging.getLogger(NOMBRE_REGISTRO)
    registro.setLevel(logging.INFO)

    # Si la funcion se llamara dos veces, los destinos se duplicarian y cada
    # mensaje saldria repetido. Limpiarlos primero evita ese efecto.
    registro.handlers.clear()

    # La carpeta de salidas puede no existir en un clon recien descargado del
    # repositorio, porque .gitignore la excluye. Se crea antes de escribir.
    carpeta = os.path.dirname(archivo_log)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

    # mode="w" reinicia el archivo en cada ejecucion, que es lo practico para
    # una entrega academica. Con mode="a" el historico se iria acumulando.
    formato_archivo = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    destino_archivo = logging.FileHandler(archivo_log, mode="w", encoding="utf-8")
    destino_archivo.setFormatter(formato_archivo)
    registro.addHandler(destino_archivo)

    # En pantalla la fecha estorba mas que ayuda, asi que el formato es corto.
    # Se envia a sys.stdout y no al stderr para que los mensajes del log y los
    # de print() conserven su orden real cuando la salida se redirige.
    formato_consola = logging.Formatter(fmt="  %(levelname)-7s | %(message)s")
    destino_consola = logging.StreamHandler(sys.stdout)
    destino_consola.setFormatter(formato_consola)
    registro.addHandler(destino_consola)

    return registro


def obtener_registro():
    """Devuelve el registro del sistema sin volver a configurarlo."""
    return logging.getLogger(NOMBRE_REGISTRO)


# ============================================================================
# 2. EL PUNTO CRITICO: LECTURA TOLERANTE A FALLOS
# ============================================================================
def cargar_transacciones(nombre_archivo):
    """
    Lee el archivo y convierte cada linea en un objeto.

    Devuelve una tupla con la lista de objetos validos y un diccionario con el
    conteo de fallos por tipo de excepcion, para poder resumir la carga.

    Un archivo inexistente si detiene el proceso: sin datos de entrada no hay
    nada que recuperar, asi que el FileNotFoundError se registra y se vuelve a
    lanzar para que quien llama decida.
    """
    registro = obtener_registro()

    validas = []
    fallos = {"ValueError": 0, "TypeError": 0}

    registro.info(f"Inicio de carga del archivo {nombre_archivo}")

    try:
        # El bloque with cierra el archivo automaticamente al terminar, incluso
        # si ocurriera un error en el camino.
        archivo = open(nombre_archivo, "r", encoding="utf-8")
    except FileNotFoundError:
        registro.error(f"No se encontro el archivo de entrada: {nombre_archivo}")
        raise

    with archivo:
        # enumerate entrega el numero real de cada linea, necesario para que el
        # log diga exactamente donde estuvo el problema.
        for numero_linea, linea in enumerate(archivo, start=1):
            linea = linea.strip()

            # Las lineas vacias no son un error: no hay nada que procesar.
            if not linea:
                continue

            # Se limpia cada campo por separado para tolerar espacios sobrantes
            # alrededor de las comas, frecuentes en archivos reales.
            datos = [dato.strip() for dato in linea.split(",")]

            try:
                # Esta es la unica linea que puede fallar, y por eso es la que
                # va dentro del try: aqui los datos crudos se convierten en un
                # objeto. El monto se entrega tal como viene del archivo, para
                # que sea el setter de la clase el que intente convertirlo y
                # aplique la regla del negativo.
                validas.append(crear_transaccion(*datos))

            # Caso 1: el dato es del tipo correcto pero su valor no sirve
            # (texto no numerico, monto vacio, monto negativo o tipo
            # desconocido). Se usa warning y no error porque el programa no
            # esta fallando: detecta el dato malo, lo aparta y sigue.
            except ValueError as error:
                fallos["ValueError"] += 1
                registro.warning(
                    f"[Linea {numero_linea:>2}] ValueError: {error}"
                    f"  ->  registro descartado: {linea}"
                )

            # Caso 2: la cantidad de datos no es la esperada. Faltan o sobran
            # columnas, asi que la llamada al constructor queda mal armada.
            except TypeError:
                fallos["TypeError"] += 1
                registro.warning(
                    f"[Linea {numero_linea:>2}] TypeError: cantidad de datos"
                    f" incorrecta  ->  registro descartado: {linea}"
                )

    total_fallos = fallos["ValueError"] + fallos["TypeError"]
    registro.info(
        f"Fin de carga de {nombre_archivo}: {len(validas)} validas, "
        f"{total_fallos} descartadas "
        f"({fallos['ValueError']} ValueError, {fallos['TypeError']} TypeError)"
    )

    return validas, fallos


# ============================================================================
# 3. OPERACIONES SOBRE LA LISTA DE OBJETOS
# ============================================================================
def calcular_monto_total(lista_transacciones):
    """Suma los montos de todas las transacciones validas."""
    total = 0.0

    for transaccion in lista_transacciones:
        total = total + transaccion.obtener_monto()

    return total


def calcular_impacto_total(lista_transacciones):
    """
    Suma el impacto de todas las transacciones.

    El ciclo no pregunta de que clase es cada objeto: siempre llama a
    calcular_impacto() y Python elige la version que corresponde. Ese es el
    polimorfismo trabajando junto con la recuperacion de errores.
    """
    total = 0.0

    for transaccion in lista_transacciones:
        total = total + transaccion.calcular_impacto()

    return total


def resumir_por_tipo(lista_transacciones):
    """Agrupa cantidad, monto e impacto por cada tipo de transaccion."""
    resumen = {}

    for transaccion in lista_transacciones:
        tipo = transaccion.tipo

        if tipo not in resumen:
            resumen[tipo] = {"cantidad": 0, "monto": 0.0, "impacto": 0.0}

        resumen[tipo]["cantidad"] += 1
        resumen[tipo]["monto"] += transaccion.obtener_monto()
        resumen[tipo]["impacto"] += transaccion.calcular_impacto()

    return resumen
