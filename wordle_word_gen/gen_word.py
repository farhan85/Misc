import boto3
import dateutil.tz
import json
import os
import random
import time
from datetime import datetime
from urllib.error import HTTPError
from urllib.request import urlopen, Request


PST = dateutil.tz.gettz('America/Los_Angeles')
ALL_WORDS_S3_KEY = 'all_words.txt'
LATEST_WORD_S3_KEY = 'latest.txt'


def send_to_slack(webhook_url, message):
    data = json.dumps({'message': message}).encode('utf-8')
    request = Request(webhook_url, data=data)
    request.add_header('Content-Type', 'application/json; charset=utf-8')
    request.add_header('Content-Length', len(data))
    try:
        with urlopen(request) as response:
            print('Sent to Slack. Response: {} {}'.format(response.getcode(), response.reason))
    except HTTPError as e:
        print(f'Slack API Error {e.code}: {e.read().decode()}')
        raise


def send_to_signal(ssm, ssm_document_name, account, group_id, message):
    ssm.send_command(
        DocumentName=ssm_document_name,
        Targets=[{'Key': 'tag:Name', 'Values': ['signal-message-sender']}],
        Parameters={
            'account': [account],
            'groupId': [group_id],
            'message': [message]
        })


def send_to_telegram(token, chat_id, message):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = json.dumps({
        'chat_id': chat_id,
        'text': message
    }).encode('utf-8')
    request = Request(url, data=data)
    request.add_header('Content-Type', 'application/json; charset=utf-8')
    request.add_header('Content-Length', str(len(data)))
    try:
        with urlopen(request) as response:
            print('Sent to Telegram. Response: {} {}'.format(response.getcode(), response.reason))
    except HTTPError as e:
        error_message = json.loads(e.read().decode()).get('description')
        print(f'Telegram API Error {e.code}: {error_message}')
        raise


def random_word(s3, bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    words = list(line for line in response['Body'].iter_lines() if len(line) == 5)
    return random.sample(words, 1)[0].decode().upper()


def set_current_word(s3, bucket, key, word):
    s3.put_object(Body=word, Bucket=bucket, Key=key)


def get_current_word(s3, bucket, key):
    return s3.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')


def is_monday(dt):
    return dt.weekday() == 0


def is_weekday(dt):
    return dt.weekday() < 5


def handler(event, context):
    print('Event:', event)
    bucket = os.environ['S3_BUCKET']
    ssm_document_name = os.getenv('SIGNAL_SENDER_DOCUMENT_NAME')

    s3 = boto3.client('s3')
    ssm = boto3.client('ssm')

    response = ssm.get_parameters(
        Names=[
            '/signal/account',
            '/signal/groupId',
            '/slack/webhook',
            '/telegram/botToken',
            '/telegram/chatId',
            ],
        WithDecryption=True)
    params = {p['Name']: p['Value'] for p in response['Parameters']}
    signal_account = params.get('/signal/account')
    signal_group = params.get('/signal/groupId')
    slack_webhook = params.get('/slack/webhook')
    telegram_bot_token = params.get('/telegram/botToken')
    telegram_chat_id = params.get('/telegram/chatId')

    today = datetime.now(tz=PST)
    day_s = today.strftime('%A')
    date_s = today.strftime('%Y-%m-%d')
    thread_emoji = '\U0001F9F5'
    thread_message = f'Wordle {thread_emoji} for {day_s} {date_s}'

    if is_monday(today):
        word = random_word(s3, bucket, ALL_WORDS_S3_KEY)
        print(f'New start word: {word}')
        set_current_word(s3, bucket, LATEST_WORD_S3_KEY , word)
        print(f'Saved start word in s3://{bucket}/{LATEST_WORD_S3_KEY}')
        message = f'New start word for this week: {word}\n{thread_message}'
        send_to_telegram(telegram_bot_token, telegram_chat_id, message)

    elif is_weekday(today):
        print(f'Retrieving current start word from s3://{bucket}/{LATEST_WORD_S3_KEY}')
        word = get_current_word(s3, bucket, LATEST_WORD_S3_KEY)
        print(f'Using current start word: {word}')
        message = f'{thread_message}. Start word: {word}'
        send_to_telegram(telegram_bot_token, telegram_chat_id, message)

    else:
        print('Today is a weekend. Not sending any message')
