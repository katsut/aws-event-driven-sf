# Example for Implementation of BPMN engine with step function

## Required

- python 3.10
- python 3.9 (cdk)
- poetry

### aws services

- AWS CDK
- AWS Stepfunctions
- AWS Lambda
- Amazon EventBridge
- Amazon EventBridge Scheduler
- AWS X-Ray

## build and deployment

### build

```bash

cd layer/lambda_common/
./build_layer_script.sh

cd app/find_next_nodes/
./build_script.sh

```

### deploy

```bash

cd cdk
cdk deploy

```
