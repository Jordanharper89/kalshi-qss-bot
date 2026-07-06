import os
import time
import base64
import json
import requests
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

load_dotenv()

KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH")
KALSHI_BASE_URL = os.getenv(
    "KALSHI_BASE_URL",
    "https://api.elections.kalshi.com/trade-api/v2"
)

SIGNING_PREFIX = "/trade-api/v2"


def load_private_key():
    with open(KALSHI_PRIVATE_KEY_PATH, "rb") as f:
        key_data = f.read()

    return serialization.load_pem_private_key(
        key_data,
        password=None,
    )


def sign_request(method, endpoint_path):
    timestamp = str(int(time.time() * 1000))
    path_to_sign = SIGNING_PREFIX + endpoint_path
    message = timestamp + method.upper() + path_to_sign

    private_key = load_private_key()

    signature = private_key.sign(
        message.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    return {
        "KALSHI-ACCESS-KEY": KALSHI_KEY_ID,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode("utf-8"),
    }


def kalshi_get(endpoint_path):
    headers = sign_request("GET", endpoint_path)
    url = KALSHI_BASE_URL + endpoint_path

    return requests.get(
        url,
        headers=headers,
        timeout=20,
    )


def get_balance():
    response = kalshi_get("/portfolio/balance")

    if response.status_code != 200:
        print("BALANCE ERROR")
        print("Status:", response.status_code)
        print(response.text)
        return

    data = response.json()

    balance_dollars = data.get("balance_dollars", "0")
    portfolio_value = data.get("portfolio_value", 0)

    try:
        portfolio_value_dollars = round(float(portfolio_value) / 100, 2)
    except:
        portfolio_value_dollars = 0

    print("=" * 40)
    print("KALSHI ACCOUNT")
    print("=" * 40)
    print("Balance: $" + str(balance_dollars))
    print("Portfolio Value: $" + str(portfolio_value_dollars))
    print("Status: Connected")
    print("=" * 40)


if __name__ == "__main__":
    get_balance()