# Documento de reglas de calidad de datos

El middleware implementa reglas de calidad antes de guardar una solicitud en Neon PostgreSQL.

## Reglas implementadas

| No. | Regla | Descripción | Acción ante error |
|---:|---|---|---|
| 1 | Código de estudiante obligatorio | Toda solicitud debe incluir `codigo_estudiante`. | Se rechaza la solicitud y se registra el error. |
| 2 | Correo institucional válido | El correo debe cumplir el formato `usuario@cecar.edu.co`. | Se rechaza la solicitud y se registra el error. |
| 3 | Fecha de solicitud válida | La fecha debe tener formato `AAAA-MM-DD` y no puede ser futura. | Se rechaza la solicitud y se registra el error. |
| 4 | Programa académico existente | El `programa_codigo` debe existir y estar activo en la tabla `programas`. | Se rechaza la solicitud y se registra el error. |
| 5 | Detección de duplicados | No puede existir otra solicitud con mismo estudiante, programa, asignatura, tipo y fecha. | Se rechaza la solicitud y se registra el error. |
| 6 | Integridad estudiante-programa | Si el estudiante ya existe, debe pertenecer al mismo programa registrado. | Se rechaza la solicitud y se registra el error. |
| 7 | Consistencia de estados | El estado debe estar dentro de los valores permitidos. | Se rechaza la solicitud y se registra el error. |

## Reporte de errores

El reporte se consulta desde:

```http
GET /api/errores
```

Ejemplo de respuesta:

```json
{
  "ok": true,
  "total": 1,
  "data": [
    {
      "id": 1,
      "campo": "correo",
      "error": "El correo debe ser institucional: usuario@cecar.edu.co.",
      "payload": {
        "codigo_estudiante": "2026003",
        "correo": "usuario@gmail.com"
      }
    }
  ]
}
```
