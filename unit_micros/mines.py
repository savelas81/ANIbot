import random
from sc2.constants import *
import copy
from sc2.unit import Unit
from sc2.position import Point2


class MineController:

    def __init__(self, bot=None):
        self.bot = bot
        self.mine_grid = None
        self.cached_pyastar_grid = None
        self.new_grid_interval = 0

    async def get_mine_grid(self):
        self.new_grid_interval -= 1
        if self.new_grid_interval <= 0:
            self.new_grid_interval = 15
            self.cached_pyastar_grid = self.bot.map_data.get_pyastar_grid()

        self.mine_grid = copy.copy(self.cached_pyastar_grid)
        mines_sorted = self.bot.mines_burrowed.sorted(lambda x: x.distance_to(self.bot.enemy_start_location))
        max_mines_for_influence = 20
        for mine in mines_sorted:
            if max_mines_for_influence <= 0:
                return
            else:
                max_mines_for_influence -= 1
            self.mine_grid = self.bot.map_data.add_cost(
                position=mine.position, radius=8, grid=self.mine_grid)
        for unit in self.bot.enemy_units.of_type(UnitTypeId.SIEGETANKSIEGED):
            self.mine_grid = self.bot.map_data.add_cost(
                position=unit.position, radius=(unit.ground_range + 2), grid=self.mine_grid, weight=300)
        for unit in self.bot.enemy_structures:
            if unit.is_detector:
                self.mine_grid = self.bot.map_data.add_cost(
                    position=unit.position, radius=(unit.sight_range + 2), grid=self.mine_grid, weight=300)

    async def move_mines(self):
        if not (self.bot.mines or self.bot.mines_burrowed):
            return
        self.mine_grid = None
        if not self.bot.enemy_start_location:
            return
        mines_ready = self.bot.mines.filter(lambda x: x.tag not in self.bot.remembered_fired_mines_by_tag)
        mines_shot = self.bot.mines.filter(lambda x: x.tag in self.bot.remembered_fired_mines_by_tag)
        mines_burrowed = self.bot.mines_burrowed
        mines_burrowed = mines_burrowed.sorted(lambda x: x.distance_to(self.bot.enemy_start_location), reverse=True)
        if self.bot.activate_all_mines:
            limit = 100
        elif self.bot.leapfrog_mines and mines_burrowed.amount > 25:
            limit = 100
        else:
            limit = 1
        cyclones = self.bot.cyclones
        units_to_ignore = [UnitTypeId.ADEPTPHASESHIFT, UnitTypeId.EGG, UnitTypeId.LARVA,
                           UnitTypeId.CHANGELINGMARINESHIELD, UnitTypeId.CHANGELINGMARINE]
        targets = self.bot.enemy_units.exclude_type(units_to_ignore)
        if cyclones.exists and self.bot.cyclone_left <= 0:
            master = cyclones.furthest_to(self.bot.homeBase)
        elif self.bot.marauders:
            master = self.bot.marauders.furthest_to(self.bot.homeBase)
        elif self.bot.siegetanks:
            master = self.bot.siegetanks.furthest_to(self.bot.homeBase)
        # elif self.bot.marines:
        #     master = self.bot.marines.furthest_to(self.bot.homeBase)
        else:
            master = None
        if not self.bot.activate_all_mines and self.bot.supply_used > 190 and self.bot.mines_left <= 0:
            self.bot.activate_all_mines = True
            self.bot.leapfrog_mines = False
            self.bot.aggressive_mines = True
            if self.bot.chat:
                await self.bot._client.chat_send("I'm done with playing around. Lets end this!", team_only=False)

        for mine in mines_shot.idle:
            if mine.distance_to(self.bot.homeBase) > 10:
                self.bot.do(mine.move(self.bot.homeBase.position.random_on_distance(6)))
            else:
                self.bot.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
            continue

        for mine in mines_ready:
            if await self.bot.avoid_own_nuke(mine):
                continue
            if self.bot.activate_all_mines:
                if targets.closer_than(6, mine):
                    self.bot.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                    continue
                if targets:
                    target = targets.closest_to(mine)
                    self.bot.do(mine.move(target))
                    continue
                if mines_ready.amount > limit and self.bot.iteraatio % 2 == 0:
                    self.bot.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                    break
                if master:
                    if mine.distance_to(master) > 20:
                        self.bot.do(mine.move(master.position))
                    continue
                if mine.distance_to(self.bot.start_location) > 10:
                    cc = self.bot.start_location
                    self.bot.do(mine.move(cc.position))
                continue
            elif targets.closer_than(8, mine):
                if targets.closer_than(6, mine):
                    self.bot.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                    continue
                if self.bot.mines_burrowed.closer_than(2, mine) and self.bot.leapfrog_mines:
                    pass
                else:
                    self.bot.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                    continue
            if await self.bot.avoid_enemy_siegetanks(mine):
                continue
            if self.bot.leapfrog_mines:
                attack_mines = self.bot.mines_burrowed.closer_than(
                    self.bot.defence_radius, self.bot.enemy_start_location)
                avg_dist = self.bot.defence_radius
                if attack_mines:
                    avg_dist = attack_mines.furthest_to(self.bot.enemy_start_location)\
                                   .distance_to(self.bot.enemy_start_location) - 1
                    # avg_dist = attack_mines.center.distance_to(self.bot.enemy_start_location)
                if mine.distance_to(self.bot.enemy_start_location) < avg_dist \
                        and not self.bot.mines_burrowed.closer_than(6, mine):
                    self.bot.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                if len(mine.orders) == 0:
                    if self.mine_grid is None:
                        await self.get_mine_grid()
                    start = mine.position
                    goal = self.bot.enemy_start_location.random_on_distance(4)
                    path = self.bot.map_data.pathfind(start=start, goal=goal, grid=self.mine_grid,
                                                      allow_diagonal=True, sensitivity=5)
                    # self.bot.map_data.plot_influenced_path\
                    #     (start=start, goal=goal, weight_array=self.mine_grid, allow_diagonal=True)
                    # self.bot.map_data.show()
                    steps_left = 6
                    if path:
                        for point in path:
                            if steps_left > 0:
                                self.bot.do(mine.move(point, queue=True))
                                steps_left -= 1
                            else:
                                continue
                    continue
                continue

            if len(mine.orders) == 2 and not self.bot.ccANDoc.closer_than(15, mine):
                self.bot.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                continue
            if len(mine.orders) == 0:
                defence_locations = self.bot.ccANDoc.filter(lambda x: x.distance_to(self.bot.start_location) > 3)
                if defence_locations:
                    cc = defence_locations.random
                else:
                    cc = self.bot.start_location
                target = random.choice(self.bot.expansion_locations_list)
                self.bot.do(mine.move(cc.position))
                self.bot.do(mine.move(target, queue=True))
                self.bot.do(mine.move(cc.position, queue=True))
            continue

        if not mines_burrowed:
            return
        for mine in mines_burrowed.sorted(lambda x: x.distance_to(self.bot.enemy_start_location), reverse=True):
            if mine.health_percentage < 1 and mine.distance_to(self.bot.homeBase) < 10:
                continue
            if mine.distance_to(self.bot.enemy_start_location) < 10:
                self.bot.leapfrog_mines = False
                self.bot.activate_all_mines = True
            if mine.buff_duration_remain > 0:
                if mine.tag not in self.bot.remembered_fired_mines_by_tag:
                    self.bot.remembered_fired_mines_by_tag[mine.tag] = mine
                    if self.bot.chat_once_mine:
                        self.bot.chat_once_mine = False
                        if self.bot.chat:
                            await self.bot._client.chat_send("You would not shoot unarmed mine, would you?",
                                                         team_only=False)
                if self.bot.already_pending(DRILLCLAWS) < 1 or mine.health_percentage < 1:
                    if mine.distance_to(self.bot.homeBase) > 10:  # and self.bot.enemy_units.closer_than(15, mine):
                        self.bot.do(mine(AbilityId.BURROWUP_WIDOWMINE))
                        continue
            else:
                if mine.health_percentage >= 1 and mine.tag in self.bot.remembered_fired_mines_by_tag:
                    del self.bot.remembered_fired_mines_by_tag[mine.tag]
                    continue
            if await self.bot.avoid_own_nuke(mine):
                self.bot.do(mine(AbilityId.BURROWUP_WIDOWMINE))
                break
            if (self.bot.iteraatio % 4 == 0 and mines_ready.amount < limit) \
                    and self.bot.mines_burrowed.amount > 1 and not targets.closer_than(8, mine) \
                    and mine.tag not in self.bot.remembered_fired_mines_by_tag:
                self.bot.do(mine(AbilityId.BURROWUP_WIDOWMINE))
                break
