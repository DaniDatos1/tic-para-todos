# TIC para Todos

Plataforma web progresiva (PWA) de alfabetización digital para adultos y adultos mayores de
sectores vulnerables de Valledupar, Cesar. Prototipo funcional del proyecto de grado
*Desarrollo de una plataforma web para el fortalecimiento de competencias TIC en comunidades
vulnerables de Valledupar, Cesar* (Ingeniería de Sistemas, UNAD, curso 202016907).

**Autores:** Daniel Andrés Mercado Trillos y Luis Del Prado Orozco.
**Metodología de desarrollo:** Scrum.  **Nivel de madurez objetivo:** TRL 5.

## Funcionalidades

| Requerimiento | Funcionalidad |
|---|---|
| RF01, RF13 | Entrada como invitado con un solo botón, sin registro ni datos personales. Quien quiera conservar su avance en otro dispositivo o recibir certificados lo guarda con nombre, celular y PIN, con consentimiento de datos (Ley 1581 de 2012) |
| RF02 | El invitado vuelve a entrar desde su dispositivo con el mismo avance. Las cuentas guardadas, los facilitadores y los administradores entran con celular y PIN; el facilitador restablece el PIN olvidado |
| RF03 | Prueba diagnóstica de 10 preguntas que recomienda el módulo inicial |
| RF04 | Rutas de aprendizaje: Alfabetización y herramientas digitales, Comunicación y productividad digital, Seguridad y ciudadanía digital, Tecnología para el empleo y el emprendimiento (20 lecciones) |
| RF05 | Lecciones con situación de la vida real, 5 pasos ilustrados con consejo, palabras clave, narración en voz alta y resumen final |
| RF06 | Dos preguntas por lección (recordar/comprender y aplicar/analizar) con distractores creíbles, explicación específica para cada opción incorrecta y orden aleatorio de las opciones |
| RF07 | Registro automático del progreso y botón "Continuar donde iba" |
| RF08 | Certificado de participación en PDF al terminar un módulo |
| RF09 | Panel del facilitador: grupos, inscripción de aprendices y avance por módulo |
| RF10 | Panel del administrador: CRUD de módulos, lecciones, actividades y usuarios |
| RF11 | Exportación del reporte de progreso en CSV |
| RF12 | Letra ampliada, alto contraste y lectura en voz alta |
| RF14 | Botón de ayuda contextual "¿Cómo uso esto?" en cada pantalla |
| RNF03 | Diseño adaptable: celular (desde 360 px), tablet y escritorio. En celular las tablas de los paneles se muestran como tarjetas |
| RNF05 | Seguridad: PIN cifrado con bcrypt, bloqueo tras 5 intentos fallidos, rechazo de PIN fáciles, sesiones firmadas, control por roles y cabeceras HTTP de seguridad (ver sección Seguridad) |
| RNF09 | Service worker: la interfaz y las lecciones visitadas funcionan sin conexión |

## Diseño de los contenidos

Las 20 lecciones (4 módulos de 5) siguen los fundamentos del documento maestro:

- **Andragogía (Knowles):** cada lección parte de una situación cotidiana de un adulto en Valledupar
  (una entrevista virtual, un mensaje de estafa, un trámite que no puede hacer en persona).
- **Taxonomía de Bloom revisada:** los pasos llevan a *aplicar*; la práctica incluye una pregunta de
  *recordar/comprender* y otra de *aplicar/analizar* sobre la situación planteada.
- **Lectura fácil:** frases cortas, trato de "usted", una idea por paso, consejos prácticos y glosario de
  palabras clave. Cada lección indica si se practica en el celular o en el computador, y la
  pantalla del paso se dibuja como uno u otro.

Una lección se marca como completada cuando el aprendiz acierta todas sus preguntas. Los contenidos
se pueden editar desde el panel del administrador sin modificar el código.

## Seguridad

| Riesgo | Medida implementada |
|---|---|
| Robo de PIN desde la base de datos | El PIN se guarda cifrado con bcrypt; nunca en texto plano |
| Adivinar el PIN probando combinaciones | La cuenta se bloquea 15 minutos tras 5 intentos fallidos; el facilitador puede desbloquearla cambiando el PIN |
| PIN débiles | Se rechazan PIN con dígitos iguales o consecutivos (0000, 1234, 9876) |
| Falsificar una sesión | Token firmado con HMAC-SHA256 y vencimiento de 12 horas; la clave se toma de `SECRET_KEY` o se genera aleatoria en `backend/.secret_key` (excluido de Git) |
| Acceso a funciones sin permiso | Cada ruta verifica el rol (aprendiz, facilitador, administrador) |
| Inyección SQL | Consultas mediante el ORM SQLAlchemy con parámetros |
| Datos de entrada inválidos | Validación con Pydantic (formato de celular, PIN, longitudes) |
| Código malicioso en pantalla (XSS) | Todo texto se escapa antes de mostrarse; política de seguridad de contenido (CSP) |
| Clickjacking y otros ataques del navegador | Cabeceras `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy` |
| Fórmulas maliciosas en el reporte CSV | Las celdas que empiezan por `=`, `+`, `-` o `@` se neutralizan |
| Datos personales | Solo nombre y celular, con consentimiento registrado (Ley 1581 de 2012) |

**Antes de un despliegue real** (fuera del alcance del prototipo TRL 5): servir la aplicación solo por
HTTPS, definir `SECRET_KEY` en el servidor, cambiar o eliminar los usuarios de prueba con PIN 1234 y
usar PostgreSQL con copias de seguridad.

## Arquitectura (tres capas)

- **Presentación:** HTML5, CSS3 y JavaScript sin frameworks (`frontend/`), instalable como PWA.
- **Lógica de negocio:** API REST con Python 3.12+ y FastAPI (`backend/app/`).
- **Datos:** SQLAlchemy con SQLite en desarrollo y PostgreSQL en producción (variable `DATABASE_URL`).

```
aprendo-digital/
├── backend/
│   ├── app/
│   │   ├── main.py          # Punto de entrada; sirve la API y la PWA
│   │   ├── config.py        # Configuración por variables de entorno
│   │   ├── database.py      # Conexión y sesión de base de datos
│   │   ├── models.py        # Modelo entidad-relación (12 tablas)
│   │   ├── schemas.py       # Validación de datos de entrada
│   │   ├── security.py      # bcrypt, tokens y control de roles
│   │   ├── servicios.py     # Cálculo de avance y serialización
│   │   ├── certificado.py   # Generación de PDF (ReportLab)
│   │   ├── seed.py          # Contenidos iniciales y usuarios de prueba
│   │   └── routers/         # auth, aprendiz, facilitador, admin
│   ├── tests/               # 49 casos de prueba automatizados (pytest)
│   └── requirements.txt
├── frontend/                # index.html, css/, js/, sw.js, manifest.json
└── docs/                    # Matriz de casos de prueba y capturas
```

## Cómo ejecutarlo

Requisitos: Python 3.12 o superior.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (en Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abra http://localhost:8000. La primera vez se crea la base de datos con los contenidos.

Para volver a cargar los contenidos originales (borra todos los datos, incluidos usuarios y progreso):

```bash
python -m app.seed --reiniciar
```
La documentación interactiva de la API está en http://localhost:8000/docs.

### Usuarios de prueba

| Rol | Celular | PIN |
|---|---|---|
| Administrador | 3000000001 | 1234 |
| Facilitador | 3000000002 | 1234 |
| Aprendiz | 3000000003 | 1234 |

Estos usuarios solo se crean en una instalación local. Los aprendices no necesitan cuenta: entran
con el botón **Empezar ahora** y, si quieren, guardan su avance con celular y PIN.

## Pruebas

```bash
cd backend
pytest                          # ejecuta los 49 casos (54 ejecuciones)
python tests/generar_matriz.py  # ejecuta y genera docs/matriz_casos_prueba.csv y .md
```

## Despliegue en Render (gratis)

El archivo `render.yaml` describe el servicio web y una base de datos PostgreSQL gratuita.

1. Cree una cuenta en https://render.com con su cuenta de GitHub.
2. **New → Blueprint**, elija este repositorio y confirme.
3. Render pide dos valores: `ADMIN_CELULAR` (10 dígitos, empieza por 3) y `ADMIN_PIN`
   (4 dígitos, no trivial). Con ellos se crea el único administrador; los usuarios de prueba de
   esta guía **no** se crean en el despliegue público.
4. Al terminar, la plataforma queda en `https://tic-para-todos.onrender.com` (o el nombre que
   Render asigne).

En el plan gratuito el servicio se duerme tras 15 minutos sin visitas y la primera carga después
tarda cerca de un minuto. La base de datos gratuita de Render vence a los 30 días.

Las pruebas también pueden ejecutarse contra PostgreSQL:
`TEST_DATABASE_URL=postgresql://usuario:clave@localhost:5432/base pytest`

## Licencia

Proyecto académico. Uso educativo.
