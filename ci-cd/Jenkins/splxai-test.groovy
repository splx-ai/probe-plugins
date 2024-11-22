// ******** SplxAI Probe Template for Jenkins CI ********
//
// ******** Description ********
// SplxAI Probe will test your GenAI application to detect vulnerabilities and provide remediation.
//
// It is recomended to create a new API key with a descriptive name
//
// The following values should be added as environment variables.
//    SPLXAI_TARGET_ID: the Target ID of the pre defined Target, from SplxAI Probe, Target Settings
//    SPLXAI_API_KEY: the API key generated from SplxAI Probe, Account Settings
//    SPLXAI_PLATFORM_URL: the SplxAI url that you login to (e.g https://probe.splx.ai/ or https://us.probe.splx.ai/)
//    SPLXAI_API_URL: the SplxAI url that you login to (e.g https://api.probe.splx.ai/ or https://api.us.probe.splx.ai/)
//
// For more configuration options, please check the technical documentation portal:
// 📚 https://probe.splx.ai/probe-documentation
//

pipeline {
  agent any
  
  environment {
    SPLXAI_TARGET_ID = 000
    SPLXAI_PLATFORM_URL = "https://probe.splx.ai"
    SPLXAI_API_URL = "https://api.probe.splx.ai"
   }

  stages {

    stage('SplxAI Test') {
      steps {
           sh '''
              apt-get -qq update
              apt-get install -y jq
           
              echo "###### Start SplxAI Test Run #######"
              REQUEST_BODY=$(cat <<-EOF
                  {
                      "targetId": $SPLXAI_TARGET_ID,
                      "probeIds": [1],
                      "name": "Jenkins CI/CD Test Run"
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
           '''
            }
        }
    }
}
