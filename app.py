import logging
import os

from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    token=os.environ["SLACK_BOT_TOKEN"],
    process_before_response=True
)

def just_ack(ack):
    ack()

import time
def run_long_process(say, body):
    logger.info("sleeping...")
    say("sleeping...")
    time.sleep(5)
    logger.info("sleep finished")
    say("sleep finished")

app.event("app_mention")(
    ack=just_ack,
    lazy=[run_long_process]
)

def handler(event, context):
    logger.info("handler called")
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
