import json
import boto3
from datetime import date
import datetime
import requests
import os

def lambda_handler(event, context):
    date_today = datetime.datetime.today()
    today = f"{date_today.year}-{str(date_today.month).zfill(2)}-{str(date_today.day).zfill(2)}"
    head_of_month = f"{date_today.year}-{str(date_today.month).zfill(2)}-01"
    services = get_montlycost(head_of_month, today) #cost messured from the head of the month to today
    block = create_block(services) #get monthly cost with services name
    header = create_headers()
    payload = create_params(block)
    res = requests.post("https://api.line.me/v2/bot/message/push", headers=header, data=payload)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"{res.content}"
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
    with open('Blocks/flex_message_frame.json') as block:
        block_dict = json.load(block)
    sum_of_cost = 0.0
    for service in services:
        if service["Metrics"]["UnblendedCost"]["Amount"] == "0":
            continue
        component = create_component()
        sum_of_cost += float(service["Metrics"]["UnblendedCost"]["Amount"])
        inserted_component = insert_info(component, service["Metrics"]["UnblendedCost"]["Amount"], service["Keys"][0], sum_of_cost)
        block_dict["contents"]["contents"].append(inserted_component)
    return block_dict

def create_component():
    with open('Blocks/flex_message_component.json') as component:
        component = json.load(component)
    return component

def insert_info(component, cost, service_name, sunk_cost):
    cost = float(cost)
    component["header"]["contents"][0]["text"] = f"{round(cost, 3)} USD"
    component["header"]["contents"][1]["text"] = f"{round(sunk_cost, 3)} USD"
    component["header"]["contents"][2]["contents"][0]["width"] = f"{int((cost/2) * 100)}%"
    component["body"]["contents"][0]["contents"][0]["text"] = service_name
    return component

def create_headers():
    token = f"Bearer {os.environ['LINE_TOKEN']}"
    header = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    return header

def create_params(block):
    payload = {
        "to": os.environ['MY_LINE_ID'],
        "messages": [ block ]
    }
    return json.dumps(payload)