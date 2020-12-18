"""Shared utils for dealing with dictionaries.
"""

def deep_merge(dest, source, overwrite_duplicate_keys=False, _path=None):
    """"deep merges source dictionary into destination dictionary.

    Parameters
    ----------
    dest : dict
        Destination dictionary to deep merge source into.
    source : dict
        Source dictionary to deep merge into dest.
    overwrite_duplicate_keys : bool
        True to overwite duplicate leaf keys in destination with source dictionary values.
        False to raise ValueError if any duplicate leaf values.

    Examples
    --------
    No Duplicate Keys:
    dict1 = {
        'A': {'value': '1'},
        'C': {'value': '1'}
    }
    dict2 = {
        'B': {'value': '2'},
    }
    expected_answer = {
        'A': {'value': '1'},
        'C': {'value': '1'},
        'B': {'value': '2'}
    }

    Duplicate keys (overwrite_duplicate_keys=True):

    dict1 = {
        'A': {'value': '1'},
        'C': {'value': 'overwriteme'}
    }
    dict2 = {
        'B': {'value': '2'},
        'C': {'value': '2'}
    }
    expected_answer = {
        'A': {'value': '1'},
        'C': {'value': '2'},
        'B': {'value': '2'}
    }

    Raises
    ------
    ValueError
        If source and destination contain a duplicate leaf key and overwrite_duplicate_keys is True

    Notes
    ------
    Modifies destination.

    Source is https://stackoverflow.com/questions/7204805/how-to-merge-dictionaries-of-dictionaries/7205107#7205107 # pylint: disable=line-too-long
    """
    if _path is None:
        _path = []

    for key in source:
        if key in dest:
            if isinstance(dest[key], dict) and isinstance(source[key], dict):
                deep_merge(
                    dest=dest[key],
                    source=source[key],
                    overwrite_duplicate_keys=overwrite_duplicate_keys,
                    _path=_path + [str(key)]
                )
            elif dest[key] == source[key]:
                pass # same leaf value
            else:
                if overwrite_duplicate_keys:
                    dest[key] = source[key]
                else:
                    raise ValueError('Conflict at %s' % '.'.join(_path + [str(key)]))
        else:
            dest[key] = source[key]
    return dest
