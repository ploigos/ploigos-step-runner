import copy
import io
import json
import re
import sys
from contextlib import redirect_stdout
from io import StringIO

import yaml
from tests.helpers.base_test_case import BaseTestCase
from ploigos_step_runner.utils.io import (TextIOIndenter, TextIOSelectiveObfuscator,
                           create_sh_redirect_to_multiple_streams_fn_callback)

class TestCreateSHRedirectToMultipleStreamsFNCallback(BaseTestCase):
    def test_one_stream(self):
        stream_one = StringIO()
        sh_redirect_to_multiple_streams_fn_callback = \
            create_sh_redirect_to_multiple_streams_fn_callback([
                stream_one
            ])

        sh_redirect_to_multiple_streams_fn_callback('data1')

        self.assertEqual('data1', stream_one.getvalue())

    def test_two_streams(self):
        stream_one = StringIO()
        stream_two = StringIO()
        sh_redirect_to_multiple_streams_fn_callback = \
            create_sh_redirect_to_multiple_streams_fn_callback([
                stream_one,
                stream_two
            ])

        sh_redirect_to_multiple_streams_fn_callback('data1')

        self.assertEqual('data1', stream_one.getvalue())
        self.assertEqual('data1', stream_two.getvalue())

class TestTextIOSelectiveObfuscator(BaseTestCase):
    def run_test(self, input, expected, randomize_replacment_length=False, obfuscation_targets=None, replacment_char=None):
        out = io.StringIO()
        with redirect_stdout(out):
            io_obfuscator = TextIOSelectiveObfuscator(
                parent_stream=sys.stdout,
                randomize_replacment_length=randomize_replacment_length
            )

            if obfuscation_targets is not None:
                io_obfuscator.add_obfuscation_targets(obfuscation_targets)
            if replacment_char is not None:
                io_obfuscator.replacement_char = replacment_char

            io_obfuscator.write(input)

            self.assertRegex(out.getvalue(), expected)

    def test_no_obfuscation(self):
        self.run_test(
            input='hello world',
            expected='hello world'
        )

    def test_single_obfuscation(self):
        self.run_test(
            input='hello world secret should be hidden because secret is not for your eyes',
            expected=r'hello world \*\*\*\*\*\* should be hidden because ' \
                     r'\*\*\*\*\*\* is not for your eyes',
            obfuscation_targets='secret'
        )

    def test_multiple_obfuscation(self):
        self.run_test(
            input='hello world secret should be hidden because secret is not for your eyes',
            expected=r'hello world \*\*\*\*\*\* should be \*\*\*\*\*\* because ' \
                     r'\*\*\*\*\*\* is not for your eyes',
            obfuscation_targets=['secret', 'hidden']
        )

    def test_custom_replacement_char(self):
        self.run_test(
            input='hello world secret should be hidden because secret is not for your eyes',
            expected='hello world !!!!!! should be hidden because !!!!!! is not for your eyes',
            obfuscation_targets=['secret'],
            replacment_char='!'
        )

    def test_random_replacement_length(self):
        self.run_test(
            input='hello world secret should be hidden because secret is not for your eyes',
            expected=r'hello world \*\*\*\*\*.* should be hidden because ' \
                     r'\*\*\*\*\*.* is not for your eyes',
            obfuscation_targets=['secret'],
            randomize_replacment_length=True
        )

    def test_byte_obfuscation(self):
        self.run_test(
            input=b'hello world secret should be hidden because secret is not for your eyes',
            expected=r'hello world \*\*\*\*\*\* should be hidden because ' \
                     r'\*\*\*\*\*\* is not for your eyes',
            obfuscation_targets='secret'
        )

    def test_obfuscating_a_target_that_needs_escaping(self):
        fake_private_key = """-----BEGIN PGP PRIVATE KEY BLOCK-----\n\nlQVYBF90si4BDACus+N9hh8
            3JFfnx0JvmEq+7T1aPW+wSmYz2uiUGHAnS04wrBX\n2QYYUPL6hKhRxI+Ns6d+P5Jk5Z44desZwewYy01+Oltud
            GOgj07WUsPw0ZFJ\nZZC+laasHS/gtWcssVcel+/o9Oqg4RdbuSr9crg2Imr8HrjVO
            7gUFRwraV7YNEZwOMt1O/Nu67LFNKRezeAlWQK4cnbqSyEhbU5zqw\nR8H+nrC/e678eyPubm4
            o7kKuxom6BzCNQQFphjLbR2JUnrUvcpD2yrWNwDe+QQM2\n5dPQ8nIUHn7AqTmdpH6MGVV3CxOPKuOIgt
            YlSzK4WdNypJgwWnQ8OzHzi43U0XXg\nOsw3MWP/kw2QmBvtZTDfrObRGrpOSgI4yhAVoDmJKSOrCvmrhuW12n
            wsBZK6bLBh\nv6uJXznXMHRUrec2W2fLuMTZ0vix83XCgNveE5yVHA56TcKjl+jIfmOrk2d/o5K3\nCZKxWGuuf
            LW80AEQEAAQAL/044pil8RXYhNgfx5p8Hulr0A3SEL8/ejgDpEkDF\nK9eBqI9LAIj813FIwVowzmp6D2p7X4mz
            2BM8z4PWR8eOyF3rmpyyAq5Ah/H2V\n3M8ylJ+9PYd27cWfnNZgZSEAJ/eHWcINdnJAQtOKkK3HCUbDLUg
            yo\n3f1OdhjtbZuFXspohgM2WtFCMNxqSbU8eLNGSn0VUm6Bqods08gkIefPdL8N9kBO\nFnjSh52BALKQFoiqR
            eoed119xn3oUn7H1k5z8zK0U9DLX+bNULhWuQE9qEUz64LJ\nWd4cCXtySl5lEjDcYU878mbqKlTNqn0K
            r+LVz6v\nhFItzlcbvPFmVcJOg2pPlKhtfy46qy3JSmYuF0CKGslc8eN7ZIV2iapd8VOf0eMRj+e67uNhre
            kDR6/YOPWYrJVQLCZjANznyRKV+wE\nZBEPustwjZ3ftVnqSVQ9UWJSgwYA0p/SP5XjazvSGe4iPMFPi0F4
            Z\n/oaokQa5IbA1mpZhJVoux9jM2TtwE+rCwedLbYv3pDT5VrgyWVznL2WohLXHR4UP\nJW/n0Llf1N
            XpAQhY395zFz1s/fUqJ7rYpsIGNRHsOQnLI2RB\nfnGEd0iQQVA/EbXy+n4s21rk1X+9UobmFobF/VxellcbDG
            RGyJkhB\nAc/HTaIJEa4t6vNqhpZcs4tnbcoXBgDUVvK1SgCllkwjDZDfLGteFYCzxPPNNQwU\n04GnuqfSN22l
            FIJOKpO/5EL49mAvQmEDgPOvuXAX7ing\nuT5aZ51wGyZWWFzuU95XhfnoP9gOADAo/AOctlvBpGhL+
            B0lnA4y\nD8gPwKiZiaI5AC4D9kDP3BPtJ0DvPipqEZLFzLWCtu/KW4L2SeJ10FHbk1WZrMtC\nT
            4noS1KFcHvK8S7sF/iVXIEo6PYtd3dwuLePyienwQC0njAOq\nONazx0EuEXRPSze66g
            VDeqkcuCzCuZ5SIo84dmbLEjbf\nKDtc+OgznYwJ1V8tsOZXEGXESZfnkhFRAn1+KHK
            oXw7csmJ\nz4p25QOFpljCCRLjjqnziSGJyr1XOhZ2FAcFOKTfALbiDVWNi6HxB1Gtxh7XHGGS\nQ1a/y
            s/Th4DJ2RV86sRONY/tEh0c3NjLXRlc3RpbmctaW1hZ2Ut\nc2lnbmVyIDxuYXBzc3BvK3Rzc2MtdGVz
            1zaWduZXJAcmVkaGF0\nLmNvbT6JAdQEEwEIAD4WIQTdcgi6CmNZ9luQaynPSsFKPRCWNwUCX3SyLgIbAw
            CQgHAgYVCgkICwIEFgIDAQIeAQIXgAAKCRDPSsFKPRCWNwA3C/92wPKY\nNu81dC6eZ/wG47ibc2/5Wf2lrJjM
            oVF4d22G9a515nRBxE7\n2xuPOo9u+oR4IJ2qvlo57/WtawmXAaoCIfhJ4vH0Mfot9hjXp5ZKEa7dqLtAuT8R
            0AhCv4BZL0\nGTo/9CbUy/4xkQaR9JOX/DEugVV9f3nvUSG0nHnM3NBf9wt/xFa80MXnA/KLwcCk\noQXaSm+
            uoc2z2ekRAySDHL8XxFSX7S8sL5PXGOnIns7CV/\nebfLMqLImYUXSbvyUGVnGci4OI1DlFMkGLLys6UjjXV3y
            j4C\na5Dnz3ycp3ttDV99HKHMfrpAVzhfupBh2nJ8ts0BZirG2zhmJoSzU8dBi+2dBVgE\nX3SyLgEMAL9yv1W
            3b3UKeF\nWh9Z+74obp8mSuGtABB7tidaw2J0kZ3lHZcDUOIInr1URSr7hCX10HYk+iLdQEPX\nsQTpcJXaKDR
            5m4SmJC9qfveZH9oLF1fv6g4/uhwirK+B\ngAo4aoM0JMhvZHDJet0FVbxTiIXPCqBF1rqpqwoaI6ApV7rAKspZ
            HKukaxw1kPcfI38kTRRAW43wl+2ESYpEjvxzDiwHBusgA37BUJ3yTf/1uUA\nvhCAbKg6mGzmiqsd7632vvTu+
            nYAlACwiu7Ny\n/mYVDqm4BqR3Lc9bIh2zDzqAxFzpO4YzN\nZvsD//g+PKYq2tqvdal4FM426HDQoKX
            ypQ\nuzEn7XCQewARAQABAAv/SvDqAOculOrrO3KS4Ax1QH58dlwo/Q6rVpoPXjoIkZ09
            \nifQN6p3JDqpequMYbkl5dAcTTN/hp
            Np2MzaC3ofsuI\nfJbg64DcRTJLcvbGQYKSNlgaraV9aa11/qwcb8H/v5hLTlOS2pS/esCP/VRWIPAj\nGMzNV
            mi08bSusMgwdr9gh/N5Je\nyqxX89Jd94v08APyPWIjqoXvZi620sXE3SZVyBXLhlFnWvFq3uu2vNjt4YW83INk
            rdfved9NCtgl4tStIsDCh42H/7E4jqyyrUvb+cSz3bMM8H3QK\nCMIOystEU9zwr1R+ezDujwC7uH2+IiL1SHr
            CPiPTYjefifqe69x1+M5Oznj\n7UBxyi2tb7nOkJU/HT8g3CUGwNI22hpUEfDNMwcntBrpjpGIM4N8sILI9S
            YDUuef\nfHcc2UXMjI+adFY1VSUhBgDV1YFw1ScLP7OFtCntakpqzwZKSY0aYfyR66+bV2CX\nCXU3w9+Yn9clRd
            u1X0pDwwRdfiByxuCHcFVZn9mYVYk7c/3GtJhnZRwBieJjJUlY\nQ2xv5+1og5YF6R+Gaj1FTXGGN8r8P6aWiV6e
            MMaClwc3AbzIdbW2krbJXO5FyXW4\nyG/JSKPkIWMavXdlDnVh2TY6waYFnov7FA0O/a3wXrgFuK5rS4YUp7oW
            ysmMp\n+e43rbbbE4LPrgOJU1L4K7MGAOUzMRk4LlGJHmV5ljySHiAAl3+uC9fzgRdu1ksr\nIK33CZr2buOrV
            lVU+W8UhHBomv0W13TpFW5LMuhGBqE7YhYF9QiwTmnHbsys7wGj\nD8d2X8HIe9WA3B8qi9OASh7oqLerykYwob
            VA4KZitTfKM8WoXmpiKOS38nC2j1zV\nPn+Z549GgHFYgc3vnwMH7PR+Y/gx9DXK2AkHGsOgI9npphf12dA9j94K
            8Zdqn7BI\n3eS5aW9i98zJU9kHCR/UqqSEGQYAmjGQXGDwW59K2b9uUDWB6vgtrWoOf9IZiPgg\n2qT72BGp5/9
            nT4wd1lfKRzZ4J8QMZNg0I9FWalhQF7rI9LMDa9YSTqLL9qhXCl\nXu0i5vRpe/GWh9fAz1QaaqkdUy4FXi+bgQ
            +BBVPo6X19JUAnTKeG6bjoWAOnCb\n/feV9GmUJSALXAsmD2PExnaUjZLXoCra2cxdTp1TYhDDuvITBqw8TIylF
            uvSB\nBdy6hZLn9GvrrL4Uo83GN7bFtX0X6f6JAbwEGAEIACYWIQTdcgi6CmNZ9luQaynP\nSsFKPRCWNwUCX3S
            IbDAUJA8JnAAAKCRDPSsFKPRCWN/iJDACF/L9uea/Mgd18\nJhEFwI3wCxaSLAe03cYrSHefsFXJ7+bzRZHERo
            Vmd/5KFxHsDUCMjVQPZNvs\nm8ovpPaL6yR5AxWkFUh4ASpJkgDCB/BV4xhIlbcpfxmoY0qFVzcDf7V
            pwtOzuyY/\n9FO3Tc89UF70m/ulUbZBIgjuO51aJ/ZHu02N/F8xxKNt/N+ow21ByJwX3/rcjP1l\nNMVJjLf
            5I4a9BQ4Zu7SfhY2raD2KSTwd9M0d4/jkbaJI3AYDJ91I1/r6qIJFbLO/\nEe8fIe0jiyhpUho6ocdDgEDmn+8m4
            OGozDYSnIM1klfMlVWCUoOVLWIQEGrizE6e\nx1pFsKraKlBNkzW5tdsIFloiFxp/yWE2yIYu375gEtBe5Zhx6HF
            xOaC79AUTjLr\n1sqHHLlvAiJ8FmnmO7tHp6lwNH+OZeGPIMDInUeF+L9oWGx+U/vVsiWo3L1sZfJg\nOp2xWe6C
            XAMkiHnag3ycXxtmCKd5m5foQ/0XEK0vDWEq8=\n=C+BM\n-----END PGP PRIVATE KEY BLOCK-----\n"""

        input = (
            '"service-name": "fruit",\n'
            '"application-name": "reference-quarkus-mvn-jenkins",\n'
            '"organization": "ploigos-team"\n'
            '"argocd-api": "argocd-server-argocd.apps.ploigos_step_runner.rht-set.com",\n'
            '"maven-mirrors": {\n'
            '    "internal-mirror": {\n'
            '        "id": "internal-mirror",\n'
            '        "url": "http://artifactory.apps.ploigos_step_runner.rht-set.com/artifactory/release/",\n'
            '        "mirror-of": "*"\n'
            '    }\n'
            '},\n'
            f'"container-image-signer-pgp-private-key": "{fake_private_key}"\n')

        self.run_test(
            input=input,
            expected=r'"container-image-signer-pgp-private-key": "\*+\s*"',
            obfuscation_targets=[fake_private_key]
        )

    def test_yaml_with_blocktext_secret(self):
        yaml_with_blocktext_secret = """---
            step-runner-config:
                sign-container-image:
                -   implementer: PodmanSign
                    config:
                        container-image-signer-pgp-private-key: |
                            -----BEGIN PGP PRIVATE KEY BLOCK-----

                            lQVYBF90si4BDACus+N9hh8s3JFfnx0JvmEq+7T1aPW+wSmYz2uiUGHAnS04wrBX
                            2QYYUPL6hKhRxI+Ns6d+P5Jk5Z44desZwewYy01+OltudfGV+GOgj07WUsPw0ZFJ
                            ZZC+laasHS/gtWcssVcel+/o9Oqg4RdbuSr9crg2Imr8HrjVOr5NR1boep9yoM0i
                            AKgzm07yoh97gUFRwraV7YNEZwOMt1O/Nu67LFNKRezeAlWQK4cnbqSyEhbU5zqw
                            R8H+nrC/e678eyPubm4o7kKuxom6BzCNQQFphjLbR2JUnrUvcpD2yrWNwDe+QQM2
                            5dPQ8nIUHn7AqTmdpH6MGVV3CxOPKuOIgtYlSzK4WdNypJgwWnQ8OzHzi43U0XXg
                            Osw3MWP/kw2QmBvtZTDfrObRGrpOSgI4yhAVoDmJKSOrCvmrhuW12nwsBZK6bLBh
                            v6uJXznXMHRUrec2W2fLuMTZ0vix83XCgNveE5yVHA56TcKjl+jIfmOrk2d/o5K3
                            CZKxWGuufd5LW80AEQEAAQAL/044pil8RXYhNgfx5p8Hulr0A3SEL8/ejgDpEkDF
                            K9eBqI9LAIj813FIwVowzmp6D2p7X4mz7hi2BM8z4PWR8eOyF3rmpyyAq5Ah/H2V
                            3M8ylJ+9PYd27cWfnNZgZSEAJ/eHWcINdnJAQtOQpRRBBsIfPOKkK3HCUbDLUgyo
                            3f1OdhjtbZuFXspohgM2WtFCMNxqSbU8eLNGSn0VUm6Bqods08gkIefPdL8N9kBO
                            FnjSh52BALKQFoiqReoed119xn3oUn7H1k5z8zK0U9DLX+bNULhWuQE9qEUz64LJ
                            Wd4cCXtySlQf5Eyjd03h8r0LBBqF94SUlL5lEjDcYU878mbqKlTNqn0KIr+LVz6v
                            hFItzlcbvPFmVcJOg2pPlKhtfy46qy3JSmYuF0CKGslc8eN7ZIV2iapd9woC/MbW
                            4cCEktpxrSIhb1K8Z8VOf0eMRj+e67uNhrekDR6/YOPWYrJVQLCZjANznyRKV+wE
                            Q1a/yVgJgcULM1kfnzs/Th4DJ2RV86sRONY/tEh0c3NjLXRlc3RpbmctaW1hZ2Ut
                            c2lnbmVyIDxuYXBzc3BvK3Rzc2MtdGVzdGluZy1pbWFnZS1zaWduZXJAcmVkaGF0
                            LmNvbT6JAdQEEwEIAD4WIQTdcgi6CmNZ9luQaynPSsFKPRCWNwUCX3SyLgIbAwUJ
                            A8JnAAULCQgHAgYVCgkICwIEFgIDAQIeAQIXgAAKCRDPSsFKPRCWNwA3C/92wPKY
                            Nu81dC6eZ/wG47ibc2/5Wf2lrJjM9VTHQVa+vLpbBK/rcoVF4d22G9a515nRBxE7
                            a5Dnz3ycp3ttDV99HKHMfrpAVzhfupBh2nJ8ts0BZirG2zhmJoSzU8dBi+2dBVgE
                            X3SyLgEMAL9yv1WmtAVxisBApZjPnXUXJAhPBtuSy1gCIpwf663pR4qA93b3UKeF
                            Wh9Z+74obp8mSuGtABB7tidaw2J0kZ3lHZcDUOIInr1URSr7hCX10HYk+iLdQEPX
                            sQTpcJXaKDRQFNBIRzOUdqvHWb/W9i05m4SmJC9qfveZH9oLF1fv6g4/uhwirK+B
                            gAo4aoM0JMhvZHDJet0FVbxTiIXPCqBF1rqpqwoaI6ApV7rAKspZWuss3yGIT3OY
                            bF8CKHKukaxw1kPcfI38kTRRAW43wl+2ESYpEjvxzDiwHBusgA37BUJ3yTf/1uUA
                            vhCAbKg6mGzmiqsd7632vvTu+jrsD12C+ByxyNETzvakl6cb+wd/nYAlACwiu7Ny
                            /mYVDqm4BqR3Lc9bIh2J227O7busSh1hpE9x0ziLRWnVrSsVL2zDzqAxFzpO4YzN
                            ZvsD//g+PKYq2tqvdal4FM426HDQoKXwxOEjFq1NG1zdnMDJzZwxColBCIzJRypQ
                            uzEn7XCQewARAQABAAv/SvDqAOculOrrO3KS4Ax1QH58dlwo/Q6rVpoPXjoIkZ09
                            ifQN6p3JDqpequMYbkl5dAcTTN/hpJIoraMT1Jh43+vt900u/iwNp2MzaC3ofsuI
                            fJbg64DcRTJLcvbGQYKSNlgaraV9aa11/qwcb8H/v5hLTlOS2pS/esCP/VRWIPAj
                            GMzNV3IjUthIfLe0ygNBWsxv7s6Pr7EE7KFuUaLIMBDmi08bSusMgwdr9gh/N5Je
                            yqxX89Jd94v08APyPWIjqoXvZi620sXE3SZVyBXLhlFnWvFq3uu2vNjt4YW83INk
                            2Jy9THjd0G5wDOardfved9NCtgl4tStIsDCh42H/7E4jqyyrUvb+cSz3bMM8H3QK
                            +e43rbbbE4LPrgOJU1L4K7MGAOUzMRk4LlGJHmV5ljySHiAAl3+uC9fzgRdu1ksr
                            IK33CZr2buOrVlVU+W8UhHBomv0W13TpFW5LMuhGBqE7YhYF9QiwTmnHbsys7wGj
                            D8d2X8HIe9WA3B8qi9OASh7oqLerykYwobVA4KZitTfKM8WoXmpiKOS38nC2j1zV
                            Pn+Z549GgHFYgc3vnwMH7PR+Y/gx9DXK2AkHGsOgI9npphf12dA9j94K8Zdqn7BI
                            3eS5aW9i98zJU9kHCR/UqqSEGQYAmjGQXGDwW59K2b9uUDWB6vgtrWoOf9IZiPgg
                            2qT72BGp5/9IVnT4wd1lfKRzZ4J8QMZNg0I9FWalhQF7rI9LMDa9YSTqLL9qhXCl
                            Xu0i5vRpe/GWh9fAz1QaaqkdUy4FXi+bgQmb+BBVPo6X19JUAnTKeG6bjoWAOnCb
                            /feV9GmUJSALXAsmD2PExnaUjZLXoCra2cxdTp1TYhDDuvITBqw8TIylFSH1uvSB
                            Bdy6hZLn9GvrrL4Uo83GN7bFtX0X6f6JAbwEGAEIACYWIQTdcgi6CmNZ9luQaynP
                            SsFKPRCWNwUCX3SyLgIbDAUJA8JnAAAKCRDPSsFKPRCWN/iJDACF/L9uea/Mgd18
                            JhEFwI3wCxaSLAe03cYrSHefsFXJ7+bzRZHERop+k3Vmd/5KFxHsDUCMjVQPZNvs
                            m8ovpPaL6yR5AxWkFUh4ASpJkgDCB/BV4xhIlbcpfxmoY0qFVzcDf7VpwtOzuyY/
                            9FO3Tc89UF70m/ulUbZBIgjuO51aJ/ZHu02N/F8xxKNt/N+ow21ByJwX3/rcjP1l
                            NMVJjLf5I4a9BQ4Zu7SfhY2raD2KSTwd9M0d4/jkbaJI3AYDJ91I1/r6qIJFbLO/
                            Ee8fIe0jiyhpUho6ocdDgEDmn+8m4OGozDYSnIM1klfMlVWCUoOVLWIQEGrizE6e
                            x1pFsKraKlBNkzW5tdsIFloiFxp/yWE2yIYu375gEtBe5Zhx6HFqxOaC79AUTjLr
                            1sqHHLlvAiJ8FmnmO7tHp6lwNH+OZeGPIMDInUeF+L9oWGx+U/vVsiWo3L1sZfJg
                            Op2xWe6CCXAMkiHnag3ycXxtmCepLxbKd5m5foQ/0XEK0vDWEq8=
                            =C+BM
                            -----END PGP PRIVATE KEY BLOCK-----"""

        dict_with_blocktext_secret = yaml.safe_load(yaml_with_blocktext_secret)

        private_key_block = dict_with_blocktext_secret \
            ['step-runner-config']['sign-container-image'][0]['config'] \
                ['container-image-signer-pgp-private-key']

        self.run_test(
            input=json.dumps(dict_with_blocktext_secret, indent=2),
            expected=r'"container\-image\-signer\-pgp\-private\-key": "\*+"',
            obfuscation_targets=private_key_block
        )

class TestTextIOIndenter(BaseTestCase):
    def __run_test(self, inputs, expected, indent_level=0, indent_size=4, indent_char=' '):
        out = io.StringIO()
        with redirect_stdout(out):
            indenter = TextIOIndenter(
                parent_stream=sys.stdout,
                indent_level=indent_level,
                indent_size=indent_size,
                indent_char=indent_char
            )

            if not isinstance(inputs, list):
                inputs = [inputs]

            for input in inputs:
                indenter.write(input)

            self.assertRegex(out.getvalue(), expected)

    def test_one_line_bytes_no_indent(self):
        self.__run_test(
            inputs=b"hello world",
            expected=r"hello world"
        )

    def test_one_line_no_indent(self):
        self.__run_test(
            inputs="hello world",
            expected=r"hello world"
        )

    def test_one_line_1_indent_leading_newline(self):
        self.__run_test(
            inputs=["\n","hello world"],
            expected=r"hello world",
            indent_level=1
        )

    def test_one_line_1_indent_no_leading_newline(self):
        self.__run_test(
            inputs="hello world",
            expected=r"hello world",
            indent_level=1
        )

    def test_one_line_2_indent_leading_newline(self):
        self.__run_test(
            inputs=["\n","hello world"],
            expected=r"        hello world",
            indent_level=2
        )

    def test_one_line_2_indent_no_leading_newline(self):
        self.__run_test(
            inputs=["hello world"],
            expected=r"hello world",
            indent_level=2
        )

    def test_one_line_trailing_newline_no_indent(self):
        self.__run_test(
            inputs="hello world\n",
            expected=r"hello world\n"
        )

    def test_one_line_trailing_newline_1_indent(self):
        self.__run_test(
            inputs="hello world\n",
            expected=r"hello world\n    ",
            indent_level=1
        )

    def test_one_line_0_indent_2_char_diff_char(self):
        self.__run_test(
            inputs="hello world",
            expected=r"hello world",
            indent_level=0,
            indent_size=2,
            indent_char='-'
        )

    def test_one_line_1_indent_2_char_diff_char(self):
        self.__run_test(
            inputs="hello world",
            expected=r"--hello world",
            indent_level=1,
            indent_size=2,
            indent_char='-'
        )

    def test_one_line_2_indent_2_char_diff_char(self):
        self.__run_test(
            inputs="hello world",
            expected=r"----hello world",
            indent_level=2,
            indent_size=2,
            indent_char='-'
        )

    def test_multi_line_no_indent(self):
        self.__run_test(
            inputs="hello\nworld",
            expected=r"hello\nworld"
        )

    def test_multi_line_1_indent(self):
        self.__run_test(
            inputs="hello\nworld",
            expected=r"    hello\n    world",
            indent_level=1
        )

    def test_multi_line_2_indent(self):
        self.__run_test(
            inputs="hello\nworld",
            expected=r"        hello\n        world",
            indent_level=2
        )

    def test_multi_line_trailing_newline_1_indent(self):
        self.__run_test(
            inputs="hello\nworld\n",
            expected=r"    hello\n    world\n",
            indent_level=1
        )

    def test_multi_line_trailing_newline_2_indent(self):
        self.__run_test(
            inputs="hello\nworld\n",
            expected=r"        hello\n        world\n",
            indent_level=2
        )

    def test_multiple_writes_new_line_on_first_write(self):
        self.__run_test(
            inputs=["hello\nworld\n","foo\nbar"],
            expected=r"    hello\n    world\n    foo\n    bar",
            indent_level=1
        )

    def test_multiple_writes_write_to_same_line_more_then_once(self):
        self.__run_test(
            inputs=[
                "hello world ",
                "foo bar\n",
                "this is a test, ",
                "more testing\n",
                "fortytwo\n"
            ],
            expected=r"    hello world foo bar\n    this is a test, more testing\n    fortytwo\n",
            indent_level=1
        )
