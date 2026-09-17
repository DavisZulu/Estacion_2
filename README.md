# Estación 2 · Segunda entrega — Quantum Core

**Proyecto:** Quantum Core — Sistema de gestión de transacciones
**Núcleo:** Fundamentos de Software · CEIPA Business School
**Autor:** Deibis Zuluaga Baena
**Docente:** Simón Peláez Loaiza
**Repositorio público:** https://github.com/DavisZulu/Estacion_2

Esta entrega **no es lo de una sola semana**: consolida en un único sistema lo construido en las
Semanas 3, 4 y 5. El objetivo no era juntar archivos, sino resolver lo que la acumulación dejó a la
vista: la misma jerarquía de clases estaba **escrita tres veces**, una por actividad. Aquí se
escribe una sola vez y cada capacidad vive en su propio módulo.

## Qué se acumula en esta entrega

| Semana | Actividad | Qué aportó | Dónde quedó |
|--------|-----------|------------|-------------|
| 3 | Actividad 1 | Encapsulamiento, herencia y polimorfismo | [`quantum_core/modelo.py`](./quantum_core/modelo.py) |
| 3 | Actividad 2 | Principios SOLID (SRP y OCP) | [`quantum_core/fabrica.py`](./quantum_core/fabrica.py) y [`quantum_core/reportes.py`](./quantum_core/reportes.py) |
| 4 | Actividad 1 | Recuperación con `try/except` y *logging* | [`quantum_core/cargador.py`](./quantum_core/cargador.py) |
| 4 | Actividad 2 | Serialización y persistencia en JSON | [`quantum_core/serializador.py`](./quantum_core/serializador.py) |
| 5 | Actividad 1 | Control de versiones con Git y GitHub | Historial de *commits* y ramas de este repositorio |

## Estructura del proyecto

```text
Estacion_2/
├── main.py                        # Punto de entrada: recorre las cuatro etapas
├── quantum_core/                  # El paquete con la solución
│   ├── __init__.py
│   ├── modelo.py                  # Qué es una transacción y cómo se comporta
│   ├── fabrica.py                 # Qué clase construir a partir del texto del tipo
│   ├── cargador.py                # Cómo entran los datos, tolerando lo corrupto
│   ├── serializador.py            # Cómo salen y vuelven los datos (JSON)
│   └── reportes.py                # Cómo se ven los datos
├── datos/
│   ├── transacciones.txt          # 10 registros limpios
│   └── transacciones_corruptas.txt # 50 registros, 12 con fallos deliberados
├── pruebas/
│   └── test_integracion.py        # 16 pruebas automáticas
├── salidas/                       # Las genera el programa; se versionan como evidencia
│   ├── errores_carga.log          # Registro de auditoría de la carga
│   └── transacciones.json         # Las 38 transacciones válidas serializadas
└── Estacion2_Informe_Tecnico_APA_Deibis_Zuluaga.pdf   # Informe técnico, normas APA
```

| Módulo | Responsabilidad única |
|--------|-----------------------|
| `modelo.py` | Las clases del dominio. No lee archivos, no escribe *logs*, no genera JSON. |
| `fabrica.py` | Traduce el texto `"CREDITO"` a la clase `TransaccionCredito`. |
| `cargador.py` | Lee texto plano y sobrevive a los registros corruptos. |
| `serializador.py` | Traduce objetos a JSON y JSON a objetos. |
| `reportes.py` | Presenta los resultados en texto, JSON o CSV. |

> **Nota:** esa separación es el principio de responsabilidad única (SRP) del taller de la Semana 3,
> aplicado ya no a una clase sino a la arquitectura completa. Cada archivo tiene **una sola razón
> para cambiar**.

## Cómo ejecutar

Requiere Python 3.10 o superior. **No usa librerías externas**: todo se resuelve con la biblioteca
estándar (`json`, `logging`, `argparse`, `os`).

```bash
cd Estacion_2

python3 main.py                                   # archivo con registros corruptos
python3 main.py --archivo datos/transacciones.txt # archivo limpio
python3 main.py --formato json                    # reporte en JSON
python3 main.py --formato csv                     # reporte en CSV

python3 -m unittest discover -s pruebas -t .      # pruebas automáticas
```

El programa **crea la carpeta `salidas/` si no existe**, de modo que funciona en un clon recién
descargado de GitHub.

> **Nota:** los dos archivos de `salidas/` están versionados a propósito. Son la evidencia de que
> la tolerancia a fallos y la serialización funcionan: `errores_carga.log` conserva los 12 descartes
> con su línea y su motivo, y `transacciones.json` las 38 transacciones válidas. El programa los
> regenera en cada ejecución, así que se pueden reproducir.

## Arquitectura: una sola jerarquía de clases

Este es el cambio de fondo respecto a las entregas semanales.

| | Antes (Semanas 3 y 4) | Ahora (Estación 2) |
|---|---|---|
| Definición de las clases | Repetida en 3 archivos | 1 sola vez en `modelo.py` |
| Corregir una regla del negocio | Hay que tocar 3 archivos | Se toca 1 |
| Riesgo | Las tres copias se desincronizan | No hay copias |

> **Nota:** la duplicación no era descuido, sino la consecuencia de entregar cada semana por
> separado. Consolidar es precisamente lo que pide esta estación.

### Los tres pilares de la POO

| Pilar | Dónde está | Cómo se comprueba |
|-------|-----------|-------------------|
| **Encapsulamiento** | El monto vive en `_monto` y solo se asigna pasando por un *setter* que valida | `TransaccionCredito("T1","CREDITO",-1)` lanza `ValueError` |
| **Herencia** | Las cuatro clases hijas reutilizan constructor, *getter*, *setter* y consultas | Ninguna hija repite el `__init__` |
| **Polimorfismo** | Cada hija implementa `calcular_impacto()` de forma distinta | El mismo `for` produce cuatro resultados diferentes |

| Clase | Regla de impacto |
|-------|------------------|
| `TransaccionCredito` | 2 % del monto |
| `TransaccionDebito` | Comisión fija de 1.500 |
| `TransaccionEfectivo` | 1 % del monto |
| `TransaccionCripto` | 3 % del monto |

### La fábrica: del `if/elif` al registro de tipos

En las semanas anteriores, `crear_transaccion()` era una cadena de condiciones. Funcionaba, pero
para admitir un tipo nuevo había que **entrar a modificar** una función que ya estaba probada, que
es justo lo que el principio abierto/cerrado (OCP) prohíbe.

Ahora la correspondencia entre el texto y la clase vive en un diccionario:

```python
_REGISTRO = {
    "CREDITO": TransaccionCredito,
    "DEBITO": TransaccionDebito,
    "EFECTIVO": TransaccionEfectivo,
    "CRIPTO": TransaccionCripto,
}
```

Agregar un tipo es agregar una entrada **desde fuera**, sin tocar la fábrica:

```python
registrar_tipo("TRANSFERENCIA", TransaccionTransferencia)
```

> **Aviso:** `registrar_tipo()` verifica que la clase herede de `TransaccionBase`. Sin esa
> comprobación se podría registrar cualquier objeto y el fallo aparecería mucho después, cuando ya
> sería difícil saber de dónde vino.

## Tolerancia a fallos

El `try` va **dentro del bucle**, no alrededor. Así cada línea queda protegida por separado y un
registro malo no arrastra a los que vienen detrás.

| Excepción | Causa | Ejemplo del archivo |
|-----------|-------|---------------------|
| `ValueError` | El valor no se puede convertir a número | `C003,DEBITO,texto_invalido` |
| `ValueError` | Es un número válido, pero incumple la regla del negocio | `C004,CREDITO,-200000` |
| `ValueError` | El tipo de transacción no está registrado | `C019,TRANSFERENCIA,540000` |
| `TypeError` | **Faltan** columnas | `C006,DEBITO` |
| `TypeError` | **Sobran** columnas | `C035,CRIPTO,1540000,EXTRA` |
| `FileNotFoundError` | No existe el archivo de entrada | `--archivo datos/no_existe.txt` |

Los cinco primeros se descartan y el proceso continúa. El último **sí detiene** el programa: sin
datos de entrada no hay nada que recuperar.

> **Nota:** los fallos se registran con `warning`, no con `error`. El sistema no está fallando:
> detecta el dato malo, lo aparta y sigue. Esa es exactamente la diferencia entre una advertencia y
> un error.

### Salida esperada

```text
  WARNING | [Linea  3] ValueError: could not convert string to float: 'texto_invalido'  ->  registro descartado: C003,DEBITO,texto_invalido
  WARNING | [Linea  4] ValueError: el monto no puede ser negativo  ->  registro descartado: C004,CREDITO,-200000
  WARNING | [Linea  6] TypeError: cantidad de datos incorrecta  ->  registro descartado: C006,DEBITO
  INFO    | Fin de carga de datos/transacciones_corruptas.txt: 38 validas, 12 descartadas (8 ValueError, 4 TypeError)

  Registros validos procesados : 38
  Registros descartados        : 12  (8 ValueError, 4 TypeError)
  Monto total acumulado        : $18,557,551.25
  Impacto total calculado      : $456,418.00
```

El mismo detalle queda con fecha y hora en `salidas/errores_carga.log`, que es el rastro auditable
de la carga.

## Serialización y persistencia

Los objetos viven en la **memoria** de Python: existen mientras el programa corre y desaparecen
cuando termina. JSON es el formato de texto que cualquier sistema entiende.

```text
Objeto Python  ->  Diccionario  ->  Texto JSON      (serializar)
Texto JSON     ->  Diccionario  ->  Objeto Python   (deserializar)
```

La escala del medio no es opcional: el módulo `json` no sabe traducir una clase propia del
proyecto, pero sí sabe traducir un diccionario.

| Qué se pierde | Qué se recupera |
|---------------|-----------------|
| Los **métodos**: el JSON guarda solo los datos | Vuelven al llamar al constructor |
| La **clase** de origen: el JSON no la guarda | La fábrica la reconstruye leyendo el dato `tipo` |

### Salida esperada

```json
{
    "cliente_id": "C002",
    "tipo": "CREDITO",
    "monto": 500000.0,
    "impacto": 10000.0
}
```

> **Aviso:** `json.dumps()` **no** devuelve un diccionario, devuelve un `str`; y `json.loads()`
> **no** devuelve un objeto, devuelve un diccionario. El último tramo hasta el objeto siempre es
> manual.

## Verificación del viaje completo

La Etapa 4 de `main.py` es la que demuestra que la integración funciona: reconstruye los objetos
desde el archivo JSON y compara el monto total con el de la carga original.

```text
  Objetos antes de serializar   : 38
  Objetos reconstruidos del JSON: 38  (0 descartados)
  Monto original                : $18,557,551.25
  Monto recuperado              : $18,557,551.25
  Integridad de los datos       : VERIFICADA
  Clase recuperada del primero  : TransaccionDebito
```

Que la última línea diga `TransaccionDebito` y no `TransaccionBase` es la prueba de que la fábrica
recuperó la clase especializada a partir del texto `"DEBITO"` guardado en el JSON.

## Pruebas automáticas

```bash
python3 -m unittest discover -s pruebas -t .
```

```text
Ran 16 tests in 0.028s

OK
```

| Grupo | Qué verifica |
|-------|--------------|
| `PruebaEncapsulamiento` | El *setter* rechaza montos negativos y no numéricos, también en asignaciones posteriores |
| `PruebaPolimorfismo` | Las cuatro clases calculan impactos distintos; la base no define fórmula |
| `PruebaFabrica` | Construye la clase correcta, rechaza tipos desconocidos y admite tipos nuevos sin modificarse |
| `PruebaToleranciaAFallos` | Carga 38 registros y descarta 12; un archivo inexistente detiene el proceso |
| `PruebaSerializacion` | El monto sobrevive al viaje, la clase se recupera y los JSON mal formados se traducen a `ValueError` |

> **Nota:** el enunciado no pide pruebas. Están porque son la forma profesional de demostrar que lo
> que el informe afirma es verificable, y no depende de que alguien lea la salida en pantalla.

## Control de versiones

El repositorio se construyó con *commits* pequeños y mensajes que explican **por qué** cambió cada
cosa, no solo qué archivo se tocó.

| Rama | Para qué |
|------|----------|
| `main` | Versión estable del sistema |
| `feature/pruebas-de-integracion` | Batería de pruebas, integrada a `main` mediante Pull Request |

### Historial de commits

| # | Commit | Qué incorpora |
|---|--------|---------------|
| 1 | Inicializa el repositorio de la Estación 2 con su `.gitignore` | Punto de partida |
| 2 | Agrega el modelo de dominio con los tres pilares de la POO | `modelo.py` · Semana 3 |
| 3 | Reemplaza la cadena `if/elif` de la fábrica por un registro de tipos | `fabrica.py` · OCP |
| 4 | Incorpora los archivos de datos de prueba de la Semana 4 | `datos/` |
| 5 | Agrega la carga tolerante a fallos con registro de auditoría | `cargador.py` · Semana 4 |
| 6 | Agrega la serialización JSON de ida y vuelta | `serializador.py` · Semana 4 |
| 7 | Separa la presentación de los resultados en el módulo de reportes | `reportes.py` · SRP |
| 8 | Agrega el punto de entrada que integra las tres semanas | `main.py` |
| 9 | Agrega `eliminar_tipo()` como operación simétrica del registro | *rama* |
| 10 | Agrega la batería de pruebas automáticas del sistema | *rama* · `pruebas/` |
| 11 | Agrega el README con la documentación completa del sistema | `README.md` |
| 12 | Cierra los destinos del log antes de reemplazarlos | Corrección detectada por las pruebas |
| 13 | Integra la corrección del cierre de handlers desde `main` | *rama* |
| 14 | Agrega el informe técnico en PDF con normas APA | `docs/` |
| 15 | Versiona las salidas que genera el programa como evidencia | `salidas/` |

### Los repositorios del curso

El proyecto se ha trabajado con un repositorio independiente por actividad, todos públicos en
[github.com/DavisZulu](https://github.com/DavisZulu):

| Entrega | Repositorio | Entrega | Repositorio |
|---|---|---|---|
| Semana 1 · Act. 1 | `Semana_1_Act_1` | Quiz Semana 3 | `QUIZ-SEMANA-3` |
| Semana 1 · Act. 2 | `Semana_1_Act_2` | **Estación 1** | `Estacion_1` |
| Semana 2 · Act. 1 | `Semana_2_Act_1` | Semana 4 · Act. 1 | `Semana_4_Act_1` |
| Quiz Semana 2 | `QUIZ-SEMANA-2` | Semana 4 · Act. 2 | `Semana_4_Act_2` |
| Semana 3 · Act. 1 | `Semana_3_Act_1` | Semana 5 · Act. 1 | `Semana_5_Act_1` |
| Semana 3 · Act. 2 | `Semana_3_Act_2` | **Estación 2** | `Estacion_2` |

```bash
git checkout -b feature/pruebas-de-integracion   # se aísla el trabajo
git add . && git commit -m "..."                 # se guarda el avance
git push -u origin feature/pruebas-de-integracion # se sube la rama
# Pull Request en GitHub, revisión y merge a main
```

## Resultados verificados

| Indicador | Resultado |
|-----------|-----------|
| Registros del archivo de prueba | 50 |
| Transacciones válidas procesadas | 38 |
| Registros descartados | 12 (8 `ValueError`, 4 `TypeError`) |
| Monto total acumulado | $18.557.551,25 |
| Impacto total calculado | $456.418,00 |
| Registros serializados a JSON | 38 |
| Objetos reconstruidos desde JSON | 38 (0 descartados) |
| Integridad de los datos | Verificada |
| Pruebas automáticas | 16, todas superadas |

## Conclusión

La entrega demuestra las cuatro competencias que la estación evalúa. La **arquitectura de software**
queda en un modelo donde la validación ocurre dentro del objeto, de modo que el resto del programa
no puede crear una transacción mal formada. La **ingeniería de confiabilidad** se comprueba sobre un
archivo que falla en 12 de 50 registros y aun así se procesa completo, dejando rastro auditable de
cada descarte. La **interoperabilidad** se verifica con un viaje de ida y vuelta a JSON que conserva
el monto al centavo y recupera la clase de origen. Y la **cultura de colaboración** queda en el
historial del repositorio: un avance por *commit*, una rama por funcionalidad y la integración
hecha mediante Pull Request.
