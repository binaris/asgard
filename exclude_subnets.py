from utils import http_error_handling
import json
import boto3
from fleece.xray import monkey_patch_botocore_for_xray
import os

monkey_patch_botocore_for_xray()

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


def find_subnets_to_exclude(unavailable, used, asg, subnet_to_az):
    unavailable_azs = unavailable[used]
    subnets_to_exclude = []
    for subnet in asg['subnets']:
        subnet_az = subnet_to_az[subnet]
        if subnet_az in unavailable_azs:
            subnets_to_exclude.append(subnet)

    return subnets_to_exclude


def record_excluded_subnets_as_tags(subnets_to_exclude, client, asg):
    excluded_subnet_tags = ["disabled-%s" % s for s in subnets_to_exclude]
    print("Adding tags to ASG: " + ",".join(excluded_subnet_tags))
    tags = [{
        'ResourceId': asg,
        'ResourceType': 'auto-scaling-group',
        'Key': t,
        'Value': 'true',
        'PropagateAtLaunch': False,
    } for t in excluded_subnet_tags]
    client.create_or_update_tags(Tags=tags)


@http_error_handling
def handler(event, context):

    print(json.dumps(event))
    asg = event['asg']['asg']
    stage = os.environ['stage']
    print("Exclude-subnets(%s)" % asg)
    if "prod" in asg and stage != 'prod':
        print("Yikes! Not touching prod...")
        return
    lc_name = event['asg']['lc']
    unavailable_types = event['unavailable_types']
    subnet_to_az = event['subnets']
    region = event['region']

    client = boto3.client("autoscaling", region_name = region)

    used_instance_type = get_lc_instance_type(client, lc_name)
    if used_instance_type not in unavailable_types:
        return False

    subnets_to_exclude = find_subnets_to_exclude(unavailable_types,
                                                 used_instance_type,
                                                 event['asg'],
                                                 subnet_to_az)

    if not len(subnets_to_exclude):
        print("No subnets to exclude")
        return False

    print("Subnets [%s] should be excluded from ASG %s"
          % (",".join(subnets_to_exclude), asg))

    current_subnets = set(event['asg']['subnets'])
    remaining = current_subnets.difference(set(subnets_to_exclude))
    remaining = ",".join(list(remaining))

    print("Updating ASG %s to include only the following subnets: %s"
          % (asg, remaining))

    record_excluded_subnets_as_tags(subnets_to_exclude, client, asg)

    client.update_auto_scaling_group(
        AutoScalingGroupName=asg,
        VPCZoneIdentifier=remaining
    )
    return True
