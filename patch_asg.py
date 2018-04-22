import json
import boto3
from fleece.xray import monkey_patch_botocore_for_xray
from utils import invoke
monkey_patch_botocore_for_xray()


def map_subnets_to_azs(subnets):
    client = boto3.client('ec2')
    subnet_descs = client.describe_subnets(SubnetIds=subnets)
    subnet_to_az = dict()
    for subnet in subnet_descs["Subnets"]:
        subnet_to_az[subnet["SubnetId"]] = subnet["AvailabilityZone"]
    return subnet_to_az


def handler(event, context):
    region = event['region']
    asg = event['asg']
    print("patch-asg(%s)" % asg['asg'])
    subnets = asg['subnets']
    unavailable_types = event['unavailable_types']
    subnet_to_az = map_subnets_to_azs(subnets)
    invoke('exclude-subnets', {
        "subnets": subnet_to_az,
        "unavailable_types": unavailable_types,
        "asg": asg,
        "region": region,
    })

    print(json.dumps(subnet_to_az, indent=2))
    return {
        "statusCode": 200,
        "body": event,
    }
