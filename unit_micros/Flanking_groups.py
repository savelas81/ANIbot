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
        self.add_to_flank_group_1 = True
        self.first_wave_to_enemy_natural = True

    async def flanking_group_micro(self):
        if self.bot.basic_marines.idle.amount >= 12 \
                and self.bot.flank_group_1. amount + self.bot.flank_group_2.amount < 5:
            if self.first_wave_to_enemy_natural:
                rally_point = self.bot.natural.towards(self.bot.game_info.map_center, 5)
                for marine in self.bot.basic_marines:
                    self.bot.add_unit_to_flank_1(marine)
                    self.bot.do(marine.attack(self.bot.enemy_natural))
                    self.bot.do(marine.attack(rally_point, queue=True))
                self.first_wave_to_enemy_natural = False
                return
            for marine in self.bot.basic_marines:
                if self.add_to_flank_group_1:
                    self.bot.add_unit_to_flank_1(marine)
                    self.add_to_flank_group_1 = False
                    self.bot.do(marine.move(marine.position, queue=False))
                    for point in reversed(self.bot.attack_route_a):
                        if not self.bot.ccANDoc.closer_than(3, point):
                            self.bot.do(marine.attack(point, queue=True))
                    self.bot.do(marine.attack(self.bot.enemy_natural, queue=True))
                    self.bot.do(marine.attack(self.bot.enemy_start_location, queue=True))
                    continue
                else:
                    self.bot.add_unit_to_flank_2(marine)
                    self.add_to_flank_group_1 = True
                    for point in reversed(self.bot.attack_route_b):
                        if not self.bot.ccANDoc.closer_than(3, point):
                            self.bot.do(marine.attack(point, queue=True))
                    self.bot.do(marine.attack(self.bot.enemy_natural, queue=True))
                    self.bot.do(marine.attack(self.bot.enemy_start_location, queue=True))
                    continue
            self.bot.send_flanking_units -= 1
            return
        for marine in self.bot.basic_marines.idle:
            rally_point = self.bot.natural.towards(self.bot.game_info.map_center, 5)
            if marine.distance_to(rally_point) > 5:
                self.bot.do(marine.attack(rally_point))
                continue
        for marine in (self.bot.flank_group_1 | self.bot.flank_group_2):
            if len(marine.orders) == 0:
                self.bot.remove_from_flanking_groups(marine)
                if marine.distance_to(self.bot.start_location) > 6:
                    point = self.bot.start_location.random_on_distance(5)
                    self.bot.do(marine.attack(point))
            if marine.distance_to(self.bot.enemy_start_location) < 5:
                self.bot.send_flanking_units = 0
                self.bot.clear_units_in_flank_1()
                self.bot.clear_units_in_flank_2()
            if marine.weapon_cooldown != 0:
                if await self.bot.can_cast(marine, AbilityId.EFFECT_STIM_MARINE) \
                        and not marine.has_buff(BuffId.STIMPACK):
                    self.bot.do(marine(AbilityId.EFFECT_STIM_MARINE))
                    continue  # continue for loop, dont execute any of the following
                # self.bot.do(marine.attack(self.bot.natural.random_on_distance(3), queue=False))
                # self.bot.remove_from_flanking_groups(marine)
                continue

        #
        #
        #
        # if self.group_1_target and not self.bot.flank_group_1:
        #     self.group_1_target = None
        #     self.attack_route_a_temp = []
        # if not self.group_1_target and self.bot.flank_group_1 and not self.attack_route_a_temp:
        #     self.attack_route_a_temp = copy.copy(self.bot.attack_route_a)
        # if not self.group_1_target and self.bot.flank_group_1 and self.attack_route_a_temp:
        #     self.group_1_target = self.attack_route_a_temp.pop()
        #     self.group_1_target = self.group_1_target.towards(self.bot.game_info.map_center, -4)
        # if self.bot.flank_group_1 and self.group_1_target:
        #     if self.bot.flank_group_1.center.distance_to(self.group_1_target) < 2 \
        #             or self.bot.structures().closer_than(5, self.group_1_target):
        #         if self.attack_route_a_temp:
        #             self.group_1_target = self.attack_route_a_temp.pop()
        #             self.group_1_target = self.group_1_target.towards(self.bot.game_info.map_center, -4)
        #         else:
        #             self.group_1_target = None
        #             self.bot.clear_units_in_flank_1()
        #     else:
        #         for unit in self.bot.flank_group_1:
        #             if unit.weapon_cooldown != 0:
        #                 if await self.bot.can_cast(unit, AbilityId.EFFECT_STIM_MARINE) \
        #                         and not unit.has_buff(BuffId.STIMPACK):
        #                     self.bot.do(unit(AbilityId.EFFECT_STIM_MARINE))
        #                     continue  # continue for loop, dont execute any of the following
        #             if self.bot.iteraatio % 4 == 0:
        #                 self.bot.do(unit.move(self.group_1_target))
        #             else:
        #                 self.bot.do(unit.attack(self.group_1_target))
        #
        # if self.group_2_target and not self.bot.flank_group_2:
        #     self.group_2_target = None
        #     self.attack_route_b_temp = []
        # if not self.group_2_target and self.bot.flank_group_2 and not self.attack_route_b_temp:
        #     self.attack_route_b_temp = copy.copy(self.bot.attack_route_b)
        # if not self.group_2_target and self.bot.flank_group_2 and self.attack_route_b_temp:
        #     self.group_2_target = self.attack_route_b_temp.pop()
        #     self.group_2_target = self.group_2_target.towards(self.bot.game_info.map_center, -4)
        # if self.bot.flank_group_2 and self.group_2_target:
        #     if self.bot.flank_group_2.center.distance_to(self.group_2_target) < 2 \
        #             or self.bot.structures().closer_than(5, self.group_2_target):
        #         if self.attack_route_b_temp:
        #             self.group_2_target = self.attack_route_b_temp.pop()
        #             self.group_2_target = self.group_2_target.towards(self.bot.game_info.map_center, -4)
        #         else:
        #             self.group_2_target = None
        #             self.bot.clear_units_in_flank_2()
        #     else:
        #         for unit in self.bot.flank_group_2:
        #             if unit.weapon_cooldown != 0:
        #                 if await self.bot.can_cast(unit, AbilityId.EFFECT_STIM_MARINE) \
        #                         and not unit.has_buff(BuffId.STIMPACK):
        #                     self.bot.do(unit(AbilityId.EFFECT_STIM_MARINE))
        #                     continue  # continue for loop, dont execute any of the following
        #             if self.bot.iteraatio % 4 == 0:
        #                 self.bot.do(unit.move(self.group_2_target))
        #             else:
        #                 self.bot.do(unit.attack(self.group_2_target))
        #
        #
        #
        #
