import json
from aws_xray_sdk.core import xray_recorder

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths

logger = Logger(service="APP")


@xray_recorder.capture("handler")
@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.EVENT_BRIDGE, log_event=True
)
def lambda_handler(event, context):
    return {"statusCode": 200, "body": json.dumps({"message": "OK"})}
