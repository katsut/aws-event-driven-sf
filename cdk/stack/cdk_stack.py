from dataclasses import dataclass
from attr import frozen
from aws_cdk import Stack, aws_lambda
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_events as events
from aws_cdk import aws_stepfunctions_tasks as sfnt
import aws_cdk
from constructs import Construct
from aws_cdk import aws_iam as iam


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

        find_next_nodes_function = aws_lambda.Function(
            self,
            "example_workflow_find_next_nodes",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            handler="workflow_execution.index.lambda_handler",
            code=aws_lambda.Code.from_asset(
                "../app/workflow_execution/dist/module.zip"
            ),
            layers=[lambda_common_layer],
            environment={
                "POWERTOOLS_SERVICE_NAME": "example_workflow_find_next_nodes",
                "LOG_LEVEL": "DEBUG",
            },
            tracing=aws_lambda.Tracing.ACTIVE,
        )

        ## TODO Implements EventBridgeScheduler Resource

        start_event_state: sfn.Pass = sfn.Pass(
            self,
            "start",
            result=None,  # TODO implements lambda
        )

        activity_run_definition: sfn.Activity = sfn.Activity(
            self,
            "run_activity_definition",
        )
        run_activity_state = sfnt.StepFunctionsInvokeActivity(
            self, "activity_run", activity=activity_run_definition
        )

        find_next_node_state: sfnt.LambdaInvoke = sfnt.LambdaInvoke(
            self, "find_next_node", lambda_function=find_next_nodes_function
        )

        node_type_branch_state: sfn.Choice = sfn.Choice(self, "node_type_branch")

        node_execution_create_state: sfn.Pass = sfn.Pass(self, "node_execution_create")
        node_execution_update_state: sfn.Pass = sfn.Pass(self, "node_execution_update")
        failed_state: sfn.Fail = sfn.Fail(self, "failed")
        succeed_state: sfn.Succeed = sfn.Succeed(self, "succeeded")

        end_event_state: sfn.Pass = sfn.Pass(self, "end")
        definition: sfn.IChainable = start_event_state.next(
            node_type_branch_state.when(
                sfn.Condition.string_equals(
                    "$.Payload.node_execution.node.node_type", "StartEvent"
                ),
                find_next_node_state.next(node_type_branch_state),  # move to next node
            )
            .when(
                sfn.Condition.string_equals(
                    "$.Payload.node_execution.node.node_type", "EndEvent"
                ),
                end_event_state,
            )
            .when(
                sfn.Condition.string_equals(
                    "$.Payload.node_execution.node.node_type", "Activity"
                ),
                run_activity_state.next(find_next_node_state),
            )
            .otherwise(failed_state)
        )

        workflow_state_macine = sfn.StateMachine(
            self,
            "WorkflowStateMachine",
            definition=definition,
            timeout=aws_cdk.Duration.minutes(30),
        )

        activity_handler_function: aws_lambda.Function = aws_lambda.Function(
            self,
            "example_workflow_activity_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            handler="workflow_execution.sfn_activity_handler.lambda_handler",
            code=aws_lambda.Code.from_asset(
                "../app/workflow_execution/dist/module.zip"
            ),
            layers=[lambda_common_layer],
            environment={
                "POWERTOOLS_SERVICE_NAME": "example_workflow_activity_handler",
                "LOG_LEVEL": "DEBUG",
                "ACTIVITY_ARN": activity_run_definition.activity_arn,
            },
            timeout=aws_cdk.Duration.seconds(30),
            tracing=aws_lambda.Tracing.ACTIVE,
        )

        worker_policy = iam.PolicyStatement(
            actions=[
                "states:DescribeActivity",
                "states:DescribeStateMachine",
                "states:ListExecutions",
                "states:StopExecution",
                "states:StartSyncExecution",
                "states:DescribeStateMachineForExecution",
                "states:SendTaskSuccess",
                "states:SendTaskFailure",
                "states:DescribeExecution",
                "states:GetExecutionHistory",
                "states:StartExecution",
                "states:DescribeMapRun",
                "states:SendTaskHeartbeat",
                "states:GetActivityTask",
                "states:ListTagsForResource",
            ],
            effect=iam.Effect.ALLOW,
            sid="ActivityWorkerPolicy",
            resources=["*"],
        )

        activity_handler_function.add_to_role_policy(worker_policy)
