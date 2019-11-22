# -*- encoding: utf-8 -*-

import os
import threading
import logging
from flask import request, jsonify, make_response, abort, redirect

from app import app, db_session, INSTANCE_ID
from app.models import Payment, PaymentStatus, Notification


logger = logging.getLogger()

REDIRECT_BOT_URL = 'https://t.me/referral_tgBot'

@app.route('/payment', methods=['POST'])
def create_payment():
    """ Create payment endpoint
    """
    logger.debug('Request for paymnet creation')
    if not request.json or 'amount' not in request.json or 'merchant_id' not in request.json:
        logger.debug('Not enough data to serve the request! Request data: {0}'.format(request.json))
        abort(400)

    amount = request.json['amount']
    merchant_id = request.json['merchant_id']
    payment = Payment.create_payment(merchant_id, amount, INSTANCE_ID, app.config['WALLET'])
    logger.debug('Payment {0} created'.format(payment))
    if not payment:
        return jsonify({'error': 'Failed to create payment instance'}), 420
    
    return jsonify({'payment_url': payment.payment_url, 'id': payment.payment_id}), 201


@app.route('/payment/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    """ Get payment information
    """
    payment = db_session.query(Payment).get(payment_id)
    if payment:
        return payment, 200
    abort(404)
    

@app.route('/payment/<payment_id>/notify', methods=['POST'])
def create_notification(payment_id):
    """ Notify about payment status
    """
    payment = db_session.query(Payment).get(payment_id)
    if not payment:
        abort(404)
    
    if not request.json or 'notification_url' not in request.json:
        logger.debug('Not enough data to create notification! Request data: {0}'.format(request.json))
        abort(400)
    
    if payment.status in [PaymentStatus.timeout, PaymentStatus.success, PaymentStatus.refused]:
        logger.debug('Payment has already finished')
        return jsonify({'error': 'Payment has already finished'}), 400
        
    user_data = request.json.get('user_data', {})
    notification = Notification(payment.payment_id, request.json.get('notification_url'), user_data)
    payment.notifications.append(notification)
    db_session.add(payment)
    db_session.commit()
    return jsonify({'id': notification.notification_id}), 201


@app.route('/handle-payment', methods=['POST', 'GET'])
def handle_payment():
    """ Handle payment redirect from payment page
    """
    logger.debug('Handling payment with request data {0}'.format(request.args))
    request_id = request.args.get('cps_context_id', 'None')
    payment = db_session.query(Payment).get(request_id)
    if not payment:
        logger.error('Handling not existing payment! Aborting.')
        abort(404)
    
    if request.args.get('status') != 'success':
        logger.warning('Receive unsuccessfull payment {0}'.format(payment))
        payment.status = PaymentStatus.refused
        db_session.add(payment)
        db_session.commit()
        Payment.notify(payment.payment_id)
        return redirect(REDIRECT_BOT_URL)
    
    logger.debug('Starting polling thread for payment {0}'.format(payment))
    thread = threading.Thread(target=Payment.poll_payment, 
                              args=(INSTANCE_ID, request_id))
    thread.start()
        
    return redirect(REDIRECT_BOT_URL)
    
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)

