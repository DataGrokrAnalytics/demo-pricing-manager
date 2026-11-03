"""Pricing tool that writes prices (fictional demo app)."""

import os

import boto3
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
dynamodb = boto3.resource("dynamodb")
prices = dynamodb.Table(os.environ.get("PRICES_TABLE", "demo-pricing-db"))

ENTERPRISE_PRICING_API = os.environ.get(
    "ENTERPRISE_PRICING_API", "https://pricing.enterprise.example.com/v2"
)


@app.get("/prices/<sku>")
def get_price(sku):
    return jsonify(prices.get_item(Key={"sku": sku}).get("Item", {}))


@app.post("/prices/<sku>")
def set_price(sku):
    body = request.get_json()
    prices.put_item(Item={"sku": sku, "price": body["price"]})
    prices.update_item(
        Key={"sku": sku},
        UpdateExpression="SET reviewed = :r",
        ExpressionAttributeValues={":r": False},
    )
    # Publish the new price to the enterprise pricing system.
    requests.post(f"{ENTERPRISE_PRICING_API}/prices", json={"sku": sku, **body}, timeout=10)
    return jsonify({"ok": True})
