# UCAB Lab 4: una carga, dos modelos

Laboratorio de 1 hora y 45 minutos para la Unidad IV de **Computación en la Nube (INFO-02028)**. Una misma carga de trabajo se procesa mediante dos modelos: un worker IaaS en Amazon EC2 y un worker FaaS en AWS Lambda. Durante el experimento se interrumpe el worker IaaS, se observa el comportamiento de ambos carriles y se consultan los resultados mediante un producto de datos.

El repositorio contiene todo lo necesario para realizar la práctica. El procedimiento operativo, los comandos y sus salidas esperadas están únicamente en [LAB_GUIDE.md](LAB_GUIDE.md); este README describe el alcance, la arquitectura y la organización del material.

## Propósito y alcance

La práctica busca hacer observable la frontera de responsabilidad entre quien consume el servicio cloud y AWS. El estudiante utilizará evidencia de una misma carga para:

- comparar IaaS y FaaS;
- distinguir infraestructura disponible de aplicación saludable;
- reconocer las responsabilidades que permanecen aun al delegar la ejecución;
- diferenciar una base de datos administrada de un producto de datos;
- evaluar PaaS como una alternativa de diseño para una aplicación con runtime estándar.

PaaS se analiza como comparación arquitectónica, pero no se despliega. Los modelos practicados directamente son IaaS, FaaS y Data as a Service.

## Arquitectura

```text
Generador ─┬─> cola SQS IaaS ─> EC2 + systemd ─┐
           └─> cola SQS FaaS ─> Lambda ────────┼─> DynamoDB
                                                │
Cliente SigV4 ─> API Gateway ─> Lambda de API ──┘
```

Los dos carriles reciben copias idénticas de cada trabajo y comparten la misma lógica de negocio. Esto permite comparar el modelo operativo sin introducir algoritmos o datos distintos.

## Servicios y conceptos

| Servicio o componente | Función en el laboratorio | Concepto que permite observar |
|---|---|---|
| Amazon EC2 | Aloja un worker Python ejecutado como servicio `systemd` | IaaS y responsabilidad sobre runtime, proceso y recuperación |
| AWS Lambda | Ejecuta el worker activado por eventos y la API de consulta | FaaS y ejecución administrada |
| Amazon SQS | Separa productores y consumidores; conserva el backlog | Desacoplamiento, reintentos y procesamiento asíncrono |
| Amazon DynamoDB | Almacena los resultados de ambos carriles | Persistencia administrada y serverless |
| Amazon API Gateway | Publica el contrato HTTP para consultar resultados | Interfaz del producto de datos |
| AWS IAM y SigV4 | Protegen recursos y solicitudes a la API | Identidad, mínimo privilegio y responsabilidad compartida |
| AWS Systems Manager | Opera EC2 sin exponer SSH | Administración remota segura |
| Amazon CloudWatch Logs | Conserva logs de las funciones | Observabilidad administrada |
| AWS CloudFormation | Crea y elimina la arquitectura como una unidad | Infraestructura como código y limpieza reproducible |

SQS y DynamoDB son servicios administrados, pero una tabla aislada no constituye por sí sola Data as a Service. En este laboratorio, el producto de datos está formado por la API, su contrato versionado, los metadatos y el control de acceso; DynamoDB es su almacenamiento interno.

## Organización del repositorio

| Ruta | Contenido |
|---|---|
| `LAB_GUIDE.md` | Único paso a paso de la práctica: tiempos, comandos, explicaciones, salidas esperadas, evidencias y preguntas finales |
| `TROUBLESHOOTING.md` | Diagnóstico y recuperación ante errores frecuentes |
| `evidence/evidence-template.md` | Plantilla para registrar observaciones y respuestas |
| `infra/lab-stack.yaml` | Plantilla de CloudFormation con la infraestructura AWS |
| `app/common/` | Validación y procesamiento compartidos por ambos carriles |
| `app/iaas/` | Adaptador del worker permanente que se ejecuta en EC2 |
| `app/faas/` | Handler de Lambda que procesa eventos de SQS |
| `app/data_api/` | Handler que expone los resultados mediante la API |
| `scripts/` | Automatización de despliegue, diagnóstico, experimento, verificación y limpieza |
| `tests/` | Pruebas unitarias y comprobaciones de consistencia del repositorio |
| `Makefile` y `pyproject.toml` | Tareas de validación y configuración del proyecto Python |
| `.github/workflows/validate.yml` | Validación automática del repositorio |

## Recorrido del experimento

La práctica comienza con una hipótesis sobre las responsabilidades de cada modelo. Después se despliega la arquitectura, se procesa una línea base y se detiene únicamente el servicio del worker IaaS mientras la instancia continúa activa. El backlog resultante se contrasta con la ejecución FaaS, se restaura el worker y finalmente se consulta el producto de datos.

El cierre compara la evidencia de IaaS, FaaS y Data as a Service con una posible implementación PaaS. La pregunta central no es qué servicio es más moderno, sino qué responsabilidad conviene conservar, cuál delegar y qué trade-off se acepta.

## Límites de seguridad y costo

- La región de trabajo es `us-east-2`.
- La instancia no acepta tráfico entrante y se opera mediante Systems Manager.
- La API requiere credenciales AWS y firma SigV4.
- Los roles de ejecución tienen permisos acotados a sus recursos.
- Los lotes admitidos contienen como máximo 20 trabajos.
- La infraestructura se administra como un único stack de CloudFormation.
- La limpieza elimina logs, colas, tabla, volumen, roles y red creados por el laboratorio.

El consumo está deliberadamente acotado, pero no se promete costo cero. La cuenta utilizada debe disponer de créditos, permisos y cuota para los servicios enumerados.

## Cómo realizar la práctica

Abre [LAB_GUIDE.md](LAB_GUIDE.md) y sigue sus secciones en orden. Allí se explica qué hace cada comando, por qué se ejecuta y qué resultado debe producir. Si una salida no coincide con la esperada, consulta [TROUBLESHOOTING.md](TROUBLESHOOTING.md) antes de continuar.
