# Foodgram
 
A recipe sharing platform. Publish recipes, follow other cooks, and download a ready-made shopping list.  
Deployed via GitHub Actions + Docker Compose.
 
## Features
 
- Recipe management with ingredients and tags
- REST API (Django REST Framework)
- JWT authentication (Djoser)
- Follow system between users
- Shopping list export
- PostgreSQL in production, SQLite for local dev
- Pytest test suite
- Full CI/CD pipeline: test → build → push → deploy

## Tech Stack

- **Python 3.11+**
- **Django 5.2.6**
- **Django REST Framework 3.16.1**
- **PostgreSQL (psycopg2-binary) 2.9.9**
- **Djoser 2.3.3**
- **Pytest 8.3.3**
- **Docker, Docker Compose, GitHub Actions**

Dependencies: `requirements.txt` · Dev/test dependencies: `requirements-dev.txt`
 
## How to Run Locally
 
```bash
# Clone the repository
git clone https://github.com/Marakes/foodgram
cd foodgram
```
 
Create `.env` in the project root:
 
```env
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=your_password
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432
 
DEBUG=False
DJANGO_SECRET=your_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1
SQLITE_ON=False
STATIC_ROOT=/backend_static
MEDIA_ROOT=/media
```
 
```bash
# Build and start containers
docker compose up -d
 
# Apply migrations and collect static
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
```
 
Once running:
 
| Service | URL |
|---|---|
| Frontend | http://127.0.0.1:8000 |
| API | http://127.0.0.1:8000/api/ |
| Admin | http://127.0.0.1:8000/admin/ |
 
## CI/CD
 
GitHub Actions pipeline triggered on push to `main`:
 
1. Run tests
2. Build Docker images — `backend`, `frontend`, `gateway`
3. Push images to DockerHub
4. Deploy to server via SSH using Docker Compose

## Author
 
[github.com/Marakes](https://github.com/Marakes)
