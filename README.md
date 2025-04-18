# Devops learning platform with React, Flask and postgres

Frontend: React

Backend: Flask

Database: Postgres

chmod +x frontend/docker-entrypoint.sh

chmod +x frontend/docker-entrypoint.sh



bash ```
# lambda deploy
# Create a deployment package
mkdir quiz-analysis-lambda
cd quiz-analysis-lambda
# Copy the Lambda function code from lambda-code.js into index.js
npm init -y
npm install aws-sdk
zip -r function.zip index.js node_modules

# Deploy CloudFormation stack
aws cloudformation create-stack \
  --stack-name devops-quiz-analysis \
  --template-body file://lambda-apigateway-dynomodb-cloudformation.yaml \
  --capabilities CAPABILITY_IAM


  # delete the stack 

  aws cloudformation delete-stack --stack-name devops-quiz-analysis

  ```


  