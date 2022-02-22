import json
import boto3
from datetime import date
import datetime



def lambda_handler(event, context):
    date_today = datetime.datetime.today()
    today = f"{date_today.year}-{str(date_today.month).zfill(2)}-{str(date_today.day).zfill(2)}"
    head_of_month = f"{date_today.year}-{str(date_today.month).zfill(2)}-01"

    services = get_montlycost(head_of_month, today)
    block = create_block(services)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": block
        }),
    }


def get_montlycost(head_of_month, today):
    billing_client = boto3.client('ce')
    response = billing_client.get_cost_and_usage(
        TimePeriod={
            'Start': head_of_month,
            'End': today },
        Granularity='MONTHLY',
        Metrics=[ 'UnblendedCost',],
        GroupBy= [
            { 'Type':'DIMENSION', 'Key':'SERVICE' }
        ],
    )
    cost_with_services = response["ResultsByTime"][0]["Groups"]
    return cost_with_services

def create_block(services):
    for service in services:
        print(service["Keys"])
        print(service["Metrics"]["UnblendedCost"])