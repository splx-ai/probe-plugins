    apt-get -qq update
    apt-get install -y jq
    
    echo "###### Start SplxAI Test Run #######"
    REQUEST_BODY=$(cat <<-EOF
        {
            "targetId": $SPLXAI_TARGET_ID,
            "probeIds": [1], # add required Probes
            "name": "SplxAI Test Run"
        }
    EOF
    )

    RESPONSE=$(curl -s --request POST \
      --url $SPLXAI_API_URL/api/v2/test-run/trigger \
      --header 'Content-Type: application/json' \
      --header "X-Api-Key: $SPLXAI_API_KEY" \
      --data "$REQUEST_BODY")
    
    TEST_RUN_ID=$(echo $RESPONSE | jq -r '.testRunId')
    if [ -z "$TEST_RUN_ID" ]; then
      echo "Error: Failed to trigger Test Run!"
      echo "Response: $RESPONSE"
      exit 1
    fi
    
    echo "###### Triggered SplxAI Test Run #######"
    echo "=> Click on the link below to see the Test Run results"
    echo "=> https://probe.splx.ai/target/$SPLXAI_TARGET_ID/test-run-history/$TEST_RUN_ID"
