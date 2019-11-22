# -*- encoding: utf-8 -*-

import os


class Config(object):
	"""
	Configuration base, for all environments.
	"""
	DEBUG = False
	TESTING = False

	# DB credentials and settings
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_DATABASE_URI = 'postgresql://admin:Password123!@localhost:5432/paymentdb_dev'

	# Yandex wallet
	CLIENT_ID = '45A321453EFA1CAAD639F90AB7AD15FED338BD33291E26B63F968F5536F166B3'
	WALLET = '4100110431911287'


class ProductionConfig(Config):
	# Yandex wallet
	CLIENT_ID = os.environ.get('CLIENT_ID')
	WALLET = os.environ.get('WALLET')

	# DB credentials and settings
	POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
	POSTGRES_DB = os.environ.get('POSTGRES_DB', 'paymentdb')
	POSTGRES_USER = os.environ.get('POSTGRES_USER')
	POSTGRES_PORT = os.environ.get('POSTGRES_PORT', 5432)
	POSTGRES_IP = os.environ.get('POSTGRES_IP', 'localhost')
	SQLALCHEMY_DATABASE_URI = 'postgresql://{0}:{1}@{4}:{2}/{3}'.format(
		POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_DB, POSTGRES_IP)

class DevelopmentConfig(Config):
	DEBUG = True

class TestingConfig(Config):
	TESTING = True
