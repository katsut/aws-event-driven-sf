import json
from datetime import datetime
from aws_xray_sdk.core import xray_recorder

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent

logger = Logger(service="APP")


@xray_recorder.capture("handler")
@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.EVENT_BRIDGE, log_event=True
)
def lambda_handler(event: EventBridgeEvent, context: LambdaContext):
