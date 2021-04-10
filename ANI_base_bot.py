import random, math, time

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.position import Pointlike, Point2, Point3
from sc2.unit import Unit
from sc2.units import Units
from typing import List, Dict, Set, Tuple, Any, Optional, Union  # mypy type checking
from sc2.ids.ability_id import AbilityId
from sharpy.knowledges import SkeletonBot


class ANI_base_bot(SkeletonBot):


    repair_group = []
    basic_marines = []
    squad_group = []
    flank_group_1 = []
    flank_group_2 = []
    kodinturvajoukot = []
    puuhapete = None
    remember_enemy_units_by_tag = {}
    remembered_detectors_by_tag = {}
    remembered_snapshots_by_tag = {}
    remembered_puuhapete_by_tag = {}
    remembered_repair_group_by_tag = {}
    remembered_friendly_units_by_tag = {}
    remembered_squad_units_by_tag = {}
    remember_flank_1_by_tag = {}
    remember_flank_2_by_tag = {}
    remembered_kodinturvajoukot_by_tag = {}
    remembered_kamikaze_troops_by_tag = {}
    remember_units_on_cooldown_tags = []
    we_win = None
    cached_expansions = []
    take_third_first = False
    expansion_builder_tag = None

    def configure_managers(self) -> Optional[List["ManagerBase"]]:
        return []

    def we_are_winning(self):
        enemy_health = 0
        our_health = 0
        units_to_ignore = [DRONE, SCV, PROBE]
        for unit in self.enemy_units_and_structures.exclude_type(units_to_ignore).filter(lambda x: x.can_attack_ground):
            enemy_health += (unit.health + unit.shield)
        for unit in self.units.exclude_type(units_to_ignore).filter(lambda x: x.can_attack_ground):
            our_health += unit.health
        if our_health > (1.8 * enemy_health):
            # print ("our health", our_health, "enemy_health", enemy_health)
            return True
        else:
            return False

    def save_units_on_cooldown(self):
        self.remember_units_on_cooldown_tags.clear()
        for unit in self.units:
            if unit.weapon_cooldown != 0:
                self.remember_units_on_cooldown_tags.append(unit.tag)

    def remember_friendly_units(self):
        # goes throug every bot unit
        # saves .is_taking_damage True or False
        self.basic_marines = sc2.units.Units([], self)
        self.squad_group = sc2.units.Units([], self)
        self.flank_group_1 = sc2.units.Units([], self)
        self.flank_group_2 = sc2.units.Units([], self)
        self.kodinturvajoukot = sc2.units.Units([], self)
        for unit in (self.units):
            unit.is_taking_damage = False
            unit.did_take_first_hit = False
            unit.is_in_squad = False
            unit.is_in_kodinturvajoukot = False
            unit.is_in_kamikaze_troops = False

            if unit.tag in self.remember_units_on_cooldown_tags:
                unit.was_on_cool_down = True
            else:
                unit.was_on_cool_down = False

            # If we already remember this friendly unit
            if unit.tag in self.remembered_friendly_units_by_tag:
                health_old = self.remembered_friendly_units_by_tag[unit.tag].health
                health_percentage_old = self.remembered_friendly_units_by_tag[unit.tag].health_percentage

                # Compare its health/shield since last step, to find out if it has taken any damage
                if unit.health < health_old:
                    unit.is_taking_damage = True
                    if not health_percentage_old < 1:
                        unit.did_take_first_hit = True

            if unit.tag in self.remembered_kamikaze_troops_by_tag:
                unit.is_in_kamikaze_troops = True
            if unit.tag in self.remembered_kodinturvajoukot_by_tag:
                unit.is_in_kodinturvajoukot = True
                self.kodinturvajoukot.append(unit)
            elif unit.tag in self.remembered_squad_units_by_tag:
                unit.is_in_squad = True
                self.squad_group.append(unit)
            elif unit.tag in self.remember_flank_1_by_tag:
                unit.is_in_flank_1 = True
                self.flank_group_1.append(unit)
            elif unit.tag in self.remember_flank_2_by_tag:
                unit.is_in_flank_2 = True
                self.flank_group_2.append(unit)
            elif unit.type_id == UnitTypeId.MARINE:
                self.basic_marines.append(unit)

            # saves units tag
            self.remembered_friendly_units_by_tag[unit.tag] = unit

    def select_contractor(self, pos: Union[Unit, Point2, Point3], force: bool = False) -> Optional[Unit]:
        """Select a worker to build a bulding with."""

        workers = self.workers
        for worker in workers.sorted_by_distance_to(pos):
            if worker.is_puuhapete:
                continue
            if worker.is_in_repair_group:
                continue
            if len(worker.orders) > 0:
                # print(scv.orders, scv.order_target)
                if worker.order_target in self.mineral_field.tags:
                    return worker
            if ((len(worker.orders) == 1
                 and worker.is_carrying_minerals
                 and worker.orders[0].ability.id in {AbilityId.MOVE, AbilityId.HARVEST_RETURN})):
                return worker

        return workers.random if force else None

    def remember_enemy_units(self):
        self.enemy_units_in_memory = sc2.units.Units([], self)
        tags_to_be_deleted = []

        # delete visible and old units from memory
        for enemy_tag_in_memory in self.remember_enemy_units_by_tag.keys():
            enemy_unit = self.remember_enemy_units_by_tag[enemy_tag_in_memory]
            enemy_unit.timer -= 1
            if enemy_unit.timer <= 0 or self.is_visible(enemy_unit.position):
                tags_to_be_deleted.append(enemy_tag_in_memory)
            else:
                self.remember_enemy_units_by_tag.update({enemy_tag_in_memory: enemy_unit})
        for tag in tags_to_be_deleted:
            self.remember_enemy_units_by_tag.pop(tag)

        # save all enemy units on memory
        for unit in self.enemy_units:
            unit.timer = 1000
            if unit.tag in self.remember_enemy_units_by_tag.keys():
                self.remember_enemy_units_by_tag.update({unit.tag: unit})
            else:
                self.remember_enemy_units_by_tag[unit.tag] = unit

        # make sc2.units object to be used in bot code
        for enemy_unit in self.remember_enemy_units_by_tag.values():
            self.enemy_units_in_memory.append(enemy_unit)

    def enemy_memories_closer_than(self, dist, unit) -> bool:
        for memory in self.enemy_units_in_memory:
            pos = memory.position
            if unit.distance_to(pos) < dist:
                return True
        return False

    def closest_unit_position(self, units_in_memory: Units, unit: Unit) -> Pointlike:
        dist = math.inf
        closest = None
        for memory in units_in_memory:
            pos = memory.position
            distance_to_pos = unit.distance_to(pos)
            if distance_to_pos < dist:
                dist = distance_to_pos
                closest = pos
        return closest

    def remember_detectors(self):
        detector_info = {}
        detector_list = []  # list of detector tags in current frame
        detectors_to_be_deleted = []

        for detector_in_memory in self.remembered_detectors_by_tag.keys():
            detector_info = self.remembered_detectors_by_tag[detector_in_memory]
            timer = detector_info["TIMER"]
            timer -= 1
            pos = detector_info["POS"]
            if timer <= 0:
                detectors_to_be_deleted.append(detector_in_memory)
                continue
            detector_info.update({"TIMER": timer})
            self.remembered_detectors_by_tag.update({detector_in_memory: detector_info})

        for detector in detectors_to_be_deleted:
            if detector in self.remembered_detectors_by_tag:
                self.remembered_detectors_by_tag.pop(detector)

        for unit in self.enemy_units.filter(lambda x: x.is_detector):
            totalrange = (unit.sight_range + 2)
            detector_list.append(unit.tag)
            detector_info = {"POS": unit.position, "RANGE": totalrange, "TIMER": 20}
            if unit.tag not in self.remembered_detectors_by_tag:
                self.remembered_detectors_by_tag[unit.tag] = detector_info
                continue
            else:
                self.remembered_detectors_by_tag.update({unit.tag: detector_info})
                continue

    def detectors_in_memory_list(self):
        detectors = []
        for tag in self.remembered_detectors_by_tag:
            detectors.append(self.remembered_detectors_by_tag[tag])
        return detectors

    def remember_snapshots(self):
        snapshot_info = {}
        snapshot_list = []  # list of snapshot tags in current frame
        snapshots_to_be_deleted = []
        for unit in self.enemy_units.filter(lambda x: x.is_snapshot):
            totalrange = (unit.ground_range + unit.radius)
            snapshot_list.append(unit.tag)
            snapshot_info = {"POS": unit.position, "RANGE": totalrange, "TIMER": 100}
            if unit.tag not in self.remembered_snapshots_by_tag:
                self.remembered_snapshots_by_tag[unit.tag] = snapshot_info
                continue
            else:
                self.remembered_snapshots_by_tag.update({unit.tag: snapshot_info})
                continue

        for snapshot_in_memory in self.remembered_snapshots_by_tag.keys():
            if snapshot_in_memory in snapshot_list:
                continue
            else:
                snapshot_info = self.remembered_snapshots_by_tag[snapshot_in_memory]
                timer = snapshot_info["TIMER"]
                timer -= 1
                pos = snapshot_info["POS"]
                if timer <= 0 or self.is_visible(pos):
                    snapshots_to_be_deleted.append(snapshot_in_memory)
                    continue
                snapshot_info.update({"TIMER": timer})
                self.remembered_snapshots_by_tag.update({snapshot_in_memory: snapshot_info})
        for snapshot in snapshots_to_be_deleted:
            if snapshot in self.remembered_snapshots_by_tag:
                self.remembered_snapshots_by_tag.pop(snapshot)

    def in_ground_range_of_units(self, unit: Unit, units: Units, bonus_distance=0):
        return units.filter(lambda x: x.distance_to(unit) < x.radius + x.ground_range + unit.radius + bonus_distance)

    def in_air_range_of_units(self, unit: Unit, units: Units, bonus_distance=0):
        return units.filter(lambda x: x.distance_to(unit) < x.radius + x.air_range + unit.radius + bonus_distance)

    def closest_snapshot_in_range(self, unit, distance=3):
        if not unit:
            return None
        closest_enemy_unit_pos = None
        distance_to_closest_enemy_threat_range = math.inf
        for enemy_tag in self.remembered_snapshots_by_tag:
            enemy_unit = self.remembered_snapshots_by_tag[enemy_tag]
            distance_to_enemy = unit.distance_to(enemy_unit["POS"])
            if distance_to_enemy < enemy_unit["RANGE"] + distance:
                distance_to_enemy_threat_range = distance_to_enemy - enemy_unit["RANGE"]
                if distance_to_enemy_threat_range < distance_to_closest_enemy_threat_range:
                    distance_to_closest_enemy_threat_range = distance_to_enemy_threat_range
                    closest_enemy_unit_pos = enemy_unit["POS"]
        return closest_enemy_unit_pos

    def threat_to_ground(self) -> "Units":
        visible = self.filter(lambda unit: unit.is_visible)
        return visible.filter(lambda unit: unit.can_attack_ground)

    async def marine_total(self):
        marineTotal = 0
        for barracks in self.units(BARRACKS).ready:
            for order in barracks.orders:
                if order.ability.id in [BARRACKSTRAIN_MARINE]:
                    marineTotal = marineTotal + 1
        marineTotal = marineTotal + self.units(MARINE).amount
        return marineTotal

    async def expand_now_ANI(self, building: UnitTypeId = None, max_distance: Union[int, float] = 10,
                             location: Optional[Point2] = None):
        """Takes new expansion."""

        if not building:
            # self.race is never Race.Random
            start_townhall_type = {Race.Protoss: UnitTypeId.NEXUS, Race.Terran: UnitTypeId.COMMANDCENTER,
                                   Race.Zerg: UnitTypeId.HATCHERY}
            building = start_townhall_type[self.race]

        assert isinstance(building, UnitTypeId)

        # if map name golden wall then third behind gold wall
        # just maybe only in certain strategies
        # 135.5, 58.5

        if self.take_third_first:
            if self.ccANDoc.closer_than(3, self.take_third_first):
                self.take_third_first = False
            else:
                location = self.take_third_first

        if not location:
            location = await self.get_next_expansion()
        if location is None:
            print("No expansions left and trying to expand!")
            return False

        unit = None
        if self.expansion_builder_tag in self.units.of_type(UnitTypeId.SCV).tags:
            for scv in self.units.of_type(UnitTypeId.SCV):
                if scv.tag == self.expansion_builder_tag:
                    unit = scv
                    self.expansion_builder_tag = "used"
                    break
        if not unit:
            unit = self.select_contractor(location)
        if not unit:
            return False

        await self.build(building, near=location, max_distance=max_distance, build_worker=unit,
                         random_alternative=False, placement_step=1)
        if self.chat_first_base and self.ccANDoc.amount == 1:
            print("SCV: Building first expansion!")
            self.chat_first_base = False
        elif self.chat_second_base == True and self.ccANDoc.amount == 2:
            print("SCV: Building second expansion!")
            self.chat_second_base = False
        return True

    async def get_next_expansion(self) -> Optional[Point2]:
        """Find next expansion location."""

        startp = self._game_info.player_start_location
        closest = None
        distance = math.inf
        for el in self.expansion_locations_dict:
            def is_near_to_expansion(t):
                return t.position.distance_to(el) < self.EXPANSION_GAP_THRESHOLD

            if any(map(is_near_to_expansion, self.townhalls)):
                # already taken
                continue

            if not await self.can_place(COMMANDCENTER, el):
                continue

            if (self.enemy_units | self.enemy_structures).closer_than(15, el):
                continue

            if not self.mineral_field.closer_than(10, el):
                continue

            d = await self._client.query_pathing(startp, el)
            if d is None:
                continue

            if d < distance:
                distance = d
                closest = el

        return closest

    async def cache_expansions(self):
        expansions = list(self.expansion_locations_dict.keys())
        print(expansions)
        exp = []
        while expansions:
            """Find next expansion location tp defend."""
            startp = self._game_info.player_start_location
            closest = None
            distance = math.inf
            for el in expansions:
                def is_near_to_expansion(t):
                    return t.position.distance_to(el) < self.EXPANSION_GAP_THRESHOLD

                if any(map(is_near_to_expansion, self.townhalls)):
                    # already taken
                    expansions.remove(el)
                    continue

                d = await self._client.query_pathing(startp, el)
                if d is None:
                    expansions.remove(el)
                    continue

                if d < distance:
                    distance = d
                    closest = el
            expansions.remove(closest)
            exp.append(closest)
        print(exp)
        for x in exp:
            print(await self._client.query_pathing(startp, x))
        self.cached_expansions = exp

    async def get_next_expansion_to_defend(self) -> Optional[Point2]:
        """Find next expansion location to defend. locations cached as SORTED list self.cached_expansions"""
        for el in self.cached_expansions:
            def is_near_to_expansion(t):
                return t.position.distance_to(el) < self.EXPANSION_GAP_THRESHOLD

            if any(map(is_near_to_expansion, self.townhalls)):
                # already taken
                continue

            if not await self.can_place(COMMANDCENTER, el) and self.structures.closer_than(8, el):
                continue

            if not self.mineral_field.closer_than(10, el):
                continue

            return el

        return None

    async def gather_gas_and_minerals(self):
        if not self.mineral_field:
            return
        rich_mineralfield = [PURIFIERRICHMINERALFIELD, PURIFIERRICHMINERALFIELD750]
        """
        Stop long distance mining
        Send random worker to gather gas.
        Send idle scvs to gather minerals
        Send idle workers to mine closest base if no jobs available
        Relocate miners to base where is jobs available
        """
        townhalls = (self.townhalls(UnitTypeId.COMMANDCENTER).ready | self.townhalls(UnitTypeId.ORBITALCOMMAND) |
                     self.townhalls(UnitTypeId.PLANETARYFORTRESS))
        scvs = self.workers()
        idle_workers = scvs.idle
        for refinery in self.gas_buildings:
            if self.enemy_units.closer_than(10, refinery):
                continue
            if (self.vespene > self.minerals + 400 and not idle_workers and refinery.assigned_harvesters > 1) \
                    or refinery.assigned_harvesters > 3:
                for scv in scvs.filter(lambda x: x.is_carrying_vespene).closer_than(5, refinery):
                    target = scv.position.towards(self.game_info.map_center, 1)
                    self.do(scv.move(target))
                    return
            # stop long distance mining
            if refinery.assigned_harvesters != 0 and not townhalls.closer_than(10, refinery):
                for scv in scvs.filter(lambda x: x.is_carrying_vespene).closer_than(5, refinery):
                    target = scv.position.towards(self.game_info.map_center, 1)
                    self.do(scv.move(target))
                    return
            elif (self.vespene < self.minerals
                  and townhalls.closer_than(10, refinery)
                  and refinery.assigned_harvesters < refinery.ideal_harvesters and not self.home_in_danger):
                scvs = scvs.filter(lambda x: x.is_returning and x.is_carrying_minerals
                                             and not x.is_in_repair_group
                                             and not x.is_puuhapete)
                for scv in self.scvs.sorted(lambda x: x.distance_to(refinery)):
                    if len(scv.orders) > 0:
                        # print(scv.orders, scv.order_target)
                        if scv.order_target in self.mineral_field.tags:
                            self.do(scv.gather(refinery))
                            return
                if scvs:
                    scv = random.choice(scvs)
                    self.do(scv.gather(refinery))
                    return

        # give job for idle scv
        for idle_worker in idle_workers:
            # gather minerals where jobs available
            townhalls_sorted = townhalls.sorted(lambda x: x.distance_to(idle_worker), reverse=False)
            for townhall in townhalls_sorted:
                units_to_ignore = [UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.OVERLORD]
                if (townhall.assigned_harvesters < townhall.ideal_harvesters
                        and not self.enemy_units_and_structures.exclude_type(
                            units_to_ignore).closer_than(10, townhall)):
                    mf = self.mineral_field.closest_to(townhall)
                    if mf.type_id in rich_mineralfield:
                        if idle_worker.distance_to(townhall) > 10:
                            self.do(idle_worker.move(townhall.position))
                        else:
                            self.do(idle_worker.gather(mf))
                    else:
                        self.do(idle_worker.gather(mf))
                    return

            # gather minerals from closest base
            for x in range(0, len(townhalls_sorted)):
                closest_mineral_field = self.mineral_field.closest_to(townhalls_sorted[x])
                if townhalls_sorted[x].distance_to(
                        closest_mineral_field) < 10 and not self.enemy_units_and_structures.closer_than(10, townhall):
                    self.do(idle_worker.gather(closest_mineral_field))
                    return

        for townhall_out_of_jobs in townhalls:
            if townhall_out_of_jobs.assigned_harvesters > (townhall_out_of_jobs.ideal_harvesters):
                for townhall_jobs_available in townhalls:
                    if townhall_jobs_available.assigned_harvesters < townhall_jobs_available.ideal_harvesters:
                        free_scvs = scvs.filter(
                            lambda x: not x.is_carrying_minerals and not x.is_carrying_vespene)\
                            .closer_than(10, townhall_out_of_jobs)
                        if free_scvs:
                            scv = random.choice(free_scvs)
                            self.do(scv.move(scv.position))
                            return

    def remember_repair_group(self):
        # manages units remembered_repair_group_by_tag
        self.repair_group = sc2.units.Units([], self)
        self.puuhapete = None
        for fixer in self.workers():
            if fixer.tag in self.remembered_repair_group_by_tag:
                fixer.is_in_repair_group = True
                self.repair_group.append(fixer)
            else:
                fixer.is_in_repair_group = False
            if fixer.tag in self.remembered_puuhapete_by_tag:
                fixer.is_puuhapete = True
                self.puuhapete = fixer
            else:
                fixer.is_puuhapete = False

    def add_unit_to_repair_group(self, fixer):
        # adds units remembered_repair_group_by_tag
        self.remembered_repair_group_by_tag[fixer.tag] = fixer

    def add_unit_to_squad_group(self, unit):
        # adds units remembered_squad_group_by_tag
        self.remembered_squad_units_by_tag[unit.tag] = unit

    def add_unit_to_flank_1(self, unit):
        # adds units remembered_squad_group_by_tag
        self.remember_flank_1_by_tag[unit.tag] = unit

    def add_unit_to_flank_2(self, unit):
        # adds units remembered_squad_group_by_tag
        self.remember_flank_2_by_tag[unit.tag] = unit

    def clear_units_in_flank_1(self):
        self.remember_flank_1_by_tag = {}

    def clear_units_in_flank_2(self):
        self.remember_flank_2_by_tag = {}

    def remove_from_flanking_groups(self, unit):
        if unit.tag in self.remember_flank_1_by_tag:
            self.remember_flank_1_by_tag.pop(unit.tag)
        elif unit.tag in self.remember_flank_2_by_tag:
            self.remember_flank_2_by_tag.pop(unit.tag)
        else:
            print("TAG ERROR: trying to remove unit.tag from self.remembered_kamikaze_troops_by_tag")


    def add_unit_to_kodinturvajoukot(self, unit):
        # adds units remembered_kodinturvajoukot_by_tag
        self.remembered_kodinturvajoukot_by_tag[unit.tag] = unit

    def add_unit_to_kamikaze_troops(self, unit):
        # adds units remembered_kamikaze_troops_by_tag
        self.remembered_kamikaze_troops_by_tag[unit.tag] = unit

    def clear_units_in_kamikaze_troops(self):
        self.remembered_kamikaze_troops_by_tag = {}

    def remove_from_kamikaze_troops(self, unit):
        if unit.tag in self.remembered_kamikaze_troops_by_tag:
            self.remembered_kamikaze_troops_by_tag.pop(unit.tag)
        else:
            print("TAG ERROR: trying to remove unit.tag from self.remembered_kamikaze_troops_by_tag")

    def assing_puuhapete(self, fixer):
        # adds units remembered_repair_group_by_tag
        self.remembered_puuhapete_by_tag[fixer.tag] = fixer
