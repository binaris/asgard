from utils import http_error_handling
import json
import boto3

@http_error_handling
def handler(event, context):

    print(json.dumps(event))
    asg = event['asg']['asg']
    print("Exclude-subnets(%s)" % asg)
    if "prod" in asg:
        print("Yikes! Not touching prod...")
        return
    lc_name = event['asg']['lc']
    unavailable_types = event['unavailable_types']
    subnet_to_az = event['subnets']
    region = event['region']

    client = boto3.client("autoscaling", region_name = region)
    desc = client.describe_launch_configurations(
        LaunchConfigurationNames=[lc_name]
    )
    lc = desc['LaunchConfigurations'][0]
    used_instance_type = lc['InstanceType']
    print("lc %s for asg %s uses instance type %s" % (lc_name, asg, used_instance_type))
    if used_instance_type not in unavailable_types:
        return False
    unavailable_azs = unavailable_types[used_instance_type]
    subnets_to_exclude = []
    for subnet in event['asg']['subnets']:
        subnet_az = subnet_to_az[subnet]
        if subnet_az in unavailable_azs:
            subnets_to_exclude.append(subnet)

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
    client.update_auto_scaling_group(
        AutoScalingGroupName=asg,
        VPCZoneIdentifier=remaining
    )
    return True
