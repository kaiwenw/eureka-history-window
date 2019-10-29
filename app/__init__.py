from flask import Flask


app = Flask(__name__, static_folder='static')

from app import logs
from app import routes
