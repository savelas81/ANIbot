from sc2.constants import *


class MarineController:
    def __init__(self):
        pass

    async def marinemicro(self):
        # if self.supply_used > 150 and self.iteraatio % 2 == 0:
        #     return
        can_stim = self.medivacs.filter(lambda x: x.energy > 30)
        units_to_ignore_marine = [ADEPTPHASESHIFT, EGG, LARVA, OVERLORD]
        units_to_fear = self.enemy_units_and_structures.of_type([ZERGLING, BANELING, ZEALOT, ARCHON, DARKTEMPLAR])
        bunker = None
        visible_enemy_structures = self.enemy_structures.filter(lambda x: x.is_visible)
        charge = False
        valid_enemies = (self.enemy_units_and_structures.filter(
            lambda
                x: not x.is_structure and x.type_id not in units_to_ignore_marine) | visible_enemy_structures.filter(
            lambda x: x.can_attack_ground or x.can_attack_air))
        # if self.siegetanks_sieged and not self.siege_behind_wall:
        #     marine_targets = valid_enemies.filter(lambda x: x.distance_to(self.siegetanks_sieged.closest_to(x)) < 14)

        if self.send_flanking_units > 0 and not self.delay_expansion and not self.delay_third \
                and not self.marauders.filter(lambda x: x.is_in_kamikaze_troops) and not self.flank_group_1 \
                and not self.flank_group_2:
            if self.basic_marines.amount > 10:
                if not self.flank_group_1 and self.create_flanking_group_1:
                    self.create_flanking_group_1 = False
                    self.send_flanking_units -= 1
                    for unit in self.basic_marines.take(8):
                        self.add_unit_to_flank_1(unit)
                elif not self.flank_group_2 and not self.create_flanking_group_1:
                    self.create_flanking_group_1 = True
                    self.send_flanking_units -= 1
                    for unit in self.basic_marines.take(8):
                        self.add_unit_to_flank_2(unit)

        if (self.basic_marines.amount >= 6 and self.squad_group.amount < 3
                and (self.ccANDoc.ready.amount >= 3
                     or self.townhalls_flying)):  # some zerg bots spread creep in expansion. We need to make this early
            counter = self.squad_group.amount
            for unit in self.basic_marines.sorted(lambda x: x.distance_to(self.start_location)):
                self.add_unit_to_squad_group(unit)
                counter += 1
                if counter >= 6:
                    break
            print(counter, "marines added to hit squad.")

        if self.enemy_units_and_structures and not self.careful_marines:
            if self.we_are_winning() or self.supply_used > 180 or self.agressive_marines:
                charge = True
        # if valid_enemies:
        #     threat_to_home = valid_enemies.closest_to(self.start_location)
        if self.bunkers.ready and not self.kamikaze_target:
            for bunker_ in self.bunkers.ready.sorted_by_distance_to(self.start_location):
                if await self.has_ability(LOAD_BUNKER, bunker_):
                    bunker = bunker_
                    break
        if self.scan_timer > 50:
            marine_scan = True
        else:
            marine_scan = False

        marines_reloading = self.basic_marines.filter(lambda x: x.weapon_cooldown != 0).amount
        if marine_scan:
            scanners = self.orbitalcommand.filter(lambda x: x.energy > 50)
            if scanners:
                scanner = scanners.first
                marines_under_fire = self.basic_marines.filter(
                    lambda x: x.did_take_first_hit and not self.enemy_units.closer_than(20, x))
                if marines_under_fire:
                    self.do(scanner(AbilityId.SCANNERSWEEP_SCAN, marines_under_fire.first.position))
                    print("Marine: Scan for cloaked units!")
                    self.scan_timer = 0
        ready_to_stutter = False
        if marines_reloading > 4:
            if self.step_timer <= 0:
                self.step_timer = 0
                ready_to_stutter = True
        self.step_timer -= 1

        activate_formation = False
        if self.show_off and self.basic_marines:
            for marauder in self.marauders:
                if marauder.is_in_kamikaze_troops:
                    activate_formation = True
                    break
            self.basic_marines = self.basic_marines.sorted(lambda x: (x.tag), reverse=False)
        marine_nro = -1
        siegetanks_need_protection = self.siegetanks_sieged.filter(
            lambda x: not self.enemy_units.visible.closer_than(14, x))
        for marine in self.basic_marines:
            if marine.is_in_kamikaze_troops:
                marine_targets = valid_enemies.further_than(self.defence_radius, self.start_location)
                if marine.distance_to(self.enemy_start_location) < 10:
                    self.remove_from_kamikaze_troops(marine)
            else:
                marine_targets = valid_enemies
            if self.show_off and marine_nro == -1:
                formation = await self.formation(marine.position, marine.facing, 1)
            marine_nro += 1
            if activate_formation:
                if marine_nro == 0:
                    if self.iteraatio % 3 == 0:
                        self.do(marine.attack(marine.position))
                    else:
                        self.do(marine.move(self.enemy_start_location))
                    continue
                place_in_formation = formation[marine_nro]
                if marine.distance_to(place_in_formation) > 0.2:
                    if self.iteraatio % 3 == 0:
                        self.do(marine.attack(place_in_formation))
                    else:
                        self.do(marine.move(place_in_formation))
                continue

            if bunker:
                self.do(marine.move(bunker.position))
                continue

            "don't abandon siegetank during encounter"
            if siegetanks_need_protection.closer_than(15, marine) \
                    and not self.siege_behind_wall and not self.agressive_marines:
                closest_siege = siegetanks_need_protection.closest_to(marine)
                if marine.distance_to(closest_siege) > 5:
                    self.do(marine.move(closest_siege.position))
                continue

            if marine.weapon_cooldown != 0 \
                    and ((marine_targets.closer_than(17, marine).amount > 2 and can_stim) or self.agressive_marines):
                if ((marine.health_percentage >= 1 or self.agressive_marines)
                        and self.ccANDoc.amount >= 2
                        and await self.can_cast(marine, AbilityId.EFFECT_STIM_MARINE)
                        and not marine.has_buff(BuffId.STIMPACK)):
                    self.do(marine(AbilityId.EFFECT_STIM_MARINE))
                    continue  # continue for loop, dont execute any of the following
            if (self.marine_drop
                    and self.dropship_sent
                    and valid_enemies.closer_than(marine.ground_range + marine.radius, marine)):
                targets = valid_enemies.closer_than(marine.ground_range + marine.radius, marine
                                                    ).sorted(lambda x: (x.health + x.shield), reverse=False)
                target = targets[0]
                self.do(marine.attack(target))
                continue
            if await self.avoid_own_nuke(marine):
                continue
            if not self.agressive_marines and await self.avoid_enemy_siegetanks(marine):
                continue

            # if (self.enemy_units_on_ground.closer_than(marine.ground_range - 1, marine)
            #         and marine.weapon_cooldown != 0
            #         and not self.agressive_marines):
            #     self.do(marine.move(self.homeBase.position.towards(self.enemy_units.closest_to(marine), -10)))
            #     continue

            # if marine_targets and self.careful_marines and marines_reloading >= 8 and marine.weapon_cooldown != 0:
            #     self.do(marine.move(marine.position.towards(marine_targets.closest_to(marine), -10)))
            #     continue
            if (marine.weapon_cooldown != 0
                    and not self.agressive_marines
                    and units_to_fear.closer_than(marine.ground_range + marine.radius, marine)):
                self.do(marine.move(marine.position.towards(units_to_fear.closest_to(marine), -10)))
                continue

            # retreat if low health
            if (marine.health_percentage < 1 / 2
                    and self.medivacs
                    and self.supply_used < 180
                    and not self.agressive_marines):
                if marine.distance_to(self.homeBase) > 15:
                    self.do(marine.attack(self.homeBase.position))
                    continue
                else:
                    continue

            if marine_targets:
                if not ready_to_stutter or not charge:
                    targets = marine_targets.in_attack_range_of(marine, 1).visible
                    if targets:
                        target = targets.sorted(lambda x: (x.health + x.shield), reverse=False)[0]
                        self.do(marine.attack(target))
                        continue
                    else:
                        self.do(marine.attack(marine_targets.closest_to(marine).position))
                        continue
                else:
                    self.do(marine.move(marine_targets.closest_to(marine).position.towards(marine, -2)))
                    continue
            if visible_enemy_structures:
                target_structure = visible_enemy_structures.closest_to(marine)
                if not ready_to_stutter:
                    self.do(marine.attack(target_structure))
                    continue  # continue for loop, don't execute any of the following
                else:
                    self.do(marine.move(target_structure.position.towards(marine, -5)))
                    continue  # continue for loop, don't execute any of the following

            if self.proxy_defence:
                proxy_structures = self.enemy_structures.closer_than(self.defence_radius,
                                                                     self.start_location).of_type(UnitTypeId.PYLON)
                if proxy_structures:
                    self.do(marine.attack(proxy_structures.closest_to(marine)))
                    continue
            marinehome = None
            if self.siegetanks_sieged:  # and not self.thors:
                front_siege = self.siegetanks_sieged.closest_to(marine)
                defence_position = front_siege.position
                if marine.distance_to(defence_position) > 20:
                    self.do(marine.attack(defence_position))
                    continue
                if marine.distance_to(defence_position) > 4:
                    self.do(marine.move(defence_position))
                    continue
            elif self.general:
                if marine.distance_to(self.general) > 10:
                    self.do(marine.move(self.general.position))
                elif self.kamikaze_target:
                    self.do(marine.attack(self.kamikaze_target))
                continue
            elif self.siegetanks:
                target = self.siegetanks.closest_to(marine)
                if marine.distance_to(target) > 10:
                    self.do(marine.attack(target.position))
                continue
            elif self.NukesLeft > 0 and self.midle_depo_position:
                marinehome = self.midle_depo_position.towards(self.main_base_ramp.bottom_center, -5)
            elif self.natural and self.ccANDoc.closer_than(3, self.natural) and not self.build_cc_home:
                marinehome = self.natural.towards(self.game_info.map_center, 6)
            else:
                marinehome = self.homeBase
            if marinehome and marine.distance_to(marinehome) > 8:
                self.do(marine.move(marinehome))
            continue
