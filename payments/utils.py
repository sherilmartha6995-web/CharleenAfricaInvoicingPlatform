

def format_phone_number(phone_number):

    phone_str = str(phone_number).strip()

    phone_str = phone_str.replace(" ", "").replace("+", "")

    if phone_str.startswith("0"):
        phone_str = "254" + phone_str[1:]

    elif phone_str.startswith("7"):
        phone_str = "254" + phone_str

    return phone_str