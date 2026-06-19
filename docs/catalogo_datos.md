# Catálogo de datos - Plataforma de Interoperabilidad CECAR

## 1. Entidad: Estudiante

| Atributo | Tipo | Longitud | Descripción | Valores permitidos | Regla de validación |
|---|---:|---:|---|---|---|
| codigo | VARCHAR | 20 | Código único del estudiante | Alfanumérico | Obligatorio, único, máximo 20 caracteres |
| nombre | VARCHAR | 120 | Nombre completo del estudiante | Texto | Obligatorio |
| correo | VARCHAR | 120 | Correo institucional | usuario@cecar.edu.co | Obligatorio, formato institucional válido, único |
| programa_codigo | VARCHAR | 20 | Código del programa académico | SIS, DER, PSI, ADM | Debe existir en la tabla programas |
| estado | VARCHAR | 20 | Estado del estudiante | ACTIVO, INACTIVO | Debe pertenecer a valores permitidos |

## 2. Entidad: Programa

| Atributo | Tipo | Longitud | Descripción | Valores permitidos | Regla de validación |
|---|---:|---:|---|---|---|
| codigo | VARCHAR | 20 | Código único del programa | SIS, DER, PSI, ADM | Obligatorio y único |
| nombre | VARCHAR | 120 | Nombre del programa académico | Texto | Obligatorio |
| estado | VARCHAR | 20 | Estado del programa | ACTIVO, INACTIVO | Solo se aceptan programas activos |

## 3. Entidad: Asignatura

| Atributo | Tipo | Longitud | Descripción | Valores permitidos | Regla de validación |
|---|---:|---:|---|---|---|
| nombre | VARCHAR | 120 | Nombre de la asignatura relacionada con la solicitud | Texto | Obligatorio |
| programa_codigo | VARCHAR | 20 | Programa al que pertenece la asignatura | SIS, DER, PSI, ADM | Debe estar asociado a un programa existente |

## 4. Entidad: Solicitud

| Atributo | Tipo | Longitud | Descripción | Valores permitidos | Regla de validación |
|---|---:|---:|---|---|---|
| id | SERIAL | N/A | Identificador interno | Numérico | Generado automáticamente |
| codigo_estudiante | VARCHAR | 20 | Código del estudiante solicitante | Alfanumérico | Obligatorio |
| programa_codigo | VARCHAR | 20 | Código del programa del estudiante | SIS, DER, PSI, ADM | Debe existir y estar activo |
| asignatura | VARCHAR | 120 | Asignatura relacionada | Texto | Obligatoria |
| tipo_solicitud | VARCHAR | 50 | Tipo de solicitud académica | ASESORIA_ACADEMICA, TUTORIA, BIENESTAR, SOPORTE_ACADEMICO | Debe pertenecer a valores permitidos |
| descripcion | TEXT | N/A | Descripción del caso | Texto | Opcional |
| estado | VARCHAR | 30 | Estado de la solicitud | RECIBIDA, EN_PROCESO, ASIGNADA, CERRADA, CANCELADA | Debe pertenecer a valores permitidos |
| fecha_solicitud | DATE | 10 | Fecha de creación de la solicitud | AAAA-MM-DD | Obligatoria, formato válido, no futura |

## 5. Entidad: Asesoría

| Atributo | Tipo | Longitud | Descripción | Valores permitidos | Regla de validación |
|---|---:|---:|---|---|---|
| id | SERIAL | N/A | Identificador interno de la asesoría | Numérico | Generado automáticamente |
| solicitud_id | INTEGER | N/A | Solicitud asociada | ID existente | Debe existir en solicitudes |
| tutor_id | INTEGER | N/A | Tutor asignado | ID existente | Debe existir en tutores |
| fecha_asesoria | DATE | 10 | Fecha programada | AAAA-MM-DD | Debe ser válida |
| estado | VARCHAR | 30 | Estado de la asesoría | PENDIENTE, REALIZADA, CANCELADA | Debe pertenecer a valores permitidos |

## 6. Entidad: Tutor

| Atributo | Tipo | Longitud | Descripción | Valores permitidos | Regla de validación |
|---|---:|---:|---|---|---|
| codigo | VARCHAR | 20 | Código único del tutor | Alfanumérico | Obligatorio y único |
| nombre | VARCHAR | 120 | Nombre completo del tutor | Texto | Obligatorio |
| correo | VARCHAR | 120 | Correo institucional del tutor | usuario@cecar.edu.co | Obligatorio, formato institucional |
| programa_codigo | VARCHAR | 20 | Programa al que apoya | SIS, DER, PSI, ADM | Debe existir en programas |
| estado | VARCHAR | 20 | Estado del tutor | ACTIVO, INACTIVO | Solo se asignan tutores activos |
