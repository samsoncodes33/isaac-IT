import os
from dotenv import load_dotenv
from datetime import timedelta


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'), override=True)

# creating a configuration class
class Config(object):
    MONGO_URI =  os.environ.get('MONGO_URI')
    