"""`StepImplementer` for `schemathesis` print implementation.
 
Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
 
 * static configuration
 * runtime configuration
 * previous step results
 
Configuration Key     | Required? | Default | Description
----------------------|-----------|---------|-----------
`name`                | Yes       | `World` | Name to receive the greeting
 
Result Artifacts
----------------
Results artifacts output by this step.
 
Result Artifact Key | Description
--------------------|------------
`message` | The complete message that was printed
"""
import os
import sys
import sh 
from ploigos_step_runner import StepImplementer, StepResult
 
DEFAULT_CONFIG = {
   'name': 'World'
}
 
REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
   'name'
]
 
 
class Schemathesis(StepImplementer):  # pylint: disable=too-few-public-methods
   """
   StepImplementer for the generate-metadata step for Git.
   """
 
   @staticmethod
   def step_implementer_config_defaults():
       """Getter for the StepImplementer's configuration defaults.
 
       Returns
       -------
       dict
           Default values to use for step configuration values.
 
       Notes
       -----
       These are the lowest precedence configuration values.
 
       """
       return DEFAULT_CONFIG
 
   @staticmethod
   def _required_config_or_result_keys():
       """Getter for step configuration or previous step result artifacts that are required before
       running this step.
 
       See Also
       --------
       _validate_required_config_or_previous_step_result_artifact_keys
 
       Returns
       -------
       array_list
           Array of configuration keys or previous step result artifacts
           that are required before running the step.
       """
       return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS
 
   def _run_step(self):
       """Runs the step implemented by this StepImplementer.
 
       Returns
       -------
       StepResult
           Object containing the dictionary results of this step.
       """
       step_result = StepResult.from_step_implementer(self)
 
       name = self.get_value('name')
       message = f'Schemathesis Hello {name}!'
 
       print(message)

## FOR NOW ADDING TOKEN HERE NEEDS TO BE MOVED
       schemathesis_success = False
       api_endpoint = self.get_value('deployed-host-urls')[0]
       print(api_endpoint)
       auth_token = sh.jq(sh.curl(
          f'-sX',
          f'POST',
          'https://keycloak-consultant360-dev.apps.tssc.rht-set.com/auth/realms/consultant360/protocol/openid-connect/token',
          f"--header", 'Content-Type: application/x-www-form-urlencoded',
          f"--data-urlencode", 'grant_type=password',
          f"--data-urlencode", 'client_id=consultant360',
          f"--data-urlencode", 'client_secret=7463e6ad-5e03-4855-877f-360cdc1ef9d6',
          f"--data-urlencode", 'username=prmanager',
          f"--data-urlencode", 'password=prmanager'),
          f'-r',
          f'.access_token').strip()
       print(auth_token)
       auth_token='eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJIM0M5WnhpVjN0QldBX1VnYzU1S3lmS1NUaGdwbzlaM2FoN0ZoQXFYT2VZIn0.eyJleHAiOjE2MzAwNzQxMjEsImlhdCI6MTYzMDA3MzgyMSwianRpIjoiODE2MTE1NjctM2ZhOS00MmMzLThiNjEtMWRlMTJkYjZlOWI5IiwiaXNzIjoiaHR0cHM6Ly9rZXljbG9hay1jb25zdWx0YW50MzYwLWRldi5hcHBzLnRzc2Mucmh0LXNldC5jb20vYXV0aC9yZWFsbXMvY29uc3VsdGFudDM2MCIsImF1ZCI6WyJiZWFyZXIiLCJhY2NvdW50Il0sInN1YiI6Ijk5ZDU4ODIzLTI5YjctNGIxZi1hYTU5LTc2MDRmMThlZmVmYiIsInR5cCI6IkJlYXJlciIsImF6cCI6ImNvbnN1bHRhbnQzNjAiLCJzZXNzaW9uX3N0YXRlIjoiZmEzNDEwMTMtYTE2OC00MTM3LWIyMGQtZTFjMzliZmY2YzVhIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwOi8vbG9jYWxob3N0OjQxODAvKiIsImh0dHA6Ly9sb2NhbGhvc3Q6OTA4MC8qIiwiaHR0cHM6Ly9mZWVkYmFjazM2MC1jb25zdWx0YW50MzYwLWRldi5hcHBzLnRzc2Mucmh0LXNldC5jb20iLCJodHRwOi8va2V5Y2xvYWs6OTA4MC8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiY29uc3VsdGFudDM2MCI6eyJyb2xlcyI6WyJ1c2VyIl19LCJiZWFyZXIiOnsicm9sZXMiOlsidXNlciJdfSwiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJQYW0gTWFuYWdlciIsInByZWZlcnJlZF91c2VybmFtZSI6InBybWFuYWdlciIsImdpdmVuX25hbWUiOiJQYW0iLCJmYW1pbHlfbmFtZSI6Ik1hbmFnZXIiLCJlbWFpbCI6InBybWFuYWdlckByZWRoYXQuY29tIn0.qf0NLSLT-F4RnLYdsfi4p3PLUl39_VWQTkvgb8VkM4H6FeJpJDSNYyY4psgiAd7Jknntz1Y99vZOaU7kl5IJVwg2zd0o-jBGRJ1Ni16ZvtrPUoGgs1kSOiMgEtgea24Ve_726BuadGChQ33Mr2bUfVWwbEFMI3VDQjBEj6H5UNa-NoxcdgimXg_rBnCMGg6zDd67hoeexb6GtU6U3VlYikL_awO951I4y_sS6PVgdtBQazroN1xBbIeqRnVicshbmK9PMnhBbdX_Nfhvn5h5hipFRyNEhrHjvmXIlpsUMJoDbbwyE_fJPhY_qqXx5dLsCLpenVuLAoewm0e4bBuwkw'

       try:
           working_directory = self.work_dir_path

           print(f'token:{auth_token}')
           scan_res = sh.schemathesis(
               "run", "--stateful=links", "--checks", "all", f"{api_endpoint}/api/v1/api-docs?group=local",
               "-H", f"Authorization: Bearer {auth_token}",
               _out=sys.stdout,
               _err=sys.stderr)
           file = open(f'{working_directory}/report-task.txt', "w")
           file.write(scan_res)
           file.close()
           schemathesis_success = True
       except sh.ErrorReturnCode as error: 
           # Error Code Other: unexpected
           step_result.success = False
           step_result.message = "Unexpected error running schemathesis analysis" \
               f" using schemathesis: {error}"

 
       step_result.add_artifact(
           name='schemathesis-result-set',
           value=f'{working_directory}/report-task.txt'
       )

       step_result.add_evidence(
           name='schemathesis-quality-gate-pass',
           value=schemathesis_success
       )
 
       return step_result
 
