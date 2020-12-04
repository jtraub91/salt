"""
Module to execute salt commands on minions with masters on same machine.
I.e. A master of master architecture
"""
import salt.client

salt_client = salt.client.LocalClient()


def __virtual__():
    # todo: check if salt-master present
    return True


def cmd(*args, **kwargs):
    """
    Publish a salt command using the local salt client
    """
    return salt_client.cmd(*args, **kwargs)


def run(command, *args, **kwargs):
    """
    Use salt-run to run a command
    """
    return False


def keys(filter=None):
    """
    View keys identified by salt master
    """
    return False
