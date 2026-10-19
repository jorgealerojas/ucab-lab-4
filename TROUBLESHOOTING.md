# Solución de problemas

## `make test` falla

No despliegues. Primero consulta qué archivos cambiaron. La salida vacía significa que no hay modificaciones:

```bash
git status --short
```

Después muestra el contenido exacto de los cambios. Este comando tampoco modifica archivos:

```bash
git diff
```

Finalmente ejecuta directamente todas las pruebas para obtener el nombre y detalle del caso que falla:

```bash
python3 -m unittest discover -s tests -v
```

Si el repositorio falla sin modificaciones, conserva la salida completa y detén el despliegue.

## El script dice que la región no es `us-east-2`

Configura la variable que usan los scripts:

```bash
export AWS_REGION=us-east-2
```

Configura también la variable compatible con otros comandos de AWS CLI:

```bash
export AWS_DEFAULT_REGION=us-east-2
```

Ambas asignaciones normalmente no imprimen salida. Confirma después que la consola también muestre Ohio.

## Ya existe `.ucab-lab-4-stack`

No crees otro stack. Ejecuta `./scripts/doctor.sh` para revisar el laboratorio registrado. Si el stack ya fue eliminado manualmente, confirma primero su ausencia en CloudFormation. Después, el siguiente comando elimina únicamente el archivo local que guardaba el identificador:

```bash
rm .ucab-lab-4-stack
```

## CloudFormation termina en `ROLLBACK_COMPLETE`

Abra **CloudFormation → stack → Events** y localice el primer `CREATE_FAILED`. Causas habituales:

- Falta de permisos IAM/VPC/EC2.
- Cuota de EC2 agotada.
- Tipo de instancia sin capacidad temporal.
- Restricción de la cuenta sobre buckets S3 o roles.
- Fallo de bootstrap antes de la señal de espera.

No crees stacks repetidos. Conserva el primer evento `CREATE_FAILED` y elimina el stack fallido desde CloudFormation después de registrar la causa.

## El bootstrap expira

Revise desde EC2 la captura de consola o, si SSM está Online, ejecute un comando para leer:

```text
/var/log/ucab-lab-4-bootstrap.log
```

Las causas comunes son falta de salida a Internet, instalación de `boto3` bloqueada o imposibilidad de descargar el artefacto temporal.

## `doctor.sh` dice que SSM está Offline

Espere un minuto y repita. Si continúa:

1. Confirme que la instancia está `Running` y sus checks aprobaron.
2. Revise la ruta a Internet y el perfil IAM.
3. No abra SSH ni agregue una regla de entrada.

## Un trabajo aparece `1/2`

- Después de `pause-iaas.sh`, es el resultado esperado.
- En la línea base, espere 10 segundos y repita `compare-results.sh`; el primer sondeo de Lambda puede tardar más que las invocaciones posteriores.
- Compruebe `queue-status.sh` y `show-iaas-logs.sh`.
- Confirme que el worker esté activo con `resume-iaas.sh`.

No reenvíe lotes repetidamente: dificultaría asociar evidencia y resultados.

## Los contadores de SQS parecen contradictorios

Son aproximados y eventualmente consistentes. Use los resultados de DynamoDB para comprobar los dos carriles y trate SQS como evidencia de backlog, no como contador transaccional exacto.

## La API devuelve `403`

La ruta requiere `execute-api:Invoke` y firma SigV4. Usa `query-data-product.py`, no `curl` sin firma. Si el script también falla, la identidad activa puede carecer del permiso `execute-api:Invoke`. Conserva el mensaje `403`; desactivar la autorización no es una solución válida.

## La API devuelve `404`

El `job_id` todavía no tiene resultados o fue escrito incorrectamente. El siguiente comando muestra el primer identificador del último lote sin modificarlo:

```bash
head -n 1 .ucab-lab-4-last-jobs
```

## `cleanup-lab.sh` falla

Abre los eventos de eliminación del stack. No borres la VPC, roles o colas por separado. Si CloudFormation indica una dependencia externa, registra el recurso exacto y el motivo. La limpieza solo se considera completa cuando `stack-delete-complete` termina correctamente.
