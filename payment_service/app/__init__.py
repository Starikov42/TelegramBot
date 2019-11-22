# -*- encoding: utf-8 -*-

import os
import sys
import logging

from yandex_money.api import Wallet, ExternalPayment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask import Flask


APPLICATION_IP = os.environ.get('APPLICATION_IP')
APPLICATION_PORT = int(os.environ.get('APPLICATION_PORT'))

# By default application is listenning at APPLICATION_IP on APPLICATION_PORT, 
#  but it may be served by reserve proxy at APPLICATION_IP on RESERVE_PROXY_PORT
RESERVE_PROXY_PORT = os.environ.get('RESERVE_PROXY_PORT')
if not RESERVE_PROXY_PORT:
    RESERVE_PROXY_PORT = APPLICATION_PORT

#! Flask application initialization
app = Flask('payment_service')

FORMAT = u'%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s'
root = logging.getLogger()
logging.basicConfig(format=FORMAT, level=logging.DEBUG,
                    handlers=[logging.FileHandler('/var/log/payment_service.log.debug',
                                                  encoding='utf-8')])

sHandler = logging.StreamHandler()
sHandler.setFormatter(logging.Formatter(FORMAT))

from app.configuration import ProductionConfig, DevelopmentConfig, Config

#!PRODUCTION CONFIGURATION
if os.environ.get('PRODUCTION'):
    app.config.from_object(ProductionConfig())
    sHandler.setLevel(logging.INFO)
    root.addHandler(sHandler)

#! DEBUG CONFIGURATION
else:
    app.config.from_object(DevelopmentConfig())
    sHandler.setLevel(logging.DEBUG)
    root.addHandler(sHandler)

INSTANCE_ID = None
response = ExternalPayment.get_instance_id(app.config['CLIENT_ID'])
if response['status'] == "success":
    INSTANCE_ID = response['instance_id']
else:
    raise Exception('Failed to get instance_id. Reason: {0}'.format(response['error']))    

db = SQLAlchemy(app)
db_session = db.session

from app.models import *
migrate = Migrate(app, db)

from app.views import *
