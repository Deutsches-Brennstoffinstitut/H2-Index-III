

def GetCmpKeys(names, ports):
    keys = []
    for name in names:
        if name in ports:
            if len(ports[name]) > 0:
                keys_in = list(dict(ports[name]).keys())
                for key in keys_in:
                    if not key in keys:
                        keys.append(key)

    return keys