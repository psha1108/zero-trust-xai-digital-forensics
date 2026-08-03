import random
from faker import Faker
import uuid
import datetime

from ml.data_generation.constants import SCENARIOS, RISK_LABELS, IP_PREFIXES, DEVICE_PREFIXES

fake = Faker()

def get_scenario_by_risk(risk_label):
    if risk_label in SCENARIOS:
        return random.choice(SCENARIOS[risk_label])
    return "normal_office_login"

def generate_ip(is_internal=True):
    prefix = random.choice(IP_PREFIXES["internal"] if is_internal else IP_PREFIXES["external"])
    if prefix.endswith('.'):
        prefix = prefix[:-1]
    octets = prefix.split('.')
    while len(octets) < 4:
        octets.append(str(random.randint(1, 254)))
    return ".".join(octets)

def generate_device_id():
    prefix = random.choice(DEVICE_PREFIXES)
    return f"{prefix}{fake.hexify(text='^^^^^^^^')}".upper()

def determine_risk_label():
    rand_val = random.random()
    if rand_val < 0.47:
        return "low"
    elif rand_val < 0.80:
        return "medium"
    else:
        return "high"
