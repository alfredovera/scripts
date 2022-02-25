"""
Generalized functions for credential handling
"""

from . import general


def sops_envfile(path: str, cred_key: str) -> str:

    cmd = "sops -d " + path
    _, lines, errors = general.shell_cmd(cmd=cmd.split())

    for line in lines.split("\n"):
        k, v = line.split("=", 1)
        if k == cred_key:
            return v

    raise Exception("Credential not found in target env file")
