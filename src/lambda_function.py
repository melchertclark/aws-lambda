import json
import requests

def lambda_handler(event, context):
    # Example: fetch something from web and return it
    res = requests.get("https://api.github.com")
    return {
        "statusCode": res.status_code,
        "body": json.dumps(res.json())
    }

# for local debugging/testing
if __name__ == "__main__":
    fake_event = {}
    print(lambda_handler(fake_event, None))
