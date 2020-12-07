from sc2.constants import *
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2, Point3
from sc2.distances import *
from typing import List
import random


class VikingController:

    def __init__(self, bot=None):
        self.bot = bot
        self.enemy_has_air = 0
        self.lowest_health_viking_tag = None

    async def viking_micro(self):
        air_grid = self.bot.viking_escape_grid
        viking_grid = self.bot.viking_grid
        if not self.bot.vikings and not self.bot.vikingassault:
            return
        enemy_units_memory = self.bot.enemy_units_in_memory
        enemy_air_units_mem = enemy_units_memory.flying.filter(lambda x: not x.is_hallucination)
        enemy_air_units_memory = (enemy_air_units_mem | enemy_units_memory.of_type(UnitTypeId.COLOSSUS)).\
            filter(lambda x: x.can_be_attacked)
        if self.bot.debug_vikings:
            for unit in enemy_air_units_memory:
                if unit.timer > (self.bot.debug_timer * 5):
                    self.bot.debug_timer = unit.timer / 5
                p = unit.position
                h2 = self.bot.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                size = 0.2
                p0 = Point3((pos.x - size, pos.y - size, pos.z + (unit.timer / self.bot.debug_timer)))
                p1 = Point3((pos.x + size, pos.y + size, pos.z - 0))
                # print(f"Drawing {p0} to {p1}")
                c = Point3((0, 255, 255))
                self.bot._client.debug_box_out(p0, p1, color=c)

        self.enemy_has_air -= 1
        if enemy_air_units_memory:
            self.enemy_has_air = 50

        if self.bot.siegetanks_sieged and not self.bot.banshees:
            need_vision = self.bot.siegetanks_sieged.closest_to(self.bot.enemy_start_location)
        else:
            need_vision = None
        viking_can_land = False
        if self.enemy_has_air < 0:
            viking_can_land = True
        if enemy_air_units_memory.of_type([UnitTypeId.VOIDRAY, UnitTypeId.CARRIER]) or not self.bot.enemy_units:
            priority_targets = None
        else:
            priority_targets = enemy_air_units_memory.of_type([UnitTypeId.TEMPEST, UnitTypeId.MOTHERSHIP])
            if priority_targets:
                priority_targets = priority_targets.filter(lambda x: x.can_be_attacked)
            else:
                priority_targets = None
        if self.lowest_health_viking_tag:
            if self.lowest_health_viking_tag not in self.bot.vikings.tags:
                self.lowest_health_viking_tag = None

        enemy_air_units_our_base = self.bot.enemy_units_on_air.closer_than(20, self.bot.homeBase)
        check_health_once = True
        if self.bot.vikings.filter(lambda x: x.health_percentage < 1):
            vikings_sorted = self.bot.vikings.sorted(lambda x: x.health_percentage)
        else:
            vikings_sorted = self.bot.vikings.sorted(lambda x: x.distance_to(self.bot.homeBase))
        for viking in vikings_sorted:
            if viking_can_land:
                viking_can_land = False
                if viking.distance_to(self.bot.homeBase) > 5:
                    start = viking.position
                    goal = self.bot.homeBase.position
                    grid = air_grid
                    path = self.bot.map_data.pathfind(start=start, goal=goal, grid=grid, allow_diagonal=True, sensitivity=3)
                    if len(path) > 0:
                        for point in path:
                            if self.bot.in_map_bounds(point):
                                self.bot.do(viking.move(point))
                                break
                            else:
                                print("Pathing error in viking landing path.")
                elif len(viking.orders) == 0:
                    self.bot.do(viking(AbilityId.MORPH_VIKINGASSAULTMODE))
                continue
            if check_health_once and not enemy_air_units_our_base:
                if not self.lowest_health_viking_tag:
                    check_health_once = False
                    if viking.health_percentage < 1:
                        self.lowest_health_viking_tag = viking.tag

            targets = self.bot.enemy_units_on_air.in_attack_range_of(viking, 0).visible
            if targets and viking.weapon_cooldown == 0:
                target = targets.sorted(lambda x: x.health + x.shield, reverse=False)[0]
                self.bot.do(viking.attack(target))
                continue
            priority_targets_this_frame = self.bot.enemy_units.\
                of_type([UnitTypeId.TEMPEST, UnitTypeId.MOTHERSHIP]).visible
            if priority_targets_this_frame:
                pt = priority_targets_this_frame.in_attack_range_of(viking, 2).visible
                if pt:
                    target = pt.closest_to(viking)
                    self.bot.do(viking.move(target.position))
                    continue

            if viking.tag == self.lowest_health_viking_tag or viking.health_percentage < 0.3 \
                    and not enemy_air_units_our_base and self.bot.max_viking > 2:
                if viking.distance_to(self.bot.homeBase) > 5:
                    start = viking.position
                    goal = self.bot.homeBase.position
                    grid = air_grid
                    path = self.bot.map_data.pathfind(start=start, goal=goal, grid=grid,
                                                      allow_diagonal=True, sensitivity=3)
                    if len(path) > 0:
                        for point in path:
                            if self.bot.in_map_bounds(point):
                                self.bot.do(viking.move(point))
                                break
                        # print("Pathing error in viking low health retreat path.")

                elif len(viking.orders) == 0:
                    self.bot.do(viking(AbilityId.MORPH_VIKINGASSAULTMODE))
                continue

            if priority_targets:
                start = viking.position
                goal = self.bot.closest_unit_position(units_in_memory=priority_targets, unit=viking)
                if not self.bot.enemy_memories_closer_than(20, viking):
                    self.bot.do(viking.move(viking.position.towards(goal, 3)))
                    self.bot.do(viking.move(goal, queue=True))
                    continue
                grid = viking_grid
                path = self.bot.map_data.pathfind(start=start, goal=goal, grid=grid,
                                                  allow_diagonal=True, sensitivity=3)
                if len(path) > 0:
                    self.bot.do(viking.move(path[0]))
                continue
            # retreat to safe spot if on cool down
            if viking.weapon_cooldown != 0 \
                    and self.bot.in_air_range_of_units(viking, self.bot.enemy_units_on_ground, bonus_distance=3):
                if self.bot.in_air_range_of_units(viking, self.bot.enemy_units, bonus_distance=2):
                    position = viking.position
                    radius = 6
                    grid = air_grid
                    retreat_points: List[Point2] = self.bot.map_data.find_lowest_cost_points(from_pos=position,
                                                                                             radius=radius, grid=grid)
                    retreat_point = random.choice(retreat_points)
                    self.bot.do(viking.move(retreat_point))
                    continue

            if len(viking.orders) > 1:
                continue

            # search and destroy
            if enemy_air_units_memory and self.bot.enemy_units:
                start = viking.position
                goal = self.bot.closest_unit_position(units_in_memory=enemy_air_units_memory, unit=viking)
                if not self.bot.enemy_memories_closer_than(20, viking)\
                        and not self.bot.enemy_structures.filter(lambda x: x.can_attack_air).closer_than(20, viking):
                    self.bot.do(viking.move(viking.position.towards(goal, 3)))
                    self.bot.do(viking.move(goal, queue=True))
                    continue
                grid = viking_grid
                path = self.bot.map_data.pathfind(start=start, goal=goal, grid=grid,
                                                  allow_diagonal=False, sensitivity=3)
                # if viking.is_taking_damage:
                #     self.bot.map_data.plot_influenced_path\
                #         (start=start, goal=goal, weight_array=grid, allow_diagonal=True)
                #     self.bot.map_data.show()
                if self.bot.debug_vikings:
                    for p in path:
                        h2 = self.bot.get_terrain_z_height(p)
                        pos = Point3((p.x, p.y, h2))
                        size = 0.2
                        p0 = Point3((pos.x - size, pos.y - size, pos.z + 1))
                        p1 = Point3((pos.x + size, pos.y + size, pos.z - 0))
                        c = Point3((255, 0, 0))
                        self.bot._client.debug_box_out(p0, p1, color=c)
                if len(path) > 0:
                    for point in path:
                        if self.bot.in_map_bounds(point):
                            self.bot.do(viking.attack(point))
                            break
                        else:
                            print("Pathing error in viking attack.")
                            # print("path =", path)
                            # print("Playable area: x",
                            #       self.bot._game_info.playable_area.x, "-",
                            #       self.bot._game_info.playable_area.x + self.bot.game_info.playable_area.width,
                            #       "y:", self.bot._game_info.playable_area.y, "-",
                            #       self.bot._game_info.playable_area.y + self.bot.game_info.playable_area.height)
                            # self.bot.map_data.plot_influenced_path\
                            #     (start=start, goal=goal, weight_array=grid, allow_diagonal=True)
                            # self.bot.map_data.show()

                continue

            # provide vision for tanks
            if need_vision:
                start = viking.position
                goal = need_vision.position
                grid = air_grid
                if viking.distance_to(goal) > 10:
                    path = self.bot.map_data.pathfind(start=start, goal=goal, grid=grid,
                                                      allow_diagonal=True, sensitivity=3)
                    if len(path) > 0:
                        for point in path:
                            if self.bot.in_map_bounds(point):
                                self.bot.do(viking.attack(point))
                                break
                            else:
                                print("Pathing error in viking tank vision path.")
                    continue
                elif len(viking.orders) == 0:
                    radius = 8
                    retreat_points: List[Point2] = self.bot.map_data.find_lowest_cost_points(from_pos=start,
                                                                                             radius=radius, grid=grid)
                    retreat_point = random.choice(retreat_points)
                    self.bot.do(viking.move(retreat_point))
                continue

            if viking.distance_to(self.bot.homeBase) > 5:
                start = viking.position
                goal = self.bot.homeBase.position
                if not self.bot.enemy_memories_closer_than(20, viking):
                    self.bot.do(viking.move(goal))
                    continue
                grid = air_grid
                path = self.bot.map_data.pathfind(start=start, goal=goal, grid=grid, allow_diagonal=True, sensitivity=3)
                self.bot.do(viking.move(path[0]))
                if len(path) > 0:
                    for point in path:
                        if self.bot.in_map_bounds(point):
                            self.bot.do(viking.attack(point))
                            break
                        else:
                            print("Pathing error in viking tank vision path.")
                continue

        for viking in self.bot.vikingassault:
            if viking.distance_to(self.bot.homeBase) < 15:
                if viking.health_percentage < 1:
                    continue
            if self.enemy_has_air > 0:
                self.bot.do(viking(AbilityId.MORPH_VIKINGFIGHTERMODE))
                continue

            if await self.bot.avoid_enemy_siegetanks(viking):
                continue

            if self.bot.enemy_units_on_ground.closer_than(self.bot.defence_radius, self.bot.homeBase):
                if viking.weapon_cooldown != 0 and viking.health_percentage < 1:
                    closest_enemy = self.bot.enemy_units_on_ground.closest_to(viking)
                    self.bot.do(viking.move(viking.position.towards(closest_enemy.position, -10)))
                    continue
                priority_targets = self.bot.enemy_units_on_ground.\
                    filter(lambda x: x.is_mechanical and
                                     x.distance_to(viking) < x.radius + x.ground_range + viking.radius)
                if priority_targets:
                    target = priority_targets.closest_to(viking)
                    self.bot.do(viking.attack(target))
                    continue
                target = self.bot.enemy_units_on_ground.closest_to(viking)
                self.bot.do(viking.attack(target.position))
                continue
            secondary_targets = self.bot.enemy_structures.filter(lambda x: x.is_visible)
            if secondary_targets and self.bot.supply_used > 190:
                target = secondary_targets.closest_to(viking)
                self.bot.do(viking.attack(target.position))
                continue
            # if self.bot.general:
            #     if viking.distance_to(self.bot.general.position) > 10:
            #         self.bot.do(viking.move(self.bot.general.position))
            #         continue
            elif viking.distance_to(self.bot.homeBase) > 8:
                self.bot.do(viking.move(self.bot.homeBase))
                continue