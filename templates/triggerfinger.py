import json
import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

stepfunctions = boto3.client('stepfunctions')

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    
    # Retrieve the pathway option from the from backend server and convert them
    option = event.get('options')
    if option == "1":
        pathway = 1
    elif option == "2":
        pathway = 2
    else:
        raise ValueError("Invalid or missing option. 'options' must be '1' or '2'.")

    # Validate required parameters
    customer_name = event.get('customerName')
    project_name = event.get('projectName')
    if not customer_name:
        raise ValueError("customerName is required")
    if not project_name:
        raise ValueError("projectName is required")

    # Check for the existence of the state machine ARN in environment variables
    state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
    if not state_machine_arn:
        raise ValueError("STATE_MACHINE_ARN is required")

    # Prepare input payload for the state function
    input_payload = {
        'pathway': pathway,
        'customerName': customer_name,
        'projectName': project_name
    }

    try:
        # Start the step function execution
        response = stepfunctions.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps(input_payload)
        )
        logger.info(f"Step Function execution started: {response}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Step Function execution started successfully',
                'executionArn': response['executionArn']
            })
        }

    except Exception as e:
        # Log and return an error response if the step function call fails
        logger.error(f"Failed to start Step Function execution: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to start Step Function execution',
                'error': str(e)
            })
        }
