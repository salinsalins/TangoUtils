false_str = ['False', 'false']
true_str = ['True', 'true']
def match_type(tout, value):
    to = type(tout)
    if to is type:
        to = tout
    if to is bool:
        try:
            return bool(int(value))
        except:
            pass
        sv = str(value)
        if sv in true_str:
            return True
        if sv in false_str:
            return False
        return None
    try:
        return to(value)
    except:
        return None

