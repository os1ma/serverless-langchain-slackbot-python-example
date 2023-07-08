import logging
import os
import time
from typing import Any

from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import LLMResult
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

CHAT_UPDATE_INTERVAL_SEC = 1

SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    token=os.environ["SLACK_BOT_TOKEN"],
    process_before_response=True,
)

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, streaming=True)


class SlackStreamingCallbackHandler(BaseCallbackHandler):
    last_send_time = time.time()
    message = ""

    def __init__(self, channel, ts):
        self.channel = channel
        self.ts = ts

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.message += token

        now = time.time()
        if now - self.last_send_time > CHAT_UPDATE_INTERVAL_SEC:
            self.last_send_time = now
            app.client.chat_update(
                channel=self.channel, ts=self.ts, text=f"{self.message}..."
            )

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        app.client.chat_update(channel=self.channel, ts=self.ts, text=self.message)


def chat(say, body):
    logger.info("chat start")

    event = body["event"]
    channel = event["channel"]
    prompt = event["text"]
    thread_ts = event["ts"]

    say_response = say("Thinking...", thread_ts=thread_ts)
    ts = say_response["ts"]

    callback = SlackStreamingCallbackHandler(channel=channel, ts=ts)
    llm.predict(prompt, callbacks=[callback])

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
