import json
from datetime import datetime, timedelta
import boto3
from fleece.xray import monkey_patch_botocore_for_xray
from utils import http_error_handling, invoke

monkey_patch_botocore_for_xray()


def list_azs(region):
    client = boto3.client("ec2", region_name=region)
    azs = client.describe_availability_zones()
    names = [a['ZoneName'] for a in azs['AvailabilityZones']]
    return names


def find_lc_instance_types(region):
    types = set()
    client = boto3.client('autoscaling', region_name=region)
    paginator = client.get_paginator('describe_launch_configurations')
    pages = paginator.paginate()
    for page in pages:
        for lc in page['LaunchConfigurations']:
            instance_type = lc['InstanceType']
            types.add(instance_type)
            # print ("found lc %s -> %s" % (lc['LaunchConfigurationName'], instance_type))
    types = list(types)
    sorted(types)
    return types


def get_spot_history(region, types):

    client = boto3.client('ec2', region_name=region)
    paginator = client.get_paginator('describe_spot_price_history')
    since = datetime.utcnow() - timedelta(hours=1)
    print('Fetching spot price history since %s' % (str(since)))
    pages = paginator.paginate(
        InstanceTypes=types,
        Filters=[
            {
                'Name': 'product-description',
                'Values': ['Linux/UNIX'],
            }
        ]
    )

    types_in_azs = dict()

    for page in pages:
        for record in page['SpotPriceHistory']:
            t = record['InstanceType']
            az = record['AvailabilityZone']
            if az not in types_in_azs:
                types_in_azs[az] = set()
            types_in_azs[az].add(t)

    return {az: list(types) for az, types in types_in_azs.items()}


def find_types_missing_in_azs(used_types, azs, available_types):
    ret = dict()
    for used_type in used_types:
        for az in azs:
            if used_type not in available_types[az]:
                print(
                    "Type %s in-use but not available in %s" %
                    (used_type, az))
                if az not in ret:
                    ret[used_type] = [az]
                else:
                    ret[used_type].append(az)
    return ret


def list_asgs(region):

    client = boto3.client('autoscaling', region_name=region)
    paginator = client.get_paginator('describe_auto_scaling_groups')
    asgs = []
    for page in paginator.paginate():
        for group in page['AutoScalingGroups']:
            asgs.append({
                "asg": group['AutoScalingGroupName'],
                "lc": group['LaunchConfigurationName'],
                "subnets": group['VPCZoneIdentifier'].split(","),
            })

    return asgs


@http_error_handling
def handler(event, _):
    region = event['region']
    if not region:
        raise Exception('region must be passed in')

    print("Looking for instance types used in region %s" % region)
    used_types = find_lc_instance_types(region)
    print("Instance types used in region %s: %s" %
          (region, ",".join(used_types)))
    azs = list_azs(region)
    print("AZs in region %s: %s" % (region, ",".join(azs)))
    history = get_spot_history(region, used_types)
    print("Spots available in each AZ: %s" % json.dumps(history, indent=1))
    unavailable_types = find_types_missing_in_azs(used_types, azs, history)

    asgs = list_asgs(region)
    for asg in asgs:
        invoke("patch-asg", {
            "asg": asg,
            "region": region,
            "unavailable_types": unavailable_types,
        })
