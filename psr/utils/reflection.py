"""
Shared utilities for dealing with Python reflection.
"""

def import_and_get_class(module_name, class_name):
    """Dynamically loads a class from a given module.

    Parameters
    ----------
    module_name : str
        Name of the module to load the class from.
    class_name : str
        Name of the class to load from the given module.

    Returns
    -------
    class or None
        The class from the the given module, or none if given class does not exist in given module.
    """

    try:
        module = __import__(module_name, fromlist=[class_name])
        clazz = getattr(module, class_name)
    except (AttributeError, ModuleNotFoundError):
        clazz = None

    return clazz
