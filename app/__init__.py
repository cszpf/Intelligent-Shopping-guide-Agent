from flask import Flask
from config import Config
from flask_bootstrap import Bootstrap
import sys
sys.path.append('app/backend')
sys.path.append('app/backend/NLU')
bootstrap = Bootstrap()

app = Flask(__name__)
app.config.from_object(Config)
from app import routes
