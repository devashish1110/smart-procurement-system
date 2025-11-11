\# 🏥 Smart Procurement System for Ayurvedic Clinics



An AI-powered procurement and inventory management system designed specifically for Ayurvedic clinics, featuring an intelligent chatbot assistant powered by Groq LLM and RAG (Retrieval-Augmented Generation).



---



\## 📋 Table of Contents



\- \[Overview](#overview)

\- \[Features](#features)

\- \[Technology Stack](#technology-stack)

\- \[System Architecture](#system-architecture)

\- \[Prerequisites](#prerequisites)

\- \[Installation](#installation)

\- \[Configuration](#configuration)

\- \[Running the Application](#running-the-application)

\- \[Usage Guide](#usage-guide)

\- \[API Documentation](#api-documentation)

\- \[Database Schema](#database-schema)

\- \[AI Chatbot](#ai-chatbot)

\- \[Troubleshooting](#troubleshooting)

\- \[Contributing](#contributing)

\- \[License](#license)



---



\## 🎯 Overview



The Smart Procurement System is a comprehensive solution for managing Ayurvedic clinic operations, with a focus on automating procurement workflows, inventory management, and providing intelligent assistance through an AI chatbot.



\### Key Highlights



\- \*\*AI-Powered Chatbot\*\*: Natural language interface for querying inventory, generating reports, and getting operational insights

\- \*\*Real-Time Inventory Tracking\*\*: Monitor stock levels, expiry dates, and generate alerts automatically

\- \*\*Procurement Automation\*\*: Streamlined purchase order creation and vendor management

\- \*\*Role-Based Access Control\*\*: Different interfaces for doctors, pharmacists, receptionists, and therapists

\- \*\*Comprehensive Reporting\*\*: Financial reports, inventory analytics, and performance metrics



---



\## ✨ Features



\### Core Functionality



1\. \*\*Inventory Management\*\*

   - Real-time stock tracking

   - Automatic low-stock alerts

   - Expiry date monitoring

   - Batch tracking

   - Multi-location support



2\. \*\*Procurement System\*\*

   - Purchase order creation and approval workflow

   - Vendor management and performance tracking

   - Order receiving and inventory updates

   - Budget tracking and reporting



3\. \*\*Patient Management\*\*

   - Patient record management

   - Appointment scheduling

   - Visit history tracking

   - Billing integration



4\. \*\*Billing \& Financial\*\*

   - Bill generation

   - Payment tracking

   - Outstanding balance management

   - Revenue analysis



5\. \*\*AI Chatbot Assistant\*\*

   - Natural language queries

   - Intent classification

   - Context-aware responses using RAG

   - Suggested actions

   - Multi-turn conversations



6\. \*\*Reports \& Analytics\*\*

   - Dashboard with key metrics

   - Financial reports

   - Inventory reports

   - Patient visit analytics

   - Procurement analysis



\### User Roles



\- \*\*Admin\*\*: Full system access

\- \*\*Doctor\*\*: Approve orders, access all patient data

\- \*\*Pharmacist\*\*: Manage inventory, create purchase orders

\- \*\*Receptionist\*\*: Appointments, basic billing

\- \*\*Therapist\*\*: Treatment management



---



\## 🛠 Technology Stack



\### Backend



\- \*\*Framework\*\*: FastAPI (Python 3.11+)

\- \*\*Database\*\*: PostgreSQL 14+

\- \*\*ORM\*\*: SQLAlchemy 2.0

\- \*\*Authentication\*\*: JWT (JSON Web Tokens)

\- \*\*AI/ML\*\*:

  - Groq LLM (llama-3.1-8b-instant)

  - FAISS (Vector similarity search)

  - Sentence Transformers (Embeddings)

  - TensorFlow (Forecasting - planned)



\### Frontend



\- \*\*Framework\*\*: React 18 with Vite

\- \*\*Routing\*\*: React Router v6

\- \*\*HTTP Client\*\*: Axios

\- \*\*Icons\*\*: Lucide React

\- \*\*Charts\*\*: Recharts

\- \*\*Styling\*\*: CSS3 with custom design system



\### Development Tools



\- \*\*API Documentation\*\*: Swagger/OpenAPI (FastAPI auto-generated)

\- \*\*Version Control\*\*: Git

\- \*\*Package Management\*\*: pip (Python), npm (JavaScript)



---



\## 🏗 System Architecture



```

┌─────────────────────────────────────────────────────────────┐

│                        FRONTEND (React)                      │

│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │

│  │Dashboard │  │Inventory │  │ Chatbot  │  │ Reports  │   │

│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │

└────────────────────────┬────────────────────────────────────┘

\&nbsp;                        │ HTTP/REST API

┌────────────────────────┴────────────────────────────────────┐

│                    BACKEND (FastAPI)                         │

│  ┌──────────────────────────────────────────────────────┐  │

│  │              API Routes (11 modules)                  │  │

│  └──────────────────────────────────────────────────────┘  │

│  ┌──────────────────────────────────────────────────────┐  │

│  │          Business Logic \\\& Services                    │  │

│  └──────────────────────────────────────────────────────┘  │

│  ┌──────────────────────────────────────────────────────┐  │

│  │    AI Engine (Chatbot, RAG, LLM, Embeddings)        │  │

│  └──────────────────────────────────────────────────────┘  │

└────────────────────────┬────────────────────────────────────┘

\&nbsp;                        │

┌────────────────────────┴────────────────────────────────────┐

│                   DATABASE (PostgreSQL)                      │

│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │

│  │ Patients │  │Medicines │  │Inventory │  │  Orders  │   │

│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │

│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │

│  │  Bills   │  │ Vendors  │  │  Chats   │  │  Alerts  │   │

│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │

└─────────────────────────────────────────────────────────────┘

```



---



\## 📦 Prerequisites



Before installation, ensure you have:



\- \*\*Python\*\*: 3.11 or higher

\- \*\*Node.js\*\*: 18 or higher

\- \*\*PostgreSQL\*\*: 14 or higher

\- \*\*Git\*\*: Latest version

\- \*\*OS\*\*: Windows 10/11, macOS, or Linux



\### Required Accounts



\- \*\*Groq API\*\*: Sign up at \[https://console.groq.com](https://console.groq.com) for free API access



---



\## 🚀 Installation



\### Step 1: Clone Repository



```bash

git clone https://github.com/your-username/smart-procurement-system.git

cd smart-procurement-system

```



\### Step 2: Database Setup



1\. \*\*Install PostgreSQL\*\* (if not installed)



2\. \*\*Create Database\*\*:

```sql

CREATE DATABASE procurement;

```



3\. \*\*Update credentials\*\* in `.env` file (see Configuration)



\### Step 3: Backend Setup



```bash

\\# Create virtual environment

python -m venv venv



\\# Activate virtual environment

\\# Windows:

venv\\\\Scripts\\\\activate

\\# macOS/Linux:

source venv/bin/activate



\\# Install dependencies

pip install -r requirements.txt



\\# Create missing tables

python scripts/create\\\_chat\\\_tables.py



\\# Populate database (if starting fresh)

python scripts/data\\\_pipeline.py



\\# Seed sample chat data (optional)

python scripts/seed\\\_chat\\\_data.py



\\# Verify setup

python scripts/verify\\\_tables.py

```



\### Step 4: Frontend Setup



```bash

\\# Navigate to frontend

cd frontend



\\# Install dependencies

npm install

```



---



\## ⚙️ Configuration



\### Environment Variables



Create/update `.env` file in project root:



```env

\\# Database Configuration

DATABASE\\\_URL=postgresql://postgres:your\\\_password@localhost:5432/procurement

DB\\\_HOST=localhost

DB\\\_PORT=5432

DB\\\_USER=postgres

DB\\\_PASSWORD=your\\\_password

DB\\\_NAME=procurement



\\# JWT Authentication

SECRET\\\_KEY=your-secret-key-here

ALGORITHM=HS256

ACCESS\\\_TOKEN\\\_EXPIRE\\\_MINUTES=1440



\\# AI/ML Configuration

GROQ\\\_API\\\_KEY=your-groq-api-key-here

MODEL\\\_NAME=llama-3.1-8b-instant

EMBEDDING\\\_MODEL=sentence-transformers/all-MiniLM-L6-v2



\\# Application Settings

DEBUG=True

ENVIRONMENT=development

API\\\_VERSION=v1

CORS\\\_ORIGINS=http://localhost:3000,http://localhost:5173



\\# Server

HOST=0.0.0.0

PORT=8000

```



\*\*Important\*\*: Replace `your\\\_password` and `your-groq-api-key-here` with actual values.



---



\## ▶️ Running the Application



\### Start Backend Server



```bash

\\# From project root with venv activated

python backend/main.py

```



\*\*Expected output:\*\*

```

✓ Knowledge base built with 405 documents

✓ Chatbot Engine initialized

Application startup complete.

Uvicorn running on http://0.0.0.0:8000

```



\### Start Frontend Development Server



Open a new terminal:



```bash

\\# Navigate to frontend

cd frontend



\\# Start dev server

npm run dev

```



\*\*Expected output:\*\*

```

\&nbsp; VITE v5.0.0  ready in 500 ms

\&nbsp; ➜  Local:   http://localhost:5173/

```



\### Access Application



Open browser and navigate to:

```

http://localhost:5173

```



---



\## 📖 Usage Guide



\### Default Login Credentials



| Role | Username | Password |

|------|----------|----------|

| Admin | admin | admin123 |

| Doctor | doctor\_1 | doctor123 |

| Pharmacist | pharmacist\_1 | pharma123 |

| Receptionist | receptionist\_1 | reception123 |

| Therapist | therapist\_1 | therapy123 |



\### Dashboard Overview



After login, you'll see:

\- \*\*Key Metrics\*\*: Patient count, revenue, low stock items, appointments

\- \*\*Revenue Breakdown\*\*: Consultation, medicine, treatment revenue

\- \*\*Quick Actions\*\*: Shortcuts to common tasks

\- \*\*Alerts\*\*: Low stock and expiry warnings



\### Inventory Management



1\. Navigate to \*\*Inventory\*\* in sidebar

2\. View all inventory items with real-time status

3\. Filter by:

   - All Items

   - Low Stock

   - Expiring Soon

4\. Search by medicine name

5\. Monitor expiry dates and quantities



\### AI Chatbot Assistant



1\. Click \*\*AI Assistant\*\* in sidebar

2\. Type queries in natural language

3\. Examples:

   - "What medicines are low in stock?"

   - "Show me expiring medicines"

   - "What was today's revenue?"

   - "How do I create a purchase order?"

   - "List all active vendors"



4\. Bot provides:

   - Intelligent responses

   - Suggested actions

   - Intent classification

   - Confidence scores



---



\## 📚 API Documentation



\### Interactive API Docs



Once backend is running, access Swagger UI:

```

http://localhost:8000/api/v1/docs

```



\### API Endpoints Overview



\#### Authentication

\- `POST /api/v1/auth/login` - User login

\- `GET /api/v1/auth/me` - Get current user

\- `POST /api/v1/auth/change-password` - Change password



\#### Inventory

\- `GET /api/v1/inventory/` - List inventory

\- `GET /api/v1/inventory/with-details` - Detailed inventory

\- `GET /api/v1/inventory/alerts/low-stock` - Low stock alerts

\- `GET /api/v1/inventory/alerts/expiring` - Expiring items

\- `GET /api/v1/inventory/stats/summary` - Statistics



\#### Chatbot

\- `POST /api/v1/chatbot/chat` - Send message

\- `GET /api/v1/chatbot/history/{session\\\_id}` - Conversation history

\- `GET /api/v1/chatbot/sessions` - User sessions

\- `GET /api/v1/chatbot/health` - Health check



\#### Reports

\- `GET /api/v1/reports/dashboard` - Dashboard data

\- `GET /api/v1/reports/financial` - Financial reports

\- `GET /api/v1/reports/inventory` - Inventory reports



\*Full API documentation available at `/api/v1/docs`\*



---



\## 🗄 Database Schema



\### Core Tables



1\. \*\*users\*\* - System users and authentication

2\. \*\*patients\*\* - Patient records

3\. \*\*medicines\*\* - Medicine catalog

4\. \*\*vendors\*\* - Vendor information

5\. \*\*inventory\_stock\*\* - Stock tracking with batches

6\. \*\*purchase\_orders\*\* - Purchase orders

7\. \*\*purchase\_order\_items\*\* - PO line items

8\. \*\*appointments\*\* - Patient appointments

9\. \*\*bills\*\* - Billing records

10\. \*\*treatments\*\* - Treatment types

11\. \*\*chat\_conversations\*\* - Chatbot history

12\. \*\*alerts\*\* - System notifications



\### Entity Relationships



```

patients ──┬── appointments ── bills

\&nbsp;          └── bills



medicines ──┬── inventory\\\_stock

\&nbsp;           └── purchase\\\_order\\\_items ── purchase\\\_orders ── vendors



users ── chat\\\_conversations

\&nbsp;     └── alerts

```



---



\## 🤖 AI Chatbot



\### How It Works



1\. \*\*User Input\*\*: User types query in natural language

2\. \*\*Intent Classification\*\*: Groq LLM identifies query type

3\. \*\*Context Retrieval\*\*: RAG pipeline searches knowledge base using FAISS

4\. \*\*Response Generation\*\*: LLM generates contextual response

5\. \*\*Action Suggestions\*\*: System provides relevant next steps



\### Knowledge Base



The chatbot's knowledge base includes:

\- All medicines and their details

\- Current inventory levels

\- Vendor information

\- FAQs and common procedures

\- System capabilities



\*\*Rebuild knowledge base\*\* after major data updates:

```bash

POST /api/v1/chatbot/rebuild-knowledge-base

```



\### Supported Intents



\- `inventory\\\_query` - Stock levels, availability

\- `procurement` - Purchase orders, vendors

\- `patient` - Patient records, appointments

\- `billing` - Bills, payments, revenue

\- `reports` - Statistics, analytics

\- `general` - Help, navigation



---



\## 🔧 Troubleshooting



\### Backend Issues



\*\*Issue\*\*: "Database connection failed"

```bash

\\# Check PostgreSQL is running

\\# Verify credentials in .env file

\\# Test connection:

psql -U postgres -d procurement

```



\*\*Issue\*\*: "Missing GROQ\_API\_KEY"

```bash

\\# Add API key to .env file

GROQ\\\_API\\\_KEY=your-key-here

\\# Restart backend

```



\*\*Issue\*\*: "Table does not exist"

```bash

\\# Run table creation scripts

python scripts/create\\\_chat\\\_tables.py

python scripts/data\\\_pipeline.py

```



\### Frontend Issues



\*\*Issue\*\*: "Cannot connect to backend"

```bash

\\# Ensure backend is running on port 8000

\\# Check no firewall blocking

\\# Verify proxy config in vite.config.js

```



\*\*Issue\*\*: "Module not found"

```bash

cd frontend

npm install

```



\### Chatbot Issues



\*\*Issue\*\*: "Knowledge base not built"

```bash

\\# Restart backend - it auto-builds on startup

\\# Or manually rebuild via API

```



\*\*Issue\*\*: "Slow responses"

```bash

\\# Groq API may be rate-limited

\\# Check internet connection

\\# Monitor backend logs for errors

```



---



\## 📊 Project Structure



```

smart-procurement-system/

├── backend/

│   ├── ai/                  # AI/ML modules

│   │   ├── embeddings.py

│   │   ├── rag\\\_pipeline.py

│   │   ├── llm\\\_service.py

│   │   └── chatbot\\\_engine.py

│   ├── api/

│   │   └── routes/         # API endpoints (11 modules)

│   ├── auth/               # Authentication

│   ├── config/             # Configuration

│   ├── models/             # Database models

│   ├── schemas/            # Pydantic schemas

│   ├── services/           # Business logic

│   ├── utils/              # Utilities

│   └── main.py             # Entry point

├── frontend/

│   ├── src/

│   │   ├── components/     # React components

│   │   ├── contexts/       # Context providers

│   │   ├── pages/          # Page components

│   │   ├── services/       # API services

│   │   ├── utils/          # Helper functions

│   │   ├── App.jsx         # Main app

│   │   └── main.jsx        # Entry point

│   └── package.json

├── scripts/                # Database scripts

├── .env                    # Environment variables

├── requirements.txt        # Python dependencies

└── README.md              # This file

```



---



\## 🎯 Future Enhancements



\- \[ ] WhatsApp integration for vendor communication

\- \[ ] Advanced demand forecasting with TensorFlow

\- \[ ] Mobile app (React Native)

\- \[ ] PDF report generation

\- \[ ] Email notifications

\- \[ ] Multi-clinic support

\- \[ ] Advanced analytics dashboard

\- \[ ] Voice interface for chatbot



---



\## 👥 Contributing



Contributions are welcome! Please follow these steps:



1\. Fork the repository

2\. Create a feature branch (`git checkout -b feature/AmazingFeature`)

3\. Commit changes (`git commit -m 'Add AmazingFeature'`)

4\. Push to branch (`git push origin feature/AmazingFeature`)

5\. Open a Pull Request



---



\## 📝 License



This project is licensed under the MIT License - see LICENSE file for details.



---



\## 🙏 Acknowledgments



\- \*\*Groq\*\* for LLM API access

\- \*\*FastAPI\*\* for excellent framework

\- \*\*React\*\* and \*\*Vite\*\* for frontend tools

\- \*\*FAISS\*\* for vector search capabilities



---



