import json
import os

print('Loading function')


def lambda_handler(event, context):

    rds_instance_name = os.environ['rds_instance_name']
    print("rds instance = " + rds_instance_name)
    return "Fin"
