#created by Cejay Henry for sememster 3 case study project
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")

    try:
        # Extract the body of the CloudFormation output from create_ecs_clusster.py
        cloudformation_output = json.loads(event['cloudformationOutput']['body'])
    except KeyError as e:
        logger.error(f"Missing key in event: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': f'Missing key in event: {e}',
                'error': str(e)
            })
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid JSON in cloudformationOutput',
                'error': str(e)
            })
        }

    
    customer_name = cloudformation_output.get('customerName')
    project_name = cloudformation_output.get('projectName')
    cluster_name = cloudformation_output.get('ClusterName')
    wordpress_task_definition = cloudformation_output.get('WordpressTaskDefinition')
    database_task_definition = cloudformation_output.get('DatabaseTaskDefinition')
    database_service_discovery_arn = cloudformation_output.get('DatabaseServiceDiscoveryArn')
    wordpress_service_discovery_arn = cloudformation_output.get('WordpressServiceDiscoveryArn')

  #parse outputt
    return {
        'customerName': customer_name,
        'projectName': project_name,
        'ClusterName': cluster_name,
        'WordpressTaskDefinition': wordpress_task_definition,
        'DatabaseTaskDefinition': database_task_definition,
        'DatabaseServiceDiscoveryArn': database_service_discovery_arn,
        'WordpressServiceDiscoveryArn': wordpress_service_discovery_arn
    }
