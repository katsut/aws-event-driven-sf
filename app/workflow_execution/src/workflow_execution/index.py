import dataclasses
from datetime import datetime, timezone
from aws_xray_sdk.core import xray_recorder
from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import parse_obj_as
from pydantic.dataclasses import dataclass
from more_itertools import first_true
import uuid
from workflow_execution.models import NodeExecution, SequenceFlow, WorkflowExecution
from pydantic.json import pydantic_encoder


logger = Logger(service="APP")


@dataclass(frozen=True)
class Payload:
    workflow_execution: WorkflowExecution
    node_execution: NodeExecution


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.EVENT_BRIDGE, log_event=True
)
@xray_recorder.capture(name="handler")
def lambda_handler(event, context: LambdaContext):
    try:
        logger.debug(f"event: {type(event)} {event}")
        payload = parse_obj_as(Payload, event["Payload"])
        previous_node_id = payload.node_execution.node.node_id

        downstream_flow = next(
            (
                flow
                for flow in payload.workflow_execution.graph.flows
                if flow.inbound_node_id == previous_node_id
            ),
            None,
        )
        if not downstream_flow:
            raise ValueError(f"Invalid argument graph or node_id {payload}")

        logger.info(f"downstream_flow: {downstream_flow}")

        next_node = next(
            (
                node
                for node in payload.workflow_execution.graph.nodes
                if node.node_id == downstream_flow.outbound_node_id
            ),
            None,
        )
        if not next_node:
            raise ValueError(f"Invalid graph {payload}")
        logger.info(f"next_node: {next_node}")

        node_execution = NodeExecution(
            node_execution_id=str(uuid.uuid4()).replace("-", ""),
            node=next_node,
            started_at=datetime.now(tz=timezone.utc).isoformat(),
            finished_at=None,
        )

        return {
            "status": "succeeded",
            "node_execution": dataclasses.asdict(node_execution),
            "workflow_execution": dataclasses.asdict(payload.workflow_execution),
        }

    except Exception as e:
        logger.exception(e)
        raise e
