# Multi-Tenant Authentication Service

A production-ready authentication and authorization service built with FastAPI, designed to support multiple tenants while maintaining strict data isolation and scalable identity management.

---

## Overview

This service provides centralized authentication for SaaS applications with support for:

* Multi-tenancy
* JWT Authentication
* Role-Based Access Control (RBAC)
* User Management
* Tenant Management
* Refresh Tokens
* API Key Support
* OAuth-ready Architecture

The goal is to provide a reusable authentication layer that can be integrated across multiple applications and services.

---

## Features

### Authentication

* User Registration
* Login
* Logout
* Password Reset
* Email Verification
* JWT Access Tokens
* Refresh Tokens

### Multi-Tenancy

* Tenant Creation
* Tenant Isolation
* Tenant-Specific Users
* Tenant-Level Configuration

### Authorization

* Role-Based Access Control (RBAC)
* Permission Management
* Resource-Level Access Control

### Security

* Password Hashing (bcrypt)
* Token Expiration
* Refresh Token Rotation
* Rate Limiting
* Audit Logging

---

## Architecture

```text
Client
  │
  ▼
FastAPI Gateway
  │
  ├── Authentication Module
  ├── Authorization Module
  ├── Tenant Module
  ├── User Module
  └── Audit Module
  │
  ▼
PostgreSQL
```

---

## Tech Stack

| Component        | Technology |
| ---------------- | ---------- |
| Backend          | FastAPI    |
| ORM              | SQLAlchemy |
| Database         | PostgreSQL |
| Authentication   | JWT        |
| Validation       | Pydantic   |
| Migrations       | Alembic    |
| Containerization | Docker     |

---

## Multi-Tenant Strategy

The system isolates data using a tenant identifier.

### User Table

```text
users
├── id
├── email
├── password_hash
├── tenant_id
└── role_id
```

Every authenticated request contains tenant context.

```text
X-Tenant-ID: tenant_123
```

All database queries are scoped by tenant_id.

---

## Authentication Flow

1. User submits credentials.
2. Credentials are validated.
3. JWT Access Token is issued.
4. Tenant information is embedded in token claims.
5. Protected endpoints validate token and tenant access.

Example JWT Payload:

```json
{
  "sub": "user_id",
  "tenant_id": "tenant_123",
  "role": "admin",
  "exp": 1700000000,
  ...
}
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Divya1804/auth-service.git auth-service
cd auth-service
```

Create virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a .env file:

```env
DATABASE_URL=postgresql://user:password@localhost/authdb
SECRET_KEY=change_me
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## Database Setup

Run migrations:

```bash
alembic upgrade head
```

---

## Running the Service

Development:

```bash
uvicorn application.main:app --reload
```

Production:

```bash
gunicorn -k uvicorn.workers.UvicornWorker application.main:app
```

---

## API Documentation

Swagger UI:

```text
http://localhost:8000/docs
```

---

## Example Requests

### Login

```bash
curl -X POST \
"http://localhost:8000/api/v1/auth/login" \
-H "Content-Type: application/json" \
-d '{
  "email":"admin@example.com",
  "password":"password"
}'
```

Response:

```json
{
  "access_token":"jwt_token",
  "refresh_token":"refresh_token",
  "token_type":"bearer"
}
```

---

## Docker

Build image:

```bash
docker build -t auth-service .
```

Run container:

```bash
docker run -p 8000:8000 auth-service
```

---

## Security Considerations

* Never store plain-text passwords.
* Use HTTPS in production.
* Rotate signing keys regularly.
* Enable rate limiting.
* Restrict CORS origins.
* Use refresh token rotation.

---

## Future Enhancements

* OAuth2 Providers
* SAML Authentication
* MFA Support
* Tenant Billing Integration
* SCIM Provisioning
* Fine-Grained Permissions

---

## Contributing

1. Fork repository
2. Create feature branch
3. Submit pull request to develop branch
