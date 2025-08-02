from flask import Flask
from pages import pages_bp 

app = Flask(__name__)

app.register_blueprint(pages_bp)

if __name__ == '__main__':
    app.run(debug=True)
