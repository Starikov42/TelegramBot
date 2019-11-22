# -*- coding: utf-8 -*-

import urllib
import time
import logging
from datetime import datetime

from yandex_money.api import Wallet, ExternalPayment

from app import db_session


logger = logging.getLogger()

def request_external_payment(instance_id, amount, wallet):
    logger.debug('Requesting exteranl payment')
    external_payment = ExternalPayment(instance_id)

    payment_options = {
        'pattern_id': 'p2p',
        'instance_id': instance_id,
        'to': wallet,
        'amount': amount,
        'message': 'Оплата бота'
    }
    request_id = None
    response = external_payment.request(payment_options)
    logger.debug('Reposnse from external_payment.request : {0}'.format(response))
    if response['status'] == "success":
        request_id = response['request_id']
    else:
        logger.error('Failed to get request_id. Reason: {0}'.format(response))
    return request_id

def process_external_payment(instance_id, request_id, auth_success_uri, auth_fail_uri):
    logger.debug('Processing exteranl payment')
    external_payment = ExternalPayment(instance_id)
    process_options = {
        "request_id": request_id,
        'instance_id': instance_id,
        'ext_auth_success_uri': auth_success_uri,
        'ext_auth_fail_uri': auth_fail_uri
    }
    response = external_payment.process(process_options)
    logger.debug('Response from external_payment.process : {0}'.format(response))
    if response['status'] == 'ext_auth_required':
        acs_uri = response['acs_uri']
        acs_params = response['acs_params']
        return response['status'], '{0}?{1}'.format(acs_uri, urllib.parse.urlencode(acs_params))

    return response['status'], None
        