// ******** SPLX Probe Template for Jenkins CI ********
//
// ******** Description ********
// SPLX Probe will test your GenAI application to detect vulnerabilities and provide remediation.
//
// It is recomended to create a new API key with a descriptive name
//
// The following values should be added as environment variables.
//    SPLX_TARGET_ID: the Target ID of the pre defined Target, from SPLX Probe, Target Settings
//    SPLX_WORKSPACE_ID: the Workspace ID of the pre defined Target, from SPLX Probe (can be found in the URL when viewing the Target - e.g 163 in https://probe.splx.ai/w/163/target/000)
//    SPLX_PROBE_IDS: list of Probe IDs to run, from SPLX Probe, Probe Settings, Details
//    SPLX_API_KEY: the API key generated from SPLX Probe, Account Settings
//    SPLX_PLATFORM_URL: the SPLX url that you login to (e.g https://probe.splx.ai/ or https://us.probe.splx.ai/)
//    SPLX_API_URL: the SPLX url that you login to (e.g https://api.probe.splx.ai/ or https://api.us.probe.splx.ai/)
//
// For more configuration options, please check the technical documentation portal:
// 📚 https://probe.splx.ai/probe-documentation
//

pipeline {
  agent any
  
  environment {
    SPLX_TARGET_ID = 000
    SPLX_WORKSPACE_ID = 000
    SPLX_PROBE_IDS = "[1]"
    SPLX_PLATFORM_URL = "https://probe.splx.ai"
    SPLX_API_URL = "https://api.probe.splx.ai"
   }

  stages {

    stage('SPLX Test') {
      steps {
           sh '''
              apt-get -qq update
              apt-get install -y jq
           
              echo "###### Start SPLX Test Run #######"
              REQUEST_BODY=$(cat <<-EOF
                  {
                      "targetId": $SPLX_TARGET_ID,
                      "probeIds": $SPLX_PROBE_IDS,
                      "name": "Jenkins CI/CD Test Run"
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
           '''
            }
        }
    }
}
