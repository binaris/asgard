from utils import http_error_handling
import boto3
from fleece.xray import monkey_patch_botocore_for_xray
import os

monkey_patch_botocore_for_xray()

cache = dict()


def get_lc_instance_type(client, lc_name):
    desc = client.describe_launch_configurations(
        LaunchConfigurationNames=[lc_name]
    )
    if not len(desc['LaunchConfigurations']):
        raise Exception('LC %s not found' % lc_name)
    lc = desc['LaunchConfigurations'][0]
    used_instance_type = lc['InstanceType']
    print("%s uses instance type %s" % (lc_name, used_instance_type))
    return used_instance_type


@http_error_handling
def handler(event, context):
    region = event['region']
    lc = event['lc']
    stage = os.environ['stage']
    if lc in cache:
        return cache[lc]

    client = boto3.client("autoscaling", region_name=region)
    used_instance_type = get_lc_instance_type(client, lc)
    cache[lc] = used_instance_type
    return used_instance_type
