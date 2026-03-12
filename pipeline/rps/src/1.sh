
echo " STEP 6.5 — Save Training Feature List"

python - << 'EOF'
import joblib, json

model = joblib.load("rps/src/models/p_ml_model.pkl")
features = list(model.feature_names_)

with open("rps/src/models/training_features.json", "w") as f:
    json.dump(features, f, indent=4)

print("Saved training feature list.")
EOF



echo " STEP 7 — Start FastAPI Server"

echo "Run this command manually in a new terminal:"
echo "---------------------------------------------"
echo "python -m uvicorn rps.src.service.api:app --reload --port 8000"
echo "---------------------------------------------"

echo " TEST CURL COMMAND"
echo ""
echo "curl -X POST \"http://127.0.0.1:8000/score\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"features\": { \"total_amount_1h\": 1200, \"txn_count_1h\": 3, \"unique_cp_1h\": 1, \"avg_amount_1h\": 400, \"max_amount_1h\": 900, \"min_amount_1h\": 100, \"total_amount_24h\": 4500, \"txn_count_24h\": 7, \"unique_cp_24h\": 4, \"avg_amount_24h\": 650, \"max_amount_24h\": 2000, \"min_amount_24h\": 50, \"total_amount_7d\": 15000, \"txn_count_7d\": 20, \"unique_cp_7d\": 5, \"avg_amount_7d\": 750, \"max_amount_7d\": 5000, \"min_amount_7d\": 50, \"total_amount_30d\": 42000, \"txn_count_30d\": 90, \"unique_cp_30d\": 15, \"avg_amount_30d\": 466, \"max_amount_30d\": 8000, \"min_amount_30d\": 20, \"incoming_outgoing_ratio_7d\": 1.2 }}'"
echo ""

