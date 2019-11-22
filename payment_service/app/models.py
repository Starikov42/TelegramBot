# -*- coding: utf-8 -*-

import logging
import time
from datetime import datetime
import enum

import requests
from yandex_money.api import Wallet, ExternalPayment

from app.src import utils
from . import db, db_session
from . import APPLICATION_IP, RESERVE_PROXY_PORT

logger = logging.getLogger()


class PaymentStatus():
    success = 'success'
    refused = 'refused'
    in_progress = 'in_progress'
    ext_auth_required = 'ext_auth_required'
    timeout = 'timeout'


class Payment(db.Model):
    __tablename__ = 'payments'
    __table_args__ = {'extend_existing': True}

    payment_id = db.Column(db.String, primary_key=True)
    merchant_id = db.Column(db.BigInteger, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, nullable=False)
    finish_datetime = db.Column(db.DateTime, nullable=True)
    start_datetime = db.Column(db.DateTime, nullable=False)
    payment_url = db.Column(db.String, nullable=True)
    
    notifications = db.relationship('Notification', backref='payment')
    
    AUTH_SUCCESS = 'http://{0}:{1}/handle-payment'.format(APPLICATION_IP, RESERVE_PROXY_PORT)
    AUTH_FAIL = 'http://{0}:{1}/handle-payment'.format(APPLICATION_IP, RESERVE_PROXY_PORT)

    def __init__(self, payment_id, merchant_id, amount, status, payment_url):
        self.payment_id = payment_id
        self.merchant_id = merchant_id
        self.amount = amount
        self.status = status
        self.payment_url = payment_url
        self.start_datetime = datetime.now()

    def __repr__(self):
        return '<Payment {0} ({1})>'.format(self.payment_id, self.status)
    
    def as_dict(self):
        return {
            'payment_id': self.payment_id,
            'merchant_id': self.merchant_id,
            'amount': self.amount,
            'status': self.status,
            'payment_url': self.payment_url,
        }
    
    @classmethod
    def notify(cls, payment_id):
        payment = db_session.query(cls).get(payment_id)
        logger.debug('Sending notifications for payment {0}'.format(payment))
        for notification in payment.notifications:
            logger.debug('Sending notification {0}'.format(notification))
            try:
                data = {'status': payment.status, 'user_data': notification.user_data}
                requests.post(notification.notification_url, json=data, verify=False)
            except Exception as err:
                logger.error('Failed to send notification. Reason: {0}'.format(err))
    
    @classmethod
    def create_payment(cls, merchant_id, amount, instance_id, wallet):
        # TODO: DEBUG CASHED PAYMENTS
        # cashed_payment = get_cashed_payment(merchant_id, amount)
        # if cashed_payment:
        #     return cashed_payment
            
        request_id = utils.request_external_payment(instance_id, amount, wallet)
        if not request_id:
            logger.error('Error while getting request_id from yandex. Aborting.')
            return None
            
        status, payment_url = utils.process_external_payment(instance_id, request_id, 
                                                             Payment.AUTH_SUCCESS, Payment.AUTH_FAIL)
        if not payment_url:
            logger.error('Failed to get payment_url from yandex')
            return None
        
        payment_instance = cls(request_id, merchant_id, amount, status, payment_url)
        db_session.add(payment_instance)
        db_session.commit()
        
        return payment_instance
    
    @classmethod
    def poll_payment(cls, instance_id, request_id, retries=120, sleep_time=1):
        logger.debug('Starting polling payment with request_id {0}'.format(request_id))
        
        payment = db_session.query(cls).get(request_id)
        status = None
        for i in range(retries):
            status, _ = utils.process_external_payment(instance_id, request_id, cls.AUTH_SUCCESS, cls.AUTH_FAIL)
            logger.info('<{0}>: Processing external payment, received status {1}'.format(i, status))
            
            if status == PaymentStatus.refused or status == PaymentStatus.success:
                logger.debug('Receive expected status {0}'.format(status))
                payment.status = status
                payment.finish_datetime = datetime.now()
                break
                
            time.sleep(sleep_time)
        
        if not status:
            status = PaymentStatus.timeout
            logger.debug('Failed to get expected status, setting {0} status'.format(status))
            payment.finish_datetime = datetime.now()
            payment.status = status

        db_session.add(payment)
        db_session.commit()
        cls.notify(payment.payment_id)
        return status


class Notification(db.Model):
    __tablename__ = 'norifications'
    __table_args__ = {'extend_existing': True}

    notification_id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String, db.ForeignKey('payments.payment_id'), nullable=False)
    notification_url = db.Column(db.String, nullable=False)
    user_data = db.Column(db.JSON)
    
    def __init__(self, payment_id, notification_url, user_data=None):
        self.payment_id = payment_id
        self.notification_url = notification_url
        self.user_data = user_data

    def __repr__(self):
        return '<Notification {0} with data {1}>'.format(self.notification_id, self.user_data)


def get_cashed_payment(merchant_id, amount):
    payment = db_session.query(Payment).filter(Payment.merchant_id == merchant_id, 
                                               Payment.amount == amount, 
                                               Payment.status.in_((PaymentStatus.in_progress, 
                                                                   PaymentStatus.ext_auth_required))).first()
    if payment:
        logger.debug('Found cashed payment <{0}>'.format(payment.payment_id))
        response = requests.get(payment.payment_url)
        if response.status_code != 302:
            logger.debug('Payment link is active. Returning cashed payment')
            return payment

        logger.debug('Payment link is expired. Need new one')
        payment.status = PaymentStatus.timeout
        payment.finish_datetime = datetime.now()
        db_session.add(payment)
        db_session.commit()
    
    logger.debug('Failed to find cashed payment')
    return None