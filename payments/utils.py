def format_phone_number(phone_number):
   
    phone_str = str(phone_number).strip()
    
    if phone_str.startswith('0'):
        return '254' + phone_str[1:]
    
    if phone_str.startswith('254'):
        return phone_str
        
    return phone_str