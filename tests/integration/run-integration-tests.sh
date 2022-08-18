#!/bin/bash
set -eux -o pipefail

# This script assumes the following environment variables are set:
# PSR_BRANCH - the branch to test
# OPENSHIFT_URL - The K8s API URL for the cluster to run the tekton pipeline in
# OPENSHIFT_USER - The user for `oc login`
# OPENSHIFT_PASSWORD - The password for `oc login`

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

STEP_RUNNER_LIB_SOURCE_URL="git+https://github.com/ploigos/ploigos-step-runner.git@${PSR_BRANCH}"
PIPELINE_NAMESPACE=devsecops
STATUS_INITIAL_WAIT=10 # Wait this many seconds after creating PipelineRun to check its status for the first time.
STATUS_RETRY_WAIT=60   # Wait this many seconds after seeing the PipelineRun is still in progress before checking again.

# Generate the Tekton PipelineRun
cp ${SCRIPT_DIR}/everything-pipelinerun-template.yml everything-pipelinerun.yml
sed -i "s,STEP_RUNNER_LIB_SOURCE_URL,${STEP_RUNNER_LIB_SOURCE_URL}," everything-pipelinerun.yml

# Create the PipelineRun
oc login --insecure-skip-tls-verify --server=${OPENSHIFT_URL} -u ${OPENSHIFT_USER} -p ${OPENSHIFT_PASSWORD}
CREATED_PIPELINERUN=$(oc create -f everything-pipelinerun.yml -n ${PIPELINE_NAMESPACE} | cut -d ' ' -f 1)

# Wait for the pipeline to finish
STATUS=Unknown
while [ "${STATUS}" == "Unknown" ]; do
    sleep ${STATUS_INITIAL_WAIT}
    CONDITIONS=$(oc get ${CREATED_PIPELINERUN} -n ${PIPELINE_NAMESPACE} -o yaml | yq .status.conditions)
    STATUS=$(echo "${CONDITIONS}" | yq .[0].status)
    if [ "${STATUS}" == "Unknown" ]; then
        sleep ${STATUS_RETRY_WAIT}
    fi
done

# Report success or failure
if [ "${STATUS}" != "True" ]; then
    echo Tekton Everything Pipeline Failed
    echo Integration Tests Failed
    exit 1
fi
echo Tekton Everything Pipeline Passed
echo Integration Tests Passed

