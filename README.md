# Smart Support — AI-Powered Ticket Automation System

## Overview

This project is a *full-stack AI-powered support ticket platform* that allows authenticated users to submit support requests and enables admins to manage tickets and users through a clean, role-based interface.

The system uses *AI-driven classification, sentiment analysis, and priority assignment* to automatically categorize and route tickets without manual intervention.

The platform is designed with *security-first authentication, **clean separation of concerns, and a **scalable full-stack architecture*, reflecting real-world Django + React + AI integration.

---

## Key Features

### Authentication & Security
- Custom *JWT authentication* with role-based access control
- Secure login, logout, and signup flow
- Role-based routing — customers go to /support, agents go to /tickets, admins go to /admin
- Protected backend APIs using Django REST Framework permissions
- Frontend route protection via authorization checks on every page load

### AI Support Engine
- Automatic ticket classification into predefined categories (billing, technical, account, etc.)
- Sentiment analysis on ticket content — detects frustration, urgency, and tone
- Priority assignment combining category + sentiment:
  - Low / Medium / High / Critical
- Structured output from the AI module:
  ```json
  {
    "category": "...",
    "sentiment_score": 0.0,
    "priority": "..."
  }
  ```

### AI Escalation & Ticketing
- Sentiment analysis detects user frustration or negative intent
- Low-confidence or high-negativity submissions trigger automatic escalation
- Support ticket is created and stored in PostgreSQL
- Ticket includes:
  - user email
  - query / description
  - timestamp
  - assigned agent
  - ticket status
- Tickets are assigned to available support staff automatically
- Ticket lifecycle:
  - `open` → `in_progress` → `resolved`

### Admin Panel
- Admin-only management at /admin
- Full user management — view, activate, deactivate accounts
- Ticket overview with filtering by status, priority, and category
- Assign tickets to agents manually or let the system auto-assign
- Monitor agent workload and ticket resolution rates

### Frontend
- Built with React.js
- Secure API communication via Django REST Framework
- Client-side authentication and role checks
- Ticket submission form with real-time AI classification preview
- Chat-style ticket thread view for back-and-forth communication
- Auto-scroll to latest message in ticket thread
- Clean login, signup, support, and admin page flow

### Backend
- Django REST Framework with custom authentication
- PostgreSQL database
- ViewSets and DefaultRouter for clean URL generation
- Clean separation between authentication, business logic, and AI integration
- Background processing for non-blocking AI classification

---

## Architecture

```
Browser (Customer / Agent / Admin)
        ↓
React.js Frontend (UI)
        ↓
Django REST API (Authentication + Business Logic)
        ↓
AI Pipeline
  ├── Category Classification
  ├── Sentiment Analysis
  └── Priority Assignment
        ↓
Confidence Evaluation
   ├── High Confidence → Auto-assign & notify
   └── Low Confidence → Escalation flag set
        ↓
Support Ticket System
        ↓
Agent Assignment Logic
        ↓
PostgreSQL Database
```

---

## Technology Stack

### Frontend
- React.js
- JavaScript
- Fetch API

### Backend
- Django
- Django REST Framework
- PostgreSQL
- SimpleJWT
- threading (background AI processing)

### AI / ML
- Python NLP pipeline (classification + sentiment)
- Scikit-learn / HuggingFace (configurable)
- FAISS (planned — for knowledge base RAG)

---

## Authentication Flow

1. User submits username and password via `/api/v1/login/`
2. Django authenticates and issues a JWT access token
3. Django returns the user's role (`customer`, `agent`, or `admin`) in the response body
4. Frontend redirects based on role — customers to `/support`, agents to `/tickets`, admins to `/admin`
5. Every protected API request verifies the JWT signature and resolves `request.user`
6. Logout clears the token client-side and invalidates the session server-side

---

## How the AI Works

1. User submits a ticket from the support page
2. Ticket is sent to Django via the REST API
3. Django authenticates the user and saves the ticket to PostgreSQL
4. The AI engine processes the ticket description:
   - Classifies the category
   - Scores the sentiment
   - Assigns a priority level
5. The system evaluates the confidence of the classification
6. If confidence is high — ticket is auto-assigned and the agent is notified
7. If confidence is low or sentiment is highly negative:
   - Escalation flag is set
   - Admin is notified for manual review
8. The updated ticket is returned to the frontend

The AI module only processes based on the ticket content, ensuring controlled and explainable output.

---

## Project Structure

```
smart-support/
│
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   │
│   ├── core/                      # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   │
│   ├── users/                     # Custom User model & JWT auth
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── tickets/                   # Ticket models, serializers, views
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   └── ai_engine/                 # AI classification & sentiment logic
│       ├── classifier.py
│       ├── sentiment.py
│       └── priority.py
│
├── frontend/
│   ├── src/
│   │   ├── components/            # Reusable UI components
│   │   ├── pages/                 # Route-level views
│   │   │   ├── Login.js
│   │   │   ├── Signup.js
│   │   │   ├── Support.js         # Customer ticket submission
│   │   │   ├── Tickets.js         # Agent ticket management
│   │   │   └── Admin.js           # Admin dashboard
│   │   ├── services/              # API call abstractions
│   │   └── App.js
│   │
│   ├── package.json
│   └── README.md
│
└── README.md
```

---

## Running the Project (Development)

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL running locally

### Backend

```bash
cd backend
python -m venv env
source env/bin/activate      # Windows: env\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm start
```

---

## Current Status

- Authentication — login, logout, signup, session validation
- Role-based routing — customers, agents, and admins
- Secure JWT authentication
- Ticket CRUD APIs
- PostgreSQL integration
- AI classification integration (basic)
- Sentiment analysis for detecting user dissatisfaction
- Automatic priority assignment
- Role-based access control
- Django Admin panel configuration

---

## Planned Enhancements

- [ ] React frontend full integration with all backend APIs
- [ ] Agent dashboard for ticket management
- [ ] Ticket resolution workflow UI
- [ ] User feedback collection after resolution
- [ ] Admin monitoring dashboard for agent performance
- [ ] Advanced filtering by status, category, and priority
- [ ] Dashboard analytics with charts
- [ ] AI auto-reply suggestion
- [ ] SLA breach prediction
- [ ] Redis + Celery for async AI processing
- [ ] Dockerization
- [ ] Production deployment (AWS / Azure)
- [ ] CI/CD pipeline

---

## Author

**Subrahmanyam**

This project was built to deeply understand:
- Secure authentication internals
- Frontend–backend communication patterns
- AI system integration into business workflows
- Real-world SaaS architecture and database modeling
- Role-based access and permission systems

---

## License

Currently for educational and demonstration purposes.
A license can be added if the project is open-sourced or deployed publicly.

---

*Active development. Core architecture, authentication, AI integration, and ticket management are stable and working end-to-end.*