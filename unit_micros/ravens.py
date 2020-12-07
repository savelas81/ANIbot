from sc2.constants import *


class RavenController:

    def __init__(self, bot=None):
        self.bot = bot
        self.interference_matrix_timer = 0

    async def ravenmicro(self):
        # ravens
        unit_types_to_dispell = [UnitTypeId.SIEGETANKSIEGED, UnitTypeId.BATTLECRUISER,
                                 UnitTypeId.VIKINGFIGHTER, UnitTypeId.RAVEN, UnitTypeId.IMMORTAL]
        units_to_dispell = self.bot.enemy_units.of_type(unit_types_to_dispell) \
            .filter(lambda x: not x.has_buff(BuffId.RAVENSCRAMBLERMISSILE))
        air_threats = self.bot.enemy_units_and_structures.filter(lambda x: x.can_attack_air).visible
        can_cast_matrix = False
        self.interference_matrix_timer -= 1
        for raven in self.bot.units(UnitTypeId.RAVEN):
            if not raven.is_idle and raven.orders[0].ability.id in [AbilityId.EFFECT_INTERFERENCEMATRIX]:
                self.interference_matrix_timer = 10
        if self.interference_matrix_timer < 0:
            can_cast_matrix = True
        for raven in self.bot.units(UnitTypeId.RAVEN):
            enemy_units_too_close = air_threats.filter(lambda x: x.target_in_range(target=raven, bonus_distance=3))
            if await self.bot.avoid_own_nuke(raven):
                continue
            if can_cast_matrix and units_to_dispell and raven.energy > 50:
                target = units_to_dispell.closest_to(raven)
                self.bot.do(raven(AbilityId.EFFECT_INTERFERENCEMATRIX, target))
                continue
            anti_armor_targets = self.bot.enemy_units.filter(
                lambda x: x.can_attack_air and not self.bot.units.closer_than(5, x))
            if anti_armor_targets and raven.energy >= 100:
                target = anti_armor_targets.closest_to(raven)
                if raven.energy >= 75:
                    self.bot.do(raven(AbilityId.EFFECT_ANTIARMORMISSILE, target))
                    continue
                else:
                    self.bot.do(raven.move(self.bot.homeBase.position))
                    continue
            if enemy_units_too_close:
                self.bot.do(raven.move(raven.position.towards(air_threats.closest_to(raven), -3)))
                continue
            cloaked_enemy_units = self.bot.enemy_units.filter(lambda x: x.is_cloaked)
            if cloaked_enemy_units:
                self.bot.do(raven.move(cloaked_enemy_units.closest_to(raven).position))
                # print("raven target position:", cloaked_enemy_units.closest_to(raven).position)
                continue
            if self.bot.banshees:
                self.bot.do(raven.move(self.bot.banshees.center))
                continue
            if self.bot.general:
                target_position = self.bot.general.position
                if raven.distance_to(target_position) > 2:
                    self.bot.do(raven.attack(target_position))
                    continue
