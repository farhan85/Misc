## Introduction

This package uses StepFunctions/Lambda/DDB to create a large hierarchy tree of connected
AssetModels. The size of the hierarchy tree is specified in a StepFunctions state
machine's input.


## Setting up dev environment

Create the virtualenv and install dependencies
```
> python -m venv venv
> ./venv/bin/pip install -r requirements.txt
```


## Testing using a local DynamoDB

In a separate terminal, start up a local DDB server
```
# Start local server
> java -Djava.library.path=path/to/DynamoDBLocal_lib -jar $LIB_DIR/DynamoDBLocal.jar -inMemory
```

Back in your dev environment, create the tables in the local DynamoDB
```
# Create tables
> ./venv/bin/python create-local-tables
```

Run Lambda functions locally (note this _will_ make SiteWise API calls to create AssetModels)
```
> ./venv/bin/lambda invoke --config-file config-initdb.yaml

# Run this command multiple times until it outputs Finished=true
> ./venv/bin/lambda invoke --config-file config-createmodels.yaml

# Run this command multiple times until it outputs Finished=true
> ./venv/bin/lambda invoke --config-file config-deletemodels.yaml
```


## Deploying to AWS

Before you can deploy, you need to specify an S3 bucket to upload the Lambda function
zip files to
* Open the `manage-stack` script in your text editor
* Locate the line that sets the variable `S3_BUCKET` and update it to an S3 bucket
  you have read/write access to

Now deploy the infra and Lambda code
```
# Create CloudFormation stack
> ./manage-stack -c

# Update Lambda functions
> ./manage-stack -l
```


## Run a load test
* Go to the StepFunctions console
* Start a new execution for the CreateModels StateMachine
* See `event.json` for an example of the state machine's input


## Cleanup resources
* Go to the StepFunctions console
* Start a new execution for the DeleteModels StateMachine
* This state machine takes no input. It knows which models to delete from the entries
  stored in the DynamoDB tables
