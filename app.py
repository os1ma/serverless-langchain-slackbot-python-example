import logging
import os

from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    token=os.environ["SLACK_BOT_TOKEN"],
    process_before_response=True
)

def respond_to_slack_within_3_seconds(body, ack):
    text = body.get("text")
    if text is None or len(text) == 0:
        ack(":x: Usage: /start-process (description here)")
    else:
        ack(f"Accepted! (task: {body['text']})")

import time
def run_long_process(respond, body):
    logger.info("run_long_process called")
    logger.info("sleeping...")
    time.sleep(5)
    logger.info("sleep finished")
    respond(f"Completed! (task: {body['text']})")

app.event("app_mention")(
    ack=respond_to_slack_within_3_seconds,
    lazy=[run_long_process]
)

def handler(event, context):
    logger.info("handler called")
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
