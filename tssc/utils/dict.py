"""
Shared utils for dealing with dictionaries.
"""

def deep_merge(dest, source, path=None):
    """"deep merges dest into source

    Raises
    ------
    ValueError
        If source and destination contain a duplicate leaf key

    Notes
    ------
    Modifies destination.

    Source is https://stackoverflow.com/questions/7204805/how-to-merge-dictionaries-of-dictionaries/7205107#7205107 # pylint: disable=line-too-long
    """
    if path is None:
        path = []

    for key in source:
        if key in dest:
            if isinstance(dest[key], dict) and isinstance(source[key], dict):
                deep_merge(dest[key], source[key], path + [str(key)])
            elif dest[key] == source[key]:
                pass # same leaf value
            else:
                raise ValueError('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            dest[key] = source[key]
    return dest
