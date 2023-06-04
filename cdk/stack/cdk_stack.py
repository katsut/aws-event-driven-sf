from aws_cdk import Stack, aws_lambda
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
