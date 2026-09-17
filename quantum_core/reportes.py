"""
reportes.py
Presenta el resultado del procesamiento en distintos formatos.

ORIGEN
------
Semana 3, Actividad 2 (taller de SOLID).

POR QUE ESTE MODULO EXISTE
--------------------------
En el codigo fragil del taller, una sola clase validaba, calculaba e imprimia.
Tenia tres razones para cambiar, y eso es lo que el principio de
responsabilidad unica (SRP) prohibe. La separacion quedo asi en todo el
paquete:

    modelo + fabrica  -> que es una transaccion y como se construye.
    cargador          -> como entran los datos.
    serializador      -> como salen y vuelven los datos.
    reportes          -> como se ven los datos.  <- este modulo

Y el principio abierto/cerrado (OCP) se cumple con la herencia: agregar un
formato nuevo es escribir una clase hija de ReporteBase, sin modificar ni una
linea de las que ya funcionan. El ReporteCSV de este archivo es exactamente
ese ejercicio.
"""

import json


# ============================================================================
# 1. CONTRATO COMUN
# ============================================================================
class ReporteBase:
    """Define el metodo que deben ofrecer todos los formatos de reporte."""

    def generar(self, transacciones, resumen):
        """
        Obliga a cada formato a implementar su propia presentacion.

        Parametros:
            transacciones: lista de objetos ya validados.
            resumen: diccionario por tipo, tal como lo devuelve
                     cargador.resumir_por_tipo().
        """
        raise NotImplementedError("Cada reporte debe implementar generar().")


# ============================================================================
# 2. FORMATOS DISPONIBLES
# ============================================================================
class ReporteTexto(ReporteBase):
    """Reporte en texto plano, pensado para leerse en la terminal."""

    def generar(self, transacciones, resumen):
        print(f"{'TIPO':<10} {'CANTIDAD':>9} {'MONTO':>18} {'IMPACTO':>15}")
        print("-" * 55)

        for tipo in sorted(resumen):
            fila = resumen[tipo]
            print(
                f"{tipo:<10} {fila['cantidad']:>9} "
                f"{fila['monto']:>18,.2f} {fila['impacto']:>15,.2f}"
            )

        total_cantidad = sum(f["cantidad"] for f in resumen.values())
        total_monto = sum(f["monto"] for f in resumen.values())
        total_impacto = sum(f["impacto"] for f in resumen.values())

        print("-" * 55)
        print(
            f"{'TOTAL':<10} {total_cantidad:>9} "
            f"{total_monto:>18,.2f} {total_impacto:>15,.2f}"
        )


class ReporteJSON(ReporteBase):
    """El mismo reporte en JSON, para que lo consuma otro sistema."""

    def generar(self, transacciones, resumen):
        contenido = {
            "registros_validos": len(transacciones),
            "resumen_por_tipo": {
                tipo: {
                    "cantidad": fila["cantidad"],
                    "monto": round(fila["monto"], 2),
                    "impacto": round(fila["impacto"], 2),
                }
                for tipo, fila in sorted(resumen.items())
            },
        }
        print(json.dumps(contenido, indent=4, ensure_ascii=False))


class ReporteCSV(ReporteBase):
    """
    Formato agregado SIN modificar ninguna clase anterior.

    Es la demostracion practica del principio abierto/cerrado: la extension
    consistio unicamente en escribir esta clase.
    """

    def generar(self, transacciones, resumen):
        print("tipo,cantidad,monto,impacto")

        for tipo in sorted(resumen):
            fila = resumen[tipo]
            print(
                f"{tipo},{fila['cantidad']},"
                f"{fila['monto']:.2f},{fila['impacto']:.2f}"
            )
