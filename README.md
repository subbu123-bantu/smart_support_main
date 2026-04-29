# Smart Support

Smart Support is a full-stack support ticket platform built with Django REST Framework and React. It combines role-based ticket workflows with a hybrid AI classification pipeline that predicts ticket category, assigns priority, flags low-confidence submissions for manual review, and helps route tickets to the right agent.

## What the project does

- Authenticates users with JWT-based login and protected APIs
- Supports three roles: `customer`, `agent`, and `admin`
- Lets customers create tickets with live AI prediction preview
- Lets admins and agents manage ticket status and workflow
- Auto-assigns tickets to available agents by matching category and workload
- Stores prediction history and exposes feedback/accuracy endpoints
- Sends email notifications for password reset, ticket creation, and ticket updates

## Current frontend experience

The React frontend currently ships with these routes:

- `/login`
- `/register`
- `/forgot-password`
- `/reset-password`
- `/dashboard`
- `/tickets`
- `/tickets/:id`
- `/create-ticket`
- `/settings/email`

Role access today is enforced through `PrivateRoute` and backend permissions:

- `customer`: can create tickets, view their own tickets, comment on tickets, and update email
- `agent`: can view only assigned tickets, update status/priority on assigned tickets, comment, and update email
- `admin`: can view all tickets, assign tickets, manage categories/agents through API access, review dashboard stats, and update email

Note: the current UI does not have separate `/support` or `/admin` pages. The main authenticated landing area is `/dashboard`, with ticket operations centered around `/tickets`.

## AI workflow

The AI layer is implemented in `backend/tickets/ai/` and currently uses a hybrid approach:

- rule-based category scoring
- keyword fallback matching
- Groq-backed AI classification
- conflict overrides for ambiguous inputs
- category-specific priority assignment
- confidence thresholding and manual-review flags

The prediction API returns:

```json
{
  "predicted_category": "billing",
  "predicted_priority": "high",
  "category_confidence": 0.91,
  "source": "rule+AI",
  "needs_manual_review": false
}
```

When a ticket is created:

1. The title and description are combined and sent through the prediction pipeline.
2. The predicted category is stored or created in the `Category` table.
3. The predicted priority is saved on the ticket.
4. A `TicketPredictionLog` entry is recorded.
5. The system attempts auto-assignment to an available agent with matching category expertise.
6. A ticket-created email is queued through Celery.

When tickets are updated by admin or agent users, prediction feedback is refreshed so actual category/priority can be compared against the original prediction.

## Backend API

Base path: `/api/`

### Authentication and user endpoints

- `POST /api/login/`
- `POST /api/logout/`
- `POST /api/register/`
- `POST /api/forgot-password/`
- `POST /api/reset-password/`
- `PATCH /api/change-email/`
- `GET /api/agents/`
- `PATCH /api/agents/<agent_id>/`

### Ticket endpoints

- `GET|POST /api/tickets/`
- `GET|PUT|PATCH /api/tickets/<id>/`
- `GET /api/categories/`
- `POST /api/predict/`
- `GET /api/stats/`
- `GET /api/prediction-stats/`
- `PATCH /api/tickets/<ticket_id>/assign/`
- `GET|POST /api/tickets/<ticket_id>/comments/`
- `DELETE /api/tickets/<ticket_id>/comments/<comment_id>/`
- `GET /api/tickets/<ticket_id>/prediction-feedback/`
- `GET /api/test/`

## Key backend behavior

- `TicketViewSet` restricts data by role:
  - admins see all tickets
  - agents see only assigned tickets
  - customers see only their own tickets
- customers can create tickets but cannot update them
- agents can only update `status` and `priority` on tickets assigned to them
- ticket deletion is blocked
- admin users can assign a ticket to a specific agent or trigger auto-assignment
- comment visibility is role-aware and supports internal notes
- dashboard stats are role-aware, with richer analytics for admin users

## Dashboard and analytics

The current dashboard uses backend stats from `/api/stats/` and includes role-aware metrics such as:

- total, open, in-progress, and closed ticket counts
- category distribution
- priority distribution
- tickets created over the last 7 days
- agent workload and average resolution time for admin users

## Notifications and async work

The backend already includes Celery integration and email notifications:

- password reset emails
- ticket created emails
- ticket status update emails

Email sending is implemented through Brevo, and Celery is configured with Redis as the broker.

## Tech stack

### Frontend

- React 19
- React Router
- Axios
- Tailwind CSS
- Recharts
- React Toastify

### Backend

- Django 6
- Django REST Framework
- SimpleJWT
- PostgreSQL
- django-filter
- Celery
- Redis

### AI and processing

- Groq API integration
- rule-based classification helpers
- keyword-based fallback logic
- category-specific priority rules

## Project structure

```text
subrahmanyam/
|-- backend/
|   |-- core/
|   |-- tests/
|   |-- tickets/
|   |   |-- ai/
|   |   |-- services/
|   |   |-- models.py
|   |   |-- serializers.py
|   |   |-- tasks.py
|   |   |-- urls.py
|   |   `-- views.py
|   |-- users/
|   |   |-- models.py
|   |   |-- permissions.py
|   |   |-- serializers.py
|   |   |-- urls.py
|   |   `-- views.py
|   |-- manage.py
|   `-- requirements.txt
|-- frontend/
|   |-- public/
|   |-- src/
|   |   |-- components/
|   |   |-- constants/
|   |   |-- pages/
|   |   |-- services/
|   |   |-- utils/
|   |   |-- __tests__/
|   |   |-- App.jsx
|   |   `-- index.js
|   `-- package.json
`-- README.md
```

## Local development

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Redis

### Backend setup

```bash
cd backend
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Create your own local `backend/.env` file and keep it untracked. Add the values your environment needs, including:

- `SECRET_KEY`
- `DEBUG`
- `DB_ENGINE`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD_LOCAL`
- `DB_HOST`
- `DB_PORT`
- `FRONTEND_URL`
- `GROQ_API_KEY`
- `BREVO_API_KEY`
- `BREVO_SMTP_USER`
- `BREVO_SMTP_PASS`
- `BREVO_SENDER_EMAIL`

To run background email jobs locally:

```bash
cd backend
celery -A core worker -l info --pool=solo
```

### Frontend setup

```bash
cd frontend
npm install
npm start
```

If needed, set `REACT_APP_API_BASE_URL` so the frontend points to the correct backend origin.

## Testing

### Backend

```bash
cd backend
python manage.py test tests
```

### Frontend

```bash
cd frontend
npm test -- --coverage --watchAll=false --runInBand --passWithNoTests
```

The frontend test suite currently covers routing, auth pages, dashboard helpers, ticket flows, comments, services, and web vitals.

## CI

GitHub Actions is configured in `.github/workflows/build.yml` to:

- start PostgreSQL for CI
- run backend migrations and tests with coverage
- run frontend tests with coverage
- upload coverage artifacts
- publish SonarCloud analysis when credentials are available

## Current status

Implemented and working end-to-end today:

- JWT login, logout, registration, password reset, and email change
- role-aware ticket listing and permissions
- ticket creation with AI prediction
- admin assignment and auto-assignment logic
- ticket comments with internal-note support
- prediction logging and feedback evaluation
- dashboard stats and charts support
- email notifications through Celery
- backend and frontend automated tests

## Planned improvements

- dedicated admin and agent management screens in the frontend
- richer prediction review and model evaluation UX
- better operational visibility around queue and email delivery
- Docker-based local setup
- production deployment configuration
- stronger observability and audit logging

## Author

Subrahmanyam

Built to explore secure authentication, role-based SaaS workflows, API-first Django architecture, and practical AI integration inside a real support system.
