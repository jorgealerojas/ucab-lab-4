# Evidencia — UCAB Lab 4

**Nombre:**  
**Cédula:**  
**Sección:**  
**Fecha:**  
**Identificador del laboratorio:**

## 1. Diagnóstico

- Resultado resumido de `make test`:
- Resultado de `doctor.sh`:
- Componentes identificados:

## 2. Línea base

- Cantidad enviada:
- Resultados IaaS:
- Resultados FaaS:
- ¿Por qué la comparación usa la misma lógica y los mismos datos?

## 3. Interrupción

- Estado del servicio IaaS:
- Estado de la instancia EC2:
- Mensajes pendientes IaaS:
- Resultados observados FaaS:
- Explicación:

## 4. Recuperación

- Evidencia de backlog drenado:
- Log relevante de `journalctl`:
- Responsabilidad que hizo falta ejercer:

## 5. Producto de datos

- `job_id` consultado:
- Versión del contrato:
- Cantidad de resultados:
- ¿Por qué esto es un producto de datos y no solamente una tabla?

## 6. Modelos observados

| Modelo | Evidencia observada | Responsabilidad conservada |
|---|---|---|
| IaaS | | |
| FaaS | | |
| Data as a Service | | |

## 7. Comparación PaaS

| Alternativa | Qué se delega | Qué se conserva | Trade-off principal |
|---|---|---|---|
| Worker en EC2 (IaaS) | | | |
| Worker en Lambda (FaaS) | | | |
| Nueva API web en PaaS | | | |

- Alternativa elegida para la nueva API:
- Evidencia del experimento que respalda la decisión:

## 8. Preguntas finales

1. ¿Qué responsabilidades aparecieron solamente en IaaS?
2. ¿Qué responsabilidades conservaron ambos carriles?
3. ¿Qué demuestra el experimento y qué no permite concluir?
4. ¿Cuándo elegirías IaaS en lugar de FaaS?
5. ¿Por qué una solución real puede combinar varios modelos?
6. ¿Qué responsabilidad delegaría PaaS y qué limitación aceptarías frente a EC2?

## 9. Limpieza

- Nombre exacto del stack eliminado:
- Resultado `LIMPIEZA COMPLETA`:
- Confirmo que eliminé únicamente mi stack: [ ]
