import json
import os
import boto3
import requests
import time
from datetime import datetime, timezone

DEBUG = True

API_URL = "https://api.limitless.ai/v1/lifelogs"
API_KEY = os.environ['API_KEY']
BUCKET_NAME = os.environ['BUCKET_NAME']
TIMEZONE = "America/New_York"
RETRY_LIMIT = 5

s3_client = boto3.client('s3')

headers = {
    "X-API-Key": API_KEY,
    "Accept": "application/json"
}

def fetch_entries(start, end):
    entries = []
    cursor = None
    batch_number = 1

    while True:
        params = {
            "start": start,
            "end": end,
            "timezone": TIMEZONE,
            "cursor": cursor,
            "direction": "asc",
            "limit": 100
        }
        if DEBUG:
            print(f"[Batch {batch_number}] Fetching entries with params: {params}")

        attempts = 0
        while attempts < RETRY_LIMIT:
            try:
                response = requests.get(API_URL, headers=headers, params=params)
                response.raise_for_status()
                break
            except Exception as e:
                attempts += 1
                print(f"Error encountered (batch {batch_number}, attempt {attempts}): {e}. Retrying...")
                time.sleep(2)
        if attempts == RETRY_LIMIT:
            print(f"Failed batch {batch_number} after {RETRY_LIMIT} attempts.")
            break

        data = response.json()
        batch = data["data"]["lifelogs"]
        entries.extend(batch)

        cursor = data["meta"]["lifelogs"].get("nextCursor")
        if not cursor:
            if DEBUG:
                print(f"No cursor found; ending after {batch_number} batches.")
            break
        
        time.sleep(1)
        batch_number += 1

    return entries

def lambda_handler(event, context):
    now = datetime.now(timezone.utc)
    end = now.isoformat().replace('+00:00', 'Z')
    start = '2025-03-13T00:00:00Z'  # Adjust as needed

    print(f"Fetching lifelog entries from {start} to {end}")
    entries = fetch_entries(start, end)
    print(f"Fetched {len(entries)} entries.")

    if entries:
        filename = now.strftime("lifelogs_catchup_%Y%m%dT%H%M%SZ.json")
        json_body = json.dumps(entries, indent=2)

        print(f"Saving entries to S3 bucket '{BUCKET_NAME}' as '{filename}'")
        s3_client.put_object(Bucket=BUCKET_NAME, Key=filename, Body=json_body)
        print("Successfully uploaded entries to S3.")
    else:
        print("No new entries fetched. Nothing uploaded to S3.")

    return {
        'statusCode': 200,
        'body': f"Fetched and uploaded {len(entries)} entries."
    }