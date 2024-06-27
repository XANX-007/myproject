#created by Cejay Henry for sememster 3 case study project
import json
import os
import boto3
import logging
from time import sleep

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")

    try:
        project_name = event['projectName']
        cluster_name = event['ClusterName']
        wordpress_task_definition = event['WordpressTaskDefinition']
        database_task_definition = event['DatabaseTaskDefinition']
        customer_name = event['customerName']
        database_service_discovery_arn = event['DatabaseServiceDiscoveryArn']
        wordpress_service_discovery_arn = event['WordpressServiceDiscoveryArn']
    except KeyError as e:
        logger.error(f"Missing key in event: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'message': f'Missing key in event: {e}', 'error': str(e)})
        }

    vpc_id = os.environ['VPC_ID']
    public_subnet_ids = os.environ['PUBLIC_SUBNET_IDS'].split(',')
    private_subnet_ids = os.environ['PRIVATE_SUBNET_IDS'].split(',')
    security_group_id = os.environ['SECURITY_GROUP_ID']
    database_security_group_id = os.environ['DATABASE_SECURITY_GROUP_ID']

    try:
        # Create Database Service in private subnets
        db_service_response = ecs.create_service(
            cluster=cluster_name,
            serviceName=f"db-service-{customer_name}-{project_name}",
            taskDefinition=database_task_definition,
            desiredCount=1,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': private_subnet_ids,
                    'securityGroups': [database_security_group_id],
                    'assignPublicIp': 'DISABLED',
                },
            },
            serviceRegistries=[{
                'registryArn': database_service_discovery_arn
            }]
        )
        logger.info(f"Database service {customer_name} project {project_name} creation initiated: {db_service_response}")

        # Create WordPress Service in public subnets
        wp_service_response = ecs.create_service(
            cluster=cluster_name,
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
            },
            serviceRegistries=[{
                'registryArn': wordpress_service_discovery_arn
            }]
        )
        logger.info(f"WordPress service {customer_name} creation initiated: {wp_service_response}")

        # Wait for the service to stabilize and retrieve the public IP
        sleep(9)  # Wait for the service to start and ENI to be available

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
