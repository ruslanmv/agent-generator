#!/bin/bash

ENV_FILE=".env"

# Exit if .env is missing
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: .env file not found."
  exit 1
fi

# Load environment variables
set -a; source "$ENV_FILE"; set +a

# Check required vars
for var in WATSONX_API_KEY WATSONX_PROJECT_ID WATSONX_URL WATSONX_MODEL; do
  if [ -z "${!var}" ]; then
    echo "Error: $var is not set in $ENV_FILE."
    exit 1
  fi
done

# Fetch IAM token (expires in ~60 mins) :contentReference[oaicite:3]{index=3}
IAM_TOKEN=$(curl -s -X POST "https://iam.cloud.ibm.com/identity/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=${WATSONX_API_KEY}" \
  | jq -r '.access_token')

if [ -z "$IAM_TOKEN" ] || [ "$IAM_TOKEN" == "null" ]; then
  echo "Error: Failed to obtain IAM token. Check your API key." 
  exit 1
fi

QUESTION="What is the capital of Italy?"

# Construct payload
read -r -d '' JSON_PAYLOAD <<EOF
{
  "project_id": "${WATSONX_PROJECT_ID}",
  "model_id": "${WATSONX_MODEL}",
  "input": "${QUESTION}",
  "parameters": {
    "max_new_tokens": 100,
    "temperature": 0.7
  }
}
EOF

echo "Sending request to ${WATSONX_URL}/ml/v1/text/generation?version=2025-02-11"

# Make request with IAM token :contentReference[oaicite:4]{index=4}
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST \
  "${WATSONX_URL}/ml/v1/text/generation?version=2025-02-11" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer ${IAM_TOKEN}" \
  -d "${JSON_PAYLOAD}")

HTTP_STATUS=$(echo "$RESPONSE" | tail -n1 | sed 's/HTTP_STATUS://')
BODY=$(echo "$RESPONSE" | sed '$d')

echo "Status: $HTTP_STATUS"
echo "Response: $BODY"

if [ "$HTTP_STATUS" -eq 200 ]; then
  TEXT=$(echo "$BODY" | jq -r '.results[0].generated_text')
  echo "✅ Success: $TEXT"
elif [ "$HTTP_STATUS" -eq 401 ]; then
  echo "❌ Unauthorized (401): Invalid or expired IAM token." 
elif [ "$HTTP_STATUS" -eq 403 ]; then
  echo "❌ Forbidden (403): Check your IAM permissions for project or model."
elif [ "$HTTP_STATUS" -eq 404 ]; then
  echo "❌ Not Found (404): Verify URL, project ID, and model ID."
else
  echo "❌ HTTP $HTTP_STATUS: See response body for details."
fi
