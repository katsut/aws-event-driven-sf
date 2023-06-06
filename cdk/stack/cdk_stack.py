from dataclasses import dataclass
from attr import frozen
from aws_cdk import Stack, aws_lambda
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_events as events
from aws_cdk import aws_stepfunctions_tasks as sfnt
from constructs import Construct


class CdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_common_layer = aws_lambda.LayerVersion(
            self,
            "lambda-common",
            code=aws_lambda.Code.from_asset("../layer/lambda_common/dist/module.zip"),
            compatible_runtimes=[
                aws_lambda.Runtime.PYTHON_3_10,
            ],
        )

        event_receiver_function = aws_lambda.Function(
            self,
            "example_event_receiver",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            handler="event_receiver.index.lambda_handler",
            code=aws_lambda.Code.from_asset("../app/event_receiver/dist/module.zip"),
            layers=[lambda_common_layer],
            environment={
                "POWERTOOLS_SERVICE_NAME": "example_event_receiver",
                "LOG_LEVEL": "DEBUG",
            },
            tracing=aws_lambda.Tracing.ACTIVE,
        )

        put_event = sfnt.EventBridgePutEvents(
            self,
            "PutEvents",
            entries=[
                sfnt.EventBridgePutEventsEntry(
                    detail=sfn.TaskInput.from_object(
                        {
                            "message": sfn.JsonPath.string_at("$.Payload.message"),
                            "payload": sfn.JsonPath.entire_payload,
                        }
                    ),
                    detail_type="move_token",
                    source="workflow.application",
                )
            ],
        )

        ## TODO Implements EventBridgeScheduler Resource

        start_event_state: sfn.Pass = sfn.Pass(
            self,
            "start",
            result=sfn.Result.from_object(
                {"Payload": {"node": {"node_id": "1", "node_type": "start_event"}}}
            ),  # TODO implements lambda
        )

        find_next_node_state = sfnt.LambdaInvoke(
            self, "ReceiveEvent", lambda_function=event_receiver_function
        )

        node_type_branch_state: sfn.Choice = sfn.Choice(self, "node_type_branch")

        node_execution_create_state: sfn.Pass = sfn.Pass(self, "node_execution_create")
        node_execution_update_state: sfn.Pass = sfn.Pass(self, "node_execution_update")
        run_activity_state: sfn.Pass = sfn.Pass(self, "activity_run")
        failed_state: sfn.Fail = sfn.Fail(self, "failed")
        succeed_state: sfn.Succeed = sfn.Succeed(self, "succeeded")

        end_event_state: sfn.Pass = sfn.Pass(self, "end")
        definition: sfn.IChainable = start_event_state.next(
            node_type_branch_state.when(
                sfn.Condition.string_equals("$.Payload.node.node_type", "start_event"),
                find_next_node_state,  # move to next node
            )
            .when(
                sfn.Condition.string_equals("$.Payload.node.node_type", "end_event"),
                end_event_state,
            )
            .otherwise(failed_state)
        )

        workflow_state_macine = sfn.StateMachine(
            self,
            "WorkflowStateMachine",
            definition=definition,
        )
