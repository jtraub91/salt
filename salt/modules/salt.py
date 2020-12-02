"""
Module to execute salt commands on minions with masters on same machine.
I.e. A master of master architecture
"""


def __virtual__():
    # todo: check if salt-master present
    return True


def cmd(tgt, command, **kwargs):
    pass
