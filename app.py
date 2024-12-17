from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app) 

API_KEY = "637ea8d2dfddfeccc53f222d"
BASE_URL = "https://v6.exchangerate-api.com/v6"
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CNY", "INR"]


# latest rate interface
@app.route('/rates', methods=['GET'])
def get_rates():
    base_currency = request.args.get('base', 'USD')
    if base_currency not in CURRENCIES:
        return jsonify({"status": "error", "error": "Invalid base currency"}), 400

    try:
        response = requests.get(f"{BASE_URL}/{API_KEY}/latest/{base_currency}", timeout=5)
        response.raise_for_status()
        data = response.json()
        if data["result"] != "success":
            return jsonify({"status": "error", "error": "Failed to fetch rates"}), 500

        rates = data["conversion_rates"]  # 提取汇率数据
        return jsonify({"status": "success", "rates": rates})
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# history rate interface
@app.route('/history', methods=['GET'])
def get_history():
    base_currency = request.args.get('base', 'USD')
    target_currency = request.args.get('target', 'EUR')
    period = request.args.get('period', '1M')

    if base_currency not in CURRENCIES or target_currency not in CURRENCIES:
        return jsonify({"status": "error", "error": "Invalid currency"}), 400

    # Range
    end_date = datetime.now()
    if period == "WEEK":
        start_date = end_date - timedelta(weeks=1)
    elif period == "MONTH":
        start_date = end_date - timedelta(days=30)
    elif period == "YEAR":
        start_date = end_date - timedelta(days=365)
    else:
        return jsonify({"status": "error", "error": "Invalid period value"}), 400

    history_data = []
    current_date = start_date
    while current_date <= end_date:
        simulated_rate = round(1.1 + random.uniform(-0.05, 0.05), 4)
        history_data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "rate": simulated_rate,
        })
        current_date += timedelta(days=1)

    return jsonify({
        "status": "success",
        "base": base_currency,
        "target": target_currency,
        "rates": history_data,
    })


@app.route('/watchlist', methods=['POST'])
def get_watchlist_rates():
    request_data = request.get_json()
    if not request_data or "items" not in request_data:
        return jsonify({"status": "error", "error": "Invalid request payload"}), 400

    watchlist = request_data["items"]
    response_data = []

    for item in watchlist:
        base_currency = item.get("baseCurrency")
        target_currency = item.get("targetCurrency")
        if base_currency not in CURRENCIES or target_currency not in CURRENCIES:
            response_data.append({
                "baseCurrency": base_currency,
                "targetCurrency": target_currency,
                "rate": None,
                "error": "Invalid currency",
            })
            continue

        try:
            simulated_rate = round(1.1 + random.uniform(-0.05, 0.05), 4)
            response_data.append({
                "baseCurrency": base_currency,
                "targetCurrency": target_currency,
                "rate": simulated_rate,
            })
        except Exception as e:
            response_data.append({
                "baseCurrency": base_currency,
                "targetCurrency": target_currency,
                "rate": None,
                "error": str(e),
            })

    return jsonify({"status": "success", "data": response_data})


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
