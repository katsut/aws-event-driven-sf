from datetime import datetime, timezone
import json
from more_itertools import first_true
from pytest import fixture
from find_next_nodes.index import Payload
from find_next_nodes.models import (
    EndEvent,
    Graph,
    NodeExecution,
    SequenceFlow,
    StartEvent,
    WorkflowExecution,
)
from pydantic.tools import parse_obj_as, parse_raw_as
from pydantic.json import pydantic_encoder


@fixture
def fixture_data():
    graph = Graph(
        flows=[
            SequenceFlow(
                sequence_flow_id="flow-0001",
                inbound_node_id="start-0001",
                outbound_node_id="end-0001",
            )
        ],
        nodes=[StartEvent(node_id="start-0001"), EndEvent(node_id="start-0002")],
    )
    yield graph


def test_index(fixture_data):
    workflow_execution = WorkflowExecution(
        workflow_execution_id="workflow_execution_1",
        workflow_document_id="workflow_document_1",
        graph=fixture_data,
    )
    node_execution = NodeExecution(
        node_execution_id="node_execution_1",
        node=StartEvent(node_id="start-0001"),
        started_at=datetime.now(tz=timezone.utc).isoformat(),
        finished_at=None,
    )
    # print(json.dumps(node_execution, default=pydantic_encoder))
    # print(json.dumps(workflow_execution, default=pydantic_encoder))
    payload = {
        "Payload": {
            "node_execution": {
                "node_execution_id": "node_execution_1",
                "node": {"node_id": "start-0001", "node_type": "StartEvent"},
                "started_at": "2023-06-06T13:17:09.917285+00:00",
                "finished_at": None,
                "status": "Started",
            },
            "workflow_execution": {
                "workflow_execution_id": "workflow_execution_1",
                "workflow_document_id": "workflow_document_1",
                "graph": {
                    "flows": [
                        {
                            "sequence_flow_id": "flow-0001",
                            "inbound_node_id": "start-0001",
                            "outbound_node_id": "end-0001",
                        }
                    ],
                    "nodes": [
                        {"node_id": "start-0001", "node_type": "StartEvent"},
                        {"node_id": "end-0002", "node_type": "EndEvent"},
                    ],
                },
            },
        }
    }

    payload = parse_obj_as(Payload, payload["Payload"])
    previous_node_id = payload.node_execution.node.node_id

    # def is_downstream_flow(flow: SequenceFlow, node_id: str):
    #     return (
    #         flow.inbound_node_id == node_id
    #     )  # If Inbound is the same as specified, downstream flow

    downstream_flow = first_true(
        payload.workflow_execution.graph.flows,
        lambda f: f.inbound_node_id == previous_node_id,
        None,
    )
    if not downstream_flow:
        raise ValueError(f"Invalid argument graph or node_id {payload}")

    next_node = first_true(
        payload.workflow_execution.graph.nodes,
        lambda n: n.node_id == downstream_flow.outbound_node_id,
        None,
    )
    if not next_node:
        raise ValueError(f"Invalid graph {payload}")

    node_execution = NodeExecution(
        node_execution_id=str(uuid.uuid4()).replace("-", ""),
        node=next_node,
        started_at=datetime.now(tz=timezone.utc).isoformat(),
        finished_at=None,
    )

    assert json.dumps(node_execution, default=pydantic_encoder) == ""
