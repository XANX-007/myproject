#created by Cejay Henry for sememster 3 case study project
import json
import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cloudformation = boto3.client('cloudformation')

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")

    customer_name = event.get('customerName')
    project_name = event.get('projectName')
    if not customer_name:
        raise ValueError("customerName is required")

    stack_name = f"ecs-stack-{customer_name}"
    template_url = "https://cf-templates--1bdmg1epah5n-eu-central-1.s3.eu-central-1.amazonaws.com/ecs-templates.yaml"
    
    vpc_id = os.environ.get('VPC_ID')
    public_subnet_ids = os.environ.get('PUBLIC_SUBNET_IDS', '').split(',')
    private_subnet_ids = os.environ.get('PRIVATE_SUBNET_IDS', '').split(',')
    security_group_id = os.environ.get('SECURITY_GROUP_ID')
    database_security_group_id = os.environ.get('DATABASE_SECURITY_GROUP_ID')
    public_namespace_id = os.environ.get('PUBLIC_NAMESPACE_ID')
    namespace_id = os.environ.get('NAMESPACE_ID')
    namespace_name = os.environ.get('NAMESPACE_NAME')
    execution_role_arn = os.environ.get('EXECUTION_ROLE_ARN')
    task_role_arn = os.environ.get('TASK_ROLE_ARN')

    # Log environment variables to ensure they are set correctly
    logger.info(f"Environment variables - VPC_ID: {vpc_id}, PUBLIC_SUBNET_IDS: {public_subnet_ids}, PRIVATE_SUBNET_IDS: {private_subnet_ids}, SECURITY_GROUP_ID: {security_group_id}, DATABASE_SECURITY_GROUP_ID: {database_security_group_id}, NAMESPACE_ID: {namespace_id}, NAMESPACE_NAME: {namespace_name}, EXECUTION_ROLE_ARN: {execution_role_arn}, TASK_ROLE_ARN: {task_role_arn}")

    # Validate that all required environment variables are present
    if not all([vpc_id, public_subnet_ids, private_subnet_ids, security_group_id, database_security_group_id, namespace_id, namespace_name, execution_role_arn, task_role_arn]):
        raise ValueError("One or more required environment variables are missing")

    try:
        logger.info(f"Starting stack creation for customer: {customer_name}")

        response = cloudformation.create_stack(
            StackName=stack_name,
            TemplateURL=template_url,
            Parameters=[
                {'ParameterKey': 'CustomerName', 'ParameterValue': customer_name},
                {'ParameterKey': 'ProjectName', 'ParameterValue': project_name},
                {'ParameterKey': 'VPCId', 'ParameterValue': vpc_id},
                {'ParameterKey': 'PublicSubnetIds', 'ParameterValue': ",".join(public_subnet_ids)},
                {'ParameterKey': 'PrivateSubnetIds', 'ParameterValue': ",".join(private_subnet_ids)},
                {'ParameterKey': 'SecurityGroupId', 'ParameterValue': security_group_id},
                {'ParameterKey': 'DatabaseSecurityGroupId', 'ParameterValue': database_security_group_id},
                {'ParameterKey': 'NamespaceId', 'ParameterValue': namespace_id},
                {'ParameterKey': 'NamespaceName', 'ParameterValue': namespace_name},
                {'ParameterKey': 'PublicNamespaceId', 'ParameterValue': public_namespace_id},
                {'ParameterKey': 'ExecutionRoleArn', 'ParameterValue': execution_role_arn},
                {'ParameterKey': 'TaskRoleArn', 'ParameterValue': task_role_arn}
            ],
            Capabilities=['CAPABILITY_NAMED_IAM'],
        )
        logger.info(f"Stack {stack_name} creation initiated: {response}")

        # Wait for stack creation to complete
        waiter = cloudformation.get_waiter('stack_create_complete')
        waiter.wait(StackName=stack_name)
        logger.info(f"Stack {stack_name} created successfully.")

        stack = cloudformation.describe_stacks(StackName=stack_name)
        outputs = {output['OutputKey']: output['OutputValue'] for output in stack['Stacks'][0]['Outputs']}
        logger.info(f"Stack outputs: {outputs}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'customerName': customer_name,
                'projectName': project_name,
                'ClusterName': outputs.get('ClusterName'),
                'WordpressTaskDefinition': outputs.get('WordpressTaskDefinition'),
                'DatabaseTaskDefinition': outputs.get('DatabaseTaskDefinition'),
                'DatabaseServiceDiscoveryArn': outputs.get('DatabaseServiceDiscoveryArn'),
                'WordpressServiceDiscoveryArn': outputs.get('WordpressServiceDiscoveryArn')
            })
        }

    except Exception as e:
        logger.error(f"Failed to create stack {stack_name}: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Failed to create stack for {customer_name}', 'error': str(e)})
        }
