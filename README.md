# Middleware de Interoperabilidad Académica - CECAR

Este repositorio contiene el middleware/orquestador principal del proyecto final de semestre.

## Funciones principales

- Recibe solicitudes académicas en JSON.
- Recibe solicitudes académicas en XML.
- Valida XML mediante XSD.
- Transforma XML a JSON.
- Transforma JSON a XML.
- Aplica reglas de calidad de datos.
- Registra errores de calidad.
- Guarda solicitudes en Neon PostgreSQL.
- Consulta sistemas externos simulados.
- Consolida respuestas.
- Expone una API REST.

## Estructura

```txt
.
├── app.py
├── requirements.txt
├── schema.sql
├── Procfile
├── .env.example
├── xsd/
│   └── solicitud.xsd
├── samples/
│   ├── solicitud_valida.xml
│   ├── solicitud_invalida.xml
│   └── solicitud.json
├── docs/
│   ├── arquitectura.md
│   ├── catalogo_datos.md
│   └── reglas_calidad.md
├── tests/
│   └── test_requests.http
└── simulador_colab/
    └── simulador_cecar.ipynb
```

## Variables de entorno

En local puedes crear un archivo `.env`, pero en Render debes agregarlas desde **Environment**.

```txt
DATABASE_URL=postgresql://usuario:password@host.neon.tech/cecar_db?sslmode=require
MOCK_SYSTEMS_URL=https://URL-DEL-REPO-DE-SISTEMAS-EXTERNOS.onrender.com
```

`DATABASE_URL` es la conexión de Neon PostgreSQL.
`MOCK_SYSTEMS_URL` es la URL pública del otro repositorio desplegado en Render.

## Base de datos Neon

1. Crea un proyecto en Neon llamado `cecar-interoperabilidad`.
2. Crea una base de datos llamada `cecar_db`.
3. Copia la cadena de conexión.
4. Ejecuta el archivo `schema.sql` en el SQL Editor de Neon.

También puedes inicializar la base desde el navegador cuando el servicio esté desplegado:

```txt
https://TU-MIDDLEWARE.onrender.com/api/init-db
```

## Despliegue en Render

Crea un Web Service con estos datos:

```txt
Name: cecar-middleware
Root Directory: vacío, porque este repo ya tiene app.py en la raíz
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

Agrega las variables:

```txt
DATABASE_URL=tu_url_de_neon
MOCK_SYSTEMS_URL=https://cecar-sistemas-externos.onrender.com
```

## Endpoints

```txt
GET  /
GET  /health
GET  /api/init-db
POST /api/solicitudes/json
POST /api/solicitudes/xml
POST /api/transform/xml-to-json
POST /api/transform/json-to-xml
GET  /api/solicitudes
GET  /api/errores
GET  /api/eventos
GET  /api/catalogo
```

## Prueba JSON

Endpoint:

```txt
POST https://TU-MIDDLEWARE.onrender.com/api/solicitudes/json
```

Body:

```json
{
  "codigo_estudiante": "2026001",
  "nombre_estudiante": "Mateo López García",
  "correo": "mateo.lopez@cecar.edu.co",
  "programa_codigo": "SIS",
  "asignatura": "Arquitectura de Software",
  "tipo_solicitud": "ASESORIA_ACADEMICA",
  "descripcion": "Solicito asesoría sobre integración de sistemas.",
  "estado": "RECIBIDA",
  "fecha_solicitud": "2026-06-18"
}
```

## Prueba XML

Endpoint:

```txt
POST https://TU-MIDDLEWARE.onrender.com/api/solicitudes/xml
```

Headers:

```txt
Content-Type: application/xml
```

Body:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<solicitud>
  <codigo_estudiante>2026002</codigo_estudiante>
  <nombre_estudiante>Juliana Pérez</nombre_estudiante>
  <correo>juliana.perez@cecar.edu.co</correo>
  <programa_codigo>SIS</programa_codigo>
  <asignatura>Bases de Datos</asignatura>
  <tipo_solicitud>ASESORIA_ACADEMICA</tipo_solicitud>
  <descripcion>Necesito apoyo con PostgreSQL y consultas.</descripcion>
  <estado>RECIBIDA</estado>
  <fecha_solicitud>2026-06-18</fecha_solicitud>
</solicitud>
```

## Repositorio relacionado

Este middleware se conecta con el repositorio separado:

```txt
cecar-sistemas-externos
```
