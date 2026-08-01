import random

from constants.VipScenarios import VIP_SCENARIOS


async def get_random_vip_scenario():
    return random.choice(VIP_SCENARIOS)

