import os
from flask import Flask, request
from config import Config
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from flask_restful import Api
from flask_cors import CORS


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

#Initialise Flask
app = Flask(__name__, static_folder='../static', template_folder='templates')
app.config.from_object(Config)

# Instantiate the cors library
cors = CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"], allow_headers='*')

# Create a flask restful api instance
api = Api(app, catch_all_404s=True)

# Mongodb setup
mongo = PyMongo(app=app, uri=Config.MONGO_URI)


from app import SIFMS