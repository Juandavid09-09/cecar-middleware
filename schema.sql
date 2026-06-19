CREATE TABLE IF NOT EXISTS programas (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    estado VARCHAR(20) DEFAULT 'ACTIVO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS estudiantes (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    correo VARCHAR(120) UNIQUE NOT NULL,
    programa_codigo VARCHAR(20) NOT NULL REFERENCES programas(codigo),
    estado VARCHAR(20) DEFAULT 'ACTIVO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS solicitudes (
    id SERIAL PRIMARY KEY,
    codigo_estudiante VARCHAR(20) NOT NULL,
    programa_codigo VARCHAR(20) NOT NULL REFERENCES programas(codigo),
    asignatura VARCHAR(120) NOT NULL,
    tipo_solicitud VARCHAR(50) NOT NULL,
    descripcion TEXT,
    estado VARCHAR(30) DEFAULT 'RECIBIDA',
    fecha_solicitud DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tutores (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    correo VARCHAR(120) NOT NULL,
    programa_codigo VARCHAR(20) NOT NULL REFERENCES programas(codigo),
    estado VARCHAR(20) DEFAULT 'ACTIVO'
);

CREATE TABLE IF NOT EXISTS asesorias (
    id SERIAL PRIMARY KEY,
    solicitud_id INTEGER REFERENCES solicitudes(id),
    tutor_id INTEGER REFERENCES tutores(id),
    fecha_asesoria DATE,
    estado VARCHAR(30) DEFAULT 'PENDIENTE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS eventos_middleware (
    id SERIAL PRIMARY KEY,
    tipo_evento VARCHAR(80) NOT NULL,
    descripcion TEXT,
    payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS errores_calidad (
    id SERIAL PRIMARY KEY,
    campo VARCHAR(80),
    error TEXT,
    payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO programas (codigo, nombre, estado)
VALUES
('SIS', 'Ingeniería de Sistemas', 'ACTIVO'),
('DER', 'Derecho', 'ACTIVO'),
('PSI', 'Psicología', 'ACTIVO'),
('ADM', 'Administración de Empresas', 'ACTIVO')
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO tutores (codigo, nombre, correo, programa_codigo, estado)
VALUES
('TUT-SIS-01', 'Laura Martínez', 'laura.martinez@cecar.edu.co', 'SIS', 'ACTIVO'),
('TUT-DER-01', 'Carlos Pérez', 'carlos.perez@cecar.edu.co', 'DER', 'ACTIVO'),
('TUT-PSI-01', 'María Gómez', 'maria.gomez@cecar.edu.co', 'PSI', 'ACTIVO'),
('TUT-ADM-01', 'Andrés Castro', 'andres.castro@cecar.edu.co', 'ADM', 'ACTIVO')
ON CONFLICT (codigo) DO NOTHING;
