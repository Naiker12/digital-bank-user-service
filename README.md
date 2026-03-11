# Bank User Service

This is the core microservice for **user management** in the banking platform. it provides robust capabilities for registration, authentication, profile management, and multimedia resource uploads (avatars), integrating natively with AWS services for high scalability and performance.

## Core Technologies

- **FastAPI:** High-performance web framework for Python.
- **Python 3.11+:** Base programming language.
- **AWS DynamoDB:** NoSQL key-value and document database for user profiles.
- **AWS S3:** Object storage service for secure profile image storage.
- **AWS Lambda:** Serverless computing for specific, scalable tasks.

## Service Responsibilities

The **User Service** is responsible for the following critical operations:

1. **User Registration:** Secure creation of new user accounts and triggering card requests via SQS.
2. **Login / Authentication:** Identity verification and JWT token generation.
3. **Profile Management:** Updating personal information and user preferences.
4. **Avatar Upload:** Direct image uploads to S3 with profile URL updates.
5. **Profile Query:** Fast retrieval of detailed user profile information.

## Architecture and Project Structure

The project follows a modular structure designed for scalability and maintainability:

```text
bank-user-service
│
├── app                     # FastAPI application core
│   ├── main.py             # Application entry point
│   ├── routes              # API endpoint definitions
│   │   └── user_routes.py
│   ├── services            # Encapsulated business logic
│   │   └── user_service.py
│   ├── models              # Schema and data model definitions
│   │   └── user_model.py
│   └── utils               # Utilities and client configurations
│       ├── dynamodb.py     # DynamoDB client
│       ├── s3.py           # AWS S3 client
│       └── jwt.py          # JWT token management logic
│
├── lambdas                 # Serverless Lambda functions
│   ├── register_user.py    # Handles user registration and SQS card requests
│   ├── login_user.py       # Handles authentication and login notifications
│   ├── update_user.py      # Handles profile updates in DynamoDB
│   ├── upload_avatar.py    # Handles S3 uploads and profile URL updates
│   └── get_profile.py      # Handles profile retrieval by UUID
│
├── deployment_package      # Package for AWS Lambda deployment
├── requirements.txt        # Project dependencies
└── README.md               # Technical documentation
```

## Implemented Lambdas

This service leverages the following Lambda functions for serverless task handling:

- `register-user-lambda`: Secure registration and SQS event dispatch for card creation.
- `login-user-lambda`: Credentials processing and login activity logging.
- `update-user-lambda`: Modifying existing data records in DynamoDB.
- `upload-avatar-lambda`: Processing image uploads and generating S3 URLs.
- `get-profile-lambda`: High-speed retrieval of user profiles via Partition Key.

## Installation and Execution Commands

### 1. Virtual Environment Configuration
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
.\venv\Scripts\activate
```

### 2. Dependency Installation
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the project root:
```env
AWS_REGION=us-east-1
USERS_TABLE=bank-users
S3_BUCKET=bank-user-avatars-suffix
JWT_SECRET=your-secret-key
CARD_QUEUE_URL=create-request-card-sqs-url
NOTIFICATION_QUEUE_URL=notification-email-sqs-url
```

### 4. Local Execution
Run the FastAPI service locally using uvicorn:
```bash
uvicorn app.main:app --reload
```

### 5. Deployment Commands (Independent Terraform)
The infrastructure is now independent. To deploy:
1. Ensure the `terraform.tfvars` file is configured with the shared infrastructure values (IAM Role, API Gateway).
2. Run deployment:
```bash
cd terraform
terraform init
terraform apply -auto-approve
```

## API Documentation

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/users/register` | Registers a new user and requests cards. | No |
| `POST` | `/users/login` | Authenticates user and returns JWT. | No |
| `GET` | `/users/profile/{user_id}` | Retrieves full user profile. | Yes |
| `PUT` | `/users/profile/{user_id}` | Updates address or phone. | Yes |
| `POST` | `/users/profile/{user_id}/avatar` | Uploads avatar to S3. | Yes |

---

