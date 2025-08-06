from flask import Flask
from db import init_db
from pages import pages_bp
from api import api_bp
from routes_api.settings import settings_bp

# initiate database connection
init_db()

app = Flask(__name__)

app.register_blueprint(pages_bp)
app.register_blueprint(api_bp)
app.register_blueprint(settings_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5055)
