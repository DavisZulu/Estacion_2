"""
main.py
Punto de entrada unico del sistema Quantum Core.

QUE HACE ESTE ARCHIVO
---------------------
Coordina, en un solo recorrido, las tres capacidades que la Estacion 2 pide
consolidar. No contiene reglas de negocio: solo llama a los modulos del paquete
en el orden correcto.

    Etapa 1  Carga tolerante a fallos      -> quantum_core.cargador   (Semana 4)
    Etapa 2  Reporte de resultados         -> quantum_core.reportes   (Semana 3)
    Etapa 3  Serializacion a JSON          -> quantum_core.serializador (Semana 4)
    Etapa 4  Deserializacion y verificacion-> quantum_core.serializador

La Etapa 4 es la que demuestra que el viaje completo funciona: se vuelven a
construir los objetos desde el archivo JSON y se compara el monto total con el
de la carga original. Si los dos numeros coinciden, ningun dato se perdio ni se
deformo en el camino.

EJECUCION
---------
    python3 main.py                                  (archivo con registros corruptos)
    python3 main.py --archivo datos/transacciones.txt
    python3 main.py --formato json
    python3 main.py --formato csv

ARCHIVOS QUE GENERA
-------------------
    salidas/errores_carga.log     registro de auditoria de la carga
    salidas/transacciones.json    las transacciones validas serializadas
"""

import argparse
import os
import sys

from quantum_core.cargador import (
    configurar_registro,
    cargar_transacciones,
    calcular_monto_total,
    calcular_impacto_total,
    resumir_por_tipo,
)
from quantum_core.reportes import ReporteTexto, ReporteJSON, ReporteCSV
from quantum_core.serializador import (
    guardar_transacciones,
    cargar_transacciones_json,
)


# Valores por omision, pensados para que el programa corra sin argumentos.
ARCHIVO_ENTRADA = os.path.join("datos", "transacciones_corruptas.txt")
ARCHIVO_JSON = os.path.join("salidas", "transacciones.json")
ARCHIVO_LOG = os.path.join("salidas", "errores_carga.log")

# Registro de formatos: agregar uno nuevo no obliga a tocar la funcion main().
FORMATOS = {
    "texto": ReporteTexto,
    "json": ReporteJSON,
    "csv": ReporteCSV,
}


def titulo(texto):
    """Imprime un encabezado de seccion para que la salida se lea ordenada."""
    print()
    print("=" * 70)
    print(texto)
    print("=" * 70)


def leer_argumentos():
    """Define y lee las opciones de la linea de comandos."""
    analizador = argparse.ArgumentParser(
        description="Sistema de gestion de transacciones Quantum Core."
    )
    analizador.add_argument(
        "--archivo",
        default=ARCHIVO_ENTRADA,
        help="Archivo de entrada con los registros a procesar.",
    )
    analizador.add_argument(
        "--formato",
        default="texto",
        choices=sorted(FORMATOS),
        help="Formato del reporte de resultados.",
    )
    return analizador.parse_args()


def main():
    """Ejecuta el flujo completo del sistema."""
    opciones = leer_argumentos()

    # El registro se configura una sola vez, antes de procesar cualquier
    # archivo, para que todos los fallos queden en el mismo log.
    configurar_registro(ARCHIVO_LOG)

    # ---- Etapa 1: carga tolerante a fallos -------------------------------
    titulo(f"ETAPA 1 · CARGA TOLERANTE A FALLOS  ({opciones.archivo})")

    try:
        transacciones, fallos = cargar_transacciones(opciones.archivo)
    except FileNotFoundError:
        print(f"\nNo se pudo continuar: no existe el archivo {opciones.archivo}")
        return 1

    descartados = fallos["ValueError"] + fallos["TypeError"]

    print()
    print(f"  Registros validos procesados : {len(transacciones)}")
    print(f"  Registros descartados        : {descartados}"
          f"  ({fallos['ValueError']} ValueError, {fallos['TypeError']} TypeError)")
    print(f"  Monto total acumulado        : ${calcular_monto_total(transacciones):,.2f}")
    print(f"  Impacto total calculado      : ${calcular_impacto_total(transacciones):,.2f}")

    if not transacciones:
        print("\nNo hay registros validos que procesar.")
        return 1

    # ---- Etapa 2: reporte -------------------------------------------------
    titulo(f"ETAPA 2 · REPORTE DE RESULTADOS  (formato {opciones.formato})")

    resumen = resumir_por_tipo(transacciones)
    reporte = FORMATOS[opciones.formato]()
    reporte.generar(transacciones, resumen)

    # ---- Etapa 3: serializacion ------------------------------------------
    titulo("ETAPA 3 · SERIALIZACION A JSON")

    escritos = guardar_transacciones(transacciones, ARCHIVO_JSON)
    print(f"\n  {escritos} registros escritos en {ARCHIVO_JSON}")

    # ---- Etapa 4: deserializacion y verificacion -------------------------
    titulo("ETAPA 4 · DESERIALIZACION Y VERIFICACION DEL VIAJE COMPLETO")

    reconstruidas, perdidos = cargar_transacciones_json(ARCHIVO_JSON)

    monto_original = calcular_monto_total(transacciones)
    monto_recuperado = calcular_monto_total(reconstruidas)
    coincide = abs(monto_original - monto_recuperado) < 0.01

    print()
    print(f"  Objetos antes de serializar   : {len(transacciones)}")
    print(f"  Objetos reconstruidos del JSON: {len(reconstruidas)}"
          f"  ({perdidos} descartados)")
    print(f"  Monto original                : ${monto_original:,.2f}")
    print(f"  Monto recuperado              : ${monto_recuperado:,.2f}")
    print(f"  Integridad de los datos       : "
          f"{'VERIFICADA' if coincide else 'NO COINCIDE'}")

    # La clase tambien se recupera: el JSON solo guardo el texto del tipo y la
    # fabrica volvio a construir la clase especializada que le corresponde.
    if reconstruidas:
        muestra = reconstruidas[0]
        print(f"  Clase recuperada del primero  : {type(muestra).__name__}")

    titulo("FIN DEL PROCESO")
    print(f"  Registro de auditoria : {ARCHIVO_LOG}")
    print(f"  Datos serializados    : {ARCHIVO_JSON}")
    print()

    return 0 if coincide else 1


if __name__ == "__main__":
    sys.exit(main())
