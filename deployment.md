# MediBridge – Deployment and Local Setup Guide

## 1. Project Information

**Project:** MediBridge – AI-Assisted Pharmacy Medicine Reordering Platform

**GitHub Repository:** https://github.com/chethanakeshava/AI-assisted-pharmacy-medicine-reordering-platform/

**Live Application:** Not deployed.

## 2. Prerequisites

Install the following software:

- Python 3.12
- Node.js 22
- npm
- Git

## 3. Clone the Repository

Open PowerShell or a terminal:

```powershell
git clone https://github.com/chethanakeshava/AI-assisted-pharmacy-medicine-reordering-platform.git

cd AI-assisted-pharmacy-medicine-reordering-platform
```

## 4. Backend Setup

Create a Python virtual environment from the project root:

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Move into the backend folder:

```powershell
cd backend
```

Install the dependencies:

```powershell
pip install -r requirements.txt
```

Create a local `.env` file using the supplied `backend/.env.example`.

Configure the required local development settings. Keep all secret values private.

Start the backend:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend address:

http://localhost:8000

API documentation:

http://localhost:8000/docs

Health endpoint:

http://localhost:8000/health

## 5. Frontend Setup

Open a second terminal from the project root.

Move into the frontend directory:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Start the development server:

```powershell
npm run dev
```

Frontend address:

http://localhost:5173

The Vite development server proxies `/api` requests to the local FastAPI backend.

## 6. Environment Variables

### Backend environment variables

Configure the following variables using `backend/.env.example` and the application configuration.

| Variable | Description |
|---|---|
| APP_ENV | Application environment |
| DATABASE_URL | Database connection URL |
| JWT_SECRET | JWT signing secret |
| OTP_SECRET | OTP hashing secret |
| FERNET_KEY | Prescription encryption key |
| GEMINI_API_KEY | Gemini API key |
| AI_PROVIDER | AI provider configuration |
| GEMINI_MODEL | Gemini model name |
| CORS_ORIGINS | Allowed frontend origins |
| UPLOAD_DIR | Prescription upload directory |

Other application settings may be configured in `backend/app/config.py`.

### Frontend environment variables

| Variable | Description |
|---|---|
| VITE_API_URL | Backend API base URL |

For local development, the default `/api` URL and Vite proxy can be used.

Never expose backend secrets through frontend environment variables.

## 7. Database Setup

The local development environment uses SQLite.

The application initializes its database using the existing SQLAlchemy setup.

Keep local database files out of the Git repository.

For production hosting, configure a PostgreSQL database and establish a proper schema migration and backup process before deployment.

## 8. Demo Accounts

The following synthetic demonstration accounts are included in the application.

| User role | Phone number |
|---|---|
| Customer – Debasish | 9000000001 |
| Customer – Rina | 9000000002 |
| Customer – Arif | 9000000003 |
| Pharmacist | 9000000010 |
| Store Staff | 9000000020 |
| Operations | 9000000030 |

### Login procedure

1. Open the application.
2. Enter the phone number associated with the desired demo account.
3. Request an OTP.
4. In development mode, use the OTP displayed by the application.
5. Verify the OTP to access the corresponding dashboard.

OTP values are generated dynamically. There is no fixed demo OTP.

## 9. Running Automated Tests

### Backend tests

From the project root:

```powershell
cd backend
python -m pytest -q
```

### Frontend tests

From the project root:

```powershell
cd frontend
npm test -- --run
```

### Frontend production build

```powershell
npm run build
```

## 10. Deployment Architecture

The proposed production hosting architecture is:

| Component | Proposed platform |
|---|---|
| Frontend | Vercel |
| Backend | Render |
| Database | Neon PostgreSQL |

**Deployment status:** The application has not yet been deployed to these services.

Before production deployment, configure the production environment variables, CORS settings, database migrations and persistent private storage for encrypted prescription files.

## 11. Security Guidelines

- Do not commit `.env` files.
- Do not publish API keys or authentication secrets.
- Do not include local database files in the repository.
- Use synthetic demonstration data.
- Keep prescription uploads private.
- Use secure production environment variables.
- Verify role-based access after deployment.

## 12. Submission Package

The take-home submission ZIP should contain exactly:

1. Technical Design Document (PDF or Word).
2. `deployment.md`.

The ZIP must not exceed 25 MB.

The GitHub repository contains the project source code. Do not include `.venv`, `node_modules`, local databases, uploaded prescriptions or secret files in the submission ZIP.