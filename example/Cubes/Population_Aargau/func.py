def replace_with_shared_dimension(value):
    if value.startswith("C_"):
        return "https://ld.admin.ch/canton/" + value[2:]
    elif value.startswith("D_"):
        return "https://ld.admin.ch/district/" + value[2:]
    else:
        return "https://ld.admin.ch/municipality/" + value [2:]