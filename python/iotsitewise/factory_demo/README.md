## Introduction

This package contains the following scripts to do the following:
- `meas-gen-stack`: Creates the Lambdas needed to generate test measurements, and to forward
  SiteWise property values to CloudWatch metrics
- `create-sitewise-resources`: Creates the SiteWise AssetModels and Assets
- `grafana-stack`: Creates a Grafana server on an EC2 instance for building a SiteWise dashboard


## Setting up dev environment

The scripts use `jq` for reading/writing json files. Ensure this is available

```
# Install jq using your distro's package management system. For example:
> sudo yum install jq
```

Create the virtualenv and install dependencies

```
> python -m venv venv
> source ./venv/bin/activate
> pip install -r requirements.txt
```

All scripts in this readme needs to be run within the virtual environment.


## Building the resources

```
# Ensure your CLI environment has the required AWS environment variables
> echo $AWS_ACCESS_KEY_ID
> echo $AWS_DEFAULT_REGION

# Create the CloudFormation stack with the Lambda functions for generating test data
> ./meas-gen-stack --create

# Create the SiteWise resources (use -h to view all configurable options)
> ./create-sitewise-resources
```

This will create a resource DB file (a json file that can be read using the python TinyDB library)
containing the test configuration and all SiteWise resources that has been created.

```
# Start generating test measurements
> ./enable-meas-gen -d <resources DB file> --start
```

Now you can view your test resources using the CLI, your own scripts using the AWS SDK, or by
visiting the [AWS IoT SiteWise console](https://console.aws.amazon.com/iotsitewise).

Metrics for the top-level Assets are also being forwarded to CloudWatch (using the custom namespace
"IoTSiteWise/AssetMetrics"), where you can create dashboards and set up alarms.


## Creating Grafana dashboards

As a pre-requisite, you must create your own [custom managed prefix list](https://docs.aws.amazon.com/vpc/latest/userguide/managed-prefix-lists.html),
specifying which host IPs can access the Grafana dashboards.

The EC2 instance running the Grafana service only accepts HTTP connections, and because of this,
access to the Grafana dashboard is restricted to a customer-managed prefix list which you should
set up separately and use to maintain a list of IPs or CIDR ranges that can have access to the
Grafana dashboard.


Open the `grafana-stack` script and edit the following two lines to include the prefix list ID
and the EC2 Key Pair name (used to SSH onto the Grafana EC2 instance).

```
EC2_KEY_NAME='...'
PREFIX_LIST='pl-...'
```

Now run the script to create the CloudFormation stack with the Grafana resources

```
> ./grafana-stack --create
```

The CloudFormation stack includes an Auto Scaling Group configured to run one EC2 instance, which
will load some bootstrap code on startup to install Grafana (with the IoT SiteWise datasource) and
Nginx to accept HTTP connections.

Wait for this EC2 instance to finish setting itself up, then get it's public IP address

```
aws ec2 describe-instances \
    --filters 'Name=instance-state-name,Values=running' \
    --query 'Reservations[*].Instances[*].[InstanceId, PublicIpAddress]' \
    --output text
```

Now go to the following URL to view and configure the Grafana dashboard

```
http://<EC2 Public IP>/grafana
```

## Cleanup resources

```
# Delete the SiteWise resources
> ./delete-sitewise-resources -d <resources DB file>

# Delete the CloudFormation stacks
> ./meas-gen-stack --delete
> ./grafana-stack --delete
```
