import json
import pprint
import boto3

def find_used_instance_types(event, context):
    region = event['region']

    types = set()

    print("Looking for instance types used in region %s" % region)
    try:
        client = boto3.client('autoscaling', region_name = region)
        paginator = client.get_paginator('describe_launch_configurations')
        pages = paginator.paginate()
        for page in pages:
            for lc in page['LaunchConfigurations']:
                instance_type = lc['InstanceType']
                types.add(instance_type)
                print ("found lc %s -> %s" % (lc['LaunchConfigurationName'], instance_type))
        types = list(types)
        sorted(types)

    except Exception as e:
        return {
            "statusCode": 500,
            "body": str(e),
        }

    return {
        "statusCode": 200,
        "body": json.dumps(types)
    }
