#!/usr/bin/env python2.7
# coding:utf-8
import os
from datetime import datetime as dt
import boto3
import botocore


def lambda_handler(event, context):

    rds_instance_name = os.environ.get('rds_instance_name')
    rds_log_prefix = os.environ.get('rds_log_prefix')
    s3_bucket_name = os.environ.get('s3_bucket_name')
    s3_bucket_prefix = os.environ.get('s3_bucket_prefix', "")

    region = os.environ.get('region', "ap-northeast-1")

    rds_client = boto3.client('rds', region_name=region)
    s3_client = boto3.client('s3', region_name=region)

    db_logs = rds_client.describe_db_log_files(DBInstanceIdentifier=rds_instance_name,
                                               FilenameContains=rds_log_prefix)

    for db_log in db_logs['DescribeDBLogFiles']:
        if db_log["LogFileName"].endswith(".log") is True:
            continue

        keyname = str(s3_bucket_prefix) + dt.fromtimestamp(float(db_log['LastWritten'])/1000).strftime('%Y%m%d%H%M%S') + "-" + str(db_log['LogFileName']).replace("/", "_")

        try:
            s3_client.head_object(Bucket=s3_bucket_name,
                                  Key=keyname)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "403":
                pass
            else:
                raise
        else:
            print("Already exist ", keyname)
            continue

        log_file = rds_client.download_db_log_file_portion(DBInstanceIdentifier=rds_instance_name,
                                                           LogFileName=db_log['LogFileName'],
                                                           Marker='0')

        log_file_data = log_file['LogFileData']
        while log_file['AdditionalDataPending']:
            log_file = rds_client.download_db_log_file_portion(DBInstanceIdentifier=rds_instance_name,
                                                               LogFileName=db_log['LogFileName'],
                                                               Marker=log_file['Marker'])
            log_file_data += log_file['LogFileData']

        res = s3_client.put_object(Bucket=s3_bucket_name,
                                   Key=keyname,
                                   Body=str.encode(log_file_data))
        print(res)
        # res = s3_client.put_object(Bucket=s3_bucket_name, Key=s3_fetch_manage_file,
        #                            Body=str.encode(json.dumps(db_logs)))
    return "end"
