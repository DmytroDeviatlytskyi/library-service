# Library Service API

API service for Library management written on DRF and Dockerized


# Installing using GitHub

Install PostgresSQL and create db


```shell
git clone https://github.com/DmytroDeviatlytskyi/library-service.git
cd library-service
python -m venv .venv
source .venv\bin\activate
pip install -r requirements.txt
set DB_HOST=<your db hostname>
set DB_NAME=<your db name>
set DB_USER=<your db username>
set DB_PASSWORD=<your db user password>
set SECRET_KEY=<your secret key>
set BOT_TOKEN=<your bot-token>
set CHAT_ID=<your chat-id>
python manage.py migrate
python manage.py runserver
```


# Run with docker

Docker should be installed (you can download it here: https://www.docker.com/)

```shell
docker-compose build
docker-compose up
```
- Create new admin user. ```docker-compose run library sh -c "python manage.py createsuperuser"```;
- Run tests using different approach: ```docker-compose run library sh -c "python manage.py test"```;


# Features

- JWT authentication
- Documentation located at `/api/v1/doc/swagger/`
- Admin panel available at `/admin/`
- CRUD books
- Receiving notifications in TG when creating new borrowings
- Filtering borrowings by is_active: (?is_active=true)
- Filtering borrowings by user_id for admin users: (?user_id=2)
