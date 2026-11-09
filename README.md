# MediBridge – AI-Assisted Pharmacy Medicine Reordering Platform

**GitHub Repository:** https://github.com/chethanakeshava/AI-assisted-pharmacy-medicine-reordering-platform

MediBridge is an AI-assisted pharmacy medicine reordering platform designed to simplify prescription-based medicine ordering. It connects customers, pharmacists, and pharmacy staff through a centralized workflow for prescription submission, verification, inventory management, and order fulfilment.

The platform uses AI-assisted prescription extraction to help identify medicine details, while keeping the final prescription approval under pharmacist control.

## Key Features

### Customer
- Sign in using phone number and OTP.
- Upload medicine prescriptions.
- View AI-extracted medicine details.
- Track prescription verification and order status.
- Upload a replacement image when a prescription is unclear.
- Receive order notifications and refill reminders.

### Pharmacist
- Review submitted prescriptions.
- Verify extracted medicine details.
- Approve or reject prescription items.
- Handle unclear prescriptions that require customer action.

### Store Staff
- Manage medicine inventory.
- Upload stock information through CSV.
- Support order fulfilment workflows.

### AI-Assisted Prescription Processing
- Extract medicine information from prescription images.
- Identify medicine names, strengths, and quantities.
- Support pharmacist review before order approval.
- Handle uncertain or unreadable prescription images through manual review.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript |
| Backend | Python, FastAPI |
| Database | SQLite, SQLAlchemy |
| Authentication | Phone OTP, JWT |
| AI Integration | Gemini API |
| Testing | Pytest, Vitest |
| Version Control | Git, GitHub |

## System Architecture

```text
             Customer / Pharmacist / Staff
                         |
                         v
                 React Frontend
                         |
                         v
                   FastAPI Backend
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
      Authentication  Order Logic   AI Processing
          |              |              |
          +--------------+--------------+
                         |
                         v
                  SQLAlchemy ORM
                         |
                         v
                     SQLite
```

## Application Workflow

1. Customer signs in using their registered phone number and OTP.
2. Customer uploads a prescription image.
3. The AI-assisted service extracts medicine information.
4. The extracted information is presented for pharmacist verification.
5. The pharmacist reviews and approves or rejects the prescription items.
6. Approved orders proceed through the fulfilment workflow.
7. Customers can track order updates and receive refill reminders.

**Important:** AI extraction is an assistance mechanism, not a substitute for pharmacist verification.

## Project Structure

```text
AI-assisted-pharmacy-medicine-reordering-platform/
│
├── backend/
│   ├── app/
│   ├── tests/
│   ├── sample_data/
│   ├── sample_prescriptions/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

Install the following:

- Python 3.12+
- Node.js 18+
- npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/chethanakeshava/AI-assisted-pharmacy-medicine-reordering-platform.git

cd AI-assisted-pharmacy-medicine-reordering-platform
```

### 2. Backend Setup

Open a terminal:

```bash
cd backend
```

Create and activate a virtual environment:

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```powershell
Copy-Item .env.example .env
```

Configure the required environment variables in `.env`. Refer to `.env.example` for the exact variable names. Do not commit API keys or secrets.

Initialize the database with sample data:

```bash
python -m app.seed
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup

Open a second terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the frontend URL displayed in the terminal, usually:

`http://localhost:5173`

## Demo Login Accounts

The following seeded accounts are available for local development and testing.

| Role | Phone Number |
|---|---|
| Customer | `9000000001` |
| Customer | `9000000002` |
| Customer | `9000000003` |
| Pharmacist | `9000000010` |
| Store Staff | `9000000020` |
| Operations | `9000000030` |

**OTP:** In development mode, the OTP is generated dynamically and returned by the API. Use the OTP displayed by the application/API during local testing.

These are test accounts only. Do not use real patient information.

## Running Tests

### Backend

From the `backend` directory:

```bash
python -m pytest -q
```

### Frontend

From the `frontend` directory:

```bash
npm test -- --run
```

### Production Build

```bash
npm run build
```

## Security Considerations

- OTP values are stored as hashes.
- OTP expiry and attempt limits are enforced.
- JWT-based authentication protects application routes.
- Role-based access controls restrict protected operations.
- Sensitive configuration is maintained through environment variables.
- Prescription uploads require appropriate validation.
- Real patient information and API credentials should never be committed to the repository.

For production deployment, additional controls such as secure file storage, database backups, audit logging, HTTPS, and production-grade monitoring should be configured.

## Current Limitations

- The application is currently intended for local development and demonstration.
- Real SMS and payment gateway integrations are not configured.
- Production cloud deployment is not currently available.
- Production-grade prescription document storage and monitoring require further implementation.
- AI-generated prescription details must be reviewed by a pharmacist before approval.

## Future Enhancements

- Integrate a real SMS/OTP provider.
- Add secure cloud-based prescription storage.
- Integrate online payment gateways.
- Improve medicine availability and pharmacy routing.
- Add advanced refill prediction and reminder scheduling.
- Introduce production monitoring and audit trails.

## Project Objective

MediBridge aims to make pharmacy medicine reordering more convenient and organized by combining AI-assisted prescription processing with pharmacist-led verification and structured order management.

---

**Note:** This project is developed for demonstration and evaluation purposes. It is not a replacement for professional medical or pharmaceutical judgment.
