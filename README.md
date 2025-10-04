## Бейджик workflow: ##
[![Main Foodgram workflow](https://github.com/Marakes/foodgram/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/Marakes/foodgram/actions/workflows/main.yml)


## Summary: ##
    Привет! 
_Данный проект - Cервис для любителей готовки самых различных блюд. Здесь можно делиться своими рецептами, подписываться на интересных вам людей и скачать готовый список покупок - удобно!_ 

**Проект разработан на Django Rest Framework. Деплой через GitHub Actions в контейнерах Docker.**

**Проект может быть полезен для тех, кто изучает Django, DRF, Docker, CI/CD и Postgres или в качестве основы для собственного проекта.**

_Даже имеются необходимые тесты на pytest!!!_

_В общем - пользуйтесь, кому понадобится!)_

---

## Стек технологий: ##

- **Python 3.11+**
- **Django 5.2.6**
- **Django REST Framework 3.16.1**
- **Psycopg2-binary 2.9.9**
- **Djoser 2.3.3**
- **Pytest 8.3.3**

Список необходимых зависимостей см. в (requirements.txt)
Список зависимостей для тестов см. в (requirements-dev.txt)

---

## **_Как запустить проект:_** ##

**_Клонировать репозиторий и перейти в него в командной строке:_**

    git clone https://github.com/Marakes/foodgram

    cd foodgram

## Создать .env файл в корне проекта: ##

    POSTGRES_DB=test_db
    POSTGRES_USER=test_user
    POSTGRES_PASSWORD=test_password
    DB_NAME=test
    DB_HOST=db
    DB_PORT=5432
    
    DEBUG=False
    DJANGO_SECRET=secret_key
    ALLOWED_HOSTS=localhost,127.0.0.1
    SQLITE_ON=False

    STATIC_ROOT=/backend_static
    MEDIA_ROOT=/media

**_Создать и запустить контейнеры (нужен установленный docker):_**

    docker compose up -d

**_Применить миграции и собрать статику:_**

    docker compose exec backend python manage.py migrate

    docker compose exec backend python manage.py collectstatic
    

**_Проверить работу:_**

   API: http://127.0.0.1:8000/api/
	
   Админка: http://127.0.0.1:8000/admin/
	
   Фронтенд: http://127.0.0.1:8000

---

### Деплой на сервере (CI/CD): ###

**Используется GitHub Actions, DockerHub, сервер с Docker Compose**

  1) Push в ветку main -> прогоняются тесты
  2) Собираются образы (backend, frontend, gateway)
  3) Пушатся в DockerHub
  4) По ssh разворачиваются на сервере

---




## Автор проекта: ##

Невероятный и непревзойдённый (как и все) студент Яндекс Практикума :)

https://github.com/Marakes
