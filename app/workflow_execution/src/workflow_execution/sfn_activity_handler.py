import dataclasses
from datetime import datetime, timezone
import os
from aws_xray_sdk.core import xray_recorder
from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_stepfunctions.client import SFNClient
from mypy_boto3_stepfunctions.type_defs import (
    GetActivityTaskOutputTypeDef,
    SendTaskSuccessInputRequestTypeDef,
)
import boto3
from botocore.exceptions import EndpointConnectionError


logger = Logger(service="APP")
activity_arn = os.environ("ACTIVITY_ARN")

config = boto3.Config(
    connect_timeout=3,
    read_timeout=10,  # No running activities if response timeout
    retries={"max_attempts": 0, "mode": "standard"},
)
sfn: SFNClient = boto3.client("stepfunctions")


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.EVENT_BRIDGE, log_event=True
)
@xray_recorder.capture(name="handler")
def lambda_handler(event, context: LambdaContext):
    while True:
        worker_name = context.aws_request_id

        try:
            response: GetActivityTaskOutputTypeDef = sfn.get_activity_task(
                activityArn=activity_arn, workerName=worker_name
            )

            logger.info(f"run worker {type(response)} {response}")
            send_request: SendTaskSuccessInputRequestTypeDef = sfn.send_task_success(
                output=response.input, taskToken=response.taskToken
            )
            logger.info(f"send task success {send_request}")
        except EndpointConnectionError as e:
            break
        except Exception as e:
            logger.error(e)
            raise e
