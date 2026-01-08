    apt-get -qq update
    apt-get install -y jq
    
    echo "###### Start SPLX Test Run #######"
    REQUEST_BODY=$(cat <<-EOF
        {
            "targetId": $SPLX_TARGET_ID,
            "probeIds": $SPLX_PROBE_IDS, # add required Probes in the list, e.g [1,2,3]
            "name": "SPLX Test Run"
        }
    EOF
    )

    RESPONSE=$(curl -s --request POST \
      --url $SPLX_API_URL/api/workspaces/$SPLX_WORKSPACE_ID/test-run/trigger \
      --header 'Content-Type: application/json' \
      --header "X-Api-Key: $SPLX_API_KEY" \
      --data "$REQUEST_BODY")
    
    TEST_RUN_ID=$(echo $RESPONSE | jq -r '.testRunId')
    if [ -z "$TEST_RUN_ID" ]; then
      echo "Error: Failed to trigger Test Run!"
      echo "Response: $RESPONSE"
      exit 1
    fi
    
    echo "###### Triggered SPLX Test Run #######"
    echo "=> Click on the link below to see the Test Run results"
    echo "=> $SPLX_PLATFORM_URL/w/$SPLX_WORKSPACE_ID/target/$SPLX_TARGET_ID/test-runs/$TEST_RUN_ID"
