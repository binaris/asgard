import traceback
import boto3
import json
import os

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

def invoke(func, params):
    j = json.dumps(params)
    stage = os.environ["stage"]
    print("Invoking %s (stage: %s) with params: %s" % (func, stage, j))
    client = boto3.client('lambda')
    client.invoke(FunctionName="asgard-%s-%s" % (stage, func),
                  InvocationType="Event",
                  Payload=bytes(j, "utf8")
                  )

