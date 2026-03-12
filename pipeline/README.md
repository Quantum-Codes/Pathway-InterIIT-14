# Setup

\<assumed git clone and cd to streaming done\>
1. cd setup
2. chmod +x *.sh
3. bash docker-init.sh (might need sudo acc to system config)
4. cd .. (now in streaming)
5. python3 -m venv venv
6. source venv/bin/activate
7. pip install -r requirements.txt
8. cp env.example .env
9. Now fill up the .env file with keys.
10. pip install -r requirements1.txt
11. pip install guardrails-ai;
12. guardrails configure;
13. guardrails hub install hub://guardrails/toxic_language
14. guardrails hub install hub://guardrails/profanity_free


# Run main pipeline
In separate terminals run: (with sourced venv)
- python3 main.py
- python3 database_update.py

Then to insert records (kyc forms):
- python3 OCR/process_kyc.py

To manually select from tables check out command style in `setup/docker-init.sh`


# Run watcher pipeline
In separate terminals run: (with sourced venv)
- python3 watcher/rag.py
- python3 watcher/scheduler.py

# Run RPS+MCP & watcher pipeline
In separate terminals run: (with sourced venv)
- python3 rps/src/WatchDog.py 
- python3 mcp/mcp_server.py
- python3 mcp/mcp_client.py
- uvicorn rps.src.service.api:app --reload --port 9000
- python3 rps/src/service/llm.py 

Then to insert transaction records:
```bash
docker exec db_tuto_postgres psql -U user -d values_db -c "
INSERT INTO Transactions (
    transaction_id, 
    user_id, 
    txn_timestamp, 
    amount, 
    currency, 
    txn_type, 
    counterparty_id, 
    is_fraud
) 
VALUES (
    3389,                        -- transaction_id
    829,       -- user_id (must exist in Users table)
    '2025-12-06 14:30:00'::timestamp,      -- txn_timestamp
    755.99,                                -- amount
    'EUR',                                 -- currency
    'PURCHASE',                            -- txn_type
    10012,        -- counterparty_id
    0                                      -- is_fraud
);
"
```
You will see output at `out/rps_output.jsonl`