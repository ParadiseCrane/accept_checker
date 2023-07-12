"""Contains soft_mkdir function"""
import os


def soft_mkdir(path: str):
    """Creates folder using specified path

    Args:
        path (str)
    """
    if os.path.exists(path) and os.path.isdir(path):
        return
    os.mkdir(path)
