import random
import copy
from sc2.constants import *
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2


class FlankingController:

    def __init__(self, bot=None):
        self.bot = bot
        self.send_group_1 = None
        self.group_1_target = None
        self.group_2_target = None
        self.attack_route_a_temp = []
        self.attack_route_b_temp = []

    async def flanking_group_micro(self):
        if self.group_1_target and not self.bot.flank_group_1:
            self.group_1_target = None
            self.attack_route_a_temp = []
        if not self.group_1_target and self.bot.flank_group_1 and not self.attack_route_a_temp:
            self.attack_route_a_temp = copy.copy(self.bot.attack_route_a)
        if not self.group_1_target and self.bot.flank_group_1 and self.attack_route_a_temp:
            self.group_1_target = self.attack_route_a_temp.pop()
        if self.bot.flank_group_1 and self.group_1_target:
            if self.bot.flank_group_1.center.distance_to(self.group_1_target) < 4:
                if self.attack_route_a_temp:
                    self.group_1_target = self.attack_route_a_temp.pop()
                else:
                    self.group_1_target = None
                    self.bot.clear_units_in_flank_1()
            else:
                for unit in self.bot.flank_group_1:
                    if unit.weapon_cooldown != 0:
                        if await self.bot.can_cast(unit, AbilityId.EFFECT_STIM_MARINE) \
                                and not unit.has_buff(BuffId.STIMPACK):
                            self.bot.do(unit(AbilityId.EFFECT_STIM_MARINE))
                            continue  # continue for loop, dont execute any of the following
                    if self.bot.iteraatio % 3 == 0:
                        self.bot.do(unit.attack(self.group_1_target.towards(unit, -5)))
                    else:
                        self.bot.do(unit.move(self.group_1_target.towards(unit, -5)))

        if self.group_2_target and not self.bot.flank_group_2:
            self.group_2_target = None
            self.attack_route_b_temp = []
        if not self.group_2_target and self.bot.flank_group_2 and not self.attack_route_b_temp:
            self.attack_route_b_temp = copy.copy(self.bot.attack_route_b)
        if not self.group_2_target and self.bot.flank_group_2 and self.attack_route_b_temp:
            self.group_2_target = self.attack_route_b_temp.pop()
        if self.bot.flank_group_2 and self.group_2_target:
            if self.bot.flank_group_2.center.distance_to(self.group_2_target) < 4:
                if self.attack_route_b_temp:
                    self.group_2_target = self.attack_route_b_temp.pop()
                else:
                    self.group_2_target = None
                    self.bot.clear_units_in_flank_2()
            else:
                for unit in self.bot.flank_group_2:
                    if unit.weapon_cooldown != 0:
                        if await self.bot.can_cast(unit, AbilityId.EFFECT_STIM_MARINE) \
                                and not unit.has_buff(BuffId.STIMPACK):
                            self.bot.do(unit(AbilityId.EFFECT_STIM_MARINE))
                            continue  # continue for loop, dont execute any of the following
                    if self.bot.iteraatio % 3 == 0:
                        self.bot.do(unit.attack(self.group_2_target.towards(unit, -5)))
                    else:
                        self.bot.do(unit.move(self.group_2_target.towards(unit, -5)))




