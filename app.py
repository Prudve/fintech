from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import joblib
import datetime

app = Flask(__name__)
CORS(app)

# 1. Load the Brain
try:
    # We use a path trick to make sure it finds the model in the main folder
    model = joblib.load('model.pkl') 
    # IMPORTANT: Replace YOUR_USERNAME above with your actual PythonAnywhere username!
    # If that's too hard, just try: model = joblib.load('model.pkl')
except:
    model = None
    print("CRITICAL ERROR: 'model.pkl' not found.")

EXCHANGE_RATES = { "USD": 1.0, "EUR": 1.08, "INR": 0.012 }

# --- NEW: THIS CONNECTS THE WEB PAGE ---
@app.route('/')
def home():
    return render_template('index.html')

# --- THE FRAUD LOGIC ---
@app.route('/analyze-risk', methods=['POST'])
def analyze_risk():
    try:
        data = request.get_json()
        tx_id = data.get('tx_id', 'TXN-MANUAL')
        currency = data.get('currency', 'USD')
        raw_amount = float(data.get('amount', 0))

        # Zero Logic
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

        # Normalization
        rate = EXCHANGE_RATES.get(currency, 1.0)
        normalized_amount = raw_amount * rate

        # Prediction
        input_data = [0.0] * 30
        input_data[29] = normalized_amount 
        
        if model:
            probability = model.predict_proba([input_data])[0][1]
        else:
            probability = 0.0 # Fallback if model missing

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
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
