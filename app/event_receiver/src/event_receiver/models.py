from abc import ABC
from pydantic.dataclasses import dataclass
from typing import Literal


class Node(ABC):
    node_id: str
    node_type: Literal["Activity", "StartEvent", "EndEvent"]


@dataclass(frozen=True)
class ActivityNode(Node):
    node_id: str
    title: str
    node_type: Literal["Activity"] = "Activity"


@dataclass(frozen=True)
class StartEvent(Node):
    node_id: str
    node_type: Literal["StartEvent"] = "StartEvent"


@dataclass(frozen=True)
class EndEvent(Node):
    node_id: str
    node_type: Literal["EndEvent"] = "EndEvent"


@dataclass(frozen=True)
class SequenceFlow:
    sequence_flow_id: str
    inbound_node_id: str
    outbound_node_id: str

    def is_inbound(self, node_id: str) -> bool:
        return self.inbound_node_id == node_id


@dataclass(frozen=True)
class Graph:
    flows: list[SequenceFlow]
    nodes: list[ActivityNode | StartEvent | EndEvent]


@dataclass(frozen=True)
class WorkflowExecution:
    workflow_execution_id: str
    workflow_document_id: str
    graph: Graph


@dataclass(frozen=True)
class NodeExecution:
    node_execution_id: str
    node: ActivityNode | StartEvent | EndEvent
    started_at: str
    finished_at: str | None
    status: Literal["Started", "Finished"] = "Started"
