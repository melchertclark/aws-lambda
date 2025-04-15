#!/bin/bash
set -e

REGION="us-east-2"
LAMBDA_NAME="fetchLifelogsCatchup"

bash build.sh

# Replace this with your actual IAM role ARN
ROLE_ARN="arn:aws:iam::036209394802:role/service-role/fetchLifelogsCatchup-role-swgkycjq"
HANDLER="lambda_function.lambda_handler"

# Check if the Lambda function exists
if aws lambda get-function --function-name $LAMBDA_NAME --region $REGION > /dev/null 2>&1; then
    echo "✅ Function exists. Updating code..."
    aws lambda update-function-code \
        --function-name $LAMBDA_NAME \
        --zip-file fileb://package.zip \
        --region $REGION
else
    echo "⚠️ Function not found. Creating it..."
    aws lambda create-function \
        --function-name $LAMBDA_NAME \
        --runtime python3.13 \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --zip-file fileb://package.zip \
        --region $REGION
fi

echo "✅ Deployment completed: $LAMBDA_NAME"
