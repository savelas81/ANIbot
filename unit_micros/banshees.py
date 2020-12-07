from sc2.constants import *
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2, Point3
from sc2.distances import *
from typing import List
import random


class BansheeController:

    def __init__(self, bot=None):
        self.take_route_a = True
        self.bot = bot
        self.banshee_targets_by_tag = {int: Point2}

    async def bansheemicro(self):
        a_target_types = [UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.MULE]
        units_to_ignore = [UnitTypeId.ADEPTPHASESHIFT, UnitTypeId.EGG, UnitTypeId.LARVA, UnitTypeId.BROODLING]
        priority_a_targets = self.bot.enemy_units.of_type(a_target_types)
        priority_b_targets = self.bot.enemy_units_on_ground.exclude_type(units_to_ignore)
        priority_c_targets = self.bot.enemy_structures.filter(lambda x: x.is_visible).\
            exclude_type([UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORBURROWED])
        enemy_townhalls = self.bot.enemy_structures.of_type([UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND,
                                                            UnitTypeId.PLANETARYFORTRESS, UnitTypeId.HATCHERY,
                                                            UnitTypeId.LAIR, UnitTypeId.HIVE, UnitTypeId.NEXUS])
        for banshee in self.bot.banshees:
            if banshee.is_taking_damage and banshee.health_percentage < 0.5 \
                    and await self.bot.can_cast(banshee, AbilityId.BEHAVIOR_CLOAKON_BANSHEE):
                self.bot.do(banshee(AbilityId.BEHAVIOR_CLOAKON_BANSHEE))
                continue
            # if banshee.has_buff(BuffId.LOCKON):
            #     closest_enemy = None
            #     enemy_cyclones = self.bot.enemy_units.of_type(UnitTypeId.CYCLONE).closer_than(20, banshee)
            #     enemy_air_threats = self.bot.enemy_units.filter(lambda x: x.can_attack_air)
            #     if enemy_cyclones:
            #         closest_enemy = enemy_cyclones.closest_to(banshee)
            #     elif enemy_air_threats:
            #         closest_enemy = enemy_air_threats.closest_to(banshee)
            #     if closest_enemy:
            #         self.bot.do(banshee.move(banshee.position.towards(closest_enemy, -10)))
            #         continue
            #     else:
            #         self.bot.do(banshee.move(self.bot.start_location))
            #         continue


            if banshee.weapon_cooldown == 0:
                targets_a_in_range = priority_a_targets.in_attack_range_of(banshee)
                targets_b_in_range = priority_b_targets.in_attack_range_of(banshee)
                targets_c_in_range = priority_c_targets.in_attack_range_of(banshee)
                target = None
                if targets_a_in_range:
                    target = targets_a_in_range.sorted(lambda x: (x.health + x.shield), reverse=False).first
                elif targets_b_in_range:
                    target = priority_b_targets.closest_to(banshee)
                elif enemy_townhalls.in_attack_range_of(banshee):
                    target = enemy_townhalls.closest_to(banshee)
                elif not enemy_townhalls and targets_c_in_range:
                    target = priority_c_targets.closest_to(banshee)
                if target:
                    self.bot.do(banshee.attack(target))
                    continue
            else:
                if banshee.tag in self.banshee_targets_by_tag:
                    self.banshee_targets_by_tag.pop(banshee.tag)
                position = banshee.position
                radius = 8
                grid = self.bot.air_grid
                retreat_points: List[Point2] = self.bot.map_data.find_lowest_cost_points(from_pos=position,
                                                                                         radius=radius, grid=grid)
                retreat_point = random.choice(retreat_points)
                self.bot.do(banshee.move(retreat_point))

                if self.bot.debug:
                    for p in retreat_points:
                        h2 = self.bot.get_terrain_z_height(p)
                        pos = Point3((p.x, p.y, h2))
                        size = 0.2
                        p0 = Point3(
                            (pos.x - size, pos.y - size, pos.z + 0.5))  # + Point2((0.5, 0.5))
                        p1 = Point3((pos.x + size, pos.y + size, pos.z - 0))  # + Point2((0.5, 0.5))
                        # print(f"Drawing {p0} to {p1}")
                        c = Point3((255, 0, 255))
                        self.bot._client.debug_box_out(p0, p1, color=c)
                    p = retreat_point
                    h2 = self.bot.get_terrain_z_height(p)
                    pos = Point3((p.x, p.y, h2))
                    size = 0.2
                    p0 = Point3(
                        (pos.x - size, pos.y - size, pos.z + 5))  # + Point2((0.5, 0.5))
                    p1 = Point3((pos.x + size, pos.y + size, pos.z - 0))  # + Point2((0.5, 0.5))
                    # print(f"Drawing {p0} to {p1}")
                    c = Point3((255, 255, 255))
                    self.bot._client.debug_box_out(p0, p1, color=c)
                continue

            if self.bot.enemy_structures:
                if banshee.tag in self.banshee_targets_by_tag:
                    target = self.banshee_targets_by_tag[banshee.tag]
                elif enemy_townhalls:
                    target = enemy_townhalls.random.position
                    self.banshee_targets_by_tag[banshee.tag] = target
                elif self.bot.enemy_structures:
                    target = self.bot.enemy_structures.random.position
                    self.banshee_targets_by_tag[banshee.tag] = target
                if target:
                    start = banshee.position
                    goal = target
                    grid = self.bot.air_grid
                    path = self.bot.map_data.pathfind(start=start, goal=goal, grid=grid, allow_diagonal=True, sensitivity=3)
                    if len(path) > 0:
                        for point in path:
                            if self.bot.in_map_bounds(point):
                                self.bot.do(banshee.move(point))
                                break
                            else:
                                print("Pathing error in banshee attack path.")
                    else:
                        self.banshee_targets_by_tag.pop(banshee.tag)

                else:
                    target = random.choice(self.bot.expansion_locations_list)
                    self.bot.do(banshee.attack(target))
            elif len(banshee.orders) == 0:
                if self.take_route_a:
                    self.take_route_a = False
                    for point in reversed(self.bot.attack_route_a):
                        self.bot.do(banshee.attack(point, queue=True))
                    # self.bot.do(banshee.attack(self.bot.enemy_natural, queue=True))
                    # self.bot.do(banshee.attack(self.bot.enemy_start_location, queue=True))
                else:
                    self.take_route_a = True
                    for point in reversed(self.bot.attack_route_b):
                        self.bot.do(banshee.attack(point, queue=True))
                    # self.bot.do(banshee.attack(self.bot.enemy_natural, queue=True))
                    # self.bot.do(banshee.attack(self.bot.enemy_start_location, queue=True))



            continue
            # unit_in_no_flight_zone = (
            #     self.bot.enemy_structures.filter(lambda x: x.can_attack_air).closer_than(12, banshee))
            # if banshee.is_taking_damage and await self.bot.can_cast(banshee, AbilityId.BEHAVIOR_CLOAKON_BANSHEE):
            #     self.bot.do(banshee(AbilityId.BEHAVIOR_CLOAKON_BANSHEE))
            #     continue
            #
            # if unit_in_no_flight_zone:
            #     # if self.supply_used < 180:
            #     if self.bot.banshee_left > 0 and self.bot.supply_used < 190:
            #         self.bot.do(banshee.move(self.bot.homeBase.position))
            #         continue
            #     else:
            #         self.bot.do(banshee.attack(unit_in_no_flight_zone.closest_to(banshee)))
            #         continue
            #
            # if await self.bot.avoid_own_nuke(banshee):
            #     self.bot.do(banshee.move(self.bot.homeBase.position))
            #     continue
            #
            # air_units_too_close = enemy_aa_units.filter(
            #     lambda unit: unit.distance_to(banshee) < unit.radius + unit.air_range + banshee.radius + 2)
            # if air_units_too_close:
            #     closest_threath = air_units_too_close.closest_to(banshee)
            #     self.bot.do(banshee.move(banshee.position.towards(closest_threath.position, -10)))
            #     continue
            #
            # if targets:
            #     if banshee.weapon_cooldown != 0:
            #         ground_units_too_close = ground_threats.filter(
            #             lambda unit: unit.distance_to(banshee) < unit.radius + unit.air_range + banshee.radius + 2)
            #         if ground_units_too_close:
            #             closest_threath = ground_units_too_close.closest_to(banshee)
            #             self.bot.do(banshee.move(banshee.position.towards(closest_threath.position, -5)))
            #             continue
            #     else:
            #         self.bot.do(banshee.attack(targets.closest_to(banshee)))
            #         continue
            # if secondary_targets:
            #     target = secondary_targets.closest_to(banshee)
            #     self.bot.do(banshee.attack(target.position))
            #     continue
            # if self.bot.pick_fight and self.bot.cyclones:
            #     target_position = self.bot.cyclones.closest_to(banshee).position
            #     if banshee.distance_to(target_position) > 3:
            #         self.bot.do(banshee.attack(target_position))
            #     continue
            #
            # if self.bot.general:
            #     target_position = self.bot.general.position.towards(self.bot.enemy_start_location, 5)
            #     if banshee.distance_to(target_position) > 3:
            #         self.bot.do(banshee.attack(target_position))
            #     continue
            #
            # if banshee.position.to2.distance_to(outpost.position.to2) > 8:
            #     self.bot.do(banshee.move(outpost))
            #     continue
            #
