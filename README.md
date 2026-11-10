# MediBridge – AI-Assisted Pharmacy Medicine Reordering Platform

**MediBridge** is an AI-assisted pharmacy medicine reordering platform that simplifies prescription-based medicine ordering and pharmacy operations. It connects customers, pharmacists, and store staff through a centralized system for prescription submission, medicine verification, inventory management, order fulfilment, and refill tracking.

The platform uses AI to assist with prescription image extraction while keeping final prescription verification and approval under pharmacist control.

**GitHub Repository:** [AI-Assisted Pharmacy Medicine Reordering Platform](https://github.com/chethanakeshava/AI-assisted-pharmacy-medicine-reordering-platform)

---

## Project Overview

MediBridge aims to make medicine reordering more convenient by connecting customers and pharmacy teams through a structured digital workflow.

Customers can upload prescriptions, order medicines for themselves or family members, track orders, and manage refills. Pharmacists can review AI-extracted prescription details, while store staff manage inventory and fulfilment activities.

## Key Features

### Customer Portal
- Phone number and OTP-based authentication.
- Upload prescription images.
- View AI-extracted medicine information.
- Order medicines for themselves or registered family members.
- Search medicines and manage shopping carts.
- Place orders and track order status.
- Reorder medicines and manage refill reminders.
- Communicate through customer-pharmacist messaging.
- Receive order updates and notifications.
- Access a multilingual interface.

### Pharmacist Portal
- View submitted prescriptions in a verification queue.
- Review AI-extracted medicine information.
- Verify medicine names, strengths, and quantities.
- Approve, edit, or reject prescription items.
- Request a clearer prescription or additional information when needed.
- Review prescriptions before orders proceed.

### Store Staff Portal
- View and manage order fulfilment tasks.
- Support picking, packing, and order handover.
- Manage medicine stock information.
- Import inventory information using CSV files.

### Operations Dashboard
- Monitor order and fulfilment activity.
- View operational information through a centralized dashboard.
- Support pharmacy workflow monitoring.

### AI-Assisted Prescription Processing
- Extract medicine information from prescription images using the Gemini API.
- Identify medicine names, strengths, and quantities where readable.
- Present extracted information for pharmacist review.
- Support manual review when prescription details are unclear or uncertain.

**Important:** AI extraction is an assistance mechanism. It does not independently approve prescriptions or replace pharmacist judgment.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript |
| Backend | Python, FastAPI |
| Database | SQLite, SQLAlchemy |
| Authentication | Phone OTP, JWT |
| AI Integration | Gemini API |
| Frontend Testing | Vitest |
| Backend Testing | Pytest |
| Version Control | Git, GitHub |

## System Architecture

```text
             Customer / Pharmacist / Store Staff
                            |
                            v
                     React Frontend
                            |
                            v
                     FastAPI Backend
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
   Authentication      Order Management   AI Processing
          |                 |                 |
          +-----------------+-----------------+
                            |
                            v
                      SQLAlchemy ORM
                            |
                            v
                          SQLite
```

## Application Workflow

1. A customer signs in using their registered phone number and OTP.
2. The customer uploads a prescription image.
3. The AI-assisted service extracts available medicine information.
4. Extracted details are presented to the pharmacist for verification.
5. The pharmacist reviews and approves, edits, or rejects prescription items.
6. The customer proceeds with the medicine ordering process.
7. Store staff handle the order fulfilment workflow.
8. Customers can track order updates and manage future refills.

---

## Project Structure

```text
AI-assisted-pharmacy-medicine-reordering-platform/
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   ├── sample_data/
│   ├── sample_prescriptions/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api.js
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.js
│
├── deployment.md
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

Install the following:

- Python 3.12 or compatible project-supported version
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

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it using Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the environment file:

```powershell
Copy-Item .env.example .env
```

Configure the required environment variables in `.env`, including the AI API key if AI prescription extraction is enabled.

Do not commit API keys or other sensitive credentials.

Initialize the database and sample data using the project's supported setup process.

If the seed module is available in your checkout, run:

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

---

## Demo Login Accounts

The following seeded accounts are intended for local development and testing.

| Role | Phone Number |
|---|---|
| Customer | `9000000001` |
| Customer | `9000000002` |
| Customer | `9000000003` |
| Pharmacist | `9000000010` |
| Store Staff | `9000000020` |
| Operations | `9000000030` |

**OTP:** In development mode, the OTP is generated dynamically. Use the OTP returned by the application or API during local testing.

These accounts are for demonstration purposes only. Do not use real patient information.

---

## Running Tests

### Backend Tests

From the `backend` directory:

```bash
python -m pytest -q
```

### Frontend Tests

From the `frontend` directory:

```bash
npm test -- --run
```

### Production Build

From the `frontend` directory:

```bash
npm run build
```

---

## Security Considerations

MediBridge includes security measures intended to protect application workflows:

- OTP-based authentication.
- Hashed OTP storage.
- OTP expiry and attempt limits.
- JWT-based authentication.
- Role-based access controls.
- Environment-based configuration for sensitive credentials.
- Prescription upload validation.

For production deployment, additional controls such as secure document storage, database backups, audit logging, HTTPS, and production monitoring should be configured.

## Current Limitations

- The application is currently intended for local development and demonstration.
- Real SMS/OTP provider integration is not configured.
- Real payment gateway integration is not configured; payment functionality should be treated as a mock or demonstration workflow.
- Production cloud deployment is not currently available.
- Production-grade prescription document storage and monitoring require further implementation.
- AI-extracted prescription information requires pharmacist verification before approval.

## Future Enhancements

- Integrate a real SMS/OTP provider.
- Add secure cloud-based prescription storage.
- Integrate real online payment gateways.
- Improve medicine availability and pharmacy routing.
- Enhance refill prediction and reminder scheduling.
- Introduce production monitoring and audit trails.
- Improve deployment scalability and reliability.

---

## Project Objective

MediBridge aims to simplify pharmacy medicine reordering by combining AI-assisted prescription processing with pharmacist-led verification, customer convenience, and structured pharmacy operations.

It demonstrates how AI, web technologies, and role-based workflows can work together to improve the medicine ordering experience.

**Disclaimer:** MediBridge is an educational and demonstration project. It is not a replacement for professional medical or pharmaceutical judgment. Real patient information should not be used in the demonstration environment.
