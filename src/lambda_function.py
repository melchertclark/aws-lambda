import json
import os
import boto3
import requests
import time
import logging
from datetime import datetime, timezone

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

API_URL = "https://api.limitless.ai/v1/lifelogs"
API_KEY = os.environ['API_KEY']
BUCKET_NAME = os.environ['BUCKET_NAME']
TIMEZONE = "America/New_York"
RETRY_LIMIT = 5
BATCH_UPLOAD_SIZE = 500  # Number of entries per S3 file

s3_client = boto3.client('s3')
headers = {
    "X-API-Key": API_KEY,
    "Accept": "application/json"
}

def fetch_entries(start, end):
    cursor = None
    batch_number = 1
    total_entries = 0

    while True:
        params = {
            "start": start,
            "end": end,
            "timezone": TIMEZONE,
            "cursor": cursor,
            "direction": "asc",
            "limit": 100
        }
        logger.info(f"[Batch {batch_number}] Fetching entries with params: {params}")

        for attempt in range(RETRY_LIMIT):
            try:
                response = requests.get(API_URL, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                break
            except Exception as e:
                logger.warning(f"Error (batch {batch_number}, attempt {attempt+1}): {e}")
                time.sleep(2)
        else:
            logger.error(f"Failed batch {batch_number} after {RETRY_LIMIT} attempts.")
            break

        data = response.json()
        batch = data["data"]["lifelogs"]
        logger.info(f"Fetched {len(batch)} entries in batch {batch_number}")

        if batch:
            yield batch, batch_number
            total_entries += len(batch)

        cursor = data["meta"]["lifelogs"].get("nextCursor")
        if not cursor:
            logger.info(f"No cursor found; ending after {batch_number} batches.")
            break

        time.sleep(1)
        batch_number += 1

def upload_batches_to_s3(all_batches, now):
    chunk = []
    chunk_number = 1
    total_uploaded = 0

    for batch, batch_number in all_batches:
        chunk.extend(batch)
        while len(chunk) >= BATCH_UPLOAD_SIZE:
            filename = now.strftime(f"lifelogs_catchup_%Y%m%dT%H%M%SZ_part{chunk_number}.json")
            json_body = json.dumps(chunk[:BATCH_UPLOAD_SIZE], indent=2)
            try:
                s3_client.put_object(Bucket=BUCKET_NAME, Key=filename, Body=json_body)
                logger.info(f"Uploaded {BATCH_UPLOAD_SIZE} entries to {filename}")
            except Exception as e:
                logger.error(f"Failed to upload {filename}: {e}")
            total_uploaded += BATCH_UPLOAD_SIZE
            chunk = chunk[BATCH_UPLOAD_SIZE:]
            chunk_number += 1

    # Upload any remaining entries
    if chunk:
        filename = now.strftime(f"lifelogs_catchup_%Y%m%dT%H%M%SZ_part{chunk_number}.json")
        json_body = json.dumps(chunk, indent=2)
        try:
            s3_client.put_object(Bucket=BUCKET_NAME, Key=filename, Body=json_body)
            logger.info(f"Uploaded {len(chunk)} entries to {filename}")
        except Exception as e:
            logger.error(f"Failed to upload {filename}: {e}")
        total_uploaded += len(chunk)

    return total_uploaded

def lambda_handler(event, context):
    now = datetime.now(timezone.utc)
    end = now.isoformat().replace('+00:00', 'Z')
    start = '2025-03-13T00:00:00Z'  # Adjust as needed

    logger.info(f"Fetching lifelog entries from {start} to {end}")
    all_batches = fetch_entries(start, end)
    uploaded_count = upload_batches_to_s3(all_batches, now)

    logger.info(f"Uploaded a total of {uploaded_count} entries to S3.")
    return {
        'statusCode': 200,
        'body': f"Fetched and uploaded {uploaded_count} entries in batches."
    }