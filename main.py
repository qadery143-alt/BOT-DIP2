import os
import requests
from flask import Flask, request

app = Flask(__name__)
TOKEN = os.environ.get('BOT_TOKEN')
TELEGRAM_API = f'https://api.telegram.org/bot{TOKEN}'


@app.route(f'/{TOKEN}', methods=['POST'])
def receive_update():
  data = request.get_json()
  if 'message' in data:
    chat_id = data['message']['chat']['id']
    text = data['message'].get('text', '')

    if text == '/start':
      send_message(
          chat_id,
          'أهلاً بك! تم تشغيل بوت إدارة الألعاب بنجاح ومحمي عبر Cloudflare.',
      )
    else:
      send_message(chat_id, f'تم استلام أمرك: {text}')

  return 'OK', 200


def send_message(chat_id, text):
  url = f'{TELEGRAM_API}/sendMessage'
  payload = {'chat_id': chat_id, 'text': text}
  requests.post(url, json=payload)


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
