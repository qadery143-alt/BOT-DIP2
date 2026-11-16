import os
from flask import Flask, request

app = Flask(__name__)
TOKEN = os.environ.get('BOT_TOKEN')


@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
  return "OK", 200


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
