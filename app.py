from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import datetime

app = Flask(__name__)
CORS(app)

# 1. Load the Brain
try:
    model = joblib.load('model.pkl')
except:
    print("CRITICAL ERROR: 'model.pkl' not found.")

# 2. Exchange Rates
EXCHANGE_RATES = { "USD": 1.0, "EUR": 1.08, "INR": 0.012 }

@app.route('/analyze-risk', methods=['POST'])
def analyze_risk():
    try:
        data = request.get_json()
        tx_id = data.get('tx_id', 'TXN-MANUAL')
        currency = data.get('currency', 'USD')
        raw_amount = float(data.get('amount', 0))

        # --- FIX 1: ZERO LOGIC ---
        # If amount is 0 or negative, return 0% immediately.
        if raw_amount <= 0:
            return jsonify({
                "tx_id": tx_id,
                "original_amount": raw_amount,
                "currency": currency,
                "normalized_usd": 0.0,
                "fraud_probability": 0.0,
                "status": "Invalid Amount",
                "time": datetime.datetime.now().strftime("%H:%M:%S")
            })

        # --- FIX 2: NORMALIZATION ---
        rate = EXCHANGE_RATES.get(currency, 1.0)
        normalized_amount = raw_amount * rate

        # --- FIX 3: STABILITY (No Randomness) ---
        # We use a solid vector of Zeros. This ensures the score is calculated 
        # PURELY based on the amount, with no random fluctuations.
        input_data = [0.0] * 30
        input_data[29] = normalized_amount 
        
        # Get Prediction
        probability = model.predict_proba([input_data])[0][1]
        
        return jsonify({
            "tx_id": tx_id,
            "original_amount": raw_amount,
            "currency": currency,
            "normalized_usd": round(normalized_amount, 2),
            "fraud_probability": float(probability),
            "status": "High Risk" if probability > 0.5 else "Safe",
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        })

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(port=5000, debug=True)