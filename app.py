import json
import os
import re
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Tuple

import psycopg2
import psycopg2.extras
import requests
from flask import Flask, Response, jsonify, request
from lxml import etree

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
MOCK_SYSTEMS_URL = os.getenv("MOCK_SYSTEMS_URL", "").rstrip("/")

BASE_DIR = Path(__file__).resolve().parent
XSD_PATH = BASE_DIR / "xsd" / "solicitud.xsd"
SCHEMA_PATH = BASE_DIR / "schema.sql"

EMAIL_INSTITUCIONAL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@cecar\.edu\.co$")
ESTADOS_PERMITIDOS = {"RECIBIDA", "EN_PROCESO", "ASIGNADA", "CERRADA", "CANCELADA"}
TIPOS_SOLICITUD_PERMITIDOS = {
    "ASESORIA_ACADEMICA",
    "TUTORIA",
    "BIENESTAR",
    "SOPORTE_ACADEMICO",
}


def db_configured() -> bool:
    return bool(DATABASE_URL)


def get_conn():
    if not db_configured():
        raise RuntimeError("DATABASE_URL no está configurada. Agrega la variable de entorno en Render.")
    return psycopg2.connect(DATABASE_URL)


def run_query(query: str, params: tuple = (), fetch: bool = False):
    conn = get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
    finally:
        conn.close()


def init_database():
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    finally:
        conn.close()


def to_json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def rows_to_json(rows):
    return [{k: to_json_safe(v) for k, v in dict(row).items()} for row in rows]


def registrar_evento(tipo_evento: str, descripcion: str, payload: Dict[str, Any] | None = None):
    payload = payload or {}
    try:
        run_query(
            """
            INSERT INTO eventos_middleware (tipo_evento, descripcion, payload)
            VALUES (%s, %s, %s)
            """,
            (tipo_evento, descripcion, psycopg2.extras.Json(payload)),
        )
    except Exception as exc:
        app.logger.warning("No se pudo registrar evento: %s", exc)


def guardar_errores_calidad(errores: List[Dict[str, str]], payload: Dict[str, Any]):
    for error in errores:
        try:
            run_query(
                """
                INSERT INTO errores_calidad (campo, error, payload)
                VALUES (%s, %s, %s)
                """,
                (error.get("campo"), error.get("mensaje"), psycopg2.extras.Json(payload)),
            )
        except Exception as exc:
            app.logger.warning("No se pudo guardar error de calidad: %s", exc)


def normalizar_solicitud(data: Dict[str, Any]) -> Dict[str, Any]:
    """Acepta datos en español o nombres alternos y devuelve el formato oficial."""
    return {
        "codigo_estudiante": str(data.get("codigo_estudiante") or data.get("student_code") or "").strip(),
        "nombre_estudiante": str(data.get("nombre_estudiante") or data.get("student_name") or "").strip(),
        "correo": str(data.get("correo") or data.get("email") or "").strip().lower(),
        "programa_codigo": str(data.get("programa_codigo") or data.get("program_code") or "").strip().upper(),
        "asignatura": str(data.get("asignatura") or data.get("subject") or "").strip(),
        "tipo_solicitud": str(data.get("tipo_solicitud") or data.get("request_type") or "ASESORIA_ACADEMICA").strip().upper(),
        "descripcion": str(data.get("descripcion") or data.get("description") or "").strip(),
        "estado": str(data.get("estado") or data.get("status") or "RECIBIDA").strip().upper(),
        "fecha_solicitud": str(data.get("fecha_solicitud") or data.get("request_date") or "").strip(),
    }


def existe_programa(programa_codigo: str) -> bool:
    rows = run_query(
        "SELECT 1 FROM programas WHERE codigo = %s AND estado = 'ACTIVO' LIMIT 1",
        (programa_codigo,),
        fetch=True,
    )
    return bool(rows)


def estudiante_existente(codigo_estudiante: str):
    rows = run_query(
        "SELECT codigo, programa_codigo FROM estudiantes WHERE codigo = %s LIMIT 1",
        (codigo_estudiante,),
        fetch=True,
    )
    return rows[0] if rows else None


def solicitud_duplicada(data: Dict[str, Any]) -> bool:
    rows = run_query(
        """
        SELECT 1
        FROM solicitudes
        WHERE codigo_estudiante = %s
          AND programa_codigo = %s
          AND LOWER(asignatura) = LOWER(%s)
          AND tipo_solicitud = %s
          AND fecha_solicitud = %s
        LIMIT 1
        """,
        (
            data["codigo_estudiante"],
            data["programa_codigo"],
            data["asignatura"],
            data["tipo_solicitud"],
            data["fecha_solicitud"],
        ),
        fetch=True,
    )
    return bool(rows)


def validar_calidad(data: Dict[str, Any]) -> List[Dict[str, str]]:
    errores: List[Dict[str, str]] = []

    campos_obligatorios = [
        "codigo_estudiante",
        "nombre_estudiante",
        "correo",
        "programa_codigo",
        "asignatura",
        "tipo_solicitud",
        "fecha_solicitud",
    ]
    for campo in campos_obligatorios:
        if not data.get(campo):
            errores.append({"campo": campo, "mensaje": f"{campo} es obligatorio."})

    if data.get("codigo_estudiante") and len(data["codigo_estudiante"]) > 20:
        errores.append({"campo": "codigo_estudiante", "mensaje": "El código no puede superar 20 caracteres."})

    if data.get("correo") and not EMAIL_INSTITUCIONAL_RE.match(data["correo"]):
        errores.append({"campo": "correo", "mensaje": "El correo debe ser institucional: usuario@cecar.edu.co."})

    if data.get("tipo_solicitud") and data["tipo_solicitud"] not in TIPOS_SOLICITUD_PERMITIDOS:
        errores.append({
            "campo": "tipo_solicitud",
            "mensaje": f"Tipo no permitido. Valores válidos: {sorted(TIPOS_SOLICITUD_PERMITIDOS)}.",
        })

    if data.get("estado") and data["estado"] not in ESTADOS_PERMITIDOS:
        errores.append({
            "campo": "estado",
            "mensaje": f"Estado no permitido. Valores válidos: {sorted(ESTADOS_PERMITIDOS)}.",
        })

    if data.get("fecha_solicitud"):
        try:
            fecha = datetime.strptime(data["fecha_solicitud"], "%Y-%m-%d").date()
            if fecha > date.today():
                errores.append({"campo": "fecha_solicitud", "mensaje": "La fecha de solicitud no puede ser futura."})
        except ValueError:
            errores.append({"campo": "fecha_solicitud", "mensaje": "La fecha debe tener formato AAAA-MM-DD."})

    # Validaciones contra la base solo se ejecutan si los datos mínimos existen.
    if data.get("programa_codigo"):
        try:
            if not existe_programa(data["programa_codigo"]):
                errores.append({"campo": "programa_codigo", "mensaje": "El programa académico no existe o no está activo."})
        except Exception as exc:
            errores.append({"campo": "base_datos", "mensaje": f"No fue posible validar programa en Neon: {exc}"})

    if data.get("codigo_estudiante") and data.get("programa_codigo"):
        try:
            estudiante = estudiante_existente(data["codigo_estudiante"])
            if estudiante and estudiante["programa_codigo"] != data["programa_codigo"]:
                errores.append({
                    "campo": "programa_codigo",
                    "mensaje": "Integridad inválida: el estudiante ya existe con otro programa.",
                })
        except Exception as exc:
            errores.append({"campo": "base_datos", "mensaje": f"No fue posible validar integridad estudiante-programa: {exc}"})

    if all(data.get(campo) for campo in ["codigo_estudiante", "programa_codigo", "asignatura", "tipo_solicitud", "fecha_solicitud"]):
        try:
            if solicitud_duplicada(data):
                errores.append({"campo": "duplicidad", "mensaje": "Ya existe una solicitud igual para el estudiante en la misma fecha."})
        except Exception as exc:
            errores.append({"campo": "base_datos", "mensaje": f"No fue posible validar duplicados: {exc}"})

    return errores


def guardar_solicitud(data: Dict[str, Any]) -> int:
    conn = get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO estudiantes (codigo, nombre, correo, programa_codigo, estado)
                    VALUES (%s, %s, %s, %s, 'ACTIVO')
                    ON CONFLICT (codigo) DO UPDATE SET
                        nombre = EXCLUDED.nombre,
                        correo = EXCLUDED.correo,
                        programa_codigo = EXCLUDED.programa_codigo
                    """,
                    (
                        data["codigo_estudiante"],
                        data["nombre_estudiante"],
                        data["correo"],
                        data["programa_codigo"],
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO solicitudes
                        (codigo_estudiante, programa_codigo, asignatura, tipo_solicitud, descripcion, estado, fecha_solicitud)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        data["codigo_estudiante"],
                        data["programa_codigo"],
                        data["asignatura"],
                        data["tipo_solicitud"],
                        data["descripcion"],
                        data["estado"],
                        data["fecha_solicitud"],
                    ),
                )
                solicitud_id = cur.fetchone()["id"]
                return int(solicitud_id)
    finally:
        conn.close()


def validar_xml_con_xsd(xml_text: str) -> Tuple[bool, List[str]]:
    try:
        xml_doc = etree.fromstring(xml_text.encode("utf-8"))
    except etree.XMLSyntaxError as exc:
        return False, [f"XML mal formado: {exc}"]

    try:
        schema_doc = etree.parse(str(XSD_PATH))
        schema = etree.XMLSchema(schema_doc)
        schema.assertValid(xml_doc)
        return True, []
    except etree.DocumentInvalid as exc:
        return False, [str(exc)]
    except Exception as exc:
        return False, [f"Error validando XSD: {exc}"]


def xml_to_dict(xml_text: str) -> Dict[str, Any]:
    root = etree.fromstring(xml_text.encode("utf-8"))
    return {child.tag: child.text or "" for child in root}


def dict_to_xml(data: Dict[str, Any], root_name: str = "solicitud") -> str:
    root = etree.Element(root_name)
    orden = [
        "codigo_estudiante",
        "nombre_estudiante",
        "correo",
        "programa_codigo",
        "asignatura",
        "tipo_solicitud",
        "descripcion",
        "estado",
        "fecha_solicitud",
    ]
    for key in orden:
        element = etree.SubElement(root, key)
        element.text = str(data.get(key, ""))
    return etree.tostring(root, pretty_print=True, encoding="unicode")


def consultar_sistemas_externos(data: Dict[str, Any]) -> Dict[str, Any]:
    """Consulta sistemas simulados si MOCK_SYSTEMS_URL está configurada."""
    if not MOCK_SYSTEMS_URL:
        return {"habilitado": False, "mensaje": "MOCK_SYSTEMS_URL no configurada."}

    resultado: Dict[str, Any] = {"habilitado": True}
    timeout = 8
    codigo = data.get("codigo_estudiante")
    programa = data.get("programa_codigo")

    try:
        resp = requests.get(f"{MOCK_SYSTEMS_URL}/sistema-academico/estudiantes/{codigo}", timeout=timeout)
        resultado["sistema_academico_xml"] = resp.text
    except Exception as exc:
        resultado["sistema_academico_error"] = str(exc)

    try:
        resp = requests.get(f"{MOCK_SYSTEMS_URL}/sistema-tutorias/tutores", params={"programa": programa}, timeout=timeout)
        resultado["sistema_tutorias_json"] = resp.json()
    except Exception as exc:
        resultado["sistema_tutorias_error"] = str(exc)

    try:
        resp = requests.get(f"{MOCK_SYSTEMS_URL}/sistema-bienestar/alertas/{codigo}", timeout=timeout)
        resultado["sistema_bienestar_json"] = resp.json()
    except Exception as exc:
        resultado["sistema_bienestar_error"] = str(exc)

    try:
        resp = requests.get(f"{MOCK_SYSTEMS_URL}/sistema-gestion-estudiantil/programas/{programa}", timeout=timeout)
        resultado["sistema_gestion_estudiantil_xml"] = resp.text
    except Exception as exc:
        resultado["sistema_gestion_estudiantil_error"] = str(exc)

    return resultado


def procesar_solicitud(payload: Dict[str, Any], origen: str):
    data = normalizar_solicitud(payload)
    registrar_evento("SOLICITUD_RECIBIDA", f"Solicitud recibida por {origen}.", data)

    errores = validar_calidad(data)
    if errores:
        guardar_errores_calidad(errores, data)
        registrar_evento("SOLICITUD_RECHAZADA", "Solicitud rechazada por errores de calidad.", {"errores": errores, "payload": data})
        return jsonify({
            "ok": False,
            "mensaje": "La solicitud no pasó las reglas de calidad.",
            "errores": errores,
            "solicitud_normalizada": data,
        }), 400

    solicitud_id = guardar_solicitud(data)
    sistemas = consultar_sistemas_externos(data)
    registrar_evento("SOLICITUD_GUARDADA", "Solicitud validada, transformada y guardada en Neon.", {"solicitud_id": solicitud_id, **data})

    return jsonify({
        "ok": True,
        "mensaje": "Solicitud procesada correctamente por el middleware.",
        "solicitud_id": solicitud_id,
        "json_generado": data,
        "xml_generado": dict_to_xml(data),
        "respuestas_consolidadas": sistemas,
    }), 201


@app.route("/")
def home():
    return jsonify({
        "sistema": "Middleware de Interoperabilidad Académica - CECAR",
        "estado": "activo",
        "endpoints": [
            "GET /health",
            "POST /api/solicitudes/json",
            "POST /api/solicitudes/xml",
            "POST /api/transform/xml-to-json",
            "POST /api/transform/json-to-xml",
            "GET /api/solicitudes",
            "GET /api/errores",
            "GET /api/eventos",
            "POST /api/init-db",
        ],
    })


@app.route("/health")
def health():
    db_status = "no_configurada"
    if db_configured():
        try:
            run_query("SELECT 1", fetch=True)
            db_status = "ok"
        except Exception as exc:
            db_status = f"error: {exc}"
    return jsonify({
        "app": "ok",
        "database": db_status,
        "mock_systems_url": MOCK_SYSTEMS_URL or "no_configurada",
    })


@app.route("/api/init-db", methods=["POST", "GET"])
def api_init_db():
    init_database()
    registrar_evento("BASE_DATOS_INICIALIZADA", "Se creó/verificó el esquema de Neon.", {})
    return jsonify({"ok": True, "mensaje": "Base de datos inicializada correctamente."})


@app.route("/api/solicitudes/json", methods=["POST"])
def recibir_json():
    if not request.is_json:
        return jsonify({"ok": False, "error": "Debes enviar Content-Type: application/json"}), 400
    return procesar_solicitud(request.get_json() or {}, "JSON")


@app.route("/api/solicitudes/xml", methods=["POST"])
def recibir_xml():
    xml_text = request.data.decode("utf-8") if request.data else ""
    if not xml_text.strip():
        return jsonify({"ok": False, "error": "Debes enviar XML en el body."}), 400

    valido, errores_xsd = validar_xml_con_xsd(xml_text)
    if not valido:
        guardar_errores_calidad(
            [{"campo": "xml_xsd", "mensaje": error} for error in errores_xsd],
            {"xml": xml_text},
        )
        return jsonify({
            "ok": False,
            "mensaje": "El XML no cumple con la estructura XSD.",
            "errores": errores_xsd,
        }), 400

    data = xml_to_dict(xml_text)
    return procesar_solicitud(data, "XML")


@app.route("/api/transform/xml-to-json", methods=["POST"])
def api_xml_to_json():
    xml_text = request.data.decode("utf-8") if request.data else ""
    valido, errores_xsd = validar_xml_con_xsd(xml_text)
    if not valido:
        return jsonify({"ok": False, "errores": errores_xsd}), 400
    return jsonify({"ok": True, "json": normalizar_solicitud(xml_to_dict(xml_text))})


@app.route("/api/transform/json-to-xml", methods=["POST"])
def api_json_to_xml():
    if not request.is_json:
        return jsonify({"ok": False, "error": "Debes enviar JSON."}), 400
    data = normalizar_solicitud(request.get_json() or {})
    return Response(dict_to_xml(data), mimetype="application/xml")


@app.route("/api/solicitudes", methods=["GET"])
def listar_solicitudes():
    rows = run_query(
        """
        SELECT id, codigo_estudiante, programa_codigo, asignatura, tipo_solicitud,
               descripcion, estado, fecha_solicitud, created_at
        FROM solicitudes
        ORDER BY id DESC
        LIMIT 100
        """,
        fetch=True,
    )
    return jsonify({"ok": True, "total": len(rows), "data": rows_to_json(rows)})


@app.route("/api/errores", methods=["GET"])
def listar_errores():
    rows = run_query(
        """
        SELECT id, campo, error, payload, created_at
        FROM errores_calidad
        ORDER BY id DESC
        LIMIT 100
        """,
        fetch=True,
    )
    return jsonify({"ok": True, "total": len(rows), "data": rows_to_json(rows)})


@app.route("/api/eventos", methods=["GET"])
def listar_eventos():
    rows = run_query(
        """
        SELECT id, tipo_evento, descripcion, payload, created_at
        FROM eventos_middleware
        ORDER BY id DESC
        LIMIT 100
        """,
        fetch=True,
    )
    return jsonify({"ok": True, "total": len(rows), "data": rows_to_json(rows)})


@app.route("/api/catalogo", methods=["GET"])
def catalogo_resumen():
    return jsonify({
        "entidades": ["Estudiante", "Programa", "Asignatura", "Solicitud", "Asesoría", "Tutor"],
        "reglas_calidad": [
            "Código de estudiante obligatorio",
            "Correo institucional válido",
            "Fecha de solicitud válida",
            "Programa académico existente",
            "Detección de duplicados",
            "Integridad estudiante-programa",
            "Consistencia de estados",
        ],
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
