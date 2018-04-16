# The Problem with Auto Scaling Groups

ASGs don't have it well when you ask them to launch *spot* instances in availability zones where a particular instance-type might not be available at all. In such cases, the ASG generates spot instance requests that simply hang forever and are never fulfilled or rejected, thus entering a stuck state where additional instances do not get launched.

As a result, when every now and then a certain instance type is not available in a particular AZ, there's a danger that ASGs that operate in it (meaning configured with subnets that reside in a problematic AZ) will not be able to scale out. Even if such a hanging spot request is cancelled, if the ASG in question has the least instances in that AZ, it will keep trying to launch spots in it, and will keep hanging.

# Asgard

Asgard is a set of Lambda functions that monitor your ASGs and when they detect a problematic AZ (one that's missing spot instances for the instance-type the ASG is using), it removes that AZ from the ASG. Asgard is thus a patch for ASGs to make them work better with spot instances. It also "returns" AZs to the ASG once spot instances are again available.

# How it works

Asgard runs every minute in every region you specify. It iterates though the ASGs in the region, finding out all the various instance-types being used. It then queries the spot market to determine if any of those instance types are missing from any of the AZs in the region. If so, it removes those AZs from any effected ASG.


# Requirements

- Docker
- AWS CLI (with credentials configured)

# Installing

`make deploy` deploys the functions to a Lambda "stage" called `dev`.

`make deploy stage=prod` will deploy to `prod`.


