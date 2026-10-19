# Guía del laboratorio: una carga, dos modelos

**Unidad:** IV — Modelos de servicios

**Duración:** 1 h 45 min (105 minutos)

**Modalidad:** individual

**Región obligatoria:** US East (Ohio), `us-east-2`

## Reto

Un sistema universitario recibe trabajos cortos y variables. Se debe decidir entre mantener un proceso permanente en una máquina virtual o delegar su ejecución a un servicio activado por eventos. Implementarás ambos caminos, enviarás exactamente los mismos datos y provocarás una interrupción controlada.

La pregunta central no es cuál tecnología es más moderna, sino qué responsabilidad conviene conservar y cuál conviene delegar.

```text
Generador ─┬─> cola IaaS ─> servicio Python en EC2 ─┐
           └─> cola FaaS ─> función Lambda ─────────┼─> tabla de resultados
                                                    │
Cliente firmado ─> API de producto de datos ────────┘
```

## Resultados de aprendizaje

Al finalizar podrás:

1. Comparar IaaS y FaaS con evidencia de una misma carga.
2. Explicar quién administra sistema operativo, runtime, proceso, código, IAM y datos.
3. Relacionar una interrupción con la carga operativa de cada modelo.
4. Distinguir una base de datos cloud de un producto de datos.
5. Evaluar PaaS como alternativa a una implementación IaaS o FaaS.
6. Reconocer que delegar infraestructura no elimina responsabilidades.

## Reglas de operación

- Usa únicamente `us-east-2`.
- Crea un solo stack mediante el script entregado.
- Conserva el tipo de instancia y el tamaño indicado de los lotes.
- Mantén sin cambios los puertos y roles IAM definidos por la práctica.
- Usa solamente datos ficticios.
- Envía como máximo 20 trabajos por lote.
- Elimina el stack completo al finalizar, en lugar de borrar sus recursos por separado.
- Mantén fuera de las evidencias credenciales, tokens, cookies y datos sensibles.

## Evidencias

Toma una captura por hito y acompáñala con una explicación propia de dos o tres frases. No es necesario capturar cada comando.

1. Diagnóstico aprobado.
2. Lote base con dos resultados por trabajo.
3. Worker IaaS detenido e instancia todavía activa.
4. Backlog del carril IaaS mientras FaaS completa su trabajo.
5. Recuperación del carril IaaS.
6. Respuesta del producto de datos y limpieza final.

Puedes usar [evidence/evidence-template.md](evidence/evidence-template.md) como lista de control.

## 0–8 min — Formular una hipótesis

Antes de desplegar, completa una primera hipótesis:

| Capa | EC2/IaaS | Lambda/FaaS |
|---|---|---|
| Sistema operativo | | |
| Runtime Python | | |
| Código | | |
| Escalado de ejecución | | |
| Datos e IAM | | |

Escribe quién crees que administra cada capa: tú o AWS. No corrijas todavía la tabla; volverás a ella después de observar ambos carriles.

## 8–20 min — Preparar y desplegar el entorno

Abre AWS CloudShell desde la consola ubicada en **US East (Ohio)**.

### 1. Confirmar la región

El siguiente comando muestra la región configurada para AWS CLI. Se comprueba antes de crear recursos para evitar que queden distribuidos entre regiones distintas.

```bash
aws configure get region
```

La salida esperada es `us-east-2`. Si aparece otra región, detente y revisa la región de CloudShell antes de continuar.

### 2. Descargar el repositorio

`git clone` crea en CloudShell una copia de los archivos, scripts, pruebas y plantilla de infraestructura.

```bash
git clone https://github.com/jorgealerojas/ucab-lab-4.git
```

La salida debe comenzar con `Cloning into 'ucab-lab-4'`. El comando crea un directorio nuevo; todavía no crea recursos en AWS.

### 3. Entrar en el directorio

`cd` cambia el directorio activo para que los comandos siguientes encuentren los archivos del laboratorio.

```bash
cd ucab-lab-4
```

Si funciona, no imprime texto. El prompt de CloudShell debe terminar en `ucab-lab-4`.

### 4. Ejecutar las pruebas locales

Este comando valida la lógica de negocio y los adaptadores antes de gastar créditos en infraestructura.

```bash
make test
```

La salida esperada termina con `Ran 21 tests` y `OK`. No despliegues si alguna prueba muestra `FAIL` o `ERROR`.

### 5. Crear el laboratorio

El script empaqueta el código, crea artefactos temporales y solicita a CloudFormation todos los recursos de la arquitectura.

```bash
./scripts/deploy-lab.sh
```

Primero verás un identificador con formato `ucab-lab-4-...`. Anótalo: distingue tu laboratorio de cualquier otro recurso. Después aparecerán mensajes de empaquetado y espera. La creación suele tardar varios minutos y termina con:

```text
LABORATORIO LISTO: ucab-lab-4-...
```

Mientras el comando trabaja puedes abrir **CloudFormation → Stacks → Events** para observar la creación. No continúes hasta recibir `LABORATORIO LISTO`.

## 20–32 min — Diagnosticar e inspeccionar

### 1. Comprobar los recursos

El diagnóstico consulta CloudFormation, Systems Manager, EC2, Lambda, DynamoDB y API Gateway. Su finalidad es detectar un entorno incompleto antes del experimento.

```bash
./scripts/doctor.sh
```

Debe mostrar varias líneas que comienzan con `OK` y terminar con `Entorno listo`. También debe informar `Python 3.12` para el worker IaaS.

### 2. Leer la lógica compartida

Este comando muestra el procesador que valida el trabajo y calcula el resultado. Es el mismo código de negocio utilizado por ambos carriles.

```bash
sed -n '1,240p' app/common/processor.py
```

Busca las funciones `parse_job`, `process_job` y `result_to_item`. La salida es código fuente; no ejecuta ni modifica nada.

### 3. Leer el adaptador IaaS

Este archivo contiene el ciclo permanente que consulta SQS, escribe en DynamoDB y elimina un mensaje solamente después de procesarlo correctamente.

```bash
sed -n '1,220p' app/iaas/worker.py
```

Busca `poll_once` y `process_message`. Observa que alguien debe mantener ese proceso ejecutándose en EC2.

### 4. Leer el adaptador FaaS

Este archivo contiene el handler invocado por Lambda cuando el mapeo de eventos obtiene mensajes de SQS.

```bash
sed -n '1,180p' app/faas/lambda_function.py
```

Busca `lambda_handler` y `batchItemFailures`. Lambda controla la invocación, pero el código debe indicar cuáles mensajes fallaron.

Antes de avanzar, responde: ¿por qué compartir `process_job` hace más justa la comparación entre IaaS y FaaS?

## 32–47 min — Establecer la línea base

### 1. Enviar seis trabajos

El generador crea seis mensajes ficticios y envía una copia idéntica a la cola IaaS y otra a la cola FaaS. Así se comparan modelos y no algoritmos diferentes.

```bash
./scripts/send-jobs.sh 6
```

La salida enumera seis identificadores `job-...` y confirma dónde se guardó la lista. Cada identificador debe aparecer una vez.

### 2. Dar tiempo a los consumidores

`sleep` pausa CloudShell durante 15 segundos. No modifica recursos; permite que EC2 y Lambda reciban los mensajes.

```bash
sleep 15
```

El comando no imprime salida. Cuando el prompt reaparezca, continúa.

### 3. Comparar los resultados

Este script consulta DynamoDB de forma consistente y cuenta cuántos modelos produjeron resultado para cada `job_id`.

```bash
./scripts/compare-results.sh
```

Cada fila debe terminar mostrando `faas iaas` y `2/2`. El primer sondeo de una cola nueva puede tardar algunos segundos; si aparece `1/2`, espera diez segundos y ejecuta nuevamente solo este comando.

### 4. Consultar las colas

Este comando muestra mensajes disponibles y mensajes temporalmente en procesamiento en cada cola.

```bash
./scripts/queue-status.sh
```

Después de completar la línea base, ambas colas deberían aproximarse a cero. SQS publica contadores aproximados, por lo que pueden tardar en reflejar el último cambio.

## 47–62 min — Provocar una interrupción controlada

### 1. Detener solamente la aplicación IaaS

El script usa Systems Manager para detener el servicio `systemd` del worker. La instancia EC2 permanece encendida.

```bash
./scripts/pause-iaas.sh
```

La salida esperada contiene `inactive` y confirma que el worker se detuvo. Esta diferencia es importante: infraestructura encendida no equivale a aplicación saludable.

### 2. Enviar un nuevo lote

Se crean cinco trabajos nuevos y se copian a los dos carriles mientras IaaS permanece detenido.

```bash
./scripts/send-jobs.sh 5
```

La salida debe enumerar cinco identificadores distintos de los usados en la línea base.

### 3. Esperar el procesamiento FaaS

La pausa permite que Lambda procese su copia de los mensajes mientras el worker IaaS permanece detenido.

```bash
sleep 15
```

El comando no imprime salida.

### 4. Observar la diferencia

El comparador permite comprobar qué carril terminó cada trabajo.

```bash
./scripts/compare-results.sh
```

El resultado esperado es `faas` y `1/2` para cada trabajo: existe el resultado FaaS, pero falta el resultado IaaS.

### 5. Confirmar el backlog

La consulta a SQS permite relacionar el resultado faltante con mensajes que todavía esperan un consumidor.

```bash
./scripts/queue-status.sh
```

La cola IaaS debe mostrar aproximadamente cinco mensajes disponibles y la cola FaaS aproximadamente cero. Esta es la evidencia de que el proceso administrado en EC2 dejó de consumir trabajo.

## 62–75 min — Restaurar y observar la recuperación

### 1. Iniciar nuevamente el worker

El script vuelve a iniciar el servicio `systemd`. No crea otra instancia ni reenvía mensajes: el worker consume el backlog que SQS conservó.

```bash
./scripts/resume-iaas.sh
```

La salida esperada contiene `active`.

### 2. Esperar que se drene la cola

Esta pausa deja que el worker recupere los mensajes que quedaron pendientes.

```bash
sleep 15
```

No se espera salida durante la pausa.

### 3. Confirmar los dos resultados

El comparador consulta nuevamente el mismo lote, sin reenviarlo.

```bash
./scripts/compare-results.sh
```

Todas las filas deben cambiar a `faas iaas` y `2/2`. Esto demuestra recuperación del proceso, no alta disponibilidad de toda la arquitectura.

### 4. Leer los logs del worker

El script usa Systems Manager para ejecutar `journalctl` dentro de EC2 sin abrir SSH.

```bash
./scripts/show-iaas-logs.sh
```

La salida debe incluir el inicio, la detención, el reinicio y líneas `processed job_id=...`. Estos eventos muestran tareas operativas que deben resolverse en IaaS.

En Lambda, AWS administra el proceso de ejecución. Aun así, continúas siendo responsable del código, configuración, permisos, idempotencia y datos.

## 75–90 min — Consumir el producto de datos

### 1. Recuperar un identificador

Este comando toma el primer `job_id` del último lote y lo guarda en la variable de shell `JOB_ID`.

```bash
JOB_ID=$(head -n 1 .ucab-lab-4-last-jobs)
```

La asignación no imprime texto.

### 2. Comprobar la variable

Este comando imprime el valor que acaba de guardarse, sin modificarlo.

```bash
printf '%s\n' "$JOB_ID"
```

Debe mostrar un identificador con formato `job-...`. Si está vacío, no ejecutes la consulta siguiente.

### 3. Consultar la API protegida

El cliente firma una solicitud HTTP con tus credenciales temporales de AWS. API Gateway valida la firma antes de invocar la función de lectura.

```bash
python3 scripts/query-data-product.py "$JOB_ID"
```

La respuesta JSON debe incluir `schema_version`, el mismo `job_id`, `result_count: 2` y una entrada para `faas` y otra para `iaas`.

La API es el producto de datos porque ofrece una interfaz, un contrato versionado, control de acceso y metadatos. DynamoDB es el almacenamiento interno; una tabla aislada no constituye por sí sola Data as a Service.

### 4. Ejecutar la verificación integral

El verificador espera hasta 60 segundos por resultados pendientes, valida ambos modelos y consulta la API con IAM.

```bash
./scripts/verify-lab.sh
```

La salida debe terminar con `Verificacion completa`. Si algo continúa pendiente después del límite, el script falla en lugar de informar un éxito falso.

### 5. Comparar observabilidad

En **CloudWatch → Log groups**, abre por separado:

- `/aws/lambda/<identificador>-faas-worker`;
- `/aws/lambda/<identificador>-data-api`.

Compara esos logs administrados con la salida de `journalctl` en EC2. Disponer de logs ayuda a diagnosticar, pero no equivale por sí solo a observabilidad completa.

## 90–98 min — Comparar la evidencia con una alternativa PaaS

### Objetivo de esta actividad

La parte práctica hizo observables IaaS, FaaS y Data as a Service. En esta actividad usarás esa evidencia para evaluar PaaS como una posible frontera de responsabilidad para una aplicación con runtime estándar. PaaS no se despliega: se analiza como alternativa para mantener el ejercicio dentro de los 105 minutos.

No se busca adivinar una sigla. En cada caso debes indicar:

1. qué capacidad se consumiría como servicio;
2. qué responsabilidad se delegaría;
3. qué responsabilidad permanecería contigo;
4. qué trade-off aceptarías.

### Parte A — Modelos observados

Resume una evidencia real del laboratorio:

| Modelo | Evidencia observada | Responsabilidad que conservaste |
|---|---|---|
| IaaS | Detención, reinicio y logs del servicio EC2 | |
| FaaS | Lambda consumió eventos sin operar un daemon | |
| Data as a Service | API firmada con contrato JSON versionado | |

### Parte B — Alternativa PaaS

Considera este caso:

**Caso PaaS.** Una nueva API web usa un runtime estándar, debe permanecer disponible y no necesita acceso especial al sistema operativo. Si se entregara el código a una plataforma administrada, ¿qué tareas dejarías de operar? Indica también una limitación que aceptarías frente a EC2.

Compara el caso con los dos carriles desplegados:

| Alternativa | Qué se delega | Qué se conserva | Trade-off principal |
|---|---|---|---|
| Worker en EC2 (IaaS) | | | |
| Worker en Lambda (FaaS) | | | |
| Nueva API web en PaaS | | | |

Concluye cuál de las tres alternativas elegirías para la nueva API. Tu respuesta debe relacionar los requisitos del caso con al menos una evidencia obtenida durante la interrupción y recuperación del worker IaaS.

## 98–105 min — Eliminar los recursos

### 1. Solicitar la limpieza

El script lee el identificador guardado localmente, valida su formato y pide a CloudFormation eliminar exactamente ese stack.

```bash
./scripts/cleanup-lab.sh
```

La eliminación puede tardar varios minutos. El comando espera hasta que CloudFormation confirma que desaparecieron la instancia, volumen, red, funciones, colas, tabla, API, logs y roles.

La salida final debe ser:

```text
LIMPIEZA COMPLETA: ucab-lab-4-... ya no existe
```

### 2. Confirmar en CloudFormation

Abre **CloudFormation → Stacks** y verifica que el identificador ya no aparezca entre los stacks activos. Conserva esta confirmación como última evidencia.

## Entregable

Responde con tus palabras y relaciona las respuestas con las evidencias obtenidas:

1. ¿Qué responsabilidades aparecieron solamente en el carril IaaS?
2. ¿Por qué detener el worker no fue equivalente a detener la instancia?
3. ¿Qué responsabilidades conservaron ambos carriles?
4. ¿Qué demuestra el backlog y qué no permite concluir este experimento?
5. ¿Por qué la API es Data as a Service y DynamoDB no basta para afirmarlo?
6. ¿Cuándo elegirías IaaS aunque implique más operación?
7. ¿Qué cambiaría al trasladar la aplicación a un PaaS?
8. Para la nueva API del caso, ¿qué responsabilidad delegaría PaaS y qué limitación aceptarías frente a EC2?

Mantén fuera del entregable credenciales, identificadores de cuenta completos y datos personales.
