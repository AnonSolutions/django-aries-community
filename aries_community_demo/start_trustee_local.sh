
curl -d '{"seed":"itution_0000o_anon_solutions_inc", "role":"TRUST_ANCHOR", "alias":"Anon Solutions Inc"}' -X POST http://localhost:9000/register
sleep 2
aca-py \
    start \
    --endpoint http://localhost:8042 \
    --label o_anon_solutions_inc \
    --auto-ping-connection \
    --auto-accept-invites \
    --auto-accept-requests \
    --auto-respond-messages \
    --inbound-transport http 0.0.0.0 8042 \
    --outbound-transport http \
    --admin 0.0.0.0 8041 \
    --admin-api-key VMS7YRZHTOKZXYKSZNJC038ES657PZSSJY3KKKZL \
    --wallet-type indy \
    --wallet-name o_anon_solutions_inc812434 \
    --wallet-key pass12345 \
    --genesis-url http://localhost:9000/genesis \
    --seed itution_0000o_anon_solutions_inc \
    --storage-type indy \
    --wallet-storage-type postgres_storage \
    --wallet-storage-config '{"url": "localhost:5432"}' \
    --wallet-storage-creds '{"account": "postgres", "password": "mysecretpassword", "admin_account": "postgres", "admin_password": "mysecretpassword"}' \
    --webhook-url http://localhost:8000/agent_cb/1JZCV9DP8ETL9O2Q7T2A
