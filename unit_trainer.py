from sc2.constants import *
from sc2.units import Units
from sc2.ids.ability_id import AbilityId
import sc2


class UnitTrainer:

    def __init__(self, bot=None):
        self.bot = bot

    async def trainer(self, maxreaper):

        reaper_total = 0
        marine_total = 0
        marauder_total = 0
        ghost_total = 0
        hellion_total = self.bot.units(UnitTypeId.HELLION).amount \
                        + self.bot.units(UnitTypeId.HELLIONTANK).amount \
                        + self.bot.already_pending(UnitTypeId.HELLION)
        raxes_with_reactors = sc2.units.Units([], self.bot)  # creates empty
        raxes_with_techlabs = sc2.units.Units([], self.bot)
        raxes_without_addon = sc2.units.Units([], self.bot)
        factories_with_reactors = sc2.units.Units([], self.bot)
        factories_with_techlabs = sc2.units.Units([], self.bot)
        factories_without_addon = sc2.units.Units([], self.bot)
        starports_with_reactors = sc2.units.Units([], self.bot)
        starports_with_techlabs = sc2.units.Units([], self.bot)
        starports_without_addon = sc2.units.Units([], self.bot)

        for facility in self.bot.barracks.ready:
            if facility.add_on_tag == 0 and facility.is_idle:
                raxes_without_addon.append(facility)
                continue
            for add_on in self.bot.structures(UnitTypeId.BARRACKSREACTOR).ready:
                if facility.add_on_tag == add_on.tag and len(facility.orders) < 2:
                    raxes_with_reactors.append(facility)
                    continue
            for add_on in self.bot.structures(UnitTypeId.BARRACKSTECHLAB).ready:
                if facility.add_on_tag == add_on.tag and facility.is_idle:
                    raxes_with_techlabs.append(facility)
                    continue

        for facility in self.bot.factories.ready:
            if facility.add_on_tag == 0 and facility.is_idle:
                factories_without_addon.append(facility)
                continue
            for add_on in self.bot.structures(UnitTypeId.FACTORYREACTOR).ready:
                if facility.add_on_tag == add_on.tag and len(facility.orders) < 2:
                    factories_with_reactors.append(facility)
                    continue
            for add_on in self.bot.structures(UnitTypeId.FACTORYTECHLAB).ready:
                if facility.add_on_tag == add_on.tag and facility.is_idle:
                    factories_with_techlabs.append(facility)
                    continue

        for facility in self.bot.starports.ready:
            if facility.add_on_tag == 0 and facility.is_idle:
                starports_without_addon.append(facility)
                continue
            for add_on in self.bot.structures(UnitTypeId.STARPORTREACTOR).ready:
                if facility.add_on_tag == add_on.tag and len(facility.orders) < 2:
                    starports_with_reactors.append(facility)
                    continue
            for add_on in self.bot.structures(UnitTypeId.STARPORTTECHLAB).ready:
                if facility.add_on_tag == add_on.tag and facility.is_idle:
                    starports_with_techlabs.append(facility)
                    continue

        raxes_all = (raxes_with_reactors | raxes_with_techlabs | raxes_without_addon)
        # factories_all = (factories_with_reactors | factories_with_techlabs | factories_without_addon)
        starports_all = (starports_with_reactors | starports_with_techlabs | starports_without_addon)

        # count all reapers and marines alive and in production
        for barracks in self.bot.barracks.ready:
            for order in barracks.orders:
                if order.ability.id in [AbilityId.BARRACKSTRAIN_REAPER]:
                    reaper_total = reaper_total + 1
                elif order.ability.id in [AbilityId.BARRACKSTRAIN_MARINE]:
                    marine_total = marine_total + 1
                elif order.ability.id in [AbilityId.BARRACKSTRAIN_MARAUDER]:
                    marauder_total = marauder_total + 1
                elif order.ability.id in [AbilityId.BARRACKSTRAIN_GHOST]:
                    ghost_total += 1
        reaper_total = reaper_total + self.bot.reapers.amount
        marine_total = marine_total + self.bot.marines.amount
        marauder_total = marauder_total + self.bot.marauders.amount
        ghost_total = ghost_total + self.bot.ghosts.amount

        # build units in barracs
        pending_addons = self.bot.already_pending(UnitTypeId.BARRACKSREACTOR) \
                         + self.bot.already_pending(UnitTypeId.BARRACKSTECHLAB)
        if self.bot.liberator_priority and self.bot.liberator_left > 0 \
                and not self.bot.already_pending(UnitTypeId.LIBERATOR):
            minerals_for_marine = 200
        elif marine_total < self.bot.min_marine:
            minerals_for_marine = 75
        elif self.bot.marines_last_resort:
            minerals_for_marine = 470
        else:
            minerals_for_marine = 300
        if not self.bot.build_barracks_addons:
            can_build_add_on = False
        elif self.bot.delay_expansion and self.bot.structures(UnitTypeId.BARRACKSREACTOR).amount > 1:
            can_build_add_on = False
        elif self.bot.super_fast_barracks and pending_addons < 3 and self.bot.vespene > 60 \
                and (self.bot.marines.amount + self.bot.already_pending(UnitTypeId.MARINE) > 1 or self.bot.max_marine < 2):
            can_build_add_on = True
        elif (self.bot.already_pending(UnitTypeId.BARRACKSREACTOR)
              or self.bot.already_pending(UnitTypeId.BARRACKSTECHLAB)):
            can_build_add_on = False
        else:
            can_build_add_on = True

        if self.bot.can_afford(UnitTypeId.REAPER) and reaper_total < maxreaper \
                and self.bot.refineries and not self.bot.marine_drop and raxes_all:
            rax = raxes_all.first
            self.bot.do(rax.train(UnitTypeId.REAPER))
            print("Training reaper")
            return

        if (self.bot.bunker_in_natural or self.bot.bunkers) and \
                (self.bot.marines.amount + self.bot.already_pending(UnitTypeId.MARINE)) < 4 and \
                raxes_all:
            for br in raxes_all:
                self.bot.do(br.train(UnitTypeId.MARINE))
                return
        full_health_raxes = raxes_without_addon.filter(lambda x: x.health_percentage >= 1)
        if can_build_add_on and self.bot.can_afford(UnitTypeId.BARRACKSREACTOR) and full_health_raxes:
            for br in full_health_raxes:
                location = br.add_on_position
                if await self.bot.can_place(UnitTypeId.SUPPLYDEPOT, location):
                    if self.bot.barracks_reactor_first \
                            and self.bot.structures(UnitTypeId.BARRACKSREACTOR).amount == 0:
                        self.bot.do(br.build(UnitTypeId.BARRACKSREACTOR))
                    elif not self.bot.barracks_reactor_first \
                            and self.bot.structures(UnitTypeId.BARRACKSTECHLAB).amount == 0:
                        self.bot.do(br.build(UnitTypeId.BARRACKSTECHLAB))
                    elif (self.bot.research_stimpack
                          or self.bot.research_combatshield
                          or self.bot.research_concussiveshels) \
                            and self.bot.structures(UnitTypeId.BARRACKSTECHLAB).amount == 0:
                        self.bot.do(br.build(UnitTypeId.BARRACKSTECHLAB))
                    elif self.bot.build_barracks_reactors:
                        self.bot.do(br.build(UnitTypeId.BARRACKSREACTOR))
                    else:
                        self.bot.do(br.build(UnitTypeId.BARRACKSTECHLAB))
                    return
                else:
                    self.bot.do(br(AbilityId.LIFT))
                    return

        if (ghost_total < self.bot.MaxGhost) and self.bot.ghost_academies.ready \
                and not self.bot.already_pending(UnitTypeId.GHOST) and raxes_with_techlabs:
            if self.bot.can_afford(UnitTypeId.GHOST):
                br = raxes_with_techlabs.first
                self.bot.do(br.train(UnitTypeId.GHOST))
                print("Training ghost")
                return
        if self.bot.marauder_push_limit != 0 and self.bot.barracks.amount >= self.bot.max_barracks:
            if raxes_with_techlabs and self.bot.can_afford(UnitTypeId.MARAUDER):
                br = raxes_with_techlabs.first
                self.bot.do(br.train(UnitTypeId.MARAUDER))
                print("Training marauder")
            return
        if marauder_total < self.bot.maxmarauder and self.bot.can_afford(UnitTypeId.MARAUDER) and raxes_with_techlabs:
            br = raxes_with_techlabs.first
            self.bot.do(br.train(UnitTypeId.MARAUDER))
            print("Training marauder")
            return
        if self.bot.minerals > 200 and self.bot.supply_used <= 190 \
                and self.bot.can_afford(UnitTypeId.MARAUDER) and raxes_with_techlabs \
                and marauder_total < 20:
            br = raxes_with_techlabs.first
            self.bot.do(br.train(UnitTypeId.MARAUDER))
            print("Training marauder")
            return
        supply_limit_for_marines = 185
        if self.bot.limit_vespene != 0 and self.bot.marauders:
            supply_limit_for_marines = 200
        if marine_total < self.bot.max_marine and self.bot.minerals > minerals_for_marine \
                and self.bot.supply_used < supply_limit_for_marines and raxes_all:
            br = None
            if raxes_with_reactors:
                br = raxes_with_reactors.first
            elif raxes_with_techlabs and self.bot.marauders.amount >= self.bot.maxmarauder:
                br = raxes_with_techlabs.first
            elif raxes_without_addon:
                br = raxes_without_addon.first
            if br:
                self.bot.do(br.train(UnitTypeId.MARINE))
                return

        thor_total = self.bot.thors.amount + self.bot.already_pending(UnitTypeId.THOR)
        siege_tank_total = self.bot.already_pending(
            UnitTypeId.SIEGETANK) + self.bot.siegetanks.amount + self.bot.siegetanks_sieged.amount
        banshees_in_production = self.bot.already_pending(UnitTypeId.BANSHEE)
        medi_total = self.bot.medivacs.amount + self.bot.already_pending(UnitTypeId.MEDIVAC)
        viking_total = self.bot.vikings.amount + \
                       self.bot.vikingassault.amount + self.bot.already_pending(UnitTypeId.VIKINGFIGHTER)
        raven_total = self.bot.units(UnitTypeId.RAVEN).amount + self.bot.already_pending(UnitTypeId.RAVEN)
        liberator_total = self.bot.liberators.amount \
                          + self.bot.liberatorsdefending.amount \
                          + self.bot.already_pending(UnitTypeId.LIBERATOR)
        if self.bot.priority_factoty_reactor or self.bot.priority_tank:
            return
        if factories_without_addon and (not self.bot.structures(UnitTypeId.FACTORYREACTOR)
                                        or self.bot.mines_left > 20):
            factory = factories_without_addon.first
            if self.bot.enemy_units.of_type([UnitTypeId.ZERGLING, UnitTypeId.ZEALOT])\
                    and not self.bot.already_pending(UnitTypeId.HELLION):
                if self.bot.can_afford(UnitTypeId.HELLION):
                    self.bot.do(factory.train(UnitTypeId.HELLION))
                    print("Training hellion to counter immediate threat!")
                return
            if self.bot.structures(UnitTypeId.FACTORYREACTOR).amount >= 2:
                pass
            elif (self.bot.hellion_left + self.bot.mines_left) > 8:
                location = factory.add_on_position
                if await self.bot.can_place(UnitTypeId.SUPPLYDEPOT, location):
                    if self.bot.can_afford(UnitTypeId.FACTORYREACTOR):
                        self.bot.do(factory.build(UnitTypeId.FACTORYREACTOR))
                elif self.bot.iteraatio % 3 == 0:
                    self.bot.do(factory(AbilityId.LIFT))
                return
            elif (not self.bot.already_pending(UnitTypeId.WIDOWMINE)
                  and not self.bot.already_pending(UnitTypeId.HELLION)):
                if self.bot.mines_left > 0:
                    if self.bot.can_afford(UnitTypeId.WIDOWMINE):
                        self.bot.do(factory.train(UnitTypeId.WIDOWMINE))
                        print("Training mine")
                    return
                elif self.bot.hellion_left > 0 \
                        and (self.bot.supply_used < 190 or self.bot.thors or self.bot.already_pending(UnitTypeId.THOR)):
                    if self.bot.can_afford(UnitTypeId.HELLION):
                        self.bot.do(factory.train(UnitTypeId.HELLION))
                        print("Training hellion")
                    return

        train_mines = False
        if self.bot.mines.amount + self.bot.mines_burrowed.amount + self.bot.already_pending(UnitTypeId.WIDOWMINE) >= 50:
            train_mines = False
        elif self.bot.supply_used < 190 or self.bot.thors or self.bot.already_pending(UnitTypeId.THOR):
           train_mines = True


        if factories_with_reactors:
            factory = factories_with_reactors.first
            if self.bot.mines_left > 0:
                if self.bot.hellion_left > 0 and self.bot.minerals > self.bot.vespene \
                        and self.bot.already_pending(UnitTypeId.WIDOWMINE) \
                        and not self.bot.already_pending(UnitTypeId.HELLION) and hellion_total < 16:
                    if self.bot.can_afford(UnitTypeId.HELLION):
                        self.bot.do(factory.train(UnitTypeId.HELLION))
                        print("Training hellion")
                    return
                elif self.bot.can_afford(UnitTypeId.WIDOWMINE) and train_mines:
                    self.bot.do(factory.train(UnitTypeId.WIDOWMINE))
                    print("Training mine")
                    return
            elif self.bot.hellion_left > 0:
                if self.bot.minerals > self.bot.vespene and hellion_total < 16 \
                        and (self.bot.supply_used < 190 or self.bot.thors) \
                        and self.bot.can_feed(UnitTypeId.HELLION):
                    self.bot.do(factory.train(UnitTypeId.HELLION))
                    print("Training hellion")
                    return
            elif factory.is_idle:
                self.bot.do(factory(AbilityId.LIFT))
                return
        # if self.cyclone_left <= 0 and self.max_siege <= 0 and self.max_thor <= 0 and not self.siege_behind_wall:
        #     continue
        # if self.MaxGhost > self.ghosts.amount and not self.already_pending(UnitTypeId.GHOST):
        #     continue
        if factories_without_addon and not self.bot.marine_drop:
            factory = factories_without_addon.first
            if self.bot.can_afford(UnitTypeId.FACTORYTECHLAB) and factory.health_percentage >= 1:
                location = factory.add_on_position
                if await self.bot.can_place(UnitTypeId.SUPPLYDEPOT, location):
                    self.bot.do(factory.build(UnitTypeId.FACTORYTECHLAB))
                elif self.bot.iteraatio % 3 == 0:
                    self.bot.do(factory(AbilityId.LIFT))
                return
        if factories_with_techlabs:
            if self.bot.liberator_priority and not self.bot.already_pending(UnitTypeId.LIBERATOR) \
                    and self.bot.starports.ready.idle and self.bot.liberator_left > 0:
                pass
            elif self.bot.max_viking == 16 > viking_total and starports_with_reactors:
                pass
            else:
                factory = factories_with_techlabs.first
                if self.bot.faster_tanks \
                        and (not self.bot.already_pending(UnitTypeId.SIEGETANK)
                             or self.bot.already_pending(UnitTypeId.CYCLONE)) \
                        and (siege_tank_total < self.bot.max_siege) and self.bot.supply_used < 190:
                    if self.bot.can_afford(UnitTypeId.SIEGETANK):
                        self.bot.do(factory.train(UnitTypeId.SIEGETANK))
                        print("Training siegetank")
                    return
                if (self.bot.cyclone_left - self.bot.already_pending(UnitTypeId.CYCLONE) > 0
                        and (siege_tank_total >= 2 or self.bot.max_siege < 2)
                        and (self.bot.supply_used <= 190 or self.bot.thors.amount >= self.bot.max_thor)):
                    if self.bot.can_afford(UnitTypeId.CYCLONE):
                        self.bot.do(factory.train(UnitTypeId.CYCLONE))
                        print("Training cyclone")
                    return
                if self.bot.can_afford(UnitTypeId.SIEGETANK) \
                        and (siege_tank_total < self.bot.max_siege or self.bot.siege_behind_wall) \
                        and (self.bot.supply_used < 190 or (thor_total >= self.bot.max_thor and self.bot.max_BC == 0)) \
                        and (viking_total >= self.bot.max_viking or self.bot.max_viking < 16):
                    self.bot.do(factory.train(UnitTypeId.SIEGETANK))
                    print("Training siegetank")
                    return
                if self.bot.can_afford(UnitTypeId.THOR) and thor_total < self.bot.max_thor:
                    if self.bot.armories.ready:
                        self.bot.do(factory(AbilityId.RALLY_BUILDING, self.bot.homeBase.position))
                        self.bot.do(factory.train(UnitTypeId.THOR))
                        print("Training THOR")
                        return
                    if not self.bot.build_armory:
                        self.bot.build_armory = True

        if self.bot.marine_drop:
            build_medivacs = False
        elif self.bot.MaxGhost > self.bot.ghosts.amount and not self.bot.already_pending(UnitTypeId.GHOST):
            build_medivacs = False
        elif self.bot.liberator_priority and self.bot.liberator_left:
            build_medivacs = False
        elif self.bot.already_pending(UnitTypeId.MEDIVAC):
            if self.bot.vikings.amount >= self.bot.max_viking and self.bot.liberator_left <= 0 \
                    and starports_with_reactors:
                build_medivacs = True
            else:
                build_medivacs = False
        else:
            build_medivacs = True

        if viking_total == 0 and self.bot.max_viking > 0 and starports_all:
            starport = starports_all.first
            if self.bot.can_afford(UnitTypeId.VIKINGFIGHTER):
                self.bot.do(starport.train(UnitTypeId.VIKINGFIGHTER))
                print("Training first viking")
            return
        if self.bot.max_viking == 0 and liberator_total == 0 and self.bot.liberator_left > 0 and starports_all:
            starport = starports_all.first
            if self.bot.can_afford(UnitTypeId.LIBERATOR):
                self.bot.do(starport.train(UnitTypeId.LIBERATOR))
                print("Training first liberator")
            return
        if self.bot.dual_liberator and liberator_total < 2 and starports_all:
            starport = starports_all.first
            if self.bot.can_afford(UnitTypeId.LIBERATOR):
                self.bot.do(starport.train(UnitTypeId.LIBERATOR))
                print("Training first liberator")
            return
        if medi_total == 0 and self.bot.maxmedivacs > 0 and starports_all:
            starport = starports_all.first
            if self.bot.can_afford(UnitTypeId.MEDIVAC):
                self.bot.do(starport.train(UnitTypeId.MEDIVAC))
                print("Training first medivac")
            return
        if starports_without_addon:
            starport = starports_without_addon.first
            starport_reactors_amount = self.bot.structures(UnitTypeId.STARPORTREACTOR).amount + \
                                       self.bot.already_pending(UnitTypeId.STARPORTREACTOR)
            if starport.health_percentage < 1:
                pass
            if self.bot.can_afford(UnitTypeId.STARPORTTECHLAB) \
                    and starport_reactors_amount < self.bot.build_starportreactor:
                location = starport.add_on_position
                if await self.bot.can_place(UnitTypeId.SUPPLYDEPOT, location):
                    if (self.bot.max_viking == 0 or self.bot.viking_priority) and not self.bot.structures(UnitTypeId.STARPORTTECHLAB):
                        self.bot.do(starport.build(UnitTypeId.STARPORTTECHLAB))
                        return
                    else:
                        self.bot.do(starport.build(UnitTypeId.STARPORTREACTOR))
                        return
                elif self.bot.iteraatio % 3 == 0:
                    self.bot.do(starport(AbilityId.LIFT))
                    return
        # if starports_with_reactors and self.bot.build_starportreactor > 0 and self.bot.max_BC > 0 \
        #         and self.bot.medivacs.amount >= self.bot.maxmedivacs \
        #         and self.bot.vikings.amount >= self.bot.max_viking and self.bot.liberator_left <= 0:
        #     if self.bot.viking_priority and self.bot.banshee_left:
        #         pass
        #     else:
        #         starport = starports_with_reactors.first
        #         self.bot.do(starport(AbilityId.LIFT))
        #         self.bot.build_starportreactor = 0
        #         return

        if medi_total < self.bot.maxmedivacs and build_medivacs:
            starport = None
            if starports_with_reactors:
                starport = starports_with_reactors.first
            elif starports_with_techlabs:
                starport = starports_with_techlabs.first
            elif starports_without_addon:
                starport = starports_without_addon.first
            if starport:
                if self.bot.can_afford(UnitTypeId.MEDIVAC):
                    print("Training medivac")
                    self.bot.do(starport.train(UnitTypeId.MEDIVAC))
                return

        elif starports_without_addon and self.bot.can_afford(UnitTypeId.STARPORTTECHLAB):
            starport = starports_without_addon.first
            if starport.health_percentage >= 1:
                location = starport.add_on_position
                if await self.bot.can_place(UnitTypeId.SUPPLYDEPOT, location):
                    self.bot.do(starport.build(UnitTypeId.STARPORTTECHLAB))
                    return
                elif self.bot.iteraatio % 3 == 0:
                    self.bot.do(starport(AbilityId.LIFT))
                    return
        elif self.bot.raven_left > 0 and raven_total <= 0 and starports_with_techlabs:
            if self.bot.can_afford(UnitTypeId.RAVEN):
                starport = starports_with_techlabs.first
                self.bot.do(starport.train(UnitTypeId.RAVEN))
                print("Training raven")
            return
        elif (viking_total < self.bot.max_viking) and self.bot.can_afford(UnitTypeId.VIKINGFIGHTER) \
                and (self.bot.supply_used < 190 or self.bot.thors or self.bot.battlecruisers):
            starport = None
            if starports_with_reactors:
                starport = starports_with_reactors.first
            elif starports_with_techlabs:
                starport = starports_with_techlabs.first
            elif starports_without_addon:
                starport = starports_without_addon.first
            if starport:
                self.bot.do(starport.train(UnitTypeId.VIKINGFIGHTER))
                print("Training viking to max viking")
                return
        elif (self.bot.banshee_left - banshees_in_production) > 0:
            if viking_total < 8 and self.bot.viking_priority and starports_all\
                    and viking_total < ((self.bot.banshees.amount + banshees_in_production) * 1):
                starport = None
                if self.bot.can_afford(UnitTypeId.VIKINGFIGHTER):
                    if starports_with_reactors:
                        starport = starports_with_reactors.first
                    elif starports_with_techlabs:
                        starport = starports_with_techlabs.first
                    elif starports_without_addon:
                        starport = starports_without_addon.first
                    if starport:
                        self.bot.do(starport.train(UnitTypeId.VIKINGFIGHTER))
                        print("Training priority viking")
                        return

            elif self.bot.can_afford(UnitTypeId.BANSHEE) and starports_with_techlabs:
                starport = starports_with_techlabs.first
                print("Training banshee")
                self.bot.do(starport.train(UnitTypeId.BANSHEE))
                return
        elif self.bot.liberator_left - self.bot.already_pending(UnitTypeId.LIBERATOR) > 0 \
                and self.bot.can_afford(UnitTypeId.LIBERATOR) and starports_all and liberator_total < 20:
            starport = starports_all.first
            self.bot.do(starport.train(UnitTypeId.LIBERATOR))
            print("Training liberator")
            return
        if (thor_total >= 1 or self.bot.max_thor == 0) and self.bot.max_BC > 0 \
                and self.bot.structures(UnitTypeId.FUSIONCORE).ready:
            if self.bot.can_afford(UnitTypeId.BATTLECRUISER) and starports_with_techlabs and self.bot.limit_vespene == 0:
                starport = starports_with_techlabs.first
                self.bot.do(starport.train(UnitTypeId.BATTLECRUISER))
                self.bot.marines_last_resort = True
                self.bot.min_marine = 1
                print("Training battlecruiser")
                return
