import traceback
import boto3
import json
import os
from fleece.xray import trace_xray_subsegment


def http_error_handling(func):
    def func_wrapper(*args, **kwds):
        try:
            ret = func(*args, **kwds)
            return {
                "statusCode": 200,
                "body": ret,
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": traceback.format_exc(),
            }
    return func_wrapper

@trace_xray_subsegment()
def invoke(func, params, block=False):
    j = json.dumps(params)
    stage = os.environ["stage"]
    print("Invoking %s (stage: %s) with params: %s" % (func, stage, j))
    client = boto3.client('lambda')
    res = client.invoke(FunctionName="asgard-%s-%s" % (stage, func),
                  InvocationType="RequestResponse" if block else "Event",
                  Payload=bytes(j, "utf8")
                  )
    if block:
        payload = res['Payload'].read()
        j = json.loads(payload)
        if j["statusCode"] != 200:
            raise Exception(payload)
        return j["body"]

