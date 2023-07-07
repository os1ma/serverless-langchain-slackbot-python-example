import logging
import os
import time

import openai
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

CHAT_UPDATE_INTERVAL_SEC = 1

SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    token=os.environ["SLACK_BOT_TOKEN"],
    process_before_response=True,
)


def chat(say, body):
    logger.info("chat start")

    event = body["event"]
    channel = event["channel"]
    prompt = event["text"]

    say_response = say("Thinking...")
    ts = say_response["ts"]

    messages = [
        {"role": "user", "content": prompt},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages, temperature=0, stream=True
    )

    message = ""
    last_send_time = time.time()

    for chunk in response:
        delta = chunk["choices"][0]["delta"].get("content", "")
        message += delta

        now = time.time()
        if now - last_send_time > CHAT_UPDATE_INTERVAL_SEC:
            last_send_time = now
            app.client.chat_update(channel=channel, ts=ts, text=f"{message}...")

    app.client.chat_update(channel=channel, ts=ts, text=message)
    logger.info("chat end")


def just_ack(ack):
    ack()


app.event("app_mention")(ack=just_ack, lazy=[chat])


def handler(event, context):
    """Lambda関数のエントリーポイント"""
    logger.info("handler called")
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)


def local_main():
    """ローカルで実行するためのエントリーポイント"""
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    local_handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    local_handler.start()


if __name__ == "__main__":
    local_main()
