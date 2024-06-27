#created by Cejay Henry for sememster 3 case study project

import json
import os
import boto3
import logging
from time import sleep

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cloudformation = boto3.client('cloudformation')
ecs = boto3.client('ecs')
ec2 = boto3.client('ec2')

def get_public_ip(task_arn, cluster_name):
    try:
        task_desc = ecs.describe_tasks(cluster=cluster_name, tasks=[task_arn])
        eni_id = next(detail['value'] for detail in task_desc['tasks'][0]['attachments'][0]['details'] if detail['name'] == 'networkInterfaceId')
        eni_desc = ec2.describe_network_interfaces(NetworkInterfaceIds=[eni_id])
        public_ip = eni_desc['NetworkInterfaces'][0]['Association']['PublicIp']
        return public_ip
    except Exception as e:
        logger.error(f"Failed to get public IP: {e}")
        return None

def get_stack_output_value(outputs, output_key):
    for output in outputs:
        if output['OutputKey'] == output_key:
            return output['OutputValue']
    return None

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")

    try:
        
        project_name = event['projectName']
        customer_name = event['customerName']
        template_url = os.environ['TEMPLATE_URL']
        stack_name =  f"lowCost-stack-{customer_name}"
    except KeyError as e:
        logger.error(f"Missing key in event: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'message': f'Missing key in event: {e}', 'error': str(e)})
        }

    cluster_name = os.environ['CLUSTER_NAME']
    vpc_id = os.environ['VPC_ID']
    public_subnet_ids = os.environ['PUBLIC_SUBNET_IDS'].split(',')
    security_group_id = os.environ['SECURITY_GROUP_ID']
    db_host = os.environ['WORDPRESS_DB_HOST']
    db_user = os.environ['WORDPRESS_DB_USER']
    db_name = os.environ['WORDPRESS_DB_NAME']
    db_password = os.environ['WORDPRESS_DB_PASSWORD']
    task_role_arn = os.environ['TASK_ROLE_ARN']
    execution_role_arn = os.environ['EXECUTION_ROLE_ARN']

    try:
        # Create the CloudFormation stack
        response = cloudformation.create_stack(
            StackName=stack_name,
            TemplateURL=template_url,
            Parameters=[
                {'ParameterKey': 'CustomerName', 'ParameterValue': customer_name},
                {'ParameterKey': 'ProjectName', 'ParameterValue': project_name},
                {'ParameterKey': 'VPCId', 'ParameterValue': vpc_id},
                {'ParameterKey': 'PublicSubnetIds', 'ParameterValue': ",".join(public_subnet_ids)},
                {'ParameterKey': 'SecurityGroupId', 'ParameterValue': security_group_id},
                {'ParameterKey': 'ExecutionRoleArn', 'ParameterValue': execution_role_arn},
                {'ParameterKey': 'TaskRoleArn', 'ParameterValue': task_role_arn},
                {'ParameterKey': 'WordpressDatabaseHost', 'ParameterValue': db_host},
                {'ParameterKey': 'WordpressDBUser', 'ParameterValue': db_user},
                {'ParameterKey': 'WordpressDBName', 'ParameterValue': db_name},
                {'ParameterKey': 'WordpressDBPassword', 'ParameterValue': db_password}
            ],
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
        )
        logger.info(f"CloudFormation stack creation initiated: {response}")

        # Wait for the stack to be created
        waiter = cloudformation.get_waiter('stack_create_complete')
        waiter.wait(StackName=stack_name)
        logger.info(f"CloudFormation stack {stack_name} created successfully")

       #stack outputs from cloud formation
        stack_description = cloudformation.describe_stacks(StackName=stack_name)
        outputs = stack_description['Stacks'][0]['Outputs']
        logger.info(f"Stack outputs: {outputs}")
        wordpress_task_definition = get_stack_output_value(outputs, 'WordpressTaskDefinition')
        

        if not wordpress_task_definition:
            logger.error("Failed to get necessary outputs from stack")
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Failed to get necessary outputs from stack'})
            }

        # Create WordPress Service in public subnets
        wp_service_response = ecs.create_service(
            cluster=cluster_name,  # Specifying the ECS cluster from environment variable
            serviceName=f"wp-service-{customer_name}-{project_name}",
            taskDefinition=wordpress_task_definition,
            desiredCount=1,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': public_subnet_ids,
                    'securityGroups': [security_group_id],
                    'assignPublicIp': 'ENABLED',
                },
            }
        )
        logger.info(f"WordPress service {customer_name} creation initiated: {wp_service_response}")

        # wait on task to statrs running
        sleep(60)  

        tasks = ecs.list_tasks(cluster=cluster_name, serviceName=f"wp-service-{customer_name}-{project_name}")['taskArns']
        if tasks:
            public_ip = get_public_ip(tasks[0], cluster_name)
        else:
            logger.error(f"No tasks found for WordPress service {customer_name}-{project_name}")
            public_ip = None

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Services for {customer_name} created successfully',
                'wordpressPublicIp': public_ip
            })
        }

    except Exception as e:
        logger.error(f"Failed to create services for {customer_name}: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Failed to create services for {customer_name}', 'error': str(e)})
        }
