def copy_property(src, dest, prop=None, replace=False):
    if prop is None:
        prop = dir(src)
    elif isinstance(prop, str):
        prop = [prop]
    for pr in prop:
        if replace or not hasattr(dest, pr):
            v = getattr(src, pr)
            setattr(dest, pr, v)
    return dest
