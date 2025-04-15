#!/bin/bash
set -e

# Replace with your AWS Lambda function name
LAMBDA_NAME="fetchLifelogsCatchup"

bash build.sh
aws lambda update-function-code \
    --function-name $LAMBDA_NAME \
    --zip-file fileb://package.zip

echo "✅ Deployed to Lambda: $LAMBDA_NAME"
