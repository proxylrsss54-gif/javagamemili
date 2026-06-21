import random

def random_donor():
    first = random.choice(["John","Mary","Robert","Jennifer","Michael","Linda"])
    last = random.choice(["Smith","Johnson","Williams","Brown","Jones"])
    email = f"{first.lower()}{random.randint(100,999)}@gmail.com"
    return {"first": first, "last": last, "email": email, 
            "address": random.choice(["123 Main St","456 Oak Ave"]), 
            "city": random.choice(["Boston","New York"]), 
            "state": random.choice(["MA","NY"]), 
            "zip": random.choice(["02101","10001"])}

def random_hex(length):
    return ''.join(random.choices('0123456789abcdef', k=length))