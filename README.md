# Servicio de Usuarios (Bank User Service)

Este es el microservicio central para la **gestión de usuarios** en la plataforma bancaria. Proporciona capacidades robustas para el registro, autenticación, gestión de perfiles y carga de recursos multimedia (avatares), integrándose nativamente con los servicios de AWS para un alto rendimiento y escalabilidad.

## Tecnologías Principales

- **FastAPI:** Framework web de alto rendimiento para Python.
- **Python 3.11+:** Lenguaje de programación base.
- **AWS DynamoDB:** Base de datos NoSQL para perfiles de usuario.
- **AWS S3:** Almacenamiento de objetos para imágenes de perfil seguras.
- **AWS Lambda:** Computación serverless para tareas específicas y escalables.

## Responsabilidades del Servicio

El **User Service** es responsable de las siguientes operaciones críticas:

1. **Registro de Usuarios:** Creación segura de nuevas cuentas de usuario y activación de solicitudes de tarjetas vía SQS.
2. **Login / Autenticación:** Verificación de identidad y generación de tokens JWT.
3. **Gestión de Perfil:** Actualización de información personal y preferencias del usuario.
4. **Carga de Avatares:** Carga directa de imágenes a S3 con actualización de la URL en el perfil.
5. **Consulta de Perfil:** Recuperación rápida de información detallada del usuario.

## Arquitectura y Estructura del Proyecto

El proyecto sigue una estructura modular diseñada para la mantenibilidad:

```text
bank-user-service
│
├── app                     # Núcleo de la aplicación FastAPI
│   ├── main.py             # Punto de entrada de la aplicación
│   ├── routes              # Definición de endpoints de la API
│   │   └── user_routes.py
│   ├── services            # Lógica de negocio encapsulada
│   │   └── user_service.py
│   ├── models              # Definiciones de esquemas y modelos de datos
│   │   └── user_model.py
│   └── utils               # Utilidades y clientes
│       ├── dynamodb.py     # Cliente DynamoDB
│       ├── s3.py           # Cliente AWS S3
│       └── jwt.py          # Lógica de gestión de tokens JWT
│
├── lambdas                 # Funciones Lambda Serverless
│   ├── register_user.py    # Maneja registro y solicitudes de tarjetas SQS
│   ├── login_user.py       # Maneja autenticación y notificaciones de login
│   ├── update_user.py      # Maneja actualizaciones en DynamoDB
│   ├── upload_avatar.py    # Maneja cargas a S3 y actualización de URLs
│   └── get_profile.py      # Maneja recuperación de perfiles por UUID
│
├── deployment_package      # Paquete para despliegue en AWS Lambda
├── requirements.txt        # Dependencias del proyecto
└── README.md               # Documentación técnica
```

## Lambdas Implementadas

Este servicio utiliza las siguientes funciones Lambda para el manejo de tareas serverless:

- `register-user-lambda`: Registro seguro y envío de eventos SQS para creación de tarjetas.
- `login-user-lambda`: Procesamiento de credenciales y registro de actividad de login.
- `update-user-lambda`: Modificación de registros existentes en DynamoDB.
- `upload-avatar-lambda`: Procesamiento de imágenes y generación de URLs de S3.
- `get-profile-lambda`: Recuperación de alta velocidad de perfiles de usuario.

## Comandos de Instalación y Ejecución

### 1. Configuración del Entorno Virtual
```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows
.\venv\Scripts\activate
```

### 2. Instalación de Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configuración del Entorno
Crea un archivo `.env` en la raíz del proyecto:
```env
AWS_REGION=us-east-1
USERS_TABLE=bank-users
S3_BUCKET=nombre-del-bucket-avatars
JWT_SECRET=tu-llave-secreta
CARD_QUEUE_URL=url-de-la-cola-de-tarjetas
NOTIFICATION_QUEUE_URL=url-de-la-cola-de-notificaciones
```

### 4. Ejecución Local
Ejecuta el servicio FastAPI localmente:
```bash
uvicorn app.main:app --reload
```

### 5. Comandos de Despliegue (Terraform Independiente)
La infraestructura ahora es independiente. Para desplegar:
1. Asegúrate de que el archivo `terraform.tfvars` esté configurado con los valores de infraestructura compartida (IAM Role, API Gateway).
2. Ejecuta el despliegue:
```bash
cd terraform
terraform init
terraform apply -auto-approve
```

## Documentación de la API

| Método | Endpoint | Descripción | Requiere Auth |
| :--- | :--- | :--- | :---: |
| `POST` | `/users/register` | Registra un nuevo usuario y solicita tarjeta. | No |
| `POST` | `/users/login` | Autentica al usuario y retorna JWT. | No |
| `GET` | `/users/profile/{user_id}` | Recupera el perfil completo del usuario. | Sí |
| `PUT` | `/users/profile/{user_id}` | Actualiza dirección o teléfono. | Sí |
| `POST` | `/users/profile/{user_id}/avatar` | Carga el avatar a S3. | Sí |
