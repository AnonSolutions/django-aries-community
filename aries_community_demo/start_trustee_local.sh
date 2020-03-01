#!/bin/bash

JQ_EXE=jq

function checkJQPresent () {
  if [ -z $(type -P "$JQ_EXE") ]; then
    echoError "The ${JQ_EXE} executable is needed and not on your path."
    echoError "Installation instructions can be found here: https://stedolan.github.io/jq/download"
    exit 1
  fi
}

checkJQPresent

if [ -z "${INDY_NETWORK}" ]; then
    export LEDGER_URL=http://localhost:9000
else
    case "${INDY_NETWORK}" in
    bcovrin-test*)
        export LEDGER_URL=http://test.bcovrin.vonx.io
        ;;
    bcovrin-greenlight*)
        export LEDGER_URL=http://greenlight.bcovrin.vonx.io
        ;;
    *)
        export LEDGER_URL=http://localhost:9000
        ;;
    esac
fi

export AGENT_ENDPOINT=$(curl http://localhost:4040/api/tunnels | ${JQ_EXE} --raw-output '.tunnels | map(select(.name | contains("trustee-agent"))) | .[0] | .public_url')
if [ -z "${AGENT_ENDPOINT}" ]; then
    export AGENT_ENDPOINT=http://localhost:8042
fi

echo "Using ${LEDGER_URL} as ledger and ${AGENT_ENDPOINT} as the agent endpoint."

curl -d '{"seed":"itution_0000o_anon_solutions_inc", "role":"TRUST_ANCHOR", "alias":"Anon Solutions Inc"}' -X POST ${LEDGER_URL}/register
sleep 2
aca-py \
    start \
    --endpoint ${AGENT_ENDPOINT} \
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
    --genesis-url ${LEDGER_URL}/genesis \
    --seed itution_0000o_anon_solutions_inc \
    --storage-type indy \
    --wallet-storage-type postgres_storage \
    --wallet-storage-config '{"url": "localhost:5432"}' \
    --wallet-storage-creds '{"account": "postgres", "password": "mysecretpassword", "admin_account": "postgres", "admin_password": "mysecretpassword"}' \
    --webhook-url http://localhost:8000/agent_cb/1JZCV9DP8ETL9O2Q7T2A
