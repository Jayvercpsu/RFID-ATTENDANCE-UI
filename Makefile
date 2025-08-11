run-local:
	cd flask && python app.py

start-local:
	cd flask && python app.py

py-install:
	pip install -r flask/requirements.txt

# migrations
seed-users:
	cd flask && python migrations/seed_users.py
