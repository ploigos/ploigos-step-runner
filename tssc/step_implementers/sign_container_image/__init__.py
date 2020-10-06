"""tssc.StepImplementers for the 'sign-container-image' TSSC step.


Step Configuration
------------------
All tssc.StepImplementers for this step should
accept minimally the following configuration options.

| Configuration Key                           | Required? | Default | Description
|---------------------------------------------|-----------|---------|-------------
| `container-image-signature-server-url`      | True      |         | Url of the signature /
                                                                      server
| `container-image-signature-server-username` | True      |         | Username to log onto /
                                                                      the signature server
| `container-image-signature-server-password` | True      |         | Password to log onto /
                                                                      the signature server
| `container-image-signer-pgp-private-key`    | True      |         | PGP Private Key /
                                                                      used to sign


Results
-------
All tssc.StepImplementers for this step should
minimally produce the following step results.

| Result Key                                          | Description
|-----------------------------------------------------|------------
| `container-image-signature-private-key-fingerprint` | Fingerprint for the private key for /
                                                        image signing
| `container-image-signature-file-path`               | File path where signature is located /
                                                        eg) /tmp/tssc-developer/hello-node@/
                                                            sha256=2cbdb73c9177e63/
                                                            e85d267f738e99e368db3f/
                                                            806eab4c541f5c6b719e69/
                                                            f1a2b/signature-1
| `container-image-signature-name`                    | Fully qualified name of the name /
                                                        including organization, repo, and hash /
                                                        eg) tssc-developer/hello-node@sha256=/
                                                            2cbdb73c9177e63e85d267f738e9/
                                                            9e368db3f806eab4c541f5c6b719/
                                                            e69f1a2b/signature-1
| `container-image-signature-url`                     | URL signature was uploaded to
| `container-image-signature-file-md5`                | MD5 hash of signature file
| `container-image-signature-file-sha1`               | SHA1 Hash of signature file
"""

from .curl_push import CurlPush
from .podman_sign import PodmanSign

__all__ = [
    'curl_push',
    'podman_sign'
]
