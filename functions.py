import json
import pprint
import boto3

def list_azs(region):
    client = boto3.client("ec2")
    azs = client.describe_availability_zones()
    names = [a['ZoneName'] for a in azs['AvailabilityZones']]
    return names

def find_lc_instance_types(region):
    types = set()
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
    return types

def find_used_instance_types(event, context):
    region = event['region']


    print("Looking for instance types used in region %s" % region)
    try:
        types = find_lc_instance_types(region)
        azs = list_azs(region)
        pprint.pprint(azs)

    except Exception as e:
        return {
            "statusCode": 500,
            "body": str(e),
        }

    return {
        "statusCode": 200,
        "body": types
    }
