import random
import math
import sc2
import time
import argparse
from MapAnalyzer.MapData import MapData
from sc2 import Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units
from ANI_base_bot import ANI_base_bot
from sc2 import Race
from trainingdata import TrainingData as trainingData
from chat_messages import ChatData as ChatData
from unit_micros.Flanking_groups import FlankingController
from unit_micros.marines import MarineController
from unit_micros.ravens import RavenController
from unit_micros.banshees import BansheeController
from unit_micros.vikings import VikingController
from unit_micros.mines import MineController
from unit_trainer import UnitTrainer

# TODO don't try to expand in same location twice
# TODO Parasitic Bomb needs to be added in code.


async def find_potential_minral_line_turret_locations(location) -> [Point2]:
    p = location.position
    offset = 3.5
    return [
        Point2((p.x - offset, p.y + offset)),
        Point2((p.x - offset, p.y - offset)),
        Point2((p.x + offset, p.y - offset)),
        Point2((p.x + offset, p.y + offset)),
        Point2((p.x, p.y + offset)),
        Point2((p.x, p.y - offset)),
        Point2((p.x + offset, p.y)),
        Point2((p.x + offset, p.y)),
    ]


class ANIbot(ANI_base_bot):
    raw_affects_selection = True  # True = fast play
    debug = False
    debug_vikings = False
    debug_vikings_escape_grid = False
    show_off = False
    chat = True
    upgrade_liberator = False
    first_base_saturation = -2
    refineries_in_first_base = 1  # note: refineries slow down first expansion!
    refineries_in_second_base = 4
    scv_limit = 80
    scv_build_speed = 2
    greedy_scv_consrtuction = False
    BuildReapers = False
    reapers_left = 3
    MaxGhost = 2
    NukesLeft = 5  # max 10. If used 11 or more changes many variables
    raven_left = 3
    mines_left = 4
    aggressive_mines = False
    leapfrog_mines = False
    cyclone_left = 0
    dual_liberator = False
    liberator_left = 0
    liberator_priority = False
    hellion_left = 0
    research_blue_flame = False  # upgrades infernaligniter.
    research_servos = False
    banshee_left = 4
    upgrade_banshee_cloak = False
    upgrade_banshee_speed = False
    min_marine = 8  # try keep this amount of marines
    max_marine = 36
    marine_drop = False
    marines_last_resort = False
    max_thor = 4
    flanking_thors = False
    thor_use_route_a = True
    max_BC = 4
    max_viking = 5
    react_to_enemy_air = True
    max_siege = 5
    faster_tanks = False
    max_barracks = 2  # maxamount of barracks
    delay_barracs = False  # makes only one barracks until starport ready
    build_barracks_addons = True
    barracks_reactor_first = False
    super_fast_barracks = False
    maxfactory = 2
    max_starports = 3
    build_extra_factories = True
    build_extra_starports = True
    build_starportreactor = 0
    max_engineeringbays = 1
    fast_engineeringbay = True
    fast_armory = False
    build_armory = True
    maxmarauder = 6
    assault_enemy_home = True
    careful_marines = False
    agressive_marines = False
    marauder_push_limit = 0
    build_missile_turrets = True
    mineral_field_turret = False
    mech_build = False
    min_thors_to_attack = 2
    expand_for_vespene = True
    expand_fast_for_vespene = False
    fast_vespene = False
    fast_orbital = True  # slow orbital makes first OC after first expansion is pending
    upgrade_marine = True
    upgrade_marine_defence_and_mech_attack = False
    upgrade_mech = True
    upgrade_vehicle_weapons = True
    maxmedivacs = 3
    build_cc_home = False
    priority_tank = False
    siege_behind_wall = False
    priority_tank_pos = None
    build_priority_cyclone = False
    limit_vespene = 0
    minimum_repairgroup = 1
    nuke_enemy_home = False
    activate_all_mines = False
    scan_cloaked_enemies = False
    more_depots = False
    delay_expansion = False
    delay_third = False
    priority_factoty_reactor = False
    nuke_rush = False
    build_barracks_reactors = True
    send_scout = True
    delay_factory = False
    debug_next_building = None
    bunker_in_natural = 0
    mine_mineral_wall = True
    wait_until_4_orbital_ready = False
    agressive_tanks = False
    scan_enemy_at_4_min = False
    send_flanking_units = 0
    create_flanking_group_1 = True

    # game state variables
    target_of_assault = None
    can_surrender = False
    last_phase = False
    last_iteration = 0
    iteraatio = 0
    last_turn = 0
    start = 0
    enemy_natural = None
    enemy_third = None
    scout_sent = False
    chat_once_1 = True
    chat_once_mine = True
    chat_once_scv_kamikaze = True
    chat_first_base = True
    chat_second_base = True
    canSiege = True
    load_dropship = False
    dropship_sent = False
    viking_target_location = None
    viking_priority = False
    enemy_air_unit_location = None
    midle_depo_position = None
    home_in_danger = False
    remembered_fired_mines_by_tag = {}
    enemy_structures_at_start_by_tag = {}
    gatekeeper = None
    pick_fight = False
    realtime_buffer = 0
    unsiegetimer = 0
    build_extra_factory_and_starport = True
    scan_timer = 0
    supply_limit_for_third = 120
    emp_timer = 0
    liberator_timer = 0
    can_gg = 1
    sergeant = None
    reaper_haras = True
    training_scv = False
    lift_cc_once = True
    locations_need_to_be_scanned = []
    next_location_to_be_scanned = None
    scan_enemy_base = True
    proxy_defence = False
    priority_raven = False
    kamikaze_target = None
    random_kamikaze_target = None
    delay_starport = False
    muster_home_defence = True
    nuke_target = None
    nuke_spotter_tag = None
    nuke_spotter_last_alive_spot = None
    nuke_spotter_last_died_spot = None
    sweep_zones = []
    sweep_timer = 0
    debug_timer = 0
    morph_to_hellbats = False

    def __init__(self):
        super().__init__("ANIbot")
        self.viking_grid = None
        self.viking_escape_grid = None
        self.air_grid = None
        self.unit_command_uses_self_do = True
        self.strategy = None
        self.new_strategy = False
        self._training_data = trainingData()
        self._chat_data = ChatData()
        self.opp_id = self.findOppId()
        self.enemy_start_location = None
        self.clear_result = True
        self.nuke_timer = 0
        self.fallout_zone = []
        self.storm_zone = []
        self.bile_positions = []
        self.enemy_liberation_zone = []
        self.last_iter = 0
        self.delay_first_expansion = False
        self.super_greed = False
        self.greedy_third = False
        self.cc_first = False
        self.real_time = False
        self.last_game_loop = -10
        self.doner_location = None
        self.research_stimpack = True
        self.research_combatshield = True
        self.research_concussiveshels = True
        self.defence_radius = 0
        self.natural = None
        self.ramps = None
        self.last_jump_target = None
        self.all_ramp_top_centers = []
        self.all_ramp_bottom_centers = []
        self.natural_ramp_top_center = None
        self.flanking_controller = FlankingController(self)
        self.marinecontroller = MarineController
        self.ravencontroller = RavenController(self)
        self.banshee_controller = BansheeController(self)
        self.viking_controller = VikingController(self)
        self.mine_controller = MineController(self)
        self.unit_trainer = UnitTrainer(self)
        self.can_do_worker_rush_defence = True
        self.kill_scout = True
        self.cached_we_should_expand = None
        self.step_timer = 0
        self.attack_route_a = []
        self.attack_route_b = []
        self.chat_warning = True

    async def on_start(self):
        await super().on_start()
        self.map_data = MapData(self, loglevel="INFO")

        # map_at_start = MapData(self)
        # map_at_start.plot_map(fontdict = {"family": "serif", "weight": "bold", "size": 6})
        # map_at_start.show()

    async def execute(self):
        iteration = self.knowledge.iteration

        if self.realtime:
            if self.chat:
                self.chat = False
                await self._client.chat_send("Hello meatbag.", team_only=False)
                print("Playing against meatbag")
            pass
        else:
            response = self._chat_data.find_response(opponent_chat_data=self.state.chat,
                                                     my_id_from_proto=self.player_id)
            if response:
                await self._client.chat_send(response, team_only=False)

        self.remember_enemy_units()

        if self.debug:
            for unit in self.enemy_units_in_memory:
                if unit.timer > (self.debug_timer * 5):
                    self.debug_timer = unit.timer / 5
                p = unit.position
                h2 = self.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                size = 0.2
                p0 = Point3((pos.x - size, pos.y - size, pos.z + (unit.timer / self.debug_timer)))
                p1 = Point3((pos.x + size, pos.y + size, pos.z - 0))
                # print(f"Drawing {p0} to {p1}")
                c = Point3((0, 255, 255))
                self._client.debug_box_out(p0, p1, color=c)
        self.remember_detectors()
        self.remember_snapshots()
        self.cached_we_should_expand = None

        my_custom_air_grid = self.map_data.get_clean_air_grid(default_weight=50)
        enemy_ga_structures = self.enemy_structures.filter(lambda x: x.can_attack_air)
        enemy_ga_units = self.enemy_units_in_memory.filter(lambda x: not x.is_flying and x.can_attack_air)
        enemy_aa_units = self.enemy_units_in_memory.filter(lambda x: x.is_flying and x.can_attack_air)
        enemy_ag_types = [UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE]
        enemy_ag_targets = self.enemy_units_in_memory.of_type(enemy_ag_types)
        for enemy_unit in enemy_ga_units:
            if enemy_unit.type_id == UnitTypeId.CYCLONE:
                enemy_total_range = enemy_unit.radius + 8
            else:
                enemy_total_range = enemy_unit.radius + enemy_unit.air_range + 3
            my_custom_air_grid = self.map_data.add_cost(
                position=enemy_unit.position, radius=enemy_total_range, grid=my_custom_air_grid)
        for enemy_unit in self.enemy_structures.of_type(UnitTypeId.BUNKER):
            enemy_total_range = enemy_unit.radius + 8
            my_custom_air_grid = self.map_data.add_cost(
                position=enemy_unit.position, radius=enemy_total_range, grid=my_custom_air_grid)
        for enemy_unit in enemy_aa_units:
            enemy_total_range = enemy_unit.radius + enemy_unit.air_range + 4
            my_custom_air_grid = self.map_data.add_cost(
                position=enemy_unit.position, radius=(enemy_total_range), grid=my_custom_air_grid)
        if self.supply_used < 190:
            for enemy_unit in enemy_ga_structures:
                enemy_total_range = enemy_unit.radius + enemy_unit.air_range + 3
                my_custom_air_grid = self.map_data.add_cost(
                    position=enemy_unit.position, radius=(enemy_total_range), grid=my_custom_air_grid)
        viking_target_types = [UnitTypeId.OBSERVER, UnitTypeId.OVERSEER, UnitTypeId.OVERLORDTRANSPORT,
                               UnitTypeId.MEDIVAC, UnitTypeId.OVERLORD, UnitTypeId.RAVEN, UnitTypeId.BANSHEE]
        viking_targets = self.enemy_units.of_type(viking_target_types)
        self.viking_escape_grid = my_custom_air_grid
        for enemy_unit in viking_targets:
            self.viking_escape_grid = self.map_data.add_cost(position=enemy_unit.position,
                                                             radius=5, grid=self.viking_escape_grid, weight=-1)
        if self.debug_vikings_escape_grid:
            self.map_data.draw_influence_in_game(grid=self.viking_escape_grid, lower_threshold=51)
            self.map_data.draw_influence_in_game(grid=self.viking_escape_grid, lower_threshold=0,
                                                 upper_threshold=50)
        for enemy_unit in enemy_ag_targets:
            my_custom_air_grid = self.map_data.add_cost(
                position=enemy_unit.position, radius=4, grid=my_custom_air_grid, weight=-1)
        if self.debug:
            self.map_data.draw_influence_in_game(grid=my_custom_air_grid, lower_threshold=51)
            self.map_data.draw_influence_in_game(grid=my_custom_air_grid, lower_threshold=0, upper_threshold=49)
        self.air_grid = my_custom_air_grid

        viking_grid = self.map_data.get_clean_air_grid(default_weight=10)
        enemy_ga_structures = self.enemy_structures.ready.filter(lambda x: x.can_attack_air)
        enemy_ga_units = self.enemy_units_in_memory.filter(lambda x: not x.is_flying and x.can_attack_air)
        enemy_aa_units = self.enemy_units_in_memory.filter(lambda x: x.is_flying and x.can_attack_air)
        for enemy_unit in enemy_ga_units:
            enemy_total_range = enemy_unit.radius + enemy_unit.air_range + 3
            viking_grid = self.map_data.add_cost(
                position=enemy_unit.position, radius=enemy_total_range, grid=viking_grid)
        for enemy_unit in enemy_aa_units:
            enemy_total_range = enemy_unit.radius + enemy_unit.air_range + 1
            viking_grid = self.map_data.add_cost(
                position=enemy_unit.position, radius=enemy_total_range, grid=viking_grid, weight=-1)
        for enemy_unit in enemy_ga_structures:
            enemy_total_range = enemy_unit.radius + enemy_unit.air_range + 3
            viking_grid = self.map_data.add_cost(
                position=enemy_unit.position, radius=(enemy_total_range), grid=viking_grid)
        if self.debug_vikings:
            self.map_data.draw_influence_in_game(grid=viking_grid, lower_threshold=11)
            self.map_data.draw_influence_in_game(grid=viking_grid, lower_threshold=0, upper_threshold=10)
        self.viking_grid = viking_grid

        if self.debug:
            for cc in self.expansion_locations_list:
                p = Point2((cc.position))
                h2 = self.get_terrain_z_height(p)
                h2 = 12
                pos = Point3((p.x, p.y, h2))
                size = 1.5
                p0 = Point3((pos.x - size, pos.y - size, pos.z + 10))  # + Point2((0.5, 0.5))
                p1 = Point3((pos.x + size, pos.y + size, pos.z - 10))  # + Point2((0.5, 0.5))
                # print(f"Drawing {p0} to {p1}")
                c = Point3((255, 0, 0))
                self._client.debug_box_out(p0, p1, color=c)

            for snapshot_in_memory in self.remembered_snapshots_by_tag.keys():
                snapshot_info = self.remembered_snapshots_by_tag[snapshot_in_memory]
                p = snapshot_info["POS"]
                h2 = self.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                size = 0.2
                p0 = Point3(
                    (pos.x - size, pos.y - size, pos.z + (snapshot_info["TIMER"] / 10)))  # + Point2((0.5, 0.5))
                p1 = Point3((pos.x + size, pos.y + size, pos.z - 0))  # + Point2((0.5, 0.5))
                # print(f"Drawing {p0} to {p1}")
                c = Point3((255, 255, 0))
                self._client.debug_box_out(p0, p1, color=c)

        self.training_scv = False

        if (self.minerals > 2000
                and self.enemy_start_location
                and len(self.locations_need_to_be_scanned) == 0
                and (not self.enemy_structures or self.scan_enemy_base)
                and self.limit_vespene == 0):
            self.scan_enemy_base = False
            if self.chat:
                await self._client.chat_send("Scanning for enemy structures.", team_only=False)
            self.locations_need_to_be_scanned = sorted(self.expansion_locations_list,
                                                       key=lambda p: p.distance_to(self.enemy_start_location),
                                                       reverse=False)
        if not self.next_location_to_be_scanned and self.locations_need_to_be_scanned:
            if self.structures.closer_than(10, self.locations_need_to_be_scanned[0]):
                self.locations_need_to_be_scanned.remove(self.locations_need_to_be_scanned[0])
            elif self.enemy_structures.closer_than(10, self.locations_need_to_be_scanned[0]):
                self.locations_need_to_be_scanned.remove(self.locations_need_to_be_scanned[0])
            else:
                self.next_location_to_be_scanned = self.locations_need_to_be_scanned[0]
                self.locations_need_to_be_scanned.remove(self.next_location_to_be_scanned)
                print("Expansions that need scan:", len(self.locations_need_to_be_scanned))

        self.defence_radius = self.start_location.distance_to(self.game_info.map_center)
        if self.can_gg and self.structures:
            number_of_buildings = self.structures.amount
            if number_of_buildings > 2 * self.can_gg:
                self.can_gg += 1
            if self.can_gg > 3 and number_of_buildings < self.can_gg:
                self.can_gg = False
                await self._client.chat_send("gg", team_only=False)
                self.chat = False
            if self.units(SCV).amount <= 3:
                self.can_gg = False
                await self._client.chat_send("gg", team_only=False)
        self.scan_timer += 1
        await self.cashe_units_fast_cycle()
        self.homeBase = None
        await self.get_homeBase()
        if not self.homeBase:
            return
        await self.move_reapers()
        await self.flanking_controller.flanking_group_micro()
        await self.marinecontroller.marinemicro(self)
        await self.ravencontroller.ravenmicro()
        await self.move_marauders()
        await self.banshee_controller.bansheemicro()
        await self.viking_controller.viking_micro()
        await self.mine_controller.move_mines()
        #        print((time.time()-self.start)*1000)
        self.start = time.time()
        self.nuke_timer -= 1

        await self.cashe_effects()

        if self.structures.amount >= 3 and not self.can_surrender:
            self.can_surrender = True
        if self.structures.amount < 3 and self.can_surrender:
            if self.clear_result:
                self.clear_result = False
                self._training_data.removeResult(self.opp_id)
                self.can_surrender = False
        if not self.last_phase \
                and self.liberator_left - self.already_pending(UnitTypeId.LIBERATOR) <= 0 \
                and self.banshee_left - self.already_pending(UnitTypeId.BANSHEE) <= 0 \
                and not self.build_extra_factory_and_starport and self.limit_vespene == 0:
            self.last_phase = True

        if self.enemy_start_location == None:
            distance = math.inf
            if self.enemy_structures.exists:
                enemy_home = self.enemy_structures.furthest_to(self.start_location)
                enemy_start_point = self.enemy_start_locations[0]
                distance = enemy_start_point.distance_to(enemy_home)
                for x in range(0, len(self.enemy_start_locations)):
                    location = self.enemy_start_locations[x]
                    if location.distance_to(enemy_home) < distance:
                        distance = location.distance_to(enemy_home)
                        enemy_start_point = location.position
                self.enemy_start_location = enemy_start_point

        self.remember_repair_group()
        if self.puuhapete == None and self.scvs.amount > 0:
            print("Assigning new handyman")
            new_puuhapete = random.choice(self.scvs)
            if new_puuhapete:
                self.assing_puuhapete(new_puuhapete)

        units_to_ignore_ghost = [ADEPTPHASESHIFT, ZERGLING, INFESTEDTERRANSEGG, MULE, DRONE, SCV, PROBE, EGG,
                                 LARVA,
                                 OVERLORD, OBSERVER, BROODLING, INTERCEPTOR, MEDIVAC, CREEPTUMOR,
                                 CREEPTUMORBURROWED,
                                 CREEPTUMORQUEEN, CREEPTUMORMISSILE, CHANGELINGMARINESHIELD]
        maxbarracks = self.max_barracks
        if self.max_starports == 0:
            if self.delay_barracs and self.ccANDoc.ready.amount < 3:
                maxbarracks = 1
        else:
            if self.delay_barracs and not self.starports:
                maxbarracks = 1
        if self.minerals > 450 and not self.expand_for_vespene and self.ccANDoc.amount > 1:
            if self.limit_vespene != 0:
                if self.minerals > (
                        self.barracks.ready.amount + self.already_pending(UnitTypeId.BARRACKS)) * 150:
                    maxbarracks = 15
            else:
                maxbarracks = 10
        if not self.BuildReapers:
            maxreaper = 0
        else:
            maxreaper = 1
        if self.agressive_tanks:
            self.canSiege = False
        else:
            self.canSiege = True

        ## scout control
        if self.puuhapete:
            if (self.enemy_structures.of_type(UnitTypeId.BARRACKS).closer_than(self.defence_radius,
                                                                               self.start_location)
                    and self.ccANDoc.amount == 1
                    and not self.townhalls_flying
                    and not self.build_cc_home):
                self.build_cc_home = True
                self.priority_tank = True
                self.siege_behind_wall = True
                self.refineries_in_first_base = 2
                if self.chat:
                    await self._client.chat_send("Proxy detected -> Panic!", team_only=False)
            if (self.enemy_units_on_ground.of_type(UnitTypeId.MARINE).amount > 2
                    and self.ccANDoc.amount == 1
                    and not self.townhalls_flying and not self.marauders.filter(
                        lambda x: x.is_in_kamikaze_troops)
                    and not self.build_cc_home):
                self.build_cc_home = True
                if self.chat:
                    await self._client.chat_send("So many marines. Marines are OP.", team_only=False)
            if self.scout_sent:
                if self.enemy_structures.of_type(UnitTypeId.BARRACKS).amount > 2:
                    if self.puuhapete:
                        self.do(self.puuhapete.move(self.natural))
                    self.super_greed = False
                    self.scout_sent = False
                    self.build_cc_home = True
                    self.priority_tank = True
                    self.siege_behind_wall = True
                    self.nuke_rush = False
                    self.marine_drop = False
                    self.priority_factoty_reactor = False
                    # self.build_priority_cyclone = False
                    self.fast_orbital = True
                    self.refineries_in_first_base = 2
                    if self.min_marine < 10:
                        self.min_marine = 10
                    for building in self.structures.closer_than(5, self.natural):
                        if await self.has_ability(AbilityId.CANCEL_BUILDINPROGRESS, building):
                            self.do(building(AbilityId.CANCEL_BUILDINPROGRESS))
                    if self.first_base_saturation < 0:
                        self.first_base_saturation = 0
                    if self.chat:
                        await self._client.chat_send("Are you planning marine rush?", team_only=False)
                    print("Marine rush detected")

                if self.enemy_units.of_type(ZERGLING).amount >= 6:
                    self.nuke_rush = False
                    self.scout_sent = False
                    self.build_cc_home = True
                    self.siege_behind_wall = True
                    if self.hellion_left < 6:
                        self.hellion_left = 6
                    if self.chat:
                        await self._client.chat_send("Ling rush?", team_only=False)
                if self.enemy_structures.of_type(UnitTypeId.SPAWNINGPOOL):
                    if self.enemy_structures.of_type(UnitTypeId.SPAWNINGPOOL).first.is_active:
                        self.scout_sent = False
                        self.build_cc_home = True
                        self.siege_behind_wall = True
                        self.build_priority_cyclone = False
                        self.BuildReapers = True
                        if self.chat:
                            await self._client.chat_send("Speedling rush?", team_only=False)
                if self.puuhapete.health_percentage < 0.5:
                    self.scout_sent = False
                    # self.build_cc_home = True
                    if self.chat:
                        await self._client.chat_send("Please don't kill my SCV!", team_only=False)
                if (len(self.puuhapete.orders) == 1 or self.enemy_structures(ROACHWARREN)):
                    # TODO Save structure type and health by tag
                    # TODO Save also worker count
                    # TODO Save also info: Was scout injured or not
                    self.scout_sent = False
                    print("Scout completed.")
                    print("Scouted buildings:")
                    spawninpool = False
                    roachwarren = False
                    natural = False
                    for structure in self.enemy_structures:
                        if structure.name == "SpawningPool":
                            print("SpawningPool detected.")
                        if structure.name == "RoachWarren":
                            print("RoachWarren detected.")
                            roachwarren = True
                        if structure.position.distance_to(self.enemy_start_location) < 2:
                            print("Home:", structure.name, structure.health_percentage)
                        elif structure.position.distance_to(self.enemy_natural) < 2:
                            print("Natural:", structure.name, structure.health_percentage)
                            natural = True
                        else:
                            print(structure.name, structure.build_progress)
                    print("End of report.")
                    if not natural and roachwarren:
                        if self.chat:
                            await self._client.chat_send("Preparing for roach rush!", team_only=False)
                        for building in self.structures:
                            for expansion in self.expansion_locations_list:
                                if building.position.distance_to(expansion) < 3:
                                    if await self.has_ability(AbilityId.CANCEL_BUILDINPROGRESS, building):
                                        self.do(building(AbilityId.CANCEL_BUILDINPROGRESS))
                        self.build_cc_home = True
                        self.bunker_in_natural = 0
                        self.priority_tank = True
                        self.siege_behind_wall = True
                        self.nuke_rush = False
                        self.marine_drop = False
                        self.priority_factoty_reactor = False
                        self.build_priority_cyclone = False
                        self.fast_orbital = True
                        self.first_base_saturation = 2
                        self.refineries_in_first_base = 2

                    if not self.enemy_structures.of_type(UnitTypeId.GATEWAY) \
                            and self.enemy_structures.of_type(UnitTypeId.NEXUS):
                        if self.chat:
                            await self._client.chat_send("No gateway! What are you up to?", team_only=False)
                        if not self.build_cc_home:
                            for building in self.structures:
                                for expansion in self.expansion_locations_list:
                                    if building.position.distance_to(expansion) < 3:
                                        if await self.has_ability(AbilityId.CANCEL_BUILDINPROGRESS, building):
                                            self.do(building(AbilityId.CANCEL_BUILDINPROGRESS))
                                        self.build_cc_home = True
                                        self.scv_build_speed = 3
                        if self.first_base_saturation < -1:
                            self.first_base_saturation = -1

                    if self.enemy_structures.of_type(
                            UnitTypeId.SUPPLYDEPOT) and not self.enemy_structures.of_type(
                            UnitTypeId.BARRACKS):
                        if self.chat:
                            await self._client.chat_send("No barracks! What are you up to?", team_only=False)
                        self.build_cc_home = True
                        self.refineries_in_first_base = 2

        if self.enemy_structures.of_type(UnitTypeId.BUNKER).amount > 1 and self.delay_third:
            self.delay_third = False
            self.scv_build_speed = 3
            self.greedy_scv_consrtuction = True
            if self.chat:
                await self._client.chat_send("Are you hiding behind those bunkers?", team_only=False)
        if self.react_to_enemy_air:
            if self.max_viking < 6 and self.enemy_structures.of_type(UnitTypeId.STARGATE):
                self.build_starportreactor = 1
                self.max_viking = 6
                if self.max_starports < 4:
                    self.max_starports += 1
                print("Stargate detected. max_starport =", self.max_starports)
                if self.chat:
                    await self._client.chat_send("Stargate detected. Preparing for air battle", team_only=False)
                self.refineries_in_second_base = 4
            if self.max_viking < 16 and self.enemy_units.of_type(UnitTypeId.TEMPEST):
                # self.limit_vespene = 0
                self.max_viking = 16
                if self.max_starports < 3:
                    self.max_starports += 2
                elif self.max_starports < 4:
                    self.max_starports += 1
                self.build_starportreactor = 2
                print("Tempest detected. max_starport =", self.max_starports)
                if self.chat:
                    await self._client.chat_send("Tempest are so last season. Figure out something new",
                                                 team_only=False)
                self.refineries_in_second_base = 4
            if self.max_viking < 6 and self.enemy_units.of_type(UnitTypeId.BATTLECRUISER):
                if self.build_starportreactor < 2:
                    self.build_starportreactor += 1
                self.max_viking = 6
                if self.max_starports < 4:
                    self.max_starports += 1
                print("BC detected. max_starport =", self.max_starports)
                if self.chat:
                    await self._client.chat_send("Take those tin cans somewhere else!", team_only=False)
                self.refineries_in_second_base = 4
            if self.max_viking < 6 and self.enemy_units.of_type((UnitTypeId.VOIDRAY)):
                self.max_viking = 6
                if self.max_starports < 4:
                    self.max_starports += 1
                self.refineries_in_second_base = 4
                self.build_priority_cyclone = True
                for unit in (self.marauders | self.marines):
                    self.add_unit_to_kamikaze_troops(unit)
                self.kamikaze_target = self.enemy_third
                print("Voidrays detected. Start Kamikaze mission and build more vikings.")
                if self.chat:
                    await self._client.chat_send("Voidrays? Are you serious?", team_only=False)
            if self.max_viking < 16 and (self.enemy_units.flying.filter(
                        lambda x: x.can_attack_ground or x.can_attack_air).amount > 2):
                for facility in self.starports:
                    abilities = await self.get_available_abilities(facility)
                    # print(abilities)
                    if CANCEL_QUEUE5 in abilities:
                        self.do(facility(CANCEL_QUEUE5))
                # self.limit_vespene = 0
                if self.max_starports < 4:
                    self.max_starports += 1
                self.build_starportreactor = 2
                if not self.build_barracks_reactors:
                    self.build_barracks_reactors = True
                for unit in (self.marauders | self.marines):
                    self.add_unit_to_kamikaze_troops(unit)
                self.kamikaze_target = self.enemy_third
                self.max_viking = 16
                print("Enemy has air. Build Vikings. max_starport =", self.max_starports)
                if self.chat:
                    await self._client.chat_send("Several air units detected. Building Vikings.", team_only=False)
                return

        ## continue construction and scout
        if self.iteraatio % 2 == 0 and self.puuhapete and not self.home_in_danger:
            all_own_buildings = self.structures.exclude_type(
                [UnitTypeId.REACTOR, UnitTypeId.TECHLAB, UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKSREACTOR,
                 UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORYREACTOR, UnitTypeId.STARPORTTECHLAB,
                 UnitTypeId.STARPORTREACTOR])
            if not self.scout_sent:
                for building in all_own_buildings:
                    if (building.health_percentage < 1
                            and await self.has_ability(AbilityId.CANCEL_BUILDINPROGRESS, building)
                            and not await self.has_ability(AbilityId.HALT_BUILDING, building)):
                        if building.health_percentage < 1 / 6:
                            self.do(building(AbilityId.CANCEL_BUILDINPROGRESS))
                            print("Building cancelled")
                        elif await self.has_ability(AbilityId.SMART, self.puuhapete):
                            self.do(self.puuhapete(AbilityId.SMART, building))
            if (self.already_pending(UnitTypeId.BARRACKS) and not self.scout_sent and self.send_scout
                    and not self.puuhapete.is_carrying_minerals and not self.home_in_danger):
                waypoints = await self.scout_points()
                for waypoint in waypoints:
                    self.do(self.puuhapete.move(waypoint, queue=True))
                # if self.chat:
                #     await self._client.chat_send("Scout sent.", team_only=False)
                self.scout_sent = True
                self.send_scout = False

            if self.techlabs_and_reactors.amount > 2:
                self.do(self.puuhapete.attack(self.techlabs_and_reactors.closest_to(self.puuhapete)))

        # mine mineral wall in golden wall
        if self.mine_mineral_wall and self.ccANDoc.ready.amount == 2:
            rich_mineralfield = self.mineral_field.of_type(
                [PURIFIERRICHMINERALFIELD, PURIFIERRICHMINERALFIELD750])
            mfss = self.mineral_field.of_type([MINERALFIELD450])
            if not rich_mineralfield:
                self.mine_mineral_wall = False
            elif rich_mineralfield and mfss:
                self.mine_mineral_wall = False
                print("Clearing path to underworld.")
                mf = min(mfss, key=lambda x: x.distance_to(self.start_location))
                task_force = self.scvs.take(6)
                # self.do(self.puuhapete.gather(mf))
                for worker in task_force:
                    if worker.is_carrying_minerals:
                        self.do(worker(AbilityId.HARVEST_RETURN))
                        self.do(worker.gather(mf, queue=True))
                    else:
                        self.do(worker.gather(mf, queue=True))

        ## fix broken things
        units_in_repair_group = 0
        new_fixer = None
        for fixer in self.scvs:
            if fixer.is_in_repair_group:
                units_in_repair_group += 1
        if (units_in_repair_group < self.minimum_repairgroup
                or ((self.build_cc_home or self.ccANDoc.amount >= 4) and units_in_repair_group < 4)):
            possible_fixers = self.scvs.filter(
                lambda x: x.is_carrying_minerals and not x.is_puuhapete and not x.is_in_repair_group)
            if possible_fixers:
                new_fixer = random.choice(possible_fixers)
            if new_fixer:
                self.add_unit_to_repair_group(new_fixer)
                print("New fixer assigned")
        repailable_units = (self.vikingassault |
                            self.hellions |
                            self.cyclones |
                            self.siegetanks |
                            self.mines_burrowed |
                            self.siegetanks_sieged |
                            self.medivacs |
                            self.battlecruisers |
                            self.vikingassault |
                            self.thors)

        if self.repair_group and self.iteraatio % 16 == 0 and not self.home_in_danger:
            ajoneuvot = repailable_units.ready.closer_than(15, self.homeBase)
            rakennukset = self.structures.ready.exclude_type([TECHLAB, REACTOR])
            potilaat = (ajoneuvot | rakennukset).filter(lambda x: x.health_percentage < 1)
            if self.marines.amount == 1 and self.enemy_units.of_type(UnitTypeId.ZEALOT):
                target = self.enemy_units.of_type(UnitTypeId.ZEALOT).closest_to(self.marines.first)
                for fixer in self.repair_group:
                    self.do(fixer.attack(target))
            elif potilaat:
                # print(potilaat)
                for fixer in self.repair_group:
                    potilas = potilaat.closest_to(fixer)
                    wall = self.structures(UnitTypeId.SUPPLYDEPOT).filter(lambda x: x.health_percentage < 1)
                    if wall:
                        potilas = wall.sorted(lambda x: x.health_percentage, reverse=False)[0]
                    self.do(fixer(EFFECT_REPAIR_SCV, potilas))
                    self.do(fixer(EFFECT_REPAIR_SCV, potilaat.random, queue=True))
                    # print(fixer.orders)
                    # print(fixer.orders[0])
                    # self.do(fixer.move(self.start_location.random_on_distance(6), queue = True))

        ## ghost reporting
        max_energy = 0
        nuke_ordered = False
        sniped_targets = []
        can_snipe = True
        self.emp_timer += 1
        if not self.nuke_target:
            self.nuke_spotter_tag = None
        if self.emp_timer > 2:
            can_emp = True
        else:
            can_emp = False
        spotter_still_alive = False
        for ghost in self.ghosts:
            if ghost.tag == self.nuke_spotter_tag:
                spotter_still_alive = True
                self.nuke_spotter_last_alive_spot = ghost.position
            if len(ghost.orders) > 0:
                if ghost.orders[0].ability.id in [AbilityId.EFFECT_GHOSTSNIPE]:
                    sniped_targets.append(ghost.orders[0].target)
            ghost.can_nuke = False
            ghost.next_in_line = False
            if len(ghost.orders) >= 1:
                if ghost.orders[0].ability.id in [AbilityId.TACNUKESTRIKE_NUKECALLDOWN]:
                    nuke_ordered = True
            if ghost.energy > max_energy and ghost.health_percentage >= 1:
                max_energy = ghost.energy
        if not spotter_still_alive and self.nuke_spotter_tag:
            self.nuke_spotter_last_died_spot = self.nuke_spotter_last_alive_spot
            self.nuke_spotter_tag = None
            print("spotter died")
        # if sniped_targets:
        #     print("sniped targets", sniped_targets)
        for ghost in self.ghosts:
            if ghost.energy == max_energy and await self.has_ability(TACNUKESTRIKE_NUKECALLDOWN, ghost):
                ghost.next_in_line = True
                if not nuke_ordered:
                    ghost.can_nuke = True
                break

        targets_for_snipe = self.enemy_units_and_structures.not_structure.exclude_type(
            units_to_ignore_ghost).filter(
            lambda x: x.is_biological and x.tag not in sniped_targets)
        for ghost in self.ghosts:
            if len(ghost.orders) > 0 and ghost.orders[0].ability.id in [AbilityId.TACNUKESTRIKE_NUKECALLDOWN]:
                self.nuke_spotter_tag = None
                self.nuke_target = None
                continue
            if ghost.tag == self.nuke_spotter_tag:
                await self.ghost_nuke_spotter_micro(ghost)
                continue
            if len(ghost.orders) > 0 and ghost.orders[0].ability.id in [AbilityId.EFFECT_GHOSTSNIPE]:
                continue
            potential_targets_EMP = (
                self.enemy_units_and_structures.not_structure.exclude_type(units_to_ignore_ghost)
                .filter(lambda x: x.shield > 40).closer_than(11 + ghost.radius, ghost))
            potential_targets = targets_for_snipe.closer_than(11 + ghost.radius, ghost)
            known_enemies = self.enemy_units_and_structures.not_structure
            if (self.NukesLeft <= 0 and ghost.health_percentage < 0.9 and await self.can_cast(ghost,
                                                                                              AbilityId.BEHAVIOR_CLOAKON_GHOST)
                    and self.enemy_units_and_structures.filter(lambda x: x.can_attack_ground).closer_than(20,
                                                                                                          ghost)
                    and self.medivacs):
                self.do(ghost(AbilityId.BEHAVIOR_CLOAKON_GHOST))
                continue

            if await self.can_cast(ghost, AbilityId.BEHAVIOR_CLOAKOFF_GHOST):
                if self.NukesLeft <= 0 and ghost.health_percentage >= 1:
                    self.do(ghost(AbilityId.BEHAVIOR_CLOAKOFF_GHOST))
                    continue
                detectors = (self.enemy_units | self.enemy_structures).filter(lambda x: x.is_detector)
                if detectors.closer_than(12, ghost) and ghost.distance_to(self.homeBase) > 20:
                    self.do(ghost.move(self.homeBase.position))
                    continue
            if await self.avoid_own_nuke(ghost):
                continue
            if await self.avoid_enemy_siegetanks(ghost):
                continue
            if ghost.can_nuke and await self.has_ability(TACNUKESTRIKE_NUKECALLDOWN, ghost):
                if self.nuke_enemy_home:
                    if ghost.energy > 70:
                        if self.enemy_structures.closer_than(3, self.enemy_natural):
                            target = self.enemy_natural
                        else:
                            target = self.enemy_start_location
                        self.nuke_spotter_tag = ghost.tag
                        self.nuke_target = target
                        self.nuke_enemy_home = False
                        if self.chat:
                            await self._client.chat_send("Nuke", team_only=False)

                        return
                elif (self.enemy_structures.exists
                      and ghost.energy > 75):
                    if not self.nuke_target:
                        expansions_sorted = sorted(self.expansion_locations_list,
                                                   key=lambda p: p.distance_to(self.enemy_start_location),
                                                   reverse=True)
                        for base in expansions_sorted:
                            if self.enemy_structures.ready.closer_than(3, base):
                                if base.position == self.enemy_natural:
                                    continue
                                if base.position == self.enemy_start_location:
                                    continue
                                else:
                                    self.nuke_target = base.position
                                    break
                        if not self.nuke_target:
                            self.nuke_target = random.choice(self.enemy_structures).position
                    if not self.nuke_spotter_tag:
                        self.nuke_spotter_tag = ghost.tag
            if ghost.weapon_cooldown != 0:
                threaths = self.enemy_units_and_structures.filter(
                    lambda x: x.can_attack_ground and x.distance_to(
                        ghost) < x.radius + x.ground_range + ghost.radius + 2)
                if threaths:
                    threath = threaths.closest_to(ghost.position)
                    self.do(ghost.move(ghost.position.towards(threath, -6)))
                    continue
            if (ghost.health_percentage < 0.5 and await self.can_cast(ghost, AbilityId.BEHAVIOR_CLOAKON_GHOST)
                    and self.enemy_units_and_structures.filter(lambda x: x.can_attack_ground).closer_than(20,
                                                                                                          ghost)
                    and self.medivacs):
                self.do(ghost(AbilityId.BEHAVIOR_CLOAKON_GHOST))
                continue
            elif not ghost.next_in_line:
                if known_enemies.closer_than(11 + ghost.radius, ghost):
                    if potential_targets_EMP and ghost.energy >= 75 and can_emp:
                        potential_targets_EMP = potential_targets_EMP.sorted(lambda x: (x.shield), reverse=True)
                        target = potential_targets_EMP[0]
                        can_emp = False
                        self.emp_timer = 0
                        self.do(ghost(AbilityId.EMP_EMP, target.position))
                        print("Ghost: EMP", target.name, target.shield)
                        continue
                    if potential_targets and ghost.energy >= 70 and can_snipe:
                        potential_targets = potential_targets.sorted(lambda x: (x.health + x.shield),
                                                                     reverse=True)
                        target = potential_targets[0]
                        can_snipe = False
                        self.do(ghost(AbilityId.EFFECT_GHOSTSNIPE, target))
                        print("Ghost: SNIPE", target.name)
                        continue
                if targets_for_snipe and ghost.energy >= 70:
                    target = targets_for_snipe.closest_to(ghost)
                    self.do(ghost.attack(target.position))
                    continue
            # light_enemies_in_range = known_enemies.closer_than(ghost_range + ghost.radius, ghost).filter(lambda x: x.is_light)
            # if light_enemies_in_range:
            #     enemies_in_range_sorted = light_enemies_in_range.sorted(lambda x: (x.health + x.shield), reverse=True)
            #     target = enemies_in_range_sorted[0]
            #     self.do(ghost.attack(target))
            #     continue
            if self.NukesLeft and await self.can_cast(ghost, AbilityId.BEHAVIOR_CLOAKOFF_GHOST):
                if not self.enemy_units.closer_than(20, ghost):
                    self.do(ghost(AbilityId.BEHAVIOR_CLOAKOFF_GHOST))
                    continue
            if self.NukesLeft <= 0 and self.enemy_units_and_structures and (
                    ghost.health_percentage >= 1 or not self.medivacs):
                self.do(ghost.attack(self.enemy_units_and_structures.closest_to(ghost).position))
                continue
            if self.general and self.thors and ghost.energy > 50:
                if ghost.distance_to(self.general.position) > 10:
                    self.do(ghost.move(self.general.position))
                continue
            if ghost.position.to2.distance_to(self.start_location) > 10:
                self.do(ghost.move(self.start_location))
                continue

        ## bunkers
        if self.bunkers.ready and self.marines:
            if self.kamikaze_target or self.ccANDoc.amount >= 4:
                for bunker in self.bunkers.ready:
                    # abilities = await self.get_available_abilities(bunker)
                    if await self.has_ability(UNLOADALL_BUNKER, bunker):
                        self.do(bunker(AbilityId.UNLOADALL_BUNKER))
                        continue  # continue for loop, dont execute any of the following
                    elif await self.has_ability(EFFECT_SALVAGE, bunker):
                        self.do(bunker(AbilityId.EFFECT_SALVAGE))
                        continue  # continue for loop, dont execute any of the following
            else:
                for bunker in self.bunkers.ready:
                    if await self.has_ability(LOAD_BUNKER, bunker):
                        marines = self.marines.closer_than(5, bunker)
                        if marines:
                            self.do(bunker(AbilityId.LOAD_BUNKER, marines.closest_to(bunker)))
                            continue  # continue for loop, dont execute any of the following

        if self.iteraatio % 3 == 0:
            if self.limit_vespene > 0 and self.minerals > 4000:
                self.limit_vespene = 0
                if self.max_starports < 4:
                    self.max_starports += 1
                print("Mineral bank sufficient. Start gas harvesting. max_starpots =", self.max_starports)
            await self.build_refinery()

        if self.ccANDoc.ready.amount == 1 and not self.delay_first_expansion:
            if self.enemy_units_and_structures.closer_than(30,
                                                           self.homeBase).amount > 2 and not self.delay_expansion:
                self.delay_first_expansion = True
                self.first_base_saturation += 3

        await self.build_workers(self.scv_limit)
        if not await self.we_should_expand():
            await self.safkaa()
        elif self.build_cc_home and self.supplydepots.amount < 3 and self.barracks:
            await self.safkaa()
        if self.enemy_structures.of_type(UnitTypeId.PLANETARYFORTRESS):
            self.kamikaze_target = None
            self.clear_units_in_kamikaze_troops()

        can_build = True

        # You have to import "from sc2.units import Units" to make this code work

        # raxes_with_reactors = sc2.units.Units([], self)  # creates empty Units objects that is populated later
        # raxes_with_techlabs = sc2.units.Units([], self)
        # raxes_without_addon = sc2.units.Units([], self)
        #
        # for rax in self.structures.of_type(UnitTypeId.BARRACKS).ready:  # cycles through every rax that is ready
        #     if rax.add_on_tag == 0 and rax.is_idle:  # if no add_on attached to rax then .add_on_tag == 0
        #         raxes_without_addon.append(rax)  # appends rax Unit object to raxes_without_addon Units object list
        #         continue
        #     for add_on in self.structures(UnitTypeId.BARRACKSREACTOR).ready:  # cycles through every reactor
        #         if rax.add_on_tag == add_on.tag and len(rax.orders) < 2:  # compares tags between rax and reactor tags
        #             raxes_with_reactors.append(rax)  # appends rax Unit object to raxes_with_reactors Units object list
        #             continue
        #     for add_on in self.structures(UnitTypeId.BARRACKSTECHLAB).ready:  # cycles through every techlab
        #         if rax.add_on_tag == add_on.tag and rax.is_idle:  # compares tags between rax and reactor tags
        #             raxes_with_techlabs.append(rax)  # appends rax Unit object to raxes_with_reactors Units object list
        #             continue
        #
        # # now you have all raxes divided in three new Units objects.
        # # Note that these objects contain only raxes that have free production slots available.
        # # now yo can use thase Units objects in your own code.
        # # In example below it train marines only in raxes with reactors
        #
        # br = None
        # if raxes_with_reactors:
        #     br = raxes_with_reactors.first
        # if br:
        #     self.do(br.train(UnitTypeId.MARINE))  # I don't know how this line is supposed to be in current Burnysc2

        # TODO make new method for this
        if self.take_third_first:
            if self.ccANDoc.closer_than(3, self.take_third_first):
                self.take_third_first = False

        if self.enemy_structures.of_type(UnitTypeId.DARKSHRINE) and not self.scan_cloaked_enemies:
            self.build_missile_turrets = True
            self.fast_engineeringbay = True
            self.scan_cloaked_enemies = True
            self.raven_left = 100
            print("DARKSHRINE detected!")
            if self.chat:
                await self._client.chat_send("Dark templars? I should prepare for that.", team_only=False)
        if self.ccANDoc.ready.amount + self.townhalls_flying.amount >= 4:
            self.wait_until_4_orbital_ready = False
        if self.marauders.amount >= self.marauder_push_limit > 0:
            self.marauder_push_limit = 0
            for unit in (self.marauders | self.marines):
                self.add_unit_to_kamikaze_troops(unit)
            self.kamikaze_target = self.enemy_start_location
        if self.delay_expansion:
            for cc in self.ccANDoc.ready:
                if cc.ideal_harvesters <= 10:
                    self.delay_expansion = False
                    self.marines_last_resort = True
                    for unit in (self.marauders | self.marines):
                        self.add_unit_to_kamikaze_troops(unit)
                    self.kamikaze_target = self.enemy_third
            if self.siegetanks:
                self.delay_expansion = False
                self.marines_last_resort = True
                for unit in (self.marauders | self.marines):
                    self.add_unit_to_kamikaze_troops(unit)
                self.kamikaze_target = self.enemy_third
            elif self.enemy_units.of_type([MUTALISK]):
                self.delay_expansion = False
                self.marines_last_resort = True
                self.max_viking = 8
                # self.limit_vespene = 0
                if self.max_starports < 4:
                    self.max_starports += 1
                self.build_starportreactor = 1
                print("Mutalisks detected. max_starport = ", self.max_starports)
                if self.chat:
                    await self._client.chat_send("Mutalisk detected. Building Vikings.", team_only=False)
            elif self.enemy_units.of_type([SIEGETANKSIEGED, SIEGETANK]) and self.banshee_left < 10:
                self.delay_expansion = False
                self.marines_last_resort = True
                self.banshee_left = 10
                self.viking_priority = True
                if self.max_starports < 4:
                    self.max_starports += 1
                self.build_starportreactor = 1
                # self.limit_vespene = 0
                print("Siegetanks detected. max_starport = ", self.max_starports)
                if self.chat:
                    await self._client.chat_send("Siegetank detected. Building Banshees and Vikings.",
                                                 team_only=False)
        if self.delay_third:
            if self.supply_used > self.supply_limit_for_third or self.enemy_units.of_type(UnitTypeId.TEMPEST):
                print("Supply used when push starts:", self.supply_used)
                # self.cyclone_left = 0
                self.delay_third = False
                self.siege_behind_wall = False
                for tank in self.siegetanks_sieged:
                    self.do(tank(AbilityId.UNSIEGE_UNSIEGE))
                    continue

                # if self.enemy_structures and not self.enemy_structures.visible:
                #     self.target_of_assault = self.enemy_structures.random.position
                # else:
                for unit in (self.marauders | self.marines):
                    self.add_unit_to_kamikaze_troops(unit)
                self.kamikaze_target = self.enemy_third

        """These override normal structure production"""
        if await self.we_need_orbital() and self.cc.ready.idle:
            if self.minerals > 150:
                for cc in self.cc.ready.idle:
                    self.do(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))
                    print("up grade orbital")
            can_build = False
        elif self.super_greed:
            if self.supplydepots.amount < 3:
                await self.safkaa()
            if not self.supplydepots.ready:
                return
            if self.barracks.amount < 1 and self.can_afford(UnitTypeId.BARRACKS):
                await self.build_for_me(UnitTypeId.BARRACKS)
                return
            if self.barracks.ready.idle:
                br = self.barracks.ready.idle.first
                self.do(br.train(UnitTypeId.MARINE))
                can_build = False
        elif self.nuke_rush:
            can_build = await self.build_nuke_rush()
        elif self.marine_drop:
            can_build = await self.manage_drop()
        elif self.priority_factoty_reactor:
            can_build = await self.build_priority_factoty_reactor()
        elif self.priority_tank:
            can_build = await self.build_priority_tank()
        elif self.build_priority_cyclone:
            can_build = await self.build_priority_cyclones()
        elif self.priority_raven:
            can_build = await self.build_priority_raven()
        elif self.bunker_in_natural and not self.nuke_enemy_home:
            can_build = await self.build_bunker_to_natural()

        if can_build and self.scvs:
            if await self.we_should_expand():
                expansion = await self.get_next_expansion()
                if expansion is None:
                    await self.buildings(maxbarracks, iteration)
                    await self.unit_trainer.trainer(maxreaper)
                elif self.minerals > 400:
                    if self.build_cc_home:
                        await self.build_cc_at_home()
                    else:
                        if self.squad_group and expansion:
                            if self.squad_group.center.distance_to(expansion) < 5:
                                scanner = self.orbitalcommand.sorted(lambda x: x.energy, reverse=True)[0]
                                if scanner and scanner.energy > 50 and await self.has_ability(SCANNERSWEEP_SCAN,
                                                                                              scanner):
                                    self.do(scanner(AbilityId.SCANNERSWEEP_SCAN, expansion))
                                    self.scan_timer = 0
                        await self.expand_now_ANI()
            elif (((self.minerals > 700 > self.vespene and not self.already_pending(UnitTypeId.COMMANDCENTER))
                   or (self.minerals > 1000 and self.expand_fast_for_vespene))
                  and self.expand_for_vespene
                  and not self.delay_third):
                expansion = await self.get_next_expansion()
                if expansion is None:
                    if self.expand_fast_for_vespene:
                        self.expand_fast_for_vespene = False
                    await self.buildings(maxbarracks, iteration)
                    await self.unit_trainer.trainer(maxreaper)
                else:
                    if self.squad_group and expansion:
                        if self.squad_group.center.distance_to(expansion) < 5:
                            scanner = self.orbitalcommand.sorted(lambda x: x.energy, reverse=True)[0]
                            if scanner and scanner.energy > 50 and await self.has_ability(SCANNERSWEEP_SCAN,
                                                                                          scanner):
                                self.do(scanner(AbilityId.SCANNERSWEEP_SCAN, expansion))
                                self.scan_timer = 0
                    await self.expand_now_ANI()
            elif not self.training_scv:
                if (await self.do_research()
                        or self.enemy_units.closer_than(self.defence_radius, self.homeBase).amount > 1):
                    await self.buildings(maxbarracks, iteration)
                    await self.unit_trainer.trainer(maxreaper)

        elif self.enemy_units.closer_than(self.defence_radius, self.homeBase).amount > 1:
            await self.unit_trainer.trainer(maxreaper)
        await self.landbuildings()
        await self.evac_orbital()
        await self.call_for_mules()
        await self.raise_lower_depots()
        await self.move_scvs(),
        await self.move_squad(),
        await self.move_thors(),
        await self.move_liberators(),
        await self.move_hellions_and_hellbats(),
        if not self.marine_drop:
            await self.move_medivacs(),
        await self.move_battle_ruiser(),
        await self.move_tanks(),
        await self.move_cyclones(),

        if self.home_in_danger and self._client.game_step > 2 and not self.realtime:
            self._client.game_step = 2

        if not self.natural:
            if len(self.enemy_start_locations) == 1:
                self.enemy_start_location = self.enemy_start_locations[0]
                self.enemy_natural = await self.get_enemy_natural()
                self.enemy_third = await self.get_enemy_third()
            last_route_a_pos = None
            last_route_b_pos = None
            add_to_route_a = True
            expansion_locations = []
            for el in self.expansion_locations_list:
                if el.distance_to_point2(self.enemy_start_location) < 3:
                    continue
                if el.distance_to_point2(self.enemy_natural) < 3:
                    continue
                if el.distance_to_point2(self.start_location) < 3:
                    continue
                d = await self._client.query_pathing(self.enemy_start_location, el)
                if d is None:
                    continue
                expansion_locations.append(el)
            while expansion_locations:
                closest = None
                distance = math.inf
                for el in expansion_locations:
                    if add_to_route_a:
                        if not last_route_a_pos:
                            d = await self._client.query_pathing(self.enemy_natural, el)
                        else:
                            d = el.distance_to_point2(last_route_a_pos)
                    else:
                        if not last_route_b_pos:
                            d = await self._client.query_pathing(self.enemy_natural, el)
                        else:
                            d = el.distance_to_point2(last_route_b_pos)
                    if d < distance:
                        distance = d
                        closest = el
                if add_to_route_a:
                    expansion_locations.remove(closest)
                    last_route_a_pos = closest
                    self.attack_route_a.append(closest)
                    add_to_route_a = False
                else:
                    expansion_locations.remove(closest)
                    last_route_b_pos = closest
                    self.attack_route_b.append(closest)
                    add_to_route_a = True

            print("Map name =", self.game_info._proto.map_name)
            self.natural = await self.get_next_expansion()
            await self.cache_expansions()
            # Split workers
            mfs = self.mineral_field.closer_than(10, self.townhalls.first.position)
            workers = self.units(UnitTypeId.SCV)
            # self.game_info._proto.map_name
            print("MINERALFIELD450", self.mineral_field.of_type(MINERALFIELD450).amount)
            print("MINERALFIELD750", self.mineral_field.of_type(MINERALFIELD750).amount)
            print("MINERALFIELD", self.mineral_field.of_type(MINERALFIELD).amount)
            print("PURIFIERRICHMINERALFIELD", self.mineral_field.of_type(PURIFIERRICHMINERALFIELD).amount)
            print("PURIFIERRICHMINERALFIELD750", self.mineral_field.of_type(PURIFIERRICHMINERALFIELD750).amount)
            rich_mineralfield = [PURIFIERRICHMINERALFIELD, PURIFIERRICHMINERALFIELD750]
            if self.mineral_field.of_type(rich_mineralfield):
                self.take_third_first = await self.get_third_base()
            for mf in mfs:  # type: Unit
                if workers:
                    worker = workers.closest_to(mf)
                    self.do(worker.gather(mf))
                    workers.remove(worker)
            for w in workers:  # type: Unit
                self.do(w.gather(mfs.closest_to(w)))

            self.ramps = self.game_info.map_ramps
            for ramp in self.game_info.map_ramps:
                if self.main_base_ramp.top_center != ramp.top_center:
                    self.all_ramp_top_centers.append(ramp.top_center)
                    self.all_ramp_bottom_centers.append(ramp.bottom_center)
            # print(self.all_ramp_top_centers)
            # natural_ramp = self.closest_ramp_to(unit)
            # for pos in self.all_ramp_top_centers:
            #     print(self.natural.position.distance_to(pos))

            "Load previous tactics that worked agains this opponent"
            if not self.opp_id:
                self.strategy = random.randint(1, 15)
                if self.enemy_race == Race.Zerg:
                    self.opp_id = "liskot"
                elif self.enemy_race == Race.Protoss:
                    self.opp_id = "avaruusmiehet"
                elif self.enemy_race == Race.Terran:
                    self.opp_id = "ihmiset"
                else:
                    self.opp_id = "satunnainen"
            else:
                print("Playing against:", self.opp_id)
                self.strategy = self._training_data.findStrat(self.opp_id)
            """
            chose tactics from 1 to 15
            1 = Greed
            2 = 2 base push
            3 = Terran Bio
            4 = Mech
            5 = Air superiority
            6 = Nuke
            7 = ghost
            8 = marine drop
            9 = test
            10 = No starport
            11 = Marauders
            12 = 1-1-1 slow expand
            13 = Minefields
            14 = MCV
            15 = cc first
            """
            # self.strategy = 13  # 2020
            # self.strategy = random.choice([13])
            # self.strategy = random.randint(1, 15)

            if self.realtime:
                self.strategy = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
                # self.strategy = random.choice([13])

            if self.strategy is None:
                self.strategy = random.randint(1, 15)
                self.chat = False
                "save strategy as victory, and remove if defeated"
                self._training_data.saveVictory(self.opp_id, self.strategy)
            print('playing with strategy', self.strategy)

            """hardcoded strategies for opponents"""
            # if self.opp_id == "d4f4776b-f4dd-4cdc-bb29-18f28c016c66":  # MicroMachine
            #     print("Opponent: MicroMachine")
            #     self.strategy = 9 # Fast cyclone
            #     self._training_data.removeResult(self.opp_id)
            # if self.opp_id == "54bca4a3-7539-4364-b84b-e918784b488a":  # Jensiiibot
            #     print("Opponent: Jensiiibot")
            #     self.strategy = 5 # Air superiority
            #     self._training_data.removeResult(self.opp_id)
            # if self.opp_id == "6ddf718d-07ec-4c41-9ee8-14c469533ffb":  # Ketroc
            #     print("Opponent: Ketroc")
            #     self.strategy = 8 # marine drop
            #     self._training_data.removeResult(self.opp_id)
            # if self.opp_id == "da677994-8e56-4fb8-ac89-19c2e870d3f5":  # TheHarvester
            #     print("Opponent: TheHarvester")
            #     self.strategy = 3
            #     self._training_data.removeResult(self.opp_id)

            # 2020
            if self.strategy == 1:  # Greed
                self.super_greed = True
                self.build_cc_home = False
                self.wait_until_4_orbital_ready = False
                self.greedy_third = False
                self.refineries_in_first_base = 0
                self.refineries_in_second_base = 3
                self.more_depots = True
                self.send_scout = True
                self.greedy_scv_consrtuction = True
                self.limit_vespene = 4
                self.scv_build_speed = 3
                self.raven_left = 100
                self.fast_orbital = True
                self.first_base_saturation = 0
                self.scv_limit = 85
                self.max_BC = 6
                self.last_phase = True
                self.assault_enemy_home = True
                self.BuildReapers = False
                self.maxmarauder = 2
                self.MaxGhost = 0
                self.expand_for_vespene = False
                self.mines_left = 0
                self.cyclone_left = 0
                self.banshee_left = 0
                self.liberator_left = 0
                self.liberator_priority = False
                self.hellion_left = 0
                self.max_siege = 0
                self.max_viking = 0  # build this amount of vikings before enemy air untis have been seen
                self.max_barracks = 3
                self.super_fast_barracks = True
                self.barracks_reactor_first = False
                self.maxfactory = 1
                self.max_starports = 2
                self.build_barracks_reactors = True
                self.build_starportreactor = 2
                self.maxmedivacs = 10
                self.min_marine = 20  # try keep this amount of marines
                self.max_marine = 120
                self.agressive_marines = True
                self.careful_marines = False
                self.agressive_tanks = True
                self.research_stimpack = True
                self.upgrade_marine = True
                self.research_concussiveshels = True
                self.marines_last_resort = False
                self.upgrade_vehicle_weapons = False
                self.max_engineeringbays = 2
                self.build_armory = False
                self.upgrade_mech = False
                self.build_missile_turrets = True
                self.mineral_field_turret = True
                self.max_thor = 0
                self.NukesLeft = 0
                self.build_extra_factories = False
                self.build_extra_starports = True
            elif self.strategy == 2:  # 2 base push
                self.refineries_in_first_base = 1
                self.refineries_in_second_base = 3
                self.take_third_first = False
                if self.mineral_field.of_type(rich_mineralfield):
                    self.natural = await self.get_third_base()
                self.delay_third = True
                self.supply_limit_for_third = 120
                self.bunker_in_natural = 2
                self.priority_tank = True
                self.fast_engineeringbay = False
                self.first_base_saturation = -10
                self.scv_build_speed = 2
                self.fast_vespene = True
                self.fast_orbital = False
                self.expand_for_vespene = True
                self.marines_last_resort = True
                self.refineries_in_first_base = 0
                self.greedy_scv_consrtuction = True
                self.minimum_repairgroup = 2
                self.max_barracks = 3
                self.super_fast_barracks = False
                self.barracks_reactor_first = False
                self.maxfactory = 2
                self.max_starports = 1
                self.build_starportreactor = 0
                self.delay_barracs = False
                self.BuildReapers = True
                self.min_marine = 10
                self.max_marine = 100
                self.maxmarauder = 12
                self.MaxGhost = 0
                if self.enemy_race == Race.Zerg:
                    self.mines_left = 0
                    self.hellion_left = 16
                    self.research_blue_flame = True
                    self.cyclone_left = 0
                else:
                    self.mines_left = 0
                    self.hellion_left = 0
                    self.research_blue_flame = False
                    self.cyclone_left = 5
                self.max_thor = 4
                self.maxmedivacs = 4
                self.max_viking = 1  # build this amount of vikings before enemy air unts have been seen
                self.raven_left = 100
                self.banshee_left = 0
                self.liberator_left = 0
                self.max_BC = 100
                self.assault_enemy_home = False
                self.build_extra_factories = False
                self.build_extra_starports = True
            elif self.strategy == 3:  # Terran Bio
                # self.priority_raven = True
                self.send_flanking_units = 10
                if self.enemy_race == Race.Protoss:
                    self.min_marine = 30
                    self.maxmarauder = 8
                    self.max_siege = 2
                    self.liberator_left = 0
                    self.upgrade_liberator = False
                    self.max_viking = 2
                    self.build_starportreactor = 0
                elif self.enemy_race == Race.Terran:
                    self.min_marine = 30
                    self.maxmarauder = 4
                    self.max_siege = 6
                    self.liberator_left = 6
                    self.upgrade_liberator = False
                    self.max_viking = 2
                    self.build_starportreactor = 1
                else:
                    self.min_marine = 30
                    self.maxmarauder = 4
                    self.max_siege = 6
                    self.liberator_left = 0
                    self.upgrade_liberator = False
                    self.max_viking = 1
                    self.build_starportreactor = 0
                self.build_missile_turrets = False
                self.mineral_field_turret = False
                self.agressive_marines = False
                self.scv_build_speed = 3
                self.more_depots = True
                self.first_base_saturation = 0
                self.delay_expansion = True
                self.delay_third = True
                self.supply_limit_for_third = 75
                self.fast_orbital = False
                self.refineries_in_first_base = 1
                self.refineries_in_second_base = 2
                self.fast_vespene = False
                self.limit_vespene = 4
                self.expand_for_vespene = False
                self.priority_tank = False
                self.mines_left = 0
                self.upgrade_mech = False
                self.scv_limit = 75
                self.send_scout = False
                self.greedy_scv_consrtuction = False
                self.cyclone_left = 0
                self.max_barracks = 4
                self.super_fast_barracks = True
                self.delay_barracs = False
                self.MaxGhost = 0
                self.maxfactory = 1
                self.max_starports = 2
                self.barracks_reactor_first = False
                self.BuildReapers = False
                self.max_marine = 100
                self.marines_last_resort = False
                self.faster_tanks = False
                self.raven_left = 100
                self.maxmedivacs = 5
                self.banshee_left = 0
                self.hellion_left = 0
                self.max_thor = 0
                self.max_BC = 6
                self.fast_engineeringbay = True
                self.build_armory = True
                self.NukesLeft = 0
                self.careful_marines = False
                self.max_engineeringbays = 1
            elif self.strategy == 4:  # Mech
                if self.enemy_race == Race.Protoss:
                    self.scan_enemy_at_4_min = True
                self.delay_expansion = False
                self.delay_third = False
                self.first_base_saturation = 0
                self.refineries_in_first_base = 2
                self.fast_vespene = True
                self.scv_limit = 80
                self.minimum_repairgroup = 2
                self.scv_build_speed = 3
                self.greedy_scv_consrtuction = True
                self.more_depots = False
                self.send_scout = True
                self.fast_orbital = True
                self.BuildReapers = False
                self.mech_build = True
                self.priority_tank = False
                self.last_phase = False
                self.fast_engineeringbay = True
                self.fast_armory = True
                self.min_marine = 4  # try keep this amount of marines
                self.max_marine = 4  # absolute maximum
                self.marines_last_resort = True
                self.maxmarauder = 0
                self.MaxGhost = 0
                self.hellion_left = 100
                self.morph_to_hellbats = True
                self.research_blue_flame = True
                self.upgrade_marine = False
                self.research_stimpack = False
                self.max_barracks = 1
                self.build_barracks_addons = False
                self.barracks_reactor_first = True
                self.delay_barracs = False
                self.maxfactory = 4
                self.priority_factoty_reactor = False
                self.max_starports = 1
                self.build_starportreactor = 1
                self.careful_marines = False
                self.banshee_left = 0
                self.max_viking = 3  # build this amount of vikings before enemy air unts have been seen
                self.liberator_left = 2
                self.upgrade_liberator = False
                self.raven_left = 0
                self.maxmedivacs = 1
                self.mines_left = 2
                self.activate_all_mines = True
                self.max_siege = 8
                self.faster_tanks = True
                self.agressive_tanks = True
                self.cyclone_left = 10
                self.max_thor = 100
                self.flanking_thors = True
                self.min_thors_to_attack = 1
                self.max_BC = 0
                self.build_extra_factories = True
                self.build_extra_starports = False
            elif self.strategy == 5:  # Air superiority
                self.cc_first = True
                self.take_third_first = False
                self.expand_for_vespene = True
                self.expand_fast_for_vespene = True
                self.priority_raven = False
                self.send_scout = False
                self.super_greed = False
                self.greedy_scv_consrtuction = False
                self.priority_tank = False
                self.refineries_in_first_base = 1
                self.fast_vespene = False
                self.first_base_saturation = 0
                self.greedy_third = False
                self.fast_orbital = True
                self.scv_limit = 80
                self.scv_build_speed = 2
                self.more_depots = False
                self.research_stimpack = False
                self.research_combatshield = False
                self.research_concussiveshels = False
                self.build_barracks_addons = False
                self.max_barracks = 1
                self.barracks_reactor_first = True
                self.build_barracks_reactors = True
                self.build_starportreactor = 1
                self.viking_priority = True
                self.maxmarauder = 0
                self.hellion_left = 2
                self.max_siege = 2
                self.min_marine = 30  # try keep this amount of marines
                self.max_marine = 30
                self.max_viking = 0  # build this amount of vikings before enemy air unts have been seen
                self.liberator_left = 0
                self.maxmedivacs = 0
                self.banshee_left = 20
                self.dual_liberator = True
                self.cyclone_left = 2
                self.upgrade_banshee_cloak = True  # researsh banshee cloak and hyper rotors. delays  banshee production
                self.upgrade_banshee_speed = True  # researsh banshee cloak and hyper rotors. delays  banshee production
                self.upgrade_liberator = True
                self.max_starports = 4
                self.max_BC = 6
                self.raven_left = 0
                self.mines_left = 0
                self.upgrade_vehicle_weapons = False
                self.max_thor = 0
                self.faster_tanks = True  # added this to defense against Jensiibot
                self.upgrade_marine = False
                self.maxfactory = 1
                self.last_phase = False
                self.max_engineeringbays = 1
                self.fast_engineeringbay = True
                self.fast_armory = False
                self.build_missile_turrets = False
                self.MaxGhost = 0
                self.NukesLeft = 0
                self.build_extra_factories = False
                self.build_extra_starports = True
            elif self.strategy == 6:  # Nuke rain
                self.greedy_scv_consrtuction = True
                self.scv_limit = 80
                self.cc_first = True
                self.BuildReapers = True
                self.reaper_haras = False
                self.scv_build_speed = 2
                self.send_scout = True
                self.first_base_saturation = 0
                self.refineries_in_first_base = 2
                self.refineries_in_second_base = 3
                self.fast_vespene = True
                self.limit_vespene = 0
                self.priority_tank = False
                self.fast_engineeringbay = False
                self.build_armory = False
                self.upgrade_mech = False
                self.fast_orbital = True
                self.raven_left = 100
                self.expand_for_vespene = False
                self.max_barracks = 2
                self.delay_barracs = True
                self.maxfactory = 1
                self.max_starports = 1
                self.build_starportreactor = 0
                self.maxmedivacs = 5
                self.banshee_left = 6
                self.upgrade_banshee_cloak = True  # researsh banshee cloak and hyper rotors. delays  banshee production
                self.upgrade_banshee_speed = True
                self.max_siege = 0
                self.min_marine = 10  # try keep this amount of marines
                self.max_marine = 100
                self.bunker_in_natural = 1
                self.maxmarauder = 2
                self.MaxGhost = 3
                self.mines_left = 4
                self.cyclone_left = 10
                self.hellion_left = 4
                self.research_blue_flame = False
                self.NukesLeft = 100
                self.nuke_rush = True
                self.nuke_enemy_home = True
                self.barracks_reactor_first = True
                self.max_thor = 10
                self.assault_enemy_home = False
                self.max_BC = 10
                self.max_viking = 2  # build this amount of vikings before enemy air unts have been seen
            elif self.strategy == 7:  # Ghost
                self.scv_limit = 90
                self.scv_build_speed = 3
                self.more_depots = True
                self.send_scout = True
                self.first_base_saturation = 0
                self.refineries_in_first_base = 2
                self.BuildReapers = False
                self.priority_tank = False
                self.maxfactory = 1
                self.max_starports = 1
                self.max_viking = 1  # build this amount of vikings before enemy air unts have been seen
                self.raven_left = 100
                self.maxmedivacs = 5
                self.banshee_left = 0
                self.max_BC = 0
                self.mines_left = 3
                self.max_siege = 4
                self.min_marine = 10  # try keep this amount of marines
                self.max_marine = 30
                self.maxmarauder = 20
                self.max_thor = 20
                self.max_barracks = 3
                self.fast_engineeringbay = False
                self.barracks_reactor_first = True
                self.priority_factoty_reactor = False
                self.hellion_left = 0
                self.research_blue_flame = False
                self.MaxGhost = 6
                self.upgrade_marine = True
                self.research_combatshield = True
                self.build_barracks_reactors = False
                self.cyclone_left = 1
                self.expand_for_vespene = True
                self.NukesLeft = 0
                self.nuke_enemy_home = False
                self.build_extra_factories = True
                self.build_extra_starports = False
            elif self.strategy == 8:  # marine drop
                self.first_base_saturation = 0
                self.scv_build_speed = 3
                self.greedy_scv_consrtuction = True
                self.fast_engineeringbay = False
                self.max_barracks = 2
                self.barracks_reactor_first = True
                self.min_marine = 8
                self.max_marine = 50
                self.research_stimpack = True
                self.upgrade_marine = False
                self.maxmarauder = 10
                self.MaxGhost = 0
                self.hellion_left = 0
                self.max_siege = 6
                self.max_thor = 4
                self.liberator_left = 8
                self.upgrade_liberator = True
                self.max_BC = 4
                self.delay_barracs = False
                self.marine_drop = True
                self.fast_orbital = False
                self.expand_for_vespene = False
                self.maxfactory = 2
                self.faster_tanks = True
                self.max_starports = 2
                self.build_starportreactor = 1
                self.mines_left = 0
                self.cyclone_left = 0
                self.banshee_left = 0
                self.upgrade_banshee_cloak = False
                self.upgrade_banshee_speed = False
                self.max_viking = 4  # build this amount of vikings before enemy air unts have been seen
            elif self.strategy == 9:  # test
                self.build_cc_home = True
                self.scv_limit = 80
                self.scv_build_speed = 3
                self.greedy_scv_consrtuction = False
                self.first_base_saturation = 4
                self.refineries_in_first_base = 2
                self.refineries_in_second_base = 4
                self.greedy_third = True
                self.delay_third = False
                self.supply_limit_for_third = 100
                self.fast_vespene = True
                self.build_priority_cyclone = True
                self.raven_left = 100
                self.barracks_reactor_first = False
                self.delay_barracs = True
                self.max_barracks = 3
                self.super_fast_barracks = False
                self.maxfactory = 1
                self.max_starports = 1
                self.build_starportreactor = 1
                self.min_marine = 4  # try keep this amount of marines
                self.max_marine = 100
                self.maxmarauder = 4
                self.MaxGhost = 0
                self.hellion_left = 0
                self.research_blue_flame = False
                self.cyclone_left = 10
                self.max_thor = 4
                self.max_BC = 5
                self.expand_for_vespene = True
                self.limit_vespene = 0
                self.marines_last_resort = False
                self.fast_orbital = True
                self.fast_engineeringbay = False
                self.build_missile_turrets = False
                self.mineral_field_turret = False
                self.mines_left = 0
                self.banshee_left = 0
                self.upgrade_banshee_cloak = False
                self.upgrade_banshee_speed = False
                self.max_viking = 0  # build this amount of vikings before enemy air unts have been seen
                self.liberator_left = 10
                self.upgrade_liberator = True
                self.maxmedivacs = 1
                self.BuildReapers = False
                self.upgrade_marine = False
                self.research_stimpack = False
                self.minimum_repairgroup = 2
                self.react_to_enemy_air = False
                self.max_siege = 0
                self.priority_tank = False
                self.siege_behind_wall = False
            elif self.strategy == 10:  # No starport
                self.first_base_saturation = 0
                self.bunker_in_natural = 1
                self.refineries_in_first_base = 1  # note: refineries slow down first expansion!
                self.refineries_in_second_base = 4
                self.scv_limit = 80  # 60
                self.scv_build_speed = 1
                self.greedy_scv_consrtuction = True
                self.BuildReapers = False
                self.MaxGhost = 0
                self.NukesLeft = 0  # max 10. If used 11 or more changes many variables
                self.raven_left = 100
                self.mines_left = 0
                self.aggressive_mines = False
                self.leapfrog_mines = False
                self.cyclone_left = 10
                self.liberator_left = 0
                self.hellion_left = 0
                self.research_blue_flame = False  # upgrades infernaligniter.
                self.banshee_left = 0
                self.upgrade_banshee_cloak = False
                self.upgrade_banshee_speed = False
                self.min_marine = 8  # try keep this amount of marines
                self.max_marine = 36
                self.research_combatshield = False
                self.marine_drop = False
                self.marines_last_resort = False
                self.max_thor = 30
                self.max_BC = 0
                self.max_viking = 0
                self.react_to_enemy_air = False  # increases max_viking to 16 if air units detected
                self.max_siege = 16
                self.faster_tanks = True
                self.max_barracks = 2  # maxamount of barracks
                self.delay_barracs = True  # makes only one barracks until starport ready
                self.barracks_reactor_first = False
                self.super_fast_barracks = False
                self.maxfactory = 3
                self.max_starports = 0
                self.build_starportreactor = 0
                self.max_engineeringbays = 1
                self.fast_engineeringbay = False
                self.build_armory = True
                self.maxmarauder = 10
                self.assault_enemy_home = True
                self.careful_marines = False
                self.agressive_marines = False
                self.build_missile_turrets = False
                self.mineral_field_turret = False
                self.mech_build = False
                self.min_thors_to_attack = 4
                self.expand_for_vespene = True
                self.fast_vespene = False
                self.fast_orbital = True  # slow orbital makes first OC after first expansion is pending
                self.upgrade_marine = True
                self.upgrade_marine_defence_and_mech_attack = False
                self.upgrade_mech = True
                self.upgrade_vehicle_weapons = True
                self.maxmedivacs = 0
                self.build_cc_home = False
                self.priority_tank = True
                self.siege_behind_wall = False
                self.priority_tank_pos = None
                self.build_priority_cyclone = False
                self.limit_vespene = 0
                self.minimum_repairgroup = 1
                self.nuke_enemy_home = False
                self.activate_all_mines = False
                self.scan_cloaked_enemies = False
                self.more_depots = False
                self.delay_expansion = False
                self.delay_third = False
                self.priority_factoty_reactor = False
                self.nuke_rush = False
                self.build_barracks_reactors = True
                self.send_scout = True
                self.delay_factory = False
                self.debug_next_building = None
                self.build_extra_factories = True
                self.build_extra_starports = False
            elif self.strategy == 11:  # Marauders
                self.marauder_push_limit = 10
                self.build_cc_home = False  # for testing only!
                self.delay_expansion = False
                self.delay_third = False
                self.supply_limit_for_third = 50
                self.upgrade_liberator = True
                self.first_base_saturation = 2
                self.fast_vespene = False
                self.refineries_in_first_base = 1  # note: refineries slow down first expansion!
                self.refineries_in_second_base = 4
                self.limit_vespene = 6
                self.scv_limit = 80
                self.scv_build_speed = 2
                self.greedy_scv_consrtuction = True
                self.BuildReapers = False
                self.MaxGhost = 0
                self.raven_left = 100
                self.mines_left = 0
                self.aggressive_mines = False
                self.leapfrog_mines = False
                self.cyclone_left = 0
                self.hellion_left = 0
                self.banshee_left = 0
                self.upgrade_banshee_cloak = False
                self.upgrade_banshee_speed = False
                self.min_marine = 0  # try keep this amount of marines
                self.max_marine = 30
                self.marine_drop = False
                self.marines_last_resort = False
                self.max_thor = 0
                self.max_BC = 4
                self.max_viking = 12  # build this amount of vikings before enemy air unts have been seen
                self.react_to_enemy_air = False  # increases max_viking to 16 if air units detected
                self.maxmedivacs = 6
                self.dual_liberator = True
                self.liberator_left = 20
                self.max_siege = 2
                self.max_barracks = 3  # maxamount of barracks
                self.super_fast_barracks = True
                self.barracks_reactor_first = False
                self.delay_barracs = False
                self.maxfactory = 1
                self.delay_factory = True
                self.max_starports = 2
                self.build_starportreactor = 2
                self.max_engineeringbays = 2
                self.build_armory = False
                self.upgrade_mech = False
                self.fast_engineeringbay = False
                self.maxmarauder = 10
                self.build_barracks_reactors = False
                self.assault_enemy_home = True
                self.careful_marines = True
                self.build_missile_turrets = False
                self.mineral_field_turret = False
                self.NukesLeft = 0  # max 10. If used 11 or more changes many variables
                self.mech_build = False
                self.expand_for_vespene = False
                self.fast_orbital = True  # slow orbital makes first OC after first expansion is pending
                self.research_stimpack = True
                self.research_combatshield = False
                self.upgrade_marine = True
                self.upgrade_marine_defence_and_mech_attack = False
                self.upgrade_vehicle_weapons = True
                self.priority_tank = False
                self.siege_behind_wall = False
                self.build_extra_factories = False
                self.build_extra_starports = True
            elif self.strategy == 12:  # 1-1-1 slow expand
                self.marauder_push_limit = 0
                self.build_cc_home = False
                self.delay_expansion = False
                self.delay_third = False
                self.supply_limit_for_third = 50
                self.upgrade_liberator = True
                self.research_servos = False
                self.first_base_saturation = 4
                self.fast_vespene = False
                self.refineries_in_first_base = 2  # note: refineries slow down first expansion!
                self.refineries_in_second_base = 4
                self.limit_vespene = 0
                self.scv_limit = 80
                self.scv_build_speed = 2
                self.greedy_scv_consrtuction = True
                self.BuildReapers = False
                self.MaxGhost = 0
                self.raven_left = 0
                self.scan_cloaked_enemies = True
                self.mines_left = 0
                self.aggressive_mines = False
                self.leapfrog_mines = False
                self.cyclone_left = 0
                self.hellion_left = 0
                self.banshee_left = 0
                self.upgrade_banshee_cloak = False
                self.upgrade_banshee_speed = False
                self.min_marine = 100  # try keep this amount of marines
                self.max_marine = 100
                self.marine_drop = False
                self.marines_last_resort = False
                self.max_thor = 2
                self.max_BC = 100
                self.max_viking = 1  # build this amount of vikings before enemy air unts have been seen
                self.maxmedivacs = 0
                self.liberator_left = 25
                self.liberator_priority = True
                self.max_siege = 8
                self.max_barracks = 1  # maxamount of barracks
                self.super_fast_barracks = False
                self.barracks_reactor_first = True
                self.delay_barracs = False
                self.maxfactory = 1
                self.delay_factory = False
                self.max_starports = 1
                self.build_starportreactor = 2
                self.max_engineeringbays = 1
                self.build_armory = True
                self.fast_armory = True
                self.upgrade_mech = True
                self.fast_engineeringbay = False
                self.maxmarauder = 0
                self.build_barracks_reactors = True
                self.assault_enemy_home = True
                self.careful_marines = False
                self.build_missile_turrets = False
                self.mineral_field_turret = True
                self.NukesLeft = 0  # max 10. If used 11 or more changes many variables
                self.mech_build = False
                self.expand_for_vespene = True
                self.fast_orbital = True  # slow orbital makes first OC after first expansion is pending
                self.research_stimpack = False
                self.research_combatshield = False
                self.upgrade_marine = False
                self.research_concussiveshels = False
                self.upgrade_marine_defence_and_mech_attack = False
                self.upgrade_vehicle_weapons = True
                self.priority_tank = False
                self.siege_behind_wall = True
                self.build_extra_factories = False
                self.build_extra_starports = True
            elif self.strategy == 13:  # Minefields
                self.marauder_push_limit = 0
                self.build_cc_home = False
                self.delay_expansion = False
                self.delay_third = False
                self.supply_limit_for_third = 50
                self.upgrade_liberator = False
                self.first_base_saturation = 0
                self.fast_vespene = True
                self.refineries_in_first_base = 1  # note: refineries slow down first expansion!
                self.refineries_in_second_base = 4
                self.limit_vespene = 0
                self.scv_limit = 80
                self.scv_build_speed = 3
                self.more_depots = True
                self.greedy_scv_consrtuction = False
                self.BuildReapers = True
                self.MaxGhost = 0
                self.raven_left = 100
                self.mines_left = 100
                self.aggressive_mines = False
                self.leapfrog_mines = True
                self.cyclone_left = 0
                self.hellion_left = 0
                self.banshee_left = 0
                self.upgrade_banshee_cloak = False
                self.upgrade_banshee_speed = False
                self.min_marine = 20  # try keep this amount of marines
                self.max_marine = 20
                self.marine_drop = False
                self.marines_last_resort = False
                self.max_thor = 100
                self.flanking_thors = True
                self.max_BC = 0
                self.max_viking = 4  # build this amount of vikings before enemy air unts have been seen
                self.react_to_enemy_air = False
                self.maxmedivacs = 0
                self.liberator_left = 0
                self.max_siege = 0
                self.max_barracks = 1  # maxamount of barracks
                self.super_fast_barracks = False
                self.barracks_reactor_first = True
                self.delay_barracs = False
                self.maxfactory = 3
                self.delay_factory = False
                self.max_starports = 1
                self.delay_starport = True
                self.build_starportreactor = 1
                self.max_engineeringbays = 1
                self.build_armory = True
                self.upgrade_mech = True
                self.fast_engineeringbay = False
                self.maxmarauder = 0
                self.build_barracks_reactors = True
                self.assault_enemy_home = True
                self.careful_marines = False
                self.build_missile_turrets = False
                self.mineral_field_turret = True
                self.NukesLeft = 0  # max 10. If used 11 or more changes many variables
                self.mech_build = False
                self.expand_for_vespene = True
                self.fast_orbital = True  # slow orbital makes first OC after first expansion is pending
                self.research_stimpack = False
                self.research_combatshield = False
                self.upgrade_marine = False
                self.research_concussiveshels = False
                self.upgrade_marine_defence_and_mech_attack = False
                self.upgrade_vehicle_weapons = True
                self.priority_tank = False
                self.siege_behind_wall = False
                self.build_extra_factories = True
                self.build_extra_starports = False
            elif self.strategy == 14:  # MCV
                self.marauder_push_limit = 0
                self.build_cc_home = False
                self.delay_expansion = False
                self.delay_third = False
                self.take_third_first = False
                self.supply_limit_for_third = 50
                self.upgrade_liberator = False
                self.first_base_saturation = -10
                self.fast_vespene = True
                self.refineries_in_first_base = 1  # note: refineries slow down first expansion!
                self.refineries_in_second_base = 2
                self.limit_vespene = 0
                self.scv_limit = 90
                self.scv_build_speed = 3
                self.scan_cloaked_enemies = True
                self.send_scout = False
                self.greedy_scv_consrtuction = True
                self.BuildReapers = True
                self.MaxGhost = 0
                self.raven_left = 100
                self.priority_raven = False
                self.mines_left = 0
                self.aggressive_mines = False
                self.leapfrog_mines = True
                self.cyclone_left = 2000
                self.build_priority_cyclone = False
                self.banshee_left = 0
                self.upgrade_banshee_cloak = False
                self.upgrade_banshee_speed = False
                self.min_marine = 100  # try keep this amount of marines
                self.max_marine = 100
                self.marine_drop = False
                self.marines_last_resort = False
                self.max_thor = 4
                self.max_BC = 0
                self.max_viking = 6  # build this amount of vikings before enemy air unts have been seen
                self.react_to_enemy_air = False  # increases max_viking to 16 if air units detected
                self.maxmedivacs = 0
                self.liberator_left = 0
                self.max_siege = 0
                self.max_barracks = 1  # maxamount of barracks
                self.build_barracks_addons = False
                self.super_fast_barracks = False
                self.barracks_reactor_first = False
                self.delay_barracs = False
                self.maxfactory = 3
                self.delay_factory = False
                if self.enemy_race == Race.Protoss:
                    self.max_starports = 2
                    self.build_starportreactor = 1
                    self.hellion_left = 10
                    self.morph_to_hellbats = True
                else:
                    self.max_starports = 1
                    self.build_starportreactor = 0
                    self.hellion_left = 0
                    self.morph_to_hellbats = False
                self.build_starportreactor = 0
                self.max_engineeringbays = 1
                self.build_armory = True
                self.fast_armory = False
                self.upgrade_mech = True
                self.fast_engineeringbay = True
                self.maxmarauder = 0
                self.build_barracks_reactors = True
                self.assault_enemy_home = False
                self.careful_marines = False
                self.build_missile_turrets = False
                self.mineral_field_turret = True
                self.NukesLeft = 0  # max 10. If used 11 or more changes many variables
                self.mech_build = False
                self.expand_for_vespene = True
                self.expand_fast_for_vespene = True
                self.fast_orbital = True  # slow orbital makes first OC after first expansion is pending
                self.research_stimpack = False
                self.research_combatshield = False
                self.upgrade_marine = False
                self.research_concussiveshels = False
                self.upgrade_marine_defence_and_mech_attack = False
                self.upgrade_vehicle_weapons = True
                self.priority_tank = False
                self.siege_behind_wall = False
                self.build_extra_factories = True
                self.build_extra_starports = False
            elif self.strategy == 15:  # cc first:
                self.more_depots = True
                self.send_scout = False
                self.cc_first = True
                self.delay_third = True
                self.supply_limit_for_third = 150
                self.fast_vespene = True
                self.scv_build_speed = 2
                self.scv_limit = 80
                self.greedy_scv_consrtuction = False
                self.fast_engineeringbay = False
                self.refineries_in_first_base = 0
                self.refineries_in_second_base = 4
                self.greedy_third = False
                self.max_barracks = 4
                self.super_fast_barracks = False
                self.delay_barracs = True
                self.barracks_reactor_first = True
                self.min_marine = 20
                self.max_marine = 60
                self.careful_marines = False
                self.maxmarauder = 20
                self.MaxGhost = 0
                self.maxfactory = 1
                self.mines_left = 0
                self.hellion_left = 0
                self.activate_all_mines = True
                self.aggressive_mines = True
                self.max_siege = 6
                self.max_starports = 2
                self.build_starportreactor = 1
                self.max_viking = 8
                self.maxmedivacs = 6
                self.dual_liberator = True
                self.banshee_left = 0

        if self.iteraatio == 25 and self.chat:
            # await self._client.chat_send("InsANIty. Friends call me ANI. 3.12.2020", team_only=False)
            await self._client.chat_send("ANI 11.12.2020. GLHF.", team_only=False)
        if self.iteraatio == 50:
            if self.strategy == 1:
                if self.chat:
                    await self._client.chat_send("Greed", team_only=False)
                print("Strat: Greed")
            elif self.strategy == 2:
                if self.chat:
                    await self._client.chat_send("Strategy: 2 base push", team_only=False)
                print("Strat: 2 base push")
            elif self.strategy == 3:
                if self.chat:
                    await self._client.chat_send("Strategy: Terran Bio", team_only=False)
                print("Strat: Terran Bio")
            elif self.strategy == 4:
                if self.chat:
                    await self._client.chat_send("Strategy: Mech build", team_only=False)
                print("Strat: Mech build")
            elif self.strategy == 5:
                if self.chat:
                    await self._client.chat_send("Strategy: Air superiority. ", team_only=False)
                    await self._client.chat_send("Thank you EladYaniv01 for MapAnalyzer. ", team_only=False)
                print("Strat: Air superiority")
            elif self.strategy == 6:
                if self.chat:
                    await self._client.chat_send("Strategy: Nuke", team_only=False)
                print("Strat: Nuke")
            elif self.strategy == 7:
                if self.chat:
                    await self._client.chat_send("Strategy: Ghost", team_only=False)
                print("Strat: Ghost")
            elif self.strategy == 8:
                if self.chat:
                    await self._client.chat_send("Strategy: Marine drop", team_only=False)
                print("Strat: Marine drop")
            elif self.strategy == 9:
                if self.chat:
                    await self._client.chat_send("Strategy: test", team_only=False)
                print("Strat: test")
            elif self.strategy == 10:
                if self.chat:
                    await self._client.chat_send("Strategy: No starport", team_only=False)
                print("Strat: No starport")
            elif self.strategy == 11:
                if self.chat:
                    await self._client.chat_send("Strategy: Marauders", team_only=False)
                print("Strat: Marauders")
            elif self.strategy == 12:
                if self.chat:
                    await self._client.chat_send("Strategy: 1-1-1 slow expand", team_only=False)
                print("Strat: 1-1-1 slow expand")
            elif self.strategy == 13:
                if self.chat:
                    await self._client.chat_send("Strategy: Minefields", team_only=False)
                print("Strat: Minefields")
            elif self.strategy == 14:
                if self.chat:
                    await self._client.chat_send("Strategy: MCV", team_only=False)
                print("Strat: MCV")
            elif self.strategy == 15:
                if self.chat:
                    await self._client.chat_send("Strategy: cc first", team_only=False)
                print("Strat: cc first")

        self.save_units_on_cooldown()
        self.iteraatio += 1

    async def ghost_nuke_spotter_micro(self, ghost):
        if not self.enemy_structures.closer_than(2, self.nuke_target):
            self.nuke_target = None
            self.nuke_spotter_tag = None
            return
        if self.nuke_target and self.is_visible(self.nuke_target.position) and ghost.distance_to(
                self.nuke_target.position) < 15:
            self.do(ghost(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, self.nuke_target.position, queue=False))
            print("NUKE")
            return
        if ghost.health_percentage < 1 or ghost.energy < 15:
            self.do(ghost.move(self.homeBase.position))
            self.nuke_target = None
            self.nuke_spotter_tag = None
            self.nuke_spotter_last_alive_spot = ghost.position
            return
        if await self.can_cast(ghost, AbilityId.BEHAVIOR_CLOAKON_GHOST):
            if self.enemy_units_and_structures.filter(lambda x: x.can_attack_ground).closer_than(20, ghost):
                self.do(ghost(AbilityId.BEHAVIOR_CLOAKON_GHOST))
                return
            if ghost.distance_to(self.start_location) > (self.defence_radius * 1.33):
                self.do(ghost(AbilityId.BEHAVIOR_CLOAKON_GHOST))
                return
        target_position = self.nuke_target.random_on_distance(3)
        grid = self.map_data.get_pyastar_grid()
        for unit in self.enemy_units_in_memory:
            if unit.is_detector:
                grid = self.map_data.add_cost(position=unit.position, radius=(unit.sight_range + 2), grid=grid)
            else:
                grid = self.map_data.add_cost(position=unit.position, radius=(unit.ground_range + 2), grid=grid)
        for zone in self.sweep_zones:
            if ghost.distance_to(zone) < 15:
                self.do(ghost.move(self.homeBase.position))
                self.nuke_target = None
                self.nuke_spotter_tag = None
                self.nuke_spotter_last_alive_spot = ghost.position
                return
            grid = self.map_data.add_cost(position=zone, radius=15, grid=grid)
            print("sweep detected")
        if self.nuke_spotter_last_died_spot:
            grid = self.map_data.add_cost(position=self.nuke_spotter_last_died_spot, radius=10, grid=grid)
            print("death spot detected")
        for detector in (self.enemy_structures).filter(lambda x: x.is_detector):
            grid = self.map_data.add_cost(position=detector.position, radius=detector.sight_range + 2,
                                          grid=grid)
            # print("detector detected")
        path = self.map_data.pathfind(start=ghost.position, goal=target_position, grid=grid,
                                      allow_diagonal=True,
                                      sensitivity=1)
        # self.map_data.plot_influenced_path(start=ghost.position, goal=target_position, weight_array=grid,
        #                                    allow_diagonal=True)
        # self.map_data.show()
        if path:
            steps_to_skipp = 3
            for step in path:
                if steps_to_skipp > 0:
                    steps_to_skipp -= 1
                    continue
                else:
                    self.do(ghost.move(step, queue=False))
                    break

    async def first_base_saturated(self):
        if self.ccANDoc.ready.amount != 1:
            print("first base saturation error")
        for cc in self.ccANDoc.ready:
            if self.barracks and cc.assigned_harvesters >= (cc.ideal_harvesters + self.first_base_saturation):
                return True
        return False

    async def we_need_orbital(self):
        if not (self.barracks.ready or self.barracksflyings):
            return False
        if not self.cc.ready.idle:
            return False
        if self.already_pending(UnitTypeId.ORBITALCOMMAND):
            return False
        for cc in self.cc.ready.idle:
            if cc.health_percentage < 1:
                return False
        if self.delay_expansion:
            if self.minerals > 200:
                return True
        if self.fast_orbital:
            return True
        elif self.ccANDoc.amount > 1:
            return True
        else:
            return False

    async def is_expansions_left(self):
        if await self.get_next_expansion() is None:
            # self.limit_vespene = 0
            print("No expansions left. is_expansions_left returns False")
            return False
        else:
            return True

    async def we_should_expand(self):
        if self.marauder_push_limit != 0:
            return False
        if self.cached_we_should_expand is not None:
            return self.cached_we_should_expand
        else:
            self.cached_we_should_expand = await self.cache_we_should_expand()
            return self.cached_we_should_expand

    async def cache_we_should_expand(self):
        if self.cc_first:
            if self.ccANDoc.amount == 1 and (self.supplydepots or self.already_pending(UnitTypeId.SUPPLYDEPOT)):
                return True
            elif self.already_pending(UnitTypeId.COMMANDCENTER):
                self.cc_first = False
            return False
        if self.first_base_saturation < 0 and self.enemy_structures.closer_than(10, self.natural):
            self.first_base_saturation = 0
        if self.townhalls_flying and self.enemy_units.closer_than(self.defence_radius,
                                                                  self.start_location).amount > 3:
            if self.super_greed:
                self.super_greed = False
                self.refineries_in_second_base = 3
                if self.chat:
                    await self._client.chat_send("I'm not ready yet. Just wait 6 minutes. Ok?", team_only=False)
                if await self.is_expansions_left():
                    return True
                else:
                    return False
            print("Expansion needed, but under attack!")
            return False
        if self.greedy_third:
            if self.ccANDoc.amount >= 3:
                self.greedy_third = False
                self.more_depots = True
                return False
            if self.ccANDoc.ready.amount == 2 and not self.enemy_units:
                print("Saving minerals for greedy expansion", self.minerals)
                if await self.is_expansions_left():
                    return True
                else:
                    return False
        if self.super_greed:
            if self.enemy_structures.closer_than(self.defence_radius, self.homeBase):
                self.super_greed = False
                for cc in self.cc:
                    if self.enemy_structures.closer_than(15, cc) and \
                            await self.has_ability(AbilityId.CANCEL_BUILDINPROGRESS, cc):
                        self.do(cc(AbilityId.CANCEL_BUILDINPROGRESS))
                if self.chat:
                    await self._client.chat_send("Take your buildings to your own base! Ok?", team_only=False)
                if await self.is_expansions_left():
                    return True
                else:
                    return False
            if self.ccANDoc.amount > 2:
                self.super_greed = False
            if self.barracks:
                if await self.is_expansions_left():
                    return True
                else:
                    return False
            else:
                return False
        if not self.barracks.ready:
            if self.minerals > 400:
                if await self.is_expansions_left():
                    return True
                else:
                    return False
            else:
                return False
        if self.build_cc_home and self.ccANDoc.amount > 1:
            for cc in self.ccANDoc:
                is_in_expansion_location = False
                for expansion in self.expansion_locations_list:
                    if cc.position.distance_to(expansion) < 3:
                        is_in_expansion_location = True
                        break
                if not is_in_expansion_location:
                    return False
        if self.townhalls_flying.filter(lambda x: x.health_percentage >= 1):
            return False

        if self.doner_location:
            print("waiting for priority building")
            return False

        if await self.we_need_orbital():
            return False
        elif self.marine_drop and not self.dropship_sent:
            return False
        elif self.already_pending(UnitTypeId.COMMANDCENTER):
            return False
        elif self.delay_third and (self.ccANDoc.amount == 2):
            return False
        elif self.delay_expansion and self.ccANDoc.amount == 1:
            if self.supply_used > 50 and self.marauders:
                self.delay_expansion = False
                for unit in (self.marauders | self.marines):
                    self.add_unit_to_kamikaze_troops(unit)
                self.kamikaze_target = self.enemy_third
            return False
        else:
            if self.ccANDoc.amount == 1:
                if await self.first_base_saturated():
                    if await self.is_expansions_left():
                        return True
                    else:
                        return False
                else:
                    return False
            jobs_available = 0 - self.already_pending(UnitTypeId.SCV)
            for cc in self.ccANDoc:
                jobs_available = jobs_available + cc.ideal_harvesters - cc.assigned_harvesters
            if jobs_available > 1:
                return False
            else:
                if await self.is_expansions_left():
                    return True
                else:
                    return False
        print("Error expand")
        return False

    async def scout_offsets(self, location):
        p = location.position
        offset_distance = 8
        return [
            Point2((p.x - offset_distance, p.y - offset_distance)),
            Point2((p.x - offset_distance, p.y + offset_distance)),
            Point2((p.x + offset_distance, p.y - offset_distance)),
            Point2((p.x + offset_distance, p.y + offset_distance)),
        ]

    async def scout_points(self):
        enemy_home_scout_points = await self.scout_offsets(self.enemy_start_location)
        return [
            self.natural,
            self.enemy_natural.towards(self.game_info.map_center, 5),
            enemy_home_scout_points[0],
            enemy_home_scout_points[1],
            enemy_home_scout_points[3],
            enemy_home_scout_points[2],
            self.enemy_natural.towards(self.game_info.map_center, 5),
            self.natural,
        ]

    async def search_for_proxy(self, unit):
        possible_proxy_locations = sorted(self.expansion_locations_list,
                                          key=lambda p: p.distance_to(self.start_location), reverse=False)
        self.do(unit.move(possible_proxy_locations[3], queue=True))
        self.do(unit.move(possible_proxy_locations[2], queue=True))
        self.do(unit.move(possible_proxy_locations[1], queue=True))

    async def cashe_effects(self):
        efektit = self.state.effects
        self.enemy_liberation_zone = []
        for effect in efektit:
            if effect.id in [EffectId.SCANNERSWEEP]:
                self.sweep_timer = 20
                for position in effect.positions:
                    if not position in self.sweep_zones:
                        self.sweep_zones.append(position)
            if effect.id in [EffectId.NUKEPERSISTENT]:
                self.nuke_timer = 10
                self.fallout_zone = []
        self.storm_zone = []
        self.bile_positions = []
        for effect in efektit:
            if effect.id in [EffectId.RAVAGERCORROSIVEBILECP]:
                for position in effect.positions:
                    self.bile_positions.append(position)
            if effect.id in [EffectId.NUKEPERSISTENT]:
                for position in effect.positions:
                    self.fallout_zone.append(position)
            if effect.id in [EffectId.PSISTORMPERSISTENT]:
                for position in effect.positions:
                    self.storm_zone.append(position)
            if effect.id in [EffectId.LIBERATORTARGETMORPHPERSISTENT]:
                if effect.is_enemy:
                    for position in effect.positions:
                        self.enemy_liberation_zone.append(position)
                        print("Enemy liberation zone detected at point:", position)
        if self.nuke_timer <= 0:
            self.fallout_zone = []
        if self.sweep_timer == 0:
            self.sweep_zones = []
        self.sweep_timer -= 1

    async def avoid_enemy_siegetanks(self, unit):
        if self.enemy_units.of_type(UnitTypeId.NOVA):
            nova = self.enemy_units.of_type(UnitTypeId.NOVA).closest_to(unit)
            if unit.distance_to(nova) < 6:
                self.do(unit.move(unit.position.towards(nova, -10)))
                return True
        if self.enemy_units.of_type(UnitTypeId.SIEGETANKSIEGED).amount > 1:
            enemy_tank = self.enemy_units.of_type(UnitTypeId.SIEGETANKSIEGED).closest_to(unit)
            if unit.distance_to(enemy_tank) < 17:
                self.do(unit.move(unit.position.towards(enemy_tank, -10)))
                return True
            else:
                return False
        return False

    async def build_bunker_to_next_expansion(self, unit):
        if self.barracks.ready:  # This makes bunker
            bunker_location = await self.get_next_expansion()
            if bunker_location != None:
                if self.can_afford(BUNKER):
                    bunker_location = bunker_location.towards(self.game_info.map_center, 8).random_on_distance(
                        2)
                    await self.build(BUNKER, near=bunker_location.position,
                                     build_worker=self.select_contractor(bunker_location))
                    print("building bunker")
                return False
        return True

    async def build_bunker_to_natural(self):
        bunker_amount = self.bunker_in_natural
        if self.bunkers.amount >= bunker_amount:
            self.bunker_in_natural = 0
        if self.already_pending(UnitTypeId.BUNKER):
            return True
        bunker_location = self.natural.towards(self.game_info.map_center, 7).random_on_distance(2)
        if self.barracks.ready and self.marines and self.bunkers.amount < bunker_amount:
            if bunker_location != None:
                if self.can_afford(BUNKER):
                    await self.build(BUNKER, near=bunker_location,
                                     build_worker=self.select_contractor(bunker_location))
                    print("building bunker")
                return False
        return True

    async def avoid_bile(self, unit):
        for position in self.bile_positions:
            if unit.distance_to(position) < 4:
                ##                print("Avoid NUKE")
                if self.enemy_units_on_ground:
                    self.do(unit.move(unit.position.towards(self.enemy_units_on_ground.closest_to(unit), -10)))
                    return True
                self.do(unit.move(self.homeBase.position))
                return True

    async def avoid_storms(self, unit):
        for position in self.storm_zone:
            if unit.distance_to(position) < 10:
                if self.enemy_units.closer_than(10, unit):
                    closest_enemy = self.enemy_units.closest_to(unit)
                    self.do(unit.move(unit.position.towards(closest_enemy, -5)))
                    return True
                self.do(unit.move(unit.position.towards(position, -5)))
                return True
        return False

    async def avoid_own_nuke(self, unit):
        if not self.fallout_zone:
            return False

        for position in self.fallout_zone:
            if unit.distance_to(position) < 11:
                ##                print("Avoid NUKE")
                self.do(unit.move(self.homeBase.position))
                return True
        return False

    async def avoid_liberation_zones(self, unit):
        if not self.enemy_liberation_zone:
            return False

        for position in self.enemy_liberation_zone:
            if unit.distance_to(position) < 6:
                self.do(unit.move(unit.position.towards(position, -3)))
                return True
        return False

    async def get_waypoint_for_dropship(self):
        wayPoints = await self.neighbors4(self.enemy_start_location, distance=40)
        wayPoints = sorted(wayPoints, key=lambda x: x.distance_to(self.game_info.map_center))
        if wayPoints[0].distance_to(self.enemy_natural) < wayPoints[1].distance_to(self.enemy_natural):
            return wayPoints[1]
        else:
            return wayPoints[0]

    # stolen from mass_reaper.py
    async def neighbors4(self, position, distance=1):
        p = position
        d = distance
        return [
            Point2((p.x - d, p.y)),
            Point2((p.x + d, p.y)),
            Point2((p.x, p.y - d)),
            Point2((p.x, p.y + d)),
        ]

        "build barracks, barracks reactor and factory"

    async def build_priority_cyclones(self):
        if self.cyclone_left == 0:
            self.build_priority_cyclone = False
            self.doner_location = None
            return True
        # wait for barracks to be ready
        if not self.barracks.ready and not self.barracksflyings:
            return True

        # if not self.reapers and not self.marauders and not self.already_pending(UnitTypeId.REAPER):
        #     for barracks in self.barracks.idle:
        #         self.do(barracks.train(UnitTypeId.REAPER))
        #     return False

        # elif self.marines.amount < 1 and not self.already_pending(MARINE):
        #     for barracks in self.barracks.idle:
        #         self.do(barracks.train(MARINE))
        #     return False

        # if self.minerals > 300 and not self.already_pending(SUPPLYDEPOT) and self.supplydepots.amount == 1:
        #     expand = random.choice(self.supplydepots)
        #     await self.build(SUPPLYDEPOT, near=expand.position.random_on_distance(10),
        #                      build_worker=self.select_contractor(expand))
        #     print("Building priority supplydepot")
        #     return False

        "build factory"
        if ((not self.factories and not self.factoriesflying)
                and not self.already_pending(UnitTypeId.FACTORY)
                and (self.barracks.ready.exists or self.barracksflyings)):
            if self.can_afford(UnitTypeId.FACTORY):
                if self.doner_location and await self.can_place(UnitTypeId.FACTORY, self.doner_location):
                    await self.build(UnitTypeId.FACTORY, self.doner_location)
                    return False
                await self.build_for_me(UnitTypeId.FACTORY)
            return False

        """Build techlab"""
        if (not self.structures(TECHLAB)
                and not self.structures(FACTORYTECHLAB)
                and not self.structures(BARRACKSTECHLAB)
                and not self.already_pending(BARRACKSTECHLAB)):
            if self.can_afford(BARRACKSTECHLAB):
                for barracks in self.barracks:
                    addonlocation = barracks.position.offset((2.5, -0.5))
                    if await self.can_place(SUPPLYDEPOT, addonlocation):
                        self.do(barracks.build(BARRACKSTECHLAB))
                    else:
                        self.do(barracks(LIFT))
                        print("Reason for lift: No room for addon.")
            return False

        if (self.structures(BARRACKSTECHLAB).ready
                and not self.structures(FACTORYTECHLAB)
                and not self.structures(TECHLAB)
                and not self.doner_location):
            for barracks in self.barracks.ready.idle:
                for lab in self.structures(BARRACKSTECHLAB).ready:
                    if barracks.add_on_tag == lab.tag:
                        self.doner_location = barracks.position
                        self.do(barracks(LIFT))
                        print("Reason for lift: doner location for factory.")
                        return False

        "move factory to techlab"
        if (self.factories.ready
                and not self.structures(FACTORYTECHLAB)
                and not self.already_pending(FACTORYTECHLAB)
                and (self.doner_location or self.structures(BARRACKSTECHLAB).ready)):
            for factory in self.factories:
                self.do(factory(LIFT))
                print("Reason for lift: Moving factory to doner location.")
                if self.structures(BARRACKSTECHLAB).ready:
                    self.do(factory.move(self.barracks.closest_to(factory).position, queue=True))
            return False
        for factory in self.factoriesflying:
            self.do(factory(LAND, self.doner_location))

        if self.structures(FACTORYTECHLAB) and self.doner_location:
            self.doner_location = None

        if await self.we_should_expand():
            return True

        "build one cyclone"
        if (self.factories.ready and self.structures(FACTORYTECHLAB).ready):
            for factory in self.factories.ready.idle:
                if not self.can_feed(CYCLONE):
                    return True
                abilities = (await self.get_available_abilities(factory))
                if (self.can_afford(CYCLONE)):
                    if not TRAIN_CYCLONE in abilities:
                        return True
                    self.do(factory.train(CYCLONE))
                    print("Training priority cyclone")
                return False
        return True

    async def build_priority_factoty_reactor(self):
        # wait for barracks to be ready
        self.fast_vespene = True
        if not (self.barracks.ready or self.barracksflyings):
            return True

        elif self.marines.amount < 1 and not self.already_pending(UnitTypeId.MARINE):
            for barracks in self.barracks.idle:
                self.do(barracks.train(UnitTypeId.MARINE))
            return False

        "build factory"
        if ((not self.factories and not self.factoriesflying)
                and not self.already_pending(FACTORY)
                and (self.barracks.ready.exists or self.barracksflyings)):
            if self.can_afford(FACTORY):
                if self.doner_location and await self.can_place(FACTORY, self.doner_location):
                    await self.build(FACTORY, self.doner_location)
                    return False
                await self.build_for_me(FACTORY)
                return False

        """Build reactor"""
        if (self.barracks.ready
                and not self.structures(REACTOR)
                and not self.structures(FACTORYREACTOR)
                and not self.structures(UnitTypeId.BARRACKSREACTOR)
                and not self.already_pending(UnitTypeId.BARRACKSREACTOR)):
            if self.can_afford(UnitTypeId.BARRACKSREACTOR):
                for barracks in self.barracks:
                    addonlocation = barracks.position.offset((2.5, -0.5))
                    if await self.can_place(SUPPLYDEPOT, addonlocation):
                        self.do(barracks.build(UnitTypeId.BARRACKSREACTOR))
                    else:
                        self.do(barracks(LIFT))
                print("Reason for lift: No room for priority factory reactor.")
                if self.vespene < 50:
                    return True
                else:
                    return False

        if self.structures(UnitTypeId.BARRACKSREACTOR).ready:
            for barracks in self.barracks.ready:
                for lab in self.structures(UnitTypeId.BARRACKSREACTOR).ready:
                    if barracks.add_on_tag == lab.tag:
                        self.doner_location = barracks.position
                        self.do(barracks(LIFT))
                        print("Reason for lift: doner location for factory reactor.")
            return False

        "move factory to reactor"
        if (self.factories.ready.idle
                and self.doner_location
                and self.structures(REACTOR)):
            for factory in self.factories:
                self.do(factory(LIFT))
                print("Reason for lift: Movinh factory to factory reactor doner location.")
            return False
        for factory in self.factoriesflying:
            self.do(factory(LAND, self.doner_location))
            self.doner_location = None
            self.priority_factoty_reactor = False
        return True

    async def find_potential_construction_locations(self, location):
        p = location.position
        return [
            Point2((p.x - 7, p.y)),
            Point2((p.x + 7, p.y)),
            Point2((p.x, p.y + 5)),
            Point2((p.x, p.y - 5)),
            Point2((p.x - 7, p.y + 5)),
            Point2((p.x - 7, p.y - 5)),
            Point2((p.x + 7, p.y - 5)),
            Point2((p.x + 7, p.y + 5)),
        ]

    async def find_potential_construction_locations_in_home(self, location):
        p = location.position
        return [
            Point2((p.x - 7, p.y + 5)),
            Point2((p.x - 7, p.y - 5)),
            Point2((p.x + 5, p.y + 5)),
            Point2((p.x + 5, p.y - 5)),
        ]

    async def pathing_points(self, location):
        p = location.position
        list = []
        for a in range(-3, 4):
            for b in range(0, 2):
                list.append(Point2((p.x + a, p.y + b)))
        # print(len(list))
        return list

    async def can_have_addon_in_this_location(self, location):
        addonlocation = location.position.offset((3, 0))
        return await self.can_place(BARRACKS, addonlocation)

    async def find_placement_for_barracks(self):
        for structure in (self.barracks | self.factories | self.starports
                          | self.engineeringbays | self.armories
                          | self.ghost_academies | self.fusioncores):
            potential_construction_locations = await self.find_potential_construction_locations(structure)
            for location in potential_construction_locations:
                if (await self.can_place(UnitTypeId.BARRACKS, location)
                        and await self.can_have_addon_in_this_location(location)
                        and self.in_pathing_grid(location)
                        # and await self.building_leaves_pathing_for_units(location)
                ):
                    print("Found place for structure around existing buildings.")
                    print("location:", location)
                    self.debug_next_building = location
                    return location
        for structure in self.ccANDoc.ready:
            potential_construction_locations = await self.find_potential_construction_locations_in_home(
                structure)
            for location in potential_construction_locations:
                if (await self.can_place(BARRACKS, location) and not self.units.closer_than(3, location)
                        and await self.can_have_addon_in_this_location(location)
                        # and await self.building_leaves_pathing_for_units(location)
                ):
                    print("Found place for structure around CC.")
                    return location
        print("Did not find place for structure around existing buildings.")
        return None

    async def build_for_me(self, structure_type):
        structure_location = await self.find_placement_for_barracks()
        if not structure_location and self.supplydepots:
            expand = random.choice(self.supplydepots)
            structure_location = await self.find_placement(UnitTypeId.BARRACKS,
                                                           near=expand.position.random_on_distance(10))
            if structure_location and not await self.can_have_addon_in_this_location(structure_location):
                print("Warning: No room for add_on!")
                return
        if structure_location:
            await self.build(structure_type, structure_location,
                             build_worker=self.select_contractor(structure_location))
            print("Building", structure_type.name)

    async def build_nuke_rush(self):
        if self.already_pending(UnitTypeId.REAPER):
            self.nuke_rush = False
        if not self.barracks.ready.exists:
            return True
        if self.barracks.ready.idle and (self.marines.amount + self.already_pending(UnitTypeId.MARINE)) < 2:
            if self.can_afford(UnitTypeId.MARINE):
                self.do(self.barracks.idle.first.train(UnitTypeId.MARINE))
            return False
        if ((not self.factories and not self.factoriesflying)
                and not self.already_pending(FACTORY)
                and (self.barracks.ready.exists or self.barracksflyings)):
            if self.can_afford(FACTORY):
                if self.doner_location:
                    if await self.can_place(FACTORY, self.doner_location):
                        await self.build(FACTORY, self.doner_location)
                        self.doner_location = None
                        print("building factory in doner location")
                        return False
                await self.build_for_me(FACTORY)
            return False
        elif (not self.structures(TECHLAB)
              and not self.structures(FACTORYTECHLAB)
              and not self.structures(BARRACKSTECHLAB)
              and not self.already_pending(BARRACKSTECHLAB)):
            if self.can_afford(BARRACKSTECHLAB):
                for barracks in self.barracks.idle:
                    self.do(barracks.build(BARRACKSTECHLAB))
            return False

        elif (self.structures(BARRACKSTECHLAB)
              and (self.ghost_academies.ready.amount + self.already_pending(GHOSTACADEMY)) < 2):
            if self.can_afford(GHOSTACADEMY):
                await self.build_for_me(GHOSTACADEMY)
            return False
        for facility in self.ghost_academies.ready:
            if len(facility.orders) >= 1:
                continue
            abilities = await self.get_available_abilities(facility)
            if not self.already_pending(PERSONALCLOAKING):
                if RESEARCH_PERSONALCLOAKING in abilities:
                    if self.can_afford(RESEARCH_PERSONALCLOAKING):
                        self.do(facility(AbilityId.RESEARCH_PERSONALCLOAKING))
                return False
        if self.ghost_academies.ready:
            if not self.ghosts and not self.already_pending(UnitTypeId.GHOST):
                if self.can_afford(GHOST):
                    for br in self.barracks.ready:
                        self.do(br.train(GHOST))
                        print("Training ghost")
                return False

        for facility in self.ghost_academies.ready.idle:
            abilities = await self.get_available_abilities(facility)
            if BUILD_NUKE in abilities:
                if self.can_afford(BUILD_NUKE):
                    self.do(facility(AbilityId.BUILD_NUKE))
                    self.NukesLeft = self.NukesLeft - 1
                return False

        for academy in self.ghost_academies:
            if len(academy.orders) > 0 and academy.orders[0].ability.id in [AbilityId.BUILD_NUKE]:
                if self.already_pending(UnitTypeId.GHOST):
                    for br in self.barracks:
                        if len(br.orders) > 1:
                            break
                        if self.can_afford(UnitTypeId.REAPER):
                            self.do(br.train(UnitTypeId.REAPER))
                            if self.chat:
                                await self._client.chat_send("Nukerush preparations ready.", team_only=False)
                        return False

        return False

    async def build_priority_raven(self):
        if self.already_pending(UnitTypeId.RAVEN) or self.units(UnitTypeId.RAVEN):
            self.priority_raven = False
        if not self.barracks.ready and not self.barracksflyings:
            return True
        if ((not self.factories and not self.factoriesflying)
                and not self.already_pending(UnitTypeId.FACTORY)
                and (self.barracks.ready.exists or self.barracksflyings)):
            if self.can_afford(UnitTypeId.FACTORY):
                await self.build_for_me(UnitTypeId.FACTORY)
            return False
        if (self.structures(UnitTypeId.BARRACKSTECHLAB)
                and not self.structures(UnitTypeId.STARPORTTECHLAB)
                and self.already_pending(UnitTypeId.STARPORT)
                and not self.doner_location):
            for br in self.structures(UnitTypeId.BARRACKS).ready.idle:
                for techlab in self.structures(UnitTypeId.BARRACKSTECHLAB):
                    if br.add_on_tag == techlab.tag and len(techlab.orders) <= 0:
                        self.doner_location = br.position
                        self.do(br(AbilityId.LIFT))
                        print("Reason for lift: doner location for priority starport techlab.")
                    return False
        if self.doner_location:
            if self.starportflying.idle:
                for sp in self.starportflying.idle:
                    self.do(sp(LAND, self.doner_location))
                    return False
            if self.structures(UnitTypeId.STARPORTTECHLAB):
                self.doner_location = None
            if not self.starports and not self.starportflying and not self.already_pending(UnitTypeId.STARPORT):
                if self.factories.ready:
                    if self.can_afford(UnitTypeId.STARPORT):
                        self.refineries_in_first_base = 2
                        await self.build(UnitTypeId.STARPORT, self.doner_location,
                                         build_worker=self.select_contractor(self.doner_location))
                        print("Building priority starport")
                    return False
                else:
                    return True
            elif not self.starportflying and self.starports:
                for sp in self.starports.ready.idle:
                    if sp.add_on_tag == 0:
                        self.do(sp(LIFT))
                        print("Reason for lift: moving to starport techlab doner location.")
                        return True
        if not self.already_pending(UnitTypeId.RAVEN):
            for sp in self.starports.ready.idle:
                for addon in self.structures(UnitTypeId.STARPORTTECHLAB):
                    if sp.add_on_tag == addon.tag:
                        if self.can_afford(RAVEN) and self.can_feed(RAVEN):
                            self.do(sp.train(RAVEN))
                            print("Training raven")
                        return False
        return True

    async def build_priority_tank(self):
        if self.already_pending(UnitTypeId.SIEGETANK):
            self.priority_tank = False
            print("Priority tank code completed. continue normal game")
        # wait for barracks to be ready
        if not self.barracks.ready and not self.barracksflyings:
            return True
        if self.doner_location:
            if self.factories.closer_than(2, self.doner_location):
                self.doner_location = None
                print("Cleared doner location in priority tank")
        if self.marines.amount < 2 and not self.already_pending(UnitTypeId.MARINE) and not self.factories:
            for barracks in self.barracks.idle:
                self.do(barracks.train(UnitTypeId.MARINE))
                print("Training marine to protect priority tank production")
                return False
        if self.refineries_in_first_base < 2 and self.already_pending(FACTORY):
            self.refineries_in_first_base = 2
            print("Add more refineries to ensure gas production for tank")

        "build factory immediately after BarracksTechlab"
        if ((not self.factories and not self.factoriesflying)
                and not self.already_pending(FACTORY)
                and (self.barracks.ready.exists or self.barracksflyings)):
            if self.can_afford(FACTORY):
                if self.doner_location:
                    if await self.can_place(FACTORY, self.doner_location):
                        await self.build(FACTORY, self.doner_location)
                        print("building factory in doner location")
                        return False
                    self.doner_location = None
                await self.build_for_me(FACTORY)
                print("building factory.")
            return False

        elif (not self.structures(TECHLAB)
              and not self.structures(FACTORYTECHLAB)
              and not self.structures(BARRACKSTECHLAB)
              and not self.already_pending(BARRACKSTECHLAB)
              and not self.factories.ready):
            if self.can_afford(BARRACKSTECHLAB):
                for barracks in self.barracks.idle:
                    self.do(barracks.build(BARRACKSTECHLAB))
                    print("Building techlab with barracks for factory.")
            return False

        elif (not self.structures(TECHLAB)
              and not self.structures(FACTORYTECHLAB)
              and not self.structures(BARRACKSTECHLAB)
              and not self.already_pending(BARRACKSTECHLAB)
              and self.factories.ready
              and self.already_pending(UnitTypeId.BARRACKSREACTOR)):
            if self.can_afford(FACTORYTECHLAB):
                for factory in self.factories.idle:
                    self.do(factory.build(FACTORYTECHLAB))
                    print("Building factory techlab. Should not happend. Check code.")
            return False

        elif (not self.structures(TECHLAB)
              and not self.structures(FACTORYTECHLAB)
              and self.structures(BARRACKSTECHLAB).ready):
            for barracks in self.barracks:
                for addon in self.structures(BARRACKSTECHLAB):
                    if barracks.add_on_tag == addon.tag:
                        self.doner_location = barracks.position
                        print("Lifting barracks and assigning doner location at:", self.doner_location)
                        self.do(barracks(LIFT))
                        return False

        "move factory to techlab"
        if (self.factories.ready.idle
                and self.doner_location
                and not self.structures(FACTORYTECHLAB)
                and not self.already_pending(FACTORYTECHLAB)
                and await self.can_place(FACTORY, self.doner_location)):
            for factory in self.factories:
                self.do(factory(LIFT))
                print("Doner location found and lifting factory for transoprt.")
            return False
        for factory in self.factoriesflying.idle:
            if self.doner_location:
                if await self.can_place(FACTORY, self.doner_location):
                    self.do(factory(LAND, self.doner_location))
                    print("Land factory to doner location")
                    return False

        if self.structures(FACTORYTECHLAB) and self.doner_location:
            self.doner_location = None

        "build one priority tank"
        if (self.factories.ready.idle and self.structures(FACTORYTECHLAB).ready):
            for factory in self.factories.ready.idle:
                if not self.can_feed(SIEGETANK):
                    print("Cant feed siegetank!")
                    return True
                if (self.can_afford(SIEGETANK)):
                    self.do(factory.train(SIEGETANK))
                    print("Training priority siegetank")
                    return False
                else:
                    print("Saving money for siegetank")
                    return False
        return True

    async def manage_drop(self):
        "for 4 player map skip marinedrop"
        if self.enemy_start_location == None:
            self.marine_drop = False
            return True
        waypoint = await self.get_waypoint_for_dropship()
        drop_point = self.mineral_field.closer_than(10.0, self.enemy_start_location).center
        drop_point = drop_point.position.towards(self.enemy_start_location, -1)

        if self.supply_used >= 13 and not self.barracks.ready and self.already_pending(BARRACKS):
            return False

        "gives load order to dropship (self.load_dropship = True)"
        if ((self.marines.ready.amount) >= 7
                and not self.dropship_sent
                and not self.load_dropship
                and self.medivacs.amount >= 1):
            self.load_dropship = True

        elif ((self.enemy_units.closer_than(self.defence_radius,
                                            self.start_location).amount > 2 or self.enemy_units_on_ground.of_type(
            ROACH))
              and not self.load_dropship and not self.dropship_sent):
            self.marine_drop = False
            self.dropship_sent = False
            self.first_base_saturation = 0
            self.build_cc_home = True
            self.priority_tank = True
            self.refineries_in_first_base = 2
            self.mines_left = 0
            self.hellion_left = 0
            self.delay_starport = True
            if self.already_pending(COMMANDCENTER):
                for building in self.cc:
                    if (await self.has_ability(CANCEL_BUILDINPROGRESS, building)):
                        self.do(building(AbilityId.CANCEL_BUILDINPROGRESS))
                        print("CC cancelled")
            if self.already_pending(UnitTypeId.STARPORT):
                for building in self.starports:
                    if (await self.has_ability(CANCEL_BUILDINPROGRESS, building)):
                        self.do(building(AbilityId.CANCEL_BUILDINPROGRESS))
                        print("Starport cancelled")
            if self.already_pending(FACTORYREACTOR):
                for factory in self.factories:
                    abilities = (await self.get_available_abilities(factory))
                    if CANCEL_FACTORYADDON in abilities:
                        self.do(factory(AbilityId.CANCEL_FACTORYADDON))
                        print("Building cancelled")

            if self.chat:
                await self._client.chat_send("Abort marinedrop strategy. Go turtle.", team_only=False)

        "expand if first base saturation reached"
        if self.ccANDoc.amount == 1 and not self.already_pending(COMMANDCENTER):
            for cc in self.ccANDoc:
                if cc.assigned_harvesters >= (cc.ideal_harvesters + self.first_base_saturation):
                    if self.minerals > 400:
                        await self.expand_now_ANI()
                    else:
                        return False

        "upgrade to orbital"
        if (self.barracks.ready and self.cc.ready.idle and self.ccANDoc.amount > 1):
            if self.minerals > 150:
                for cc in self.cc.ready.idle:
                    self.do(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))
                    print("up grade orbital")
            return False

        "After dropship departure we expand"
        if (self.dropship_sent or self.load_dropship) and not self.already_pending(COMMANDCENTER):
            expand = True
            for cc in self.ccANDoc:
                if cc.assigned_harvesters < cc.ideal_harvesters:
                    expand = False
            if expand:
                if self.minerals > 400:
                    await self.expand_now_ANI()
                else:
                    return False

        "if dropship is full remove load command from dropship (self.load_dropship = False)"
        dropship_is_full = 0
        if self.medivacs.amount >= 1:
            for dropship in self.medivacs:
                abilities = (await self.get_available_abilities(dropship))
                if not (LOAD_MEDIVAC in abilities) and (UNLOADALLAT_MEDIVAC in abilities):
                    dropship_is_full = dropship_is_full + 1
            if dropship_is_full >= 1 and self.load_dropship:
                self.load_dropship = False
        if self.dropship_sent:
            if not self.medivacs:
                self.marine_drop = False
                self.dropship_sent = False
            for medivac in self.medivacs:
                if self.enemy_structures.of_type([UnitTypeId.MISSILETURRET, UnitTypeId.SPORECRAWLER])\
                        .closer_than(15, medivac):
                    abilities = (await self.get_available_abilities(medivac))
                    if AbilityId.UNLOADALLAT_MEDIVAC in abilities:
                        self.do(medivac(AbilityId.UNLOADALLAT_MEDIVAC, medivac.position))
                        continue
                if len(medivac.orders) < 1:
                    self.marine_drop = False
                    self.dropship_sent = False

        "land flying starport to rector"
        if self.starportflying and self.doner_location:
            for starport in self.starportflying:
                self.do(starport(LAND, self.doner_location))
                return False

        "wait for first supplydepot"
        if not self.supplydepots or not self.enemy_natural:
            return True
        expand = random.choice(self.supplydepots)

        "make first refinery"
        if not self.refineries:
            await self.execute_build_refinery()
            return False

        if self.marines.amount < 2:
            for barracks in self.barracks.idle:
                self.do(barracks.train(UnitTypeId.MARINE))
                return False

        "Build 1 barracks"
        if (self.barracks.amount + self.barracksflyings.amount) < 1:
            if self.minerals > 150:
                await self.build_for_me(BARRACKS)
            return False

        "Build 2nd barracks"
        if (self.barracks.amount + self.barracksflyings.amount) < 2 and self.factories:
            if self.minerals > 150:
                await self.build_for_me(BARRACKS)
            return False

        "build factory"
        if not self.factories and not self.already_pending(FACTORY) and self.barracks.ready:
            if self.can_afford(FACTORY):
                await self.build_for_me(FACTORY)
            return False

        "build starport"
        if ((self.starports.amount + self.starportflying.amount) == 0
                and not self.already_pending(STARPORT)
                and self.factories.ready):
            if self.can_afford(STARPORT):
                await self.build_for_me(STARPORT)
            return False

        if self.doner_location:
            if self.starports.closer_than(1, self.doner_location):
                self.doner_location = None
                return False

        if self.doner_location and self.starports.ready:
            sp = random.choice(self.starports.ready)
            self.do(sp(LIFT))
            print("Reason for lift: doner location detected. Preparing for SP reactor.")
            return False

        "build medivac and marines"
        if ((self.medivacs.amount + self.already_pending(UnitTypeId.MEDIVAC)) < 1):
            for starport in self.starports.ready:
                if self.can_afford(MEDIVAC) and self.can_feed(MEDIVAC):
                    print("Training dropship")
                    self.do(starport.train(MEDIVAC))
                return False
        elif (self.minerals > 50
              and not self.dropship_sent
              and dropship_is_full < 1
              and not self.load_dropship):
            for barracks in self.barracks:
                if len(barracks.orders) >= 2:
                    continue
                if len(barracks.orders) >= 1 and barracks.add_on_tag == 0:
                    continue
                self.do(barracks.train(UnitTypeId.MARINE))
                return False
            if self.minerals > 300:
                return True
            else:
                return False

        # load and send dropship
        if not self.dropship_sent and self.load_dropship:
            for dropship in self.medivacs.idle:
                if self.marines and self.load_dropship:
                    marine = self.marines.closest_to(dropship)
                    self.do(dropship(AbilityId.LOAD_MEDIVAC, marine, queue=True))
                    continue  # continue for loop, dont execute any of the following
        if dropship_is_full >= 1 and not self.dropship_sent:
            for dropship in self.medivacs:
                self.do(dropship.move(waypoint, queue=True))
                self.do(dropship.move(drop_point, queue=True))
                self.do(dropship(AbilityId.UNLOADALLAT_MEDIVAC, drop_point, queue=True))
                self.do(dropship.move(waypoint, queue=True))
                self.do(dropship.move(self.homeBase.position, queue=True))
                self.dropship_sent = True
        return True

    async def build_cc_at_home(self):
        build_site = await self.find_placement(UnitTypeId.COMMANDCENTER, near=self.homeBase.position,
                                               max_distance=30)
        if build_site:
            contractor = self.select_contractor(build_site)
            await self.build(COMMANDCENTER, build_site, build_worker=contractor)
        else:
            await self._client.chat_send("COMMANDCENTER placement error!!!", team_only=False)
            self.build_cc_home = False

    async def cashe_units_fast_cycle(self):
        self.cc = self.townhalls(UnitTypeId.COMMANDCENTER)
        self.orbitalcommand = self.townhalls(UnitTypeId.ORBITALCOMMAND)
        self.ccANDoc = (self.cc | self.orbitalcommand | self.townhalls(UnitTypeId.PLANETARYFORTRESS))
        self.townhalls_flying = (self.townhalls(UnitTypeId.COMMANDCENTERFLYING) |
                                 self.townhalls(UnitTypeId.ORBITALCOMMANDFLYING))
        self.outpost = None
        self.outpost = await self.get_outpost()
        self.reapers = self.units(UnitTypeId.REAPER)
        self.marines = self.units(UnitTypeId.MARINE)
        self.medivacs = self.units(UnitTypeId.MEDIVAC)
        self.marauders = self.units(UnitTypeId.MARAUDER)
        self.siegetanks_sieged = self.units(UnitTypeId.SIEGETANKSIEGED)
        self.hellions = self.units(UnitTypeId.HELLION)
        self.cyclones = self.units(UnitTypeId.CYCLONE)
        self.thors = self.units(UnitTypeId.THORAP)
        self.banshees = self.units(UnitTypeId.BANSHEE)
        self.vikings = self.units(UnitTypeId.VIKINGFIGHTER)
        self.enemy_units_and_structures = (self.enemy_units | self.enemy_structures).filter(
            lambda x: x.is_visible)
        self.enemy_units_on_ground = self.enemy_units_and_structures.not_structure.not_flying.filter(
            lambda x: not x.is_hallucination)
        self.remember_friendly_units()
        self.bunkers = self.structures(UnitTypeId.BUNKER)
        self.general = None
        if self.dropship_sent and self.hellions:
            self.general = self.hellions.furthest_to(self.start_location)
        elif self.thors.exists:
            self.general = self.thors.furthest_to(self.start_location)
        elif self.marauders.exists:
            self.general = self.marauders.furthest_to(self.start_location)
        self.scvs = self.workers(UnitTypeId.SCV)
        self.supplydepots = (
                self.structures(UnitTypeId.SUPPLYDEPOT) | self.structures(UnitTypeId.SUPPLYDEPOTLOWERED))
        self.refineries = self.gas_buildings
        self.barracks = self.structures(UnitTypeId.BARRACKS)
        self.barracksflyings = self.structures(UnitTypeId.BARRACKSFLYING)
        self.starports = self.structures(UnitTypeId.STARPORT)
        self.starportflying = self.structures(UnitTypeId.STARPORTFLYING)
        self.engineeringbays = self.structures(UnitTypeId.ENGINEERINGBAY)
        self.ghost_academies = self.structures(UnitTypeId.GHOSTACADEMY)
        self.armories = self.structures(UnitTypeId.ARMORY)
        self.factories = self.structures(UnitTypeId.FACTORY)
        self.factory_reactors = self.structures(UnitTypeId.FACTORYREACTOR)
        self.factory_techlabs = self.structures(UnitTypeId.FACTORYTECHLAB)
        self.factoriesflying = self.structures(UnitTypeId.FACTORYFLYING)
        self.fusioncores = self.structures(UnitTypeId.FUSIONCORE)
        self.techlabs_and_reactors = (self.structures(UnitTypeId.TECHLAB) | self.structures(UnitTypeId.REACTOR))
        self.enemy_units_on_air = self.enemy_units.flying.filter(lambda x: not x.is_hallucination)
        self.ghosts = self.units(UnitTypeId.GHOST)
        self.hell_bats = self.units(UnitTypeId.HELLIONTANK)
        self.mines = self.units(UnitTypeId.WIDOWMINE)
        self.mines_burrowed = self.units(UnitTypeId.WIDOWMINEBURROWED)
        self.siegetanks = self.units(UnitTypeId.SIEGETANK)
        self.vikingassault = self.units(UnitTypeId.VIKINGASSAULT)
        self.vikings_total = (self.units(UnitTypeId.VIKINGFIGHTER) | self.units(UnitTypeId.VIKINGASSAULT))
        self.liberators = self.units(UnitTypeId.LIBERATOR)
        self.liberatorsdefending = self.units(UnitTypeId.LIBERATORAG)
        self.all_liberators = (self.liberators | self.liberatorsdefending)
        self.battlecruisers = self.units(UnitTypeId.BATTLECRUISER)
        self.proxy_structures = self.enemy_structures.closer_than(self.defence_radius, self.start_location)


    async def formation(self, first_point, facing_angle, distance_between_units):
        def row(target_point, angle, distance):
            angle_1 = angle + 0.5 * math.pi
            angle_2 = angle + 1.5 * math.pi
            dx1, dy1 = math.cos(angle_1), math.sin(angle_1)
            dx2, dy2 = math.cos(angle_2), math.sin(angle_2)
            dx3, dy3 = math.cos(angle_1), math.sin(angle_1)
            dx4, dy4 = math.cos(angle_2), math.sin(angle_2)
            p = target_point.position
            return [
                Point2((p.x, p.y)),
                Point2((p.x + dx1 * distance, p.y + dy1 * distance)),
                Point2((p.x + dx2 * distance, p.y + dy2 * distance)),
                Point2((p.x + dx3 * distance * 2, p.y + dy3 * distance * 2)),
                Point2((p.x + dx4 * distance * 2, p.y + dy4 * distance * 2))
            ]

        angle = facing_angle + math.pi
        formaatio = []
        dx, dy = math.cos(angle), math.sin(angle)
        for x in range(0, 20):
            current_point = Point2(
                (first_point.x + dx * distance_between_units * x,
                 first_point.y + dy * distance_between_units * x))
            for y in range(0, 5):
                formaatio.append(row(current_point, angle, distance_between_units * 1)[y])
            # formaatio.append(row(current_point, angle, distance_between_units * 1)[0])
        return formaatio

    async def facing_towards(self, enemy_unit):
        origin = enemy_unit.position
        angle = enemy_unit.facing
        distance = enemy_unit.movement_speed
        dx, dy = math.cos(angle), math.sin(angle)
        return Point2((origin.x + dx * distance, origin.y + dy * distance))

    async def get_enemy_natural(self):
        """Find enemy natural."""
        if self.enemy_start_location == None:
            return None
        closest = None
        distance = math.inf
        for el in self.expansion_locations_list:
            d = await self._client.query_pathing(self.enemy_start_location, el)
            if d is None:
                continue
            if d < 10:
                continue
            if d < distance:
                distance = d
                closest = el
        return closest

    async def get_enemy_third(self):
        if self.enemy_start_location == None:
            return None
        if not self.enemy_natural:
            return None
        closest = None
        distance = math.inf
        for el in self.expansion_locations_list:
            if el.distance_to(self.enemy_natural) < 3:
                continue
            d = await self._client.query_pathing(self.enemy_start_location, el)
            if d is None:
                continue
            if d < 10:
                continue
            if d < distance:
                distance = d
                closest = el
        return closest

    async def get_third_base(self):
        if self.start_location == None:
            return None
        if not self.natural:
            return None
        closest = None
        distance = math.inf
        for el in self.expansion_locations_list:
            if el.distance_to(self.natural) < 3:
                continue
            d = await self._client.query_pathing(self.start_location, el)
            if d is None:
                continue
            if d < 10:
                continue
            if d < distance:
                distance = d
                closest = el
        return closest

    async def move_scvs(self):
        if not self.ccANDoc:
            return
        allOwnBuildings = self.structures.exclude_type(
            [UnitTypeId.REACTOR, UnitTypeId.TECHLAB, UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKSREACTOR,
             UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORYREACTOR, UnitTypeId.STARPORTTECHLAB,
             UnitTypeId.STARPORTREACTOR, UnitTypeId.SUPPLYDEPOTLOWERED, UnitTypeId.SUPPLYDEPOT])
        scvs = self.scvs
        units_to_ignore = [UnitTypeId.REAPER]
        targets = self.enemy_units.not_flying.filter(lambda x: x.type_id not in units_to_ignore)

        if self.enemy_structures:
            mierals_left = False
            for cc in self.ccANDoc:
                if self.mineral_field.closer_than(10, cc):
                    mierals_left = True
                    break
            if not mierals_left and self.enemy_structures:
                if self.chat and self.chat_once_scv_kamikaze:
                    self.chat_once_scv_kamikaze = False
                    await self._client.chat_send("No minerals left. KAMIKAZE SCV STRATEGY INITIATED!",
                                                 team_only=False)
                if self.scvs.idle.amount > 20:
                    for scv in self.scvs.idle:
                        if scv.is_puuhapete or scv.is_in_repair_group:
                            continue
                        self.do(scv.attack(self.enemy_structures.random.position))
                        return
                return

        templars = self.enemy_units.of_type(UnitTypeId.DARKTEMPLAR)
        if templars:
            for scv in self.scvs:
                if templars.closer_than(5, scv):
                    templar = templars.closest_to(scv)
                    self.do(scv.move(scv.position.towards(templar, -10)))
                    continue

        if self.enemy_liberation_zone:
            avoiding_liberators = False
            for scv in scvs:
                if await self.avoid_liberation_zones(scv):
                    avoiding_liberators = True
            if avoiding_liberators:
                return

        if self.proxy_structures and not self.barracks.ready \
                and not self.factories and not self.starports and self.muster_home_defence:
            self.scout_sent = False
            self.proxy_defence = True
            self.can_do_worker_rush_defence = False
            self.minimum_repairgroup = 2
            for building in self.structures.closer_than(5, self.natural):
                if await self.has_ability(AbilityId.CANCEL_BUILDINPROGRESS, building):
                    self.do(building(AbilityId.CANCEL_BUILDINPROGRESS))
            if self.chat:
                await self._client.chat_send("Proxy build detected -> Panic!", team_only=False)

        if self.proxy_defence:
            if self.refineries_in_first_base < 2:
                self.first_base_saturation = 4
                self.refineries_in_first_base = 2
            proxy_defence_force = scvs.filter(lambda x: x.is_in_kodinturvajoukot)
            if self.muster_home_defence:
                self.muster_home_defence = False
                units = (scvs.filter(lambda x: not x.is_in_kodinturvajoukot
                                               and not x.is_in_repair_group
                                               and not x.is_puuhapete)).random_group_of(8)
                for unit in units:
                    self.add_unit_to_kodinturvajoukot(unit)
                print("proxy defence force is made")
                return
            proxy_structures = self.proxy_structures.of_type(UnitTypeId.PYLON)
            if not proxy_structures:
                proxy_structures = self.proxy_structures
            if proxy_structures and self.kodinturvajoukot.amount > 0:
                for unit in self.kodinturvajoukot:
                    if len(unit.orders) < 4:
                        self.do(unit.attack(proxy_structures.random, queue=True))
                        print("Attacking random enemy structure")
                enemy_workers = self.enemy_units.of_type([UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE])
                if enemy_workers:
                    if self.puuhapete:
                        self.do(self.puuhapete.attack(enemy_workers.closest_to(self.puuhapete)))
                    # for unit in self.repair_group:
                    #     self.do(unit.attack(enemy_workers.closest_to(unit)))
                elif self.puuhapete:
                    self.do(self.puuhapete.attack(proxy_structures.closest_to(self.puuhapete)))
                return
            else:
                self.proxy_defence = False

        if self.kill_scout and self.time < 180:
            enemy_scouts = self.enemy_units.of_type([UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE])\
                .closer_than(20, self.start_location)
            if enemy_scouts and scvs:
                if self.chat:
                    await self._client.chat_send("Enemy scout detected.", team_only=False)
                    print("Enemy scout detected.")
                scout = enemy_scouts.first
                scv = scvs.filter(lambda x: not x.is_puuhapete).closest_to(self.start_location)
                self.do(scv.attack(scout))
                self.kill_scout = False

        if targets and scvs and self.can_do_worker_rush_defence:
            mf = self.mineral_field.closest_to(self.homeBase)
            enemy_mf = self.mineral_field.closest_to(self.enemy_start_location)
            targets_near_home = targets.closer_than(25, self.start_location)
            if targets_near_home.amount > 2 and self.supplydepots.amount < 3 and self.ccANDoc.amount == 1:
                if not self.home_in_danger and self.puuhapete:
                    self.do(self.puuhapete.gather(mf))
                self.home_in_danger = True
                self.build_cc_home = True
                if self.first_base_saturation < 0:
                    self.first_base_saturation = 0
                for unit in scvs:
                    if unit.is_puuhapete:
                        continue
                    else:
                        self.add_unit_to_kodinturvajoukot(unit)

            if self.home_in_danger and not self.enemy_structures.closer_than(30, self.start_location):
                if self.enemy_units_on_ground.of_type([SCV, PROBE]).amount > 2:
                    for building in allOwnBuildings:
                        if (building.health_percentage < 1
                                and await self.has_ability(CANCEL_BUILDINPROGRESS, building)):
                            self.do(building(AbilityId.CANCEL_BUILDINPROGRESS))
                            print("Building cancelled")

            scvs_that_need_repair = scvs.filter(lambda x: x.health_percentage < 1)
            for scv in scvs:
                if templars.closer_than(5, scv):
                    continue
                if self.home_in_danger and scv.is_in_kodinturvajoukot:
                    if scv.is_carrying_minerals:
                        self.do(scv(AbilityId.HARVEST_RETURN, self.ccANDoc.closest_to(scv)))
                        continue
                    if scv.health_percentage < 1 / 2 and self.minerals > 10:
                        if self.enemy_units_and_structures.closer_than(1, scv):
                            closest_enemy = self.enemy_units.closest_to(self.start_location)
                            if closest_enemy:
                                mfs = self.mineral_field.closer_than(10, self.start_location)
                                if mfs:
                                    mf = mfs.furthest_to(closest_enemy)
                            self.do(scv.gather(mf))
                        elif scvs_that_need_repair.further_than(0.1, scv):
                            need_first_aid = scvs_that_need_repair.further_than(0.1, scv).closest_to(scv)
                            self.do(scv(AbilityId.EFFECT_REPAIR_SCV, need_first_aid))
                        continue
                    if scv.weapon_cooldown != 0 \
                            and (self.minerals < 100
                                 or self.enemy_units_on_ground.of_type([UnitTypeId.DRONE]).closer_than(10,
                                                                                                       scv)):
                        self.do(scv.gather(enemy_mf))
                    else:
                        target = self.enemy_start_location
                        self.do(scv.attack(target.position.towards(scv, -5)))
                    continue
                if scv.is_puuhapete or scv.is_in_repair_group:
                    continue
                if (self.scvs.amount <= (self.scv_limit - 7)
                        and scv.distance_to(self.homeBase) > 10):
                    scv_targets = targets.exclude_type \
                        ([UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE]).closer_than(10, scv)
                    if scv_targets.amount > 1:
                        self.do(scv.gather(mf))
                        continue
        elif self.home_in_danger:
            self.home_in_danger = False
            if scvs:
                mf = self.mineral_field.closest_to(self.homeBase)
                for scv in scvs:
                    if scv.is_in_kodinturvajoukot:
                        self.do(scv.gather(mf))
                        continue

        # if self.iteraatio % 10 == 0:
        #     if self.supply_used > 190 and not self.enemy_structures.exists:
        #         target = random.choice(self.vespene_geyser)
        #         scout = self.scvs.random
        #         self.do(scout.attack(target.position))
        if self.iteraatio % 2 == 0:
            await self.gather_gas_and_minerals()

    async def priority_train(self, unit):
        """
        called example: await self.priority_train(MARAUDER)
        return False if no training facility, resourses, or supply left.
        return True if managed to train unit or waiting for minerals.
        max queue for units = 2
        """

        if not self.can_afford(unit):
            return True

        # find facility that producecs this unit
        barracks_units = [MARINE, MARAUDER, REAPER, GHOST]
        factory_units = [HELLION, HELLIONTANK, SIEGETANK, CYCLONE, WIDOWMINE, THOR]
        starport_units = [VIKINGFIGHTER, MEDIVAC, LIBERATOR, RAVEN, BANSHEE, BATTLECRUISER]
        if unit in barracks_units:
            FACILITY = BARRACKS
        elif unit in factory_units:
            FACILITY = FACTORY
        elif unit in starport_units:
            FACILITY = STARPORT
        else:
            return False

        # find ability that is needed to build this unit
        unit_creation_ability = {
            MARINE: BARRACKSTRAIN_MARINE,
            MARAUDER: BARRACKSTRAIN_MARAUDER,
            REAPER: BARRACKSTRAIN_REAPER,
            GHOST: BARRACKSTRAIN_GHOST,
            HELLION: FACTORYTRAIN_HELLION,
            HELLIONTANK: TRAIN_HELLBAT,
            SIEGETANK: FACTORYTRAIN_SIEGETANK,
            CYCLONE: TRAIN_CYCLONE,
            WIDOWMINE: FACTORYTRAIN_WIDOWMINE,
            THOR: FACTORYTRAIN_THOR,
            VIKINGFIGHTER: STARPORTTRAIN_VIKINGFIGHTER,
            MEDIVAC: STARPORTTRAIN_MEDIVAC,
            LIBERATOR: STARPORTTRAIN_LIBERATOR,
            RAVEN: STARPORTTRAIN_RAVEN,
            BANSHEE: STARPORTTRAIN_BANSHEE,
            BATTLECRUISER: STARPORTTRAIN_BATTLECRUISER
        }
        ability = unit_creation_ability.get(unit)
        for building in self.structures(FACILITY):
            if len(building.orders) > 1:
                continue
            if self.can_feed(unit) and await self.has_ability(ability, unit=building):
                await self.do(building.train(unit))
                return True
        return False

    async def has_ability(self, ability, unit):
                abilities = await self.get_available_abilities(unit)
                if ability in abilities:
                    return True
                else:
                    return False

    async def move_reapers(self):
        units_to_ignore = [UnitTypeId.ADEPTPHASESHIFT, UnitTypeId.EGG, UnitTypeId.LARVA]
        home_base = None
        if self.ccANDoc:
            home_base = self.homeBase
        if not self.reapers:
            return
        if not home_base:
            return
        if self.reapers.exists:
            # reaperGrenadeRange = self._game_data.abilities[AbilityId.KD8CHARGE_KD8CHARGE.value]._proto.cast_range
            if self.reaper_haras:
                enemy_ground_units = self.enemy_units_and_structures.not_structure.not_flying. \
                    exclude_type(units_to_ignore).further_than(self.defence_radius, self.start_location)
            else:
                enemy_ground_units = self.enemy_units_and_structures.not_structure.not_flying.exclude_type(
                    units_to_ignore)
            enemy_towers = self.enemy_structures.filter(lambda x: x.can_attack_ground)
            for reaper in self.reapers:
                if self.reaper_haras:
                    if len(reaper.orders) < 2:
                        self.do(
                            reaper.move(self.enemy_start_location.towards(self.enemy_natural, 3), queue=True))
                        self.do(reaper.move(self.enemy_start_location, queue=True))
                    elif reaper.health_percentage < 1:
                        self.reaper_haras = False
                if await self.avoid_own_nuke(reaper):
                    continue
                if await self.avoid_enemy_siegetanks(reaper):
                    continue
                enemy_towers_too_close = enemy_towers.filter(
                    lambda unit: unit.distance_to(reaper) < unit.radius + unit.ground_range + reaper.radius + 3)
                if enemy_towers_too_close:
                    self.do(reaper.move(reaper.position.towards(enemy_towers_too_close.closest_to(reaper), -6)))
                    continue
                ground_units_too_close = enemy_ground_units.filter(
                    lambda unit: unit.distance_to(reaper) < unit.radius + unit.ground_range + reaper.radius + 3)
                if not ground_units_too_close:
                    ground_units_too_close = enemy_ground_units.closer_than(3 + reaper.radius, reaper)
                if enemy_ground_units:
                    closest_enemy = enemy_ground_units.closest_to(reaper)
                    advance_to_closest_enemy = await self.facing_towards(closest_enemy)
                    # back of not to get killed after shot or low on health
                    if reaper.weapon_cooldown != 0 or reaper.health_percentage < 0.5:
                        if ground_units_too_close:
                            target = reaper.position.towards(ground_units_too_close.closest_to(reaper), -6)
                            self.do(reaper.move(target))
                            continue
                        elif reaper.health_percentage < 1:
                            self.do(reaper.move(
                                home_base.position.towards(self.enemy_units.closest_to(reaper), -6)))
                            continue
                        else:
                            self.do(reaper.attack(closest_enemy))
                        continue
                    abilities = (await self.get_available_abilities(reaper))
                    # print(abilities)
                    # unit_height = self.get_terrain_z_height(Point2(unit.position))
                    if enemy_ground_units.closer_than(15, reaper).amount == 1:
                        if self.ccANDoc.amount < 3:
                            self.do(reaper.attack(advance_to_closest_enemy))
                            continue
                        else:
                            self.do(reaper.attack(closest_enemy))
                            continue
                    if not self.ghosts.closer_than(10, reaper) and KD8CHARGE_KD8CHARGE in abilities:
                        self.do(reaper(AbilityId.KD8CHARGE_KD8CHARGE, enemy_ground_units.closest_to(
                            reaper).position))
                        continue
                    elif ground_units_too_close:
                        self.do(
                            reaper.move(reaper.position.towards(ground_units_too_close.closest_to(reaper), -6)))
                    else:
                        self.do(reaper.attack(enemy_ground_units.closest_to(reaper)))
                    continue
                if len(reaper.orders) > 0:
                    if reaper.orders[0].ability.id in [AbilityId.KD8CHARGE_KD8CHARGE]:
                        self.do(reaper.attack(reaper.position))
                if self.NukesLeft > 0 and self.ghosts:
                    ghost = self.ghosts.closest_to(self.enemy_start_location)
                    if reaper.distance_to(ghost.position) > 8:
                        self.do(reaper.move(ghost.position))
                    else:
                        self.do(reaper.move(self.enemy_start_location))
                    continue
                if self.ccANDoc.amount >= 3 and self.general and self.iteraatio % 3 == 0:
                    if reaper.distance_to(self.general) > 5 and len(reaper.orders) < 5:
                        self.do(reaper.move(self.general.position, queue=True))
                    continue
                if len(reaper.orders) == 0:
                    hidden_visible_geysers = (self.vespene_geyser.filter(
                        lambda x: x.is_visible == False and x.distance_to(
                            self.start_location) < self.defence_radius))
                    if not hidden_visible_geysers:
                        hidden_visible_geysers = (self.vespene_geyser.filter(
                            lambda x: x.is_visible == False))
                    if hidden_visible_geysers:
                        target = random.choice(hidden_visible_geysers)
                    else:
                        target = (self.homeBase.position.random_on_distance(8))
                    self.do(reaper.attack(target.position, queue=True))
                    continue

    async def move_thors(self):
        # outpost = await self.get_outpost()
        outpost = self.homeBase.position.towards(self.game_info.map_center, 5)
        if self.supply_used > 190:
            thors_to_attack = 1
            idle_thors = self.thors.idle.filter(lambda x: x.health_percentage >= 1)
        else:
            thors_to_attack = self.min_thors_to_attack
            idle_thors = self.thors.idle.filter(lambda x: x.health_percentage >= 1).closer_than(10, outpost.position)
        thorMinHealth = 5 / 10  # minimum health for thor to continue fight
        for thor in self.units(UnitTypeId.THOR):
            if await self.has_ability(AbilityId.MORPH_THORHIGHIMPACTMODE, thor):
                self.do(thor(AbilityId.MORPH_THORHIGHIMPACTMODE))
                return
        for thor in self.thors:
            if thor.health_percentage < thorMinHealth:
                if thor.distance_to(outpost) > 10:
                    self.do(thor.attack(outpost.position.random_on_distance(6)))
                    continue  # continue for loop, dont execute any of the following
        if len(idle_thors) >= thors_to_attack or len(idle_thors) >= self.max_thor:
            if self.min_thors_to_attack < 10:
                self.min_thors_to_attack += 1
            if self.flanking_thors:
                for thor in idle_thors:
                    if self.thor_use_route_a:
                        self.thor_use_route_a = False
                        for point in reversed(self.attack_route_a):
                            if self.structures.closer_than(3, point):
                                continue
                            self.do(thor.attack(point, queue=True))
                        self.do(thor.attack(self.enemy_natural, queue=True))
                        self.do(thor.attack(self.enemy_start_location, queue=True))
                    else:
                        self.thor_use_route_a = True
                        for point in reversed(self.attack_route_b):
                            if self.structures.closer_than(3, point):
                                continue
                            self.do(thor.attack(point, queue=True))
                        self.do(thor.attack(self.enemy_natural, queue=True))
                        self.do(thor.attack(self.enemy_start_location, queue=True))
                    if self.enemy_structures:
                        target_of_assault = random.choice(self.enemy_structures)
                        self.do(thor.attack(target_of_assault.position, queue=True))
                        continue  # continue for loop, dont execute any of the following

                return
            elif self.enemy_structures.exists:
                target_of_assault = random.choice(self.enemy_structures)
            else:
                target_of_assault = random.choice(self.vespene_geyser.filter(lambda x: x.is_visible == False))
            for thor in idle_thors:
                self.do(thor.attack(target_of_assault.position))
                continue  # continue for loop, dont execute any of the following
        else:
            for thor in self.thors.idle:
                if thor.distance_to(outpost.position) > 10:
                    self.do(thor.attack(outpost.position))
                    continue  # continue for loop, don't execute any of the following

    async def move_liberators(self):
        if not (self.liberators or self.liberatorsdefending):
            return
        if self.siege_behind_wall and self.priority_tank_pos:
            for liberator in self.liberators.idle:
                self.do(liberator.move(self.priority_tank_pos, queue=True))
                self.do(
                    liberator(AbilityId.MORPH_LIBERATORAGMODE, self.main_base_ramp.bottom_center, queue=True))
                continue
            return
        units_to_ignore = [UnitTypeId.ADEPTPHASESHIFT, UnitTypeId.EGG, UnitTypeId.LARVA,
                           UnitTypeId.BROODLING, UnitTypeId.CHANGELINGMARINESHIELD]
        liberator_targets = self.enemy_units_on_ground.exclude_type(units_to_ignore)
        can_attack = True
        if self.liberators and liberator_targets:
            liberators = self.liberators.sorted(lambda x: x.distance_to(liberator_targets.closest_to(x)))
        else:
            liberators = self.liberators
        for liberator in liberators:
            if not self.enemy_units and self.enemy_structures and self.minerals > 5000 and len(
                    liberator.orders) == 0:
                self.do(liberator.move(self.enemy_structures.random.position))
                continue
            unit_in_no_flight_zone = (
                self.enemy_structures.filter(lambda x: x.can_attack_air).closer_than(11, liberator))
            if await self.avoid_own_nuke(liberator):
                self.do(liberator.move(self.homeBase.position))
                continue
            if unit_in_no_flight_zone:
                self.do(liberator.move(
                    liberator.position.towards(unit_in_no_flight_zone.closest_to(liberator), -5)))
                continue

            if liberator_targets and can_attack:
                if self.enemy_units_on_ground.of_type([SIEGETANKSIEGED]):
                    target = self.enemy_units_on_ground.of_type([SIEGETANKSIEGED]).closest_to(liberator)
                    liberation_range = 4
                else:
                    target = (liberator_targets.closest_to(liberator))
                    if self.already_pending(
                            LIBERATORAGRANGEUPGRADE) < 1 and self.liberatorsdefending.amount < 5:
                        liberation_range = 4
                    else:
                        liberation_range = 1
                can_attack = False
                if await self.has_ability(MORPH_LIBERATORAGMODE, liberator):
                    self.do(liberator(AbilityId.MORPH_LIBERATORAGMODE,
                                      target.position.towards(liberator, liberation_range)))
                continue
            if len(liberator.orders) == 0 and self.ccANDoc:
                if self.general:
                    self.do(liberator.move(self.general.position.random_on_distance(6)))
                else:
                    self.do(liberator.move(random.choice(self.ccANDoc).position))
                    continue

        if not self.liberatorsdefending:
            self.liberator_timer = 0
        elif self.liberatorsdefending.amount < 10:
            self.liberator_timer += self.liberatorsdefending.amount
        else:
            self.liberator_timer += 10
        liberator_unsiege_speed = 140

        max_distance_to_closest_enemy = 0
        furthest_liberator_tag = None
        if self.enemy_units_on_ground:
            if self.liberatorsdefending and self.liberator_timer > liberator_unsiege_speed:
                self.liberator_timer = 0
                for liberator in self.liberatorsdefending:
                    distance_to_closest_enemy = liberator.distance_to(
                        self.enemy_units_on_ground.closest_to(liberator))
                    if max_distance_to_closest_enemy < distance_to_closest_enemy:
                        max_distance_to_closest_enemy = distance_to_closest_enemy
                        furthest_liberator_tag = liberator.tag
                    # if not self.enemy_units_on_ground.closer_than(17, liberator):
                    #     self.do(liberator(AbilityId.MORPH_LIBERATORAAMODE))
                for liberator in self.liberatorsdefending:
                    if liberator.tag == furthest_liberator_tag:
                        self.do(liberator(AbilityId.MORPH_LIBERATORAAMODE))
                        break
        elif self.liberator_timer > 40:
            self.liberator_timer = 0
            self.do(self.liberatorsdefending.random(AbilityId.MORPH_LIBERATORAAMODE))
            return

            # elif not self.siegetanks_sieged:
            #     for liberator in self.liberatorsdefending.idle:
            #         self.do(liberator(AbilityId.MORPH_LIBERATORAAMODE))
            #         break

    async def move_medivacs(self):
        priority_units = (self.ghosts)
        healable_units = (self.marines |
                          self.ghosts |
                          self.hell_bats |
                          self.marauders)
        priority_healing = priority_units.filter(lambda x: x.health_percentage < 0.9)
        needs_healing = healable_units.filter(lambda x: x.health_percentage < 1)
        target_for_standby = None
        if self.marauders.exists:
            target_for_standby = self.marauders.furthest_to(self.homeBase)
        if target_for_standby:
            target_position = target_for_standby.position.towards(self.homeBase, 5)
        for healer in self.medivacs:
            enemy_threats = self.in_air_range_of_units(healer, self.enemy_units_and_structures, 2)
            if healer.position.to2.distance_to(self.homeBase.position.to2) < 10:
                if healer.health_percentage < 1:
                    if self.iteraatio % 60 == 0:
                        self.do(healer.move(self.homeBase.position.random_on_distance(6)))
                    continue
            if await self.avoid_own_nuke(healer):
                continue

            if enemy_threats:
                closest_enemy = enemy_threats.closest_to(healer)
                self.do(healer.move(healer.position.towards(closest_enemy, -10)))
                continue
            if healer.health_percentage > 0.5:
                if priority_healing and self.NukesLeft > 10:
                    target = priority_healing.closest_to(healer)
                    if await self.can_cast(healer, AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS):
                        self.do(healer(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS))
                        continue
                    self.do(healer.attack(target.position))
                    continue
                if needs_healing:
                    if healer.energy > 25 and await self.can_cast(healer,
                                                                  AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS):
                        self.do(healer(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS))
                        continue
                    target = needs_healing.closest_to(healer).position.towards(healer, -2)
                    self.do(healer.attack(target))
                    continue
                if target_for_standby and healer.health_percentage >= 0.9:
                    if healer.position.distance_to(target_position) > 5:
                        self.do(healer.move(target_position))
                    continue
            if healer.distance_to(self.homeBase) > 15:
                if await self.can_cast(healer, AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS):
                    self.do(healer(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS))
                    continue
                self.do(healer.move(self.homeBase.position))

    async def move_hellions_and_hellbats(self):
        hellions = self.hellions
        hell_bats = self.hell_bats
        units_to_ignore = [ADEPTPHASESHIFT, EGG, LARVA]
        enemy_threats = self.enemy_units_on_ground.exclude_type(units_to_ignore)
        primary_targets = enemy_threats.filter(lambda x: x.is_light)
        outpost = await self.get_outpost()
        for hellion in hellions.sorted(lambda x: x.health_percentage, reverse=False):
            if (self.hellions.amount > 10 or self.morph_to_hellbats) and await self.has_ability(
                    AbilityId.MORPH_HELLBAT, hellion) and self.iteraatio % 5 == 0:
                self.do(hellion(AbilityId.MORPH_HELLBAT))
                break
            # if hellion.health_percentage < 0.5 and hellion.distance_to(self.homeBase) > 10 and not self.marine_drop:
            #     self.do(hellion.move(self.homeBase.position))
            #     continue
            if hellion.distance_to(self.homeBase) < 10 and hellion.health_percentage < 1:
                continue
            if await self.avoid_own_nuke(hellion):
                continue
            if await self.avoid_enemy_siegetanks(hellion):
                continue
            if enemy_threats:
                if hellion.weapon_cooldown != 0 and enemy_threats.closer_than(hellion.ground_range, hellion):
                    retreat_point = hellion.position.towards(enemy_threats.closest_to(hellion), -10)
                    self.do(hellion.move(retreat_point))
                    continue
                elif primary_targets.in_attack_range_of(hellion):
                    target = primary_targets.closest_to(hellion)
                    self.do(hellion.attack(target))
                    continue
                else:
                    target = enemy_threats.closest_to(hellion)
                    self.do(hellion.attack(target))
                    continue

            if self.marine_drop and self.enemy_start_location and self.medivacs:
                dropship = self.medivacs.furthest_to(self.start_location)
                if self.dropship_sent and dropship.distance_to(self.enemy_start_location) < hellion.distance_to(
                        self.enemy_start_location):
                    self.do(hellion.attack(self.enemy_start_location))
                    continue
            # if self.general:
            #     if hellion.distance_to(self.general) > 7:
            #         self.do(hellion.attack(self.general.position))
            #     continue
            if hellion.distance_to(self.start_location) > 10:
                self.do(hellion.move(self.start_location))
                continue

        ## hellion tank
        for unit in hell_bats:
            if await self.avoid_own_nuke(unit):
                continue
            # if await self.avoid_enemy_siegetanks(unit):
            #     continue

            if enemy_threats:
                self.do(unit.attack(enemy_threats.closest_to(unit).position))
                continue
            if self.general:
                if unit.distance_to(self.general) > 10:
                    self.do(unit.attack(self.general.position))
                    continue
            elif self.siegetanks:
                target = self.siegetanks.closest_to(unit)
                if unit.distance_to(target) > 10:
                    self.do(unit.attack(target.position))
                continue
            elif unit.distance_to(outpost) > 10:
                self.do(unit.move(outpost.position))
                continue

    async def raise_lower_depots(self):
        if self.super_greed and self.build_cc_home:
            return
        # Raise depos when enemies are nearby
        if (self.midle_depo_position
                and (self.enemy_units_on_ground.closer_than(6, self.midle_depo_position)
                     or (self.build_cc_home and self.enemy_units_on_ground))):
            for depo in self.structures(SUPPLYDEPOTLOWERED).ready.closer_than(6, self.midle_depo_position):
                self.do(depo(MORPH_SUPPLYDEPOT_RAISE))
                continue
        else:
            for depo in self.structures(SUPPLYDEPOT).ready.filter(lambda x: x.health_percentage >= 1):
                self.do(depo(MORPH_SUPPLYDEPOT_LOWER))

    async def move_tanks(self):
        tank_range = 14
        if self.bunkers and (self.delay_third or (self.max_starports == 0 and self.ccANDoc.amount < 3)):
            bunker = self.bunkers.random.position
            waypoint = self.vespene_geyser.closest_to(bunker).position
            for tank in self.siegetanks.idle:
                self.do(tank.attack(waypoint))
                self.do(tank.attack(bunker.position, queue=True))
                self.do(tank(AbilityId.SIEGEMODE_SIEGEMODE, queue=True))
                continue
            return
        if self.siege_behind_wall:
            if self.siegetanks.amount + self.siegetanks_sieged.amount > 2 or self.ccANDoc.amount > 2:
                self.siege_behind_wall = False
                return
            "siege priority tank behind wall"
            for tank in self.siegetanks.idle:
                if self.priority_tank_pos:
                    self.do(tank.move(self.priority_tank_pos, queue=True))
                    self.do(tank(AbilityId.SIEGEMODE_SIEGEMODE, queue=True))
                    continue
            return

        units_to_ignore = [ADEPTPHASESHIFT, EGG, LARVA, DRONE, SCV, PROBE]
        siegetank_targets = self.enemy_units_and_structures.not_flying.filter(lambda x: x.is_visible)
        siegetank_primary_targets = siegetank_targets.filter(lambda x: x.can_attack_ground)
        for tank in self.siegetanks:
            no_siege_allowed_targets = self.enemy_units.of_type([UnitTypeId.ZERGLING, UnitTypeId.ZEALOT]). \
                closer_than(17, tank)
            enemyAttackRange = siegetank_primary_targets.closer_than(tank_range, tank)
            if await self.avoid_own_nuke(tank):
                continue
            if await self.avoid_storms(tank):
                continue
            # if await self.avoid_enemy_siegetanks(tank):
            #     continue
            # check if enemy ground units exists
            if tank.health_percentage < 0.5 and tank.weapon_cooldown == 0:
                if tank.distance_to(self.homeBase) > 15:
                    self.do(tank.attack(self.homeBase.position))
                    continue
            if tank.health_percentage < 1 and tank.distance_to(self.homeBase) < 15:
                continue

            if siegetank_targets:
                # siegemode if close enough to enemy
                if self.canSiege and enemyAttackRange.exclude_type(
                        units_to_ignore) and not no_siege_allowed_targets \
                        and await self.can_cast(tank, AbilityId.SIEGEMODE_SIEGEMODE):
                    self.do(tank(AbilityId.SIEGEMODE_SIEGEMODE))
                    self.canSiege = False
                    continue
                if tank.weapon_cooldown != 0:
                    # if self.canSiege:
                    #     self.do(tank(AbilityId.SIEGEMODE_SIEGEMODE))
                    #     self.canSiege = False
                    #     continue
                    if siegetank_targets.in_attack_range_of(tank, bonus_distance=-0.5):
                        self.do(tank.move(tank.position.towards(siegetank_targets.closest_to(tank), -10)))
                        continue
                self.do(tank.attack(siegetank_targets.closest_to(tank)))
                continue

            if self.general:
                target_position = self.general.position
                if tank.distance_to(target_position) > 8:
                    self.do(tank.attack(target_position))
                continue

            if tank.position.to2.distance_to((await self.get_outpost()).position.to2) > 8:
                self.do(tank.move(await self.get_outpost()))
                continue

        ## SIEGETANK deside target and if need to turn tank mode
        if self.build_cc_home:
            return
        if self.bunkers and self.delay_third:
            return
        artillery = self.siegetanks_sieged
        if self.agressive_tanks or self.minerals > 2000:
            for tank in artillery:
                if not self.enemy_units_on_ground.in_attack_range_of(tank) \
                        and not self.enemy_structures.in_attack_range_of(tank):
                    self.do(tank(AbilityId.UNSIEGE_UNSIEGE))
            return

        max_distance_to_closest_enemy = 0
        self.unsiegetimer += 1
        for tank in artillery:
            enemyAttackRange = siegetank_targets.closer_than(tank_range, tank)
            if enemyAttackRange:
                self.unsiegetimer = 0
                break
        if self.unsiegetimer > 20:
            self.unsiegetimer = 0
            for tank in self.siegetanks_sieged.take(3):
                self.do(tank(AbilityId.UNSIEGE_UNSIEGE))
                continue
            return

        if siegetank_targets:
            if self.siegetanks.filter(
                    lambda x: x.health_percentage > 0.5).amount < 2 and self.siegetanks_sieged.amount > 2:
                tank_to_unsiege = None
                for tank in artillery:
                    if siegetank_targets.closer_than(tank_range, tank):
                        continue
                    distance_to_closest_enemy = tank.distance_to(siegetank_targets.closest_to(tank))
                    if max_distance_to_closest_enemy < distance_to_closest_enemy:
                        max_distance_to_closest_enemy = distance_to_closest_enemy
                        tank_to_unsiege = tank
                if tank_to_unsiege:
                    self.do(tank_to_unsiege(AbilityId.UNSIEGE_UNSIEGE))

    async def move_battle_ruiser(self):
        if not self.battlecruisers:
            return
        units_to_ignore = [UnitTypeId.CHANGELINGMARINE, UnitTypeId.CHANGELINGMARINESHIELD]
        bcs = self.battlecruisers
        FreshMeat = self.enemy_units_and_structures.exclude_type(units_to_ignore).filter(
            lambda x: x.can_attack_air)
        if self.iteraatio % 8 == 0:
            can_yamato = True
        else:
            can_yamato = False
        perform_assault = False
        bcs_ready_for_jump = 0
        expansions_sorted = sorted(self.expansion_locations_list,
                                   key=lambda p: p.distance_to(self.enemy_start_location),
                                   reverse=True)
        assault_target = None
        assault_target_base = None
        for base in expansions_sorted:
            if self.enemy_structures.closer_than(3, base):
                if base.position == self.last_jump_target:
                    continue
                if base.position == self.enemy_natural:
                    continue
                if base.position == self.enemy_start_location:
                    continue
                else:
                    assault_target_base = base
                    break

        if (bcs.amount >= (self.max_BC)
                and self.enemy_start_location and (self.enemy_structures.exists or self.assault_enemy_home)):
            for battle_ruiser in bcs:
                if not await self.has_ability(EFFECT_TACTICALJUMP,
                                              battle_ruiser) or battle_ruiser.health_percentage < 0.8:
                    battle_ruiser.jump_ready = False
                else:
                    battle_ruiser.jump_ready = True
                    bcs_ready_for_jump += 1
            if bcs_ready_for_jump >= self.max_BC:
                perform_assault = True
        if self.assault_enemy_home:
            assault_target = self.enemy_start_location
        elif assault_target_base:
            assault_target = assault_target_base
        elif self.enemy_structures and not self.enemy_structures.visible:
            assault_target = random.choice(self.enemy_structures)
        else:
            assault_target = None
        if perform_assault and self.assault_enemy_home:
            self.assault_enemy_home = False
            if self.chat:
                await self._client.chat_send("Tactical jump time!", team_only=False)

        delay_assault = False
        if self.assault_enemy_home and (bcs_ready_for_jump < self.max_BC):
            delay_assault = True
        if bcs_ready_for_jump > self.max_BC:
            bcs_ready_for_jump = self.max_BC

        if assault_target == self.enemy_start_location:
            waypoints_after_jump = sorted(self.expansion_locations_list,
                                          key=lambda p: p.distance_to(self.enemy_start_location), reverse=False)

        for battle_ruiser in bcs:
            if perform_assault and battle_ruiser.jump_ready and bcs_ready_for_jump > 0 and assault_target:
                self.do(battle_ruiser(AbilityId.EFFECT_TACTICALJUMP, assault_target.position))
                self.last_jump_target = assault_target.position
                # if assault_target == self.enemy_start_location:
                # for target in waypoints_after_jump:
                #     self.do(battle_ruiser.move(target.position, queue= True))
                bcs_ready_for_jump -= 1
                continue
            if battle_ruiser.distance_to(self.homeBase) < 10 and (
                    battle_ruiser.health_percentage < 1 or delay_assault or not await self.has_ability(
                EFFECT_TACTICALJUMP, battle_ruiser)):
                if self.iteraatio % 70 == 0:
                    self.do(battle_ruiser.move(self.homeBase.position.random_on_distance(5)))
                continue
            if battle_ruiser.health < 200:
                if await self.has_ability(EFFECT_TACTICALJUMP, battle_ruiser):
                    self.do(battle_ruiser(AbilityId.EFFECT_TACTICALJUMP,
                                          self.homeBase.position.random_on_distance(5)))
                    print("batlecruiser emergency retreat")
                continue
            if await self.avoid_own_nuke(battle_ruiser):
                continue
            if can_yamato:
                targets = self.enemy_units_and_structures.closer_than(10, battle_ruiser).filter(
                    lambda x: (x.shield + x.health) > 100).filter(lambda x: x.can_attack_air)
                if targets and await self.has_ability(YAMATO_YAMATOGUN, battle_ruiser):
                    target = targets.random
                    self.do(battle_ruiser(AbilityId.YAMATO_YAMATOGUN, target))
                    can_yamato = False
                    continue
            if FreshMeat.amount > 2:  # and await self.has_ability(EFFECT_TACTICALJUMP, battle_ruiser):
                target = FreshMeat.closest_to(battle_ruiser)
                if FreshMeat.in_attack_range_of(battle_ruiser, bonus_distance=-1):
                    self.do(battle_ruiser.move(battle_ruiser.position.towards(target, -5)))
                    continue
                if FreshMeat.in_attack_range_of(battle_ruiser, bonus_distance=0):
                    if len(battle_ruiser.orders) > 0:
                        self.do(battle_ruiser.move(battle_ruiser.position))
                    continue
                self.do(battle_ruiser.move(target.position))
                continue
            if not self.assault_enemy_home:
                if (self.enemy_structures
                        and (self.supply_used > 190
                             or not await self.has_ability(EFFECT_TACTICALJUMP, battle_ruiser))):
                    if len(battle_ruiser.orders) < 2:
                        target = self.enemy_structures.random.position.random_on_distance(1)
                        self.do(battle_ruiser.move(target, queue=True))
                    continue
                if self.enemy_structures.filter(lambda x: x.is_visible):
                    if len(battle_ruiser.orders) < 2:
                        target = self.enemy_structures.filter(lambda x: x.is_visible).random
                        self.do(battle_ruiser.move(target.position, queue=True))
                    continue
            if len(battle_ruiser.orders) > 1:
                continue
            if self.enemy_units_and_structures:
                target = self.enemy_units_and_structures.closest_to(battle_ruiser)
                self.do(battle_ruiser.move(target.position))
                continue
            if self.general and battle_ruiser.health_percentage >= 1:
                if battle_ruiser.distance_to(self.general) > 6:
                    self.do(battle_ruiser.move(self.general.position))
                continue
            elif battle_ruiser.distance_to(self.homeBase) > 10:
                self.do(battle_ruiser.move(self.homeBase.position))
                continue

    async def move_cyclones(self):
        if not self.cyclones:
            return
        units_to_ignore = [UnitTypeId.CHANGELINGMARINE, UnitTypeId.CHANGELINGMARINESHIELD]
        cyclones = self.cyclones
        enemy_threats = self.enemy_units_and_structures.filter(lambda x: x.can_attack_ground).exclude_type(
            units_to_ignore)
        cyclones_full_health = True
        if self.cyclone_left <= 0 and self.cyclones.amount >= 4:
            for cyclone in cyclones:
                if cyclone.health_percentage < 1:
                    cyclones_full_health = False
                if cyclone.health_percentage < 0.5:
                    self.pick_fight = False
                    break
            if cyclones_full_health:
                self.pick_fight = True
        else:
            self.pick_fight = False
        for cyclone in cyclones:
            enemies_in_threath_range = enemy_threats.filter(
                lambda x: x.distance_to(
                    cyclone) < x.radius + x.ground_range + cyclone.radius + 3 or x.distance_to(
                    cyclone) < cyclone.ground_range)
            closest_snapshot = self.closest_snapshot_in_range(cyclone)
            if await self.avoid_own_nuke(cyclone):
                continue
            if await self.avoid_storms(cyclone):
                continue
            if await self.avoid_liberation_zones(cyclone):
                continue
            if self.cyclone_left < 10:
                if await self.avoid_enemy_siegetanks(cyclone):
                    continue
            if (cyclone.distance_to(self.homeBase) < 10
                    and cyclone.health_percentage < 0.9
                    and not self.enemy_units.closer_than(self.defence_radius, self.start_location)):
                continue
            if cyclone.has_buff(BuffId.LOCKON):
                closest_enemy = None
                enemy_cyclones = self.enemy_units.of_type(UnitTypeId.CYCLONE).closer_than(20, cyclone)
                enemy_ground_threats = self.enemy_units.filter(lambda x: x.can_attack_ground)
                if enemy_cyclones:
                    closest_enemy = enemy_cyclones.closest_to(cyclone)
                elif enemy_ground_threats:
                    closest_enemy = enemy_ground_threats.closest_to(cyclone)
                if closest_enemy:
                    self.do(cyclone.move(cyclone.position.towards(closest_enemy, -10)))
                    continue
                else:
                    self.do(cyclone.move(self.start_location))
                    continue
            abilities = await self.get_available_abilities(cyclone)
            if CANCEL_LOCKON in abilities:
                if enemy_threats:
                    if enemies_in_threath_range:
                        closest_threath = enemies_in_threath_range.closest_to(cyclone)
                        self.do(cyclone.move(cyclone.position.towards(closest_threath, -10)))
                        continue
                    else:
                        if closest_snapshot:
                            self.do(cyclone.move(cyclone.position.towards(closest_snapshot, -10)))
                            continue
                        target = enemy_threats.closest_to(cyclone)
                        self.do(cyclone.move(target.position))
                        continue  # continue for loop, dont execute any of the following
                else:
                    continue  # continue for loop, dont execute any of the following

            # Wait at home until cyclone is repaired
            # if cyclone.distance_to(self.homeBase) < 10 and cyclone.health_percentage < 1:
            #     continue
            if LOCKON_LOCKON in abilities:
                if closest_snapshot:
                    self.do(cyclone.move(cyclone.position.towards(closest_snapshot, -10)))
                    continue
                if enemy_threats:
                    closestEnemy = enemy_threats.closest_to(cyclone)
                    self.do(cyclone.attack(closestEnemy.position))
                    continue  # continue for loop, dont execute any of the following
                if self.pick_fight:
                    if self.enemy_structures:
                        closestEnemy = self.enemy_structures.closest_to(cyclone)
                        self.do(cyclone.attack(closestEnemy.position))
                        continue  # continue for loop, dont execute any of the following
                    else:
                        self.do(cyclone.attack(self.enemy_start_location))
                        continue  # continue for loop, dont execute any of the following

            if enemy_threats:
                if enemies_in_threath_range:
                    closest_threath = enemies_in_threath_range.closest_to(cyclone)
                    self.do(cyclone.move(cyclone.position.towards(closest_threath, -10)))
                    continue
                else:
                    if closest_snapshot:
                        self.do(cyclone.move(cyclone.position.towards(closest_snapshot, -10)))
                        continue
                    target = enemy_threats.closest_to(cyclone)
                    self.do(cyclone.attack(target.position))
                    continue  # continue for loop, dont execute any of the following

            if self.thors.exists and (cyclone.health_percentage > 0.5):
                closest_thor = self.thors.closest_to(cyclone)
                if cyclone.distance_to(closest_thor) > 10:
                    self.do(cyclone.move(closest_thor.position))
                    continue
            if cyclone.distance_to(self.homeBase) > 10:
                self.do(cyclone.move(self.homeBase.position))
                continue  # continue for loop, dont execute any of the following

    async def move_marauders(self):
        if not self.marauders:
            return
        can_stim = self.medivacs.filter(lambda x: x.energy > 30)
        units_to_ignore = [UnitTypeId.ADEPTPHASESHIFT, UnitTypeId.EGG, UnitTypeId.LARVA]
        enemy_ground_units = self.enemy_units_on_ground.exclude_type(units_to_ignore)
        nuke_ready = False
        if self.ccANDoc.amount > 1:
            limit_for_attack = 2
        else:
            limit_for_attack = 1
        if self.agressive_marines:
            limit_for_agression = 190
        else:
            limit_for_agression = 190
        if ((self.supply_used > limit_for_agression or nuke_ready) and not self.target_of_assault
                and not self.thors):
            if self.enemy_structures and not self.enemy_structures.visible:
                self.target_of_assault = self.enemy_structures.random.position
        if (self.target_of_assault
                and (self.enemy_structures.visible or self.marauders.closer_than(2, self.target_of_assault))):
            self.target_of_assault = None
        if self.target_of_assault and self.enemy_units.amount >= 5:
            self.target_of_assault = None
        outpost = await self.get_outpost()
        units_to_fear = self.enemy_units.filter(lambda x: not x.is_hallucination).of_type(
            [UnitTypeId.BANELING, UnitTypeId.ARCHON, UnitTypeId.DARKTEMPLAR])
        ArmoredTargets = enemy_ground_units.filter(lambda x: x.is_armored)
        secondary_targets = self.enemy_structures.filter(lambda x: x.is_visible)
        secondary_target = None
        if self.general and secondary_targets:
            secondary_target = secondary_targets.closest_to(self.general)

        if self.cc.not_ready:
            CC_under_construction = True
            target_CC = self.cc.not_ready.closest_to(self.homeBase)
        else:
            CC_under_construction = False
        siegetanks_need_protection = self.siegetanks_sieged.filter(
            lambda x: not self.enemy_units_on_ground.closer_than(14, x))
        if self.enemy_units.of_type(UnitTypeId.SIEGETANKSIEGED):
            self.kamikaze_target = None
            self.clear_units_in_kamikaze_troops()
        if not self.marauders.filter(lambda x: x.is_in_kamikaze_troops):
            self.kamikaze_target = None
        for marauder in self.marauders:
            if await self.avoid_own_nuke(marauder):
                continue
            if not self.agressive_marines and await self.avoid_enemy_siegetanks(marauder):
                continue
            if self.ccANDoc.amount == 1 \
                    and self.enemy_structures.of_type(UnitTypeId.PLANETARYFORTRESS).closer_than(20, marauder):
                self.kamikaze_target = None
                self.clear_units_in_kamikaze_troops()
                self.do(marauder.move(self.homeBase.position))
                continue
            "don't abandon siege tanks during encounter"
            if siegetanks_need_protection.closer_than(15, marauder) \
                    and not self.siege_behind_wall and not self.agressive_marines:
                closest_siege = siegetanks_need_protection.closest_to(marauder)
                if marauder.distance_to(closest_siege) > 5:
                    self.do(marauder.move(closest_siege.position))
                continue

            if marauder.health_percentage < 1 / 3 and self.supply_used < 190:
                if marauder.is_in_kamikaze_troops:
                    self.remove_from_kamikaze_troops(marauder)
                if marauder.position.distance_to(self.homeBase.position) > 10:
                    if self.enemy_units_on_ground.in_attack_range_of(
                            marauder) and marauder.weapon_cooldown == 0:
                        self.do(marauder.attack(self.homeBase.position))
                        continue  # continue for loop, don't execute any of the following
                    else:
                        self.do(marauder.move(self.homeBase.position))
                        continue  # continue for loop, don't execute any of the following
                elif self.enemy_units_on_ground.closer_than(20, self.homeBase.position):
                    self.do(marauder.attack(enemy_ground_units.closest_to(self.homeBase.position)))
                    continue
                else:
                    continue

            if marauder.is_in_kamikaze_troops and self.kamikaze_target:
                marauder_targets = enemy_ground_units.further_than(self.defence_radius, self.start_location)
                if self.random_kamikaze_target and marauder.distance_to(self.kamikaze_target) < 5:
                    if self.enemy_structures:
                        self.kamikaze_target = self.enemy_structures.random.position
                    else:
                        self.kamikaze_target = random.choice(self.expansion_locations_list)
                elif self.kamikaze_target == self.enemy_third and marauder.distance_to(self.enemy_third) < 5:
                    self.kamikaze_target = self.enemy_natural
                elif self.kamikaze_target == self.enemy_natural and marauder.distance_to(
                        self.enemy_natural) < 5:
                    self.kamikaze_target = self.enemy_start_location
                elif marauder.distance_to(self.enemy_start_location) < 5:
                    self.random_kamikaze_target = True
                    self.kamikaze_target = random.choice(self.expansion_locations_list)
            else:
                marauder_targets = enemy_ground_units
            if marauder.weapon_cooldown != 0:  # Stim when in combat
                if (marauder.health_percentage >= 1
                        and self.ccANDoc.amount >= 2
                        and await self.can_cast(marauder, AbilityId.EFFECT_STIM_MARAUDER)
                        and not marauder.has_buff(BuffId.STIMPACKMARAUDER)
                        and marauder_targets.closer_than(17, marauder).amount > 2
                        and can_stim):
                    self.do(marauder(AbilityId.EFFECT_STIM_MARAUDER))
                    continue  # continue for loop, don't execute any of the following
                elif marauder.health < 100:
                    if self.in_ground_range_of_units(marauder, enemy_ground_units):
                        self.do(marauder.move(
                            marauder.position.towards(enemy_ground_units.closest_to(marauder), -10)))
                        continue
                    elif len(marauder.orders) > 0:
                        self.do(marauder.move(marauder.position))
                        continue

            if units_to_fear.closer_than((marauder.ground_range + marauder.radius), marauder):
                if marauder.weapon_cooldown != 0:
                    if self.siegetanks_sieged.closer_than(15, marauder):
                        closest_siege = self.siegetanks_sieged.closest_to(marauder)
                        if marauder.distance_to(closest_siege) > 4:
                            self.do(marauder.move(closest_siege.position))
                            continue
                        else:
                            self.do(marauder.attack(units_to_fear.closest_to(marauder).position))
                            continue
                    if self.ccANDoc.ready.amount < 3:
                        self.do(marauder.move(
                            self.homeBase.position.towards(units_to_fear.closest_to(marauder), -10)))
                        continue
                    else:
                        self.do(
                            marauder.move(marauder.position.towards(units_to_fear.closest_to(marauder), -10)))
                        continue
                else:
                    self.do(marauder.attack(units_to_fear.closest_to(marauder.position)))
                    continue
            # check if enemy ground units exists
            if (marauder_targets.amount >= limit_for_attack
                    or marauder_targets.closer_than(10, marauder)):
                if ArmoredTargets:
                    priority = ([UnitTypeId.IMMORTAL])
                    armored_targets_in_range = ArmoredTargets.of_type(priority).in_attack_range_of(marauder)
                    if not armored_targets_in_range:
                        armored_targets_in_range = ArmoredTargets.in_attack_range_of(marauder)
                    if armored_targets_in_range:
                        self.do(marauder.attack(armored_targets_in_range.closest_to(marauder)))
                        continue

                enemies_in_range = marauder_targets.exclude_type(units_to_ignore).in_attack_range_of(marauder)
                if enemies_in_range:
                    enemies_in_range_sorted = enemies_in_range.sorted(lambda x: (x.health + x.shield),
                                                                      reverse=False)
                    self.do(marauder.attack(enemies_in_range_sorted[0]))
                    continue
                else:
                    target = marauder_targets.closest_to(marauder)
                    self.do(marauder.attack(target.position))
                    continue
            # elif (len(self.enemy_units_and_structures.flying.filter(lambda x: x.can_attack_ground)) > 2
            #       and not marauder.is_in_kamikaze_troops):
            #     if marauder.position.to2.distance_to(self.homeBase.position.to2) > 10:
            #         self.do(marauder.move(self.homeBase))
            #         continue  # continue for loop, don't execute any of the following

            "don't abandon siegetanks"
            if self.siegetanks_sieged and self.supply_used < 170 and not self.siege_behind_wall:
                front_siege = self.siegetanks_sieged.closest_to(marauder)
                defence_position = front_siege.position
                if marauder.distance_to(defence_position) > 4:
                    self.do(marauder.move(defence_position))
                continue
            if self.show_off and marauder.is_in_kamikaze_troops and self.marines:
                if marauder.distance_to(self.marines.closest_to(marauder)) > 3:
                    self.do(marauder.attack(self.marines.closest_to(marauder).position))
                else:
                    self.do(marauder.attack(marauder.position))
                continue

            if marauder.is_in_kamikaze_troops and self.kamikaze_target:
                self.do(marauder.attack(self.kamikaze_target))
                continue
            if secondary_target:
                self.do(marauder.attack(secondary_target.position))
                continue
            # if no enemies, but thor exists then follow it
            if self.general and self.thors:
                if marauder.distance_to(self.general) > 10:
                    self.do(marauder.move(self.general))
                    continue
            if self.target_of_assault:
                self.do(marauder.attack(self.target_of_assault.position))
                continue
            if CC_under_construction:
                if marauder.position.to2.distance_to(target_CC.position.to2) > 8:
                    self.do(marauder.move(target_CC))
                continue  # continue for loop, don't execute any of the following
            if marauder.position.to2.distance_to(outpost.position.to2) > 10:
                self.do(marauder.move(outpost.position))
                continue  # continue for loop, don't execute any of the following

    async def move_squad(self):
        if not self.squad_group:
            return
        units_to_ignore_marine = [UnitTypeId.ADEPTPHASESHIFT, UnitTypeId.EGG, UnitTypeId.LARVA]
        if self.ccANDoc.amount < 3 or self.scvs.amount < 30:
            defend_location = self.start_location
            valid_enemies = (self.enemy_units_and_structures.filter(
                lambda x: x.type_id not in units_to_ignore_marine and x.distance_to(defend_location) < 25))
        else:
            defend_location = await self.get_next_expansion_to_defend()
            if not defend_location:
                defend_location = self.game_info.map_center
            valid_enemies = (self.enemy_units_and_structures.filter(
                lambda x: x.type_id not in units_to_ignore_marine and x.distance_to(defend_location) < 15))
        squad_center = self.squad_group.center
        closest_enemy = None
        marine_scan = True
        if valid_enemies:
            closest_enemy = valid_enemies.closest_to(defend_location)
        for unit in self.squad_group:
            if (unit.did_take_first_hit
                    and self.ccANDoc
                    and not self.enemy_units_and_structures.closer_than(20, unit)
                    and marine_scan):
                for cc in self.ccANDoc:
                    if await self.has_ability(AbilityId.SCANNERSWEEP_SCAN, cc):
                        self.do(self.homeBase(AbilityId.SCANNERSWEEP_SCAN, unit.position))
                        print("Scan for cloaked units!")
                        marine_scan = False
                        break
        for unit in self.squad_group:
            changelings = self.enemy_units.of_type(
                [UnitTypeId.CHANGELINGMARINE, UnitTypeId.CHANGELINGMARINESHIELD])
            if changelings and changelings.in_attack_range_of(unit):
                self.do(unit.attack(changelings.closest_to(unit)))
                continue

            if closest_enemy:
                self.do(unit.attack(closest_enemy.position))
                continue
            elif defend_location:
                if len(unit.orders) < 2 and self.scan_timer > 80:
                    hidden_enemies = self.enemy_units.filter(
                        lambda x: x.is_cloaked or x.is_burrowed).closer_than(8, defend_location)
                    if (squad_center.is_closer_than(5, defend_location)
                            and self.orbitalcommand
                            and (self.has_creep(unit.position)
                                 or hidden_enemies)):
                        scanner = self.orbitalcommand.sorted(lambda x: x.energy, reverse=True)[0]
                        if scanner and scanner.energy > 50 and await self.has_ability(SCANNERSWEEP_SCAN,
                                                                                      scanner):
                            self.do(scanner(AbilityId.SCANNERSWEEP_SCAN, unit.position))
                            self.scan_timer = 0
                            if self.chat:
                                await self._client.chat_send("Clear this mining site boys!.", team_only=False)
                            return
                    if not self.already_pending(COMMANDCENTER):
                        self.do(unit.attack(defend_location.random_on_distance(4)))
                        self.do(unit.attack(defend_location.random_on_distance(4), queue=True))
                        self.do(unit.attack(defend_location.random_on_distance(4), queue=True))
                        self.do(unit.attack(defend_location.random_on_distance(4), queue=True))
                    elif unit.distance_to(defend_location) > 6:
                        self.do(unit.attack(defend_location.random_on_distance(5)))
                        self.do(unit.attack(defend_location.random_on_distance(5), queue=True))
                        self.do(unit.attack(defend_location.random_on_distance(5), queue=True))
                        self.do(unit.attack(defend_location.random_on_distance(5), queue=True))
                        self.do(unit.attack(defend_location.random_on_distance(5), queue=True))
                        self.do(unit.attack(defend_location.random_on_distance(5), queue=True))

    async def get_homeBase(self):
        if self.homeBase != None:
            return self.homeBase
        if (self.ccANDoc.amount + self.townhalls_flying.amount) > 2:
            self.homeBase = self.ccANDoc.closest_to(self.natural)
        elif self.ccANDoc:
            self.homeBase = self.ccANDoc.closest_to(self.start_location)
        if not self.homeBase:
            self.homeBase = self.start_location
        return self.homeBase

    async def get_outpost(self):
        if not self.ccANDoc:
            self.outpost = self.start_location
        elif self.enemy_start_location:
            self.outpost = self.ccANDoc.closest_to(self.enemy_start_location).position
        else:
            self.outpost = self.ccANDoc.furthest_to(self.start_location).position
        return self.outpost

    async def repair_planetaries(self):
        for PF in self.structures(UnitTypeId.PLANETARYFORTRESS):
            if PF.did_take_first_hit:
                for scv in self.scvs.closer_than(10, PF):
                    self.do(scv(EFFECT_REPAIR_SCV, PF))

    async def call_for_mules(self):
        for cc in self.townhalls_flying.idle:
            if cc.health_percentage < 1:
                self.do(cc(MOVE, self.start_location, queue=True))
            expand = await self.get_next_expansion()
            if not expand:
                expand = random.choice(self.vespene_geyser)
                expand = await self.find_placement(UnitTypeId.COMMANDCENTER,
                                                   near=expand.position.random_on_distance(8))
            self.do(cc(AbilityId.LAND, expand, queue=True))
            continue
        if self.ccANDoc.ready:
            time_between_scans = 85
            energy_limit_to_mule = 52
            if self.minerals > 2000 and not self.next_location_to_be_scanned and self.limit_vespene == 0:
                if self.minerals > 10000:
                    energy_limit_to_mule = 1000
                else:
                    energy_limit_to_mule = 150
            elif self.scan_enemy_at_4_min and 230 > self.time > 170 and self.ccANDoc.filter(
                    lambda x: x.energy > 50).amount < 2:
                energy_limit_to_mule = 100
            elif self.scan_cloaked_enemies:  # and self.ccANDoc.filter(lambda x: x.energy > 50).amount < 2:
                energy_limit_to_mule = 100
            if (not self.scan_cloaked_enemies
                    and self.enemy_units.exclude_type(UnitTypeId.OBSERVER).filter(lambda x: x.is_cloaked)):
                if self.enemy_units.of_type(UnitTypeId.BANSHEE):
                    self.mineral_field_turret = True
                else:
                    self.build_missile_turrets = True
                self.fast_engineeringbay = True
                self.scan_cloaked_enemies = True
                self.raven_left = 100
                # self.priority_raven = True
                # self.scv_limit += 5
                print("Hidden units detected!")
                if self.chat:
                    await self._client.chat_send("Hidden units detected.", team_only=False)

            if self.scan_timer > time_between_scans and not self.units(UnitTypeId.RAVEN):
                if self.enemy_units_and_structures.of_type([UnitTypeId.TEMPEST]):
                    cloaked_enemy_units = self.enemy_units.of_type([UnitTypeId.TEMPEST]).filter(
                        lambda x: x.is_snapshot)
                elif self.leapfrog_mines or self.minerals > 1000:
                    cloaked_enemy_units = self.enemy_units.filter(lambda x: x.is_cloaked or x.is_burrowed)
                else:
                    cloaked_enemy_units = self.enemy_units.filter(
                        lambda x: x.is_cloaked or x.is_burrowed).exclude_type(UnitTypeId.OBSERVER)
                if cloaked_enemy_units and self.orbitalcommand:
                    # print(cloaked_enemy_units.random)
                    oc = max(self.orbitalcommand, key=lambda x: x.energy)
                    if oc.energy > 50:
                        self.scan_timer = 0
                        self.do(oc(AbilityId.SCANNERSWEEP_SCAN,
                                   cloaked_enemy_units.random.position))
                        return
            if self.iteraatio % 10 == 0 and self.orbitalcommand:
                oc = max(self.orbitalcommand, key=lambda x: x.energy)
                if oc.energy > energy_limit_to_mule:
                    if self.scan_enemy_at_4_min and self.time > 230:
                        self.scan_enemy_at_4_min = False
                        target = None
                        if self.enemy_structures.of_type(UnitTypeId.PYLON):
                            target = self.enemy_structures.of_type(UnitTypeId.PYLON). \
                                closer_than(20, self.enemy_start_location).furthest_to(
                                self.enemy_start_location).position
                        if target:
                            self.do(oc(AbilityId.SCANNERSWEEP_SCAN, target))
                            return
                    if self.next_location_to_be_scanned:
                        self.do(oc(AbilityId.SCANNERSWEEP_SCAN, self.next_location_to_be_scanned))
                        self.next_location_to_be_scanned = None
                        return
                    else:
                        rich_mineralfield = [UnitTypeId.PURIFIERRICHMINERALFIELD,
                                             UnitTypeId.PURIFIERRICHMINERALFIELD750]
                        mineral_fields_for_mule = self.mineral_field.exclude_type(rich_mineralfield)
                        healthy_ccs = self.ccANDoc.filter(lambda x: x.health_percentage >= 1)
                        mfs = mineral_fields_for_mule.filter(lambda x: healthy_ccs.ready.closer_than(10, x))
                        if mfs:
                            mf = max(mfs, key=lambda x: x.mineral_contents)
                            self.do(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf))

    async def evac_orbital(self):
        for cc in (self.orbitalcommand.ready.idle | self.cc.ready.idle):
            if not self.townhalls_flying and cc.health_percentage < 0.9 and self.enemy_units.closer_than(10,
                                                                                                         cc):
                if len(cc.orders) == 0:
                    self.do(cc(AbilityId.LIFT, queue=True))
                    self.lift_cc_once = False
                    continue
        for cc in self.orbitalcommand.ready.idle:
            if not self.super_greed:
                is_in_expansion_location = False
                for expansion in self.expansion_locations_list:
                    if cc.position.distance_to(expansion) < 3:
                        is_in_expansion_location = True
                        break
                if not is_in_expansion_location:
                    if cc.energy >= 50 and self.mineral_field.visible:
                        mf = self.mineral_field.closest_to(self.start_location)
                        self.do(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf))
                    elif len(cc.orders) != 0:
                        self.do(cc(AbilityId.CANCEL_QUEUECANCELTOSELECTION))
                    else:
                        self.do(cc(AbilityId.LIFT, queue=True))
                        self.build_cc_home = False

    async def build_workers(self, maxscv):
        "Make supplydepot after scv"
        if self.minerals < 50 or (self.minerals > 1000 and self.scvs.amount > 16):
            return
        if self.scvs.amount >= 13 and not self.already_pending(
                UnitTypeId.SUPPLYDEPOT) and self.supplydepots.amount == 0:
            return

        "Slowdown scv production if under attack"
        if self.enemy_units.closer_than(self.defence_radius, self.homeBase).amount > 2:
            if self.already_pending(UnitTypeId.SCV):  # and not self.greedy_scv_consrtuction:
                return

        if self.home_in_danger and self.enemy_units_on_ground.of_type(UnitTypeId.PROBE).amount > 2:
            return

        # if self.ccANDoc.ready.amount == 3 and self.already_pending(UnitTypeId.COMMANDCENTER):
        #     return

        scv_in_production = 0
        for cc in self.ccANDoc:
            if len(cc.orders) != 0:
                if cc.orders[0].ability.id in [AbilityId.COMMANDCENTERTRAIN_SCV]:
                    scv_in_production += 1
        if scv_in_production >= self.scv_build_speed:
            return

        if await self.we_need_orbital():
            return

        if self.greedy_third and self.ccANDoc.ready.amount == 2:
            return

        scvTotal = (self.supply_workers + self.already_pending(UnitTypeId.SCV))
        if scvTotal >= maxscv:
            return

        if (self.can_afford(UnitTypeId.SCV) and self.supply_used < 180
                and self.supply_left > 0 and self.mineral_field.filter(lambda x: x.is_visible)):
            jobs_available = 0 - self.already_pending(UnitTypeId.SCV)
            if self.ccANDoc.amount == 1:
                jobs_available = jobs_available + self.first_base_saturation
            for cc in self.ccANDoc:
                jobs_available = jobs_available + cc.ideal_harvesters - cc.assigned_harvesters
            if (self.greedy_scv_consrtuction
                    or jobs_available > 0):
                for cc in self.ccANDoc.ready.idle.sorted(lambda x: x.surplus_harvesters, reverse=False):
                    if (self.enemy_units.closer_than(10, cc) or not self.mineral_field.closer_than(10, cc)):
                        continue
                    is_in_expansion_location = False
                    for expansion in self.expansion_locations_list:
                        if cc.position.distance_to(expansion) < 3:
                            is_in_expansion_location = True
                            break
                    if not is_in_expansion_location:
                        continue
                    self.training_scv = True
                    self.do(cc.train(UnitTypeId.SCV))
                    return

    async def closest_ramp_to(self, unit):
        ramp = min(
            (ramp for ramp in self.game_info.map_ramps),
            key=lambda r: unit.position.distance_to(r.top_center),
        )
        return ramp

    async def find_potential_supplydepot_locations(self, location):
        p = location.position
        return [
            Point2((p.x - 2.5, p.y - 2.5)),
            Point2((p.x - 2.5, p.y + 2.5)),
            Point2((p.x + 4.5, p.y - 2.5)),
            Point2((p.x + 4.5, p.y + 2.5)),
        ]

    async def find_placement_for_supplydepot(self):
        for structure in (self.barracks | self.factories | self.starports
                          | self.engineeringbays | self.armories
                          | self.ghost_academies | self.fusioncores):
            potential_supplydepot_locations = await self.find_potential_supplydepot_locations(structure)
            for location in potential_supplydepot_locations:
                if await self.can_place(UnitTypeId.SUPPLYDEPOT, location) and not self.units.closer_than(2,
                                                                                                         location):
                    return location
        return None

    async def middle_depot_location(self) -> [Point2]:
        depot_placement_positions = self.main_base_ramp.corner_depots
        d1 = depot_placement_positions.pop()
        d2 = depot_placement_positions.pop()
        d = 2
        if d1.x < d2.x:
            x_position = d1.x + d
        else:
            x_position = d1.x - d
        if d2.y < d1.y:
            y_position = d2.y + d
        else:
            y_position = d2.y - d
        target_depot_location = Point2((x_position, y_position))
        if not await self.can_place(UnitTypeId.SUPPLYDEPOT, target_depot_location):
            if d1.x < d2.x:
                x_position = d2.x - d
            else:
                x_position = d2.x + d
            if d2.y < d1.y:
                y_position = d1.y - d
            else:
                y_position = d1.y + d
            target_depot_location = Point2((x_position, y_position))
        if await self.can_place(UnitTypeId.SUPPLYDEPOT, target_depot_location):
            return target_depot_location
        else:
            return None

    async def safkaa(self):
        if not self.scvs:
            return
        if self.home_in_danger and not self.build_cc_home:
            return
        if self.minerals < 110 or not self.ccANDoc or not self.scvs:
            return
        if self.marine_drop and self.supplydepots.amount == 2 and not self.starports:
            return
        if (self.supplydepots.amount == 1
                and self.ccANDoc.amount == 1
                and not self.delay_expansion
                and not self.build_priority_cyclone
                and not self.build_cc_home
                and not self.super_greed
                and self.supply_left > 1
                and self.first_base_saturation < 0):
            return
        if self.ccANDoc.ready.amount < 2:
            if self.delay_expansion and self.barracks:
                max_pending_sd = 2
            else:
                max_pending_sd = 1
        elif self.more_depots:
            max_pending_sd = 3
        else:
            max_pending_sd = 2
        if self.build_cc_home and self.supplydepots.amount < 3 and self.barracks:
            multiplier = 100
        elif self.delay_expansion and self.supplydepots.amount < 3 and self.barracks:
            multiplier = 100
        else:
            multiplier = 6
        sds_in_production = self.already_pending(UnitTypeId.SUPPLYDEPOT)
        if not self.midle_depo_position:
            self.midle_depo_position = await self.middle_depot_location()
            closest_ramp = await self.closest_ramp_to(self.midle_depo_position)
            self.priority_tank_pos = self.midle_depo_position.towards(closest_ramp.bottom_center, -7)
        if sds_in_production < max_pending_sd and self.supplydepots.amount < 22:
            if self.supply_left < (max_pending_sd - sds_in_production) * multiplier:
                if self.supplydepots.amount < 5 and self.ccANDoc.amount < 3 \
                        and self.ccANDoc.closer_than(3, self.start_location):
                    depot_placement_positions = self.main_base_ramp.corner_depots
                    # Choose any depot location
                    if depot_placement_positions:
                        for pos in depot_placement_positions:
                            if await self.can_place(UnitTypeId.SUPPLYDEPOT, pos):
                                scv = self.select_contractor(pos)
                                if scv:
                                    await self.build(UnitTypeId.SUPPLYDEPOT, pos, build_worker=scv)
                                    print("Supplydepots in production :", sds_in_production)
                                    print("supply depos total",
                                          (len(self.supplydepots.ready) + sds_in_production + 1))
                                    return
                    if await self.can_place(UnitTypeId.SUPPLYDEPOT, self.midle_depo_position):
                        worker = self.select_contractor(self.midle_depo_position)
                        if worker:
                            self.do(worker.build(UnitTypeId.SUPPLYDEPOT, self.midle_depo_position))
                            print("Supplydepots in production :", sds_in_production)
                            print("supply depots total", (len(self.supplydepots.ready) + sds_in_production + 1))
                        return
                location = await self.find_placement_for_supplydepot()
                if location:
                    await self.build(UnitTypeId.SUPPLYDEPOT, location,
                                     build_worker=self.select_contractor(location))
                    print("Supplydepots in production :", sds_in_production)
                    print("Building supplydepot", (len(self.supplydepots.ready) + sds_in_production + 1))
                    return
                if self.supplydepots:
                    expand = random.choice(self.supplydepots)
                else:
                    expand = self.start_location
                await self.build(UnitTypeId.SUPPLYDEPOT, near=expand.position.random_on_distance(10),
                                 build_worker=self.select_contractor(expand))
                print("Building supplydepot", (len(self.supplydepots.ready) + sds_in_production + 1))

    async def build_refinery(self):
        if self.home_in_danger:
            return
        if self.cc_first:
            return
        if self.wait_until_4_orbital_ready:
            return
        if self.minerals < self.vespene + 100:  # we have enough vespene. No refinery needed.
            return
        if self.super_greed:
            return
        if self.mech_build and self.ccANDoc.amount == 2 and self.refineries.amount >= 2:
            return
        if not self.expand_for_vespene and self.already_pending(UnitTypeId.REFINERY):
            return
        elif self.barracks or (self.fast_vespene and self.supplydepots):
            if self.ccANDoc.amount == 1:
                if self.refineries_in_first_base >= 2 and self.factories:
                    maxrefinery = self.refineries_in_first_base
                elif self.refineries_in_first_base > 0:
                    maxrefinery = 1
                else:
                    maxrefinery = 0
            elif self.ccANDoc.amount == 2:
                maxrefinery = self.refineries_in_second_base
            elif self.limit_vespene > 0:
                maxrefinery = self.limit_vespene
                if self.vespene > 300:
                    return
                if self.already_pending(UnitTypeId.REFINERY):
                    return
            else:
                maxrefinery = 100

            refineries = self.refineries.filter(
                lambda x: x.vespene_contents > 200 and self.ccANDoc.closer_than(10, x)).amount
            if refineries < maxrefinery:
                await self.execute_build_refinery()

    async def execute_build_refinery(self):
        if self.ccANDoc.amount <= 2:
            CC_that_need_refinery = self.ccANDoc.ready
        else:
            CC_that_need_refinery = self.ccANDoc.filter(lambda x: x.health_percentage > 0.6)
        if self.refineries_in_first_base == 0:
            max_pending_refineries = 1
        elif self.expand_fast_for_vespene:
            max_pending_refineries = 4
        else:
            max_pending_refineries = 2
        if self.minerals < 75:
            return
        for cc in CC_that_need_refinery:
            gasmines = self.vespene_geyser.closer_than(10.0, cc)
            for gasmine in gasmines:
                if not self.refineries.closer_than(1.0, gasmine).exists:
                    worker = self.select_build_worker(gasmine)
                    if worker is None:
                        return
                    if (self.already_pending(UnitTypeId.REFINERY) + self.already_pending(
                            UnitTypeId.REFINERYRICH)) >= max_pending_refineries:
                        return
                    self.do(worker.build(UnitTypeId.REFINERY, gasmine))
                    return

    async def buildings(self, maxbarracks, iteration):
                if self.home_in_danger:
                    return
                if self.cc_first:
                    return
                if self.delay_starport and not self.build_extra_factory_and_starport:
                    self.delay_starport = False
                # if self.home_in_danger and self.supplydepots:
                #     if len(self.barracks | self.barracksflyings) < 1:
                #         if (not self.already_pending(BARRACKS)):
                #             if self.can_afford(BARRACKS):
                #                 await self.build_for_me(BARRACKS)
                #             return
                #     return
                if not self.scvs:
                    return
                if self.minerals > 500 and self.vespene > 500:
                    if self.build_extra_factory_and_starport and self.limit_vespene == 0:
                        print("Enough bank. Starting to tech up!")
                        if self.chat:
                            await self._client.chat_send("Making more tech buildings.", team_only=False)
                        if self.build_extra_factories and not self.build_extra_starports:
                            self.maxfactory = 10
                        elif not self.build_extra_factories and self.build_extra_starports:
                            self.max_starports = 8
                        else:
                            self.maxfactory = 4
                            self.max_starports = 4
                        self.build_extra_factory_and_starport = False
                if self.supplydepots.ready.exists:
                    if (len(self.barracks.ready | self.barracksflyings) + self.already_pending(
                            UnitTypeId.BARRACKS)) < maxbarracks:
                        if self.barracks and self.max_starports == 0 and not self.factories:
                            pass
                        elif not self.already_pending(UnitTypeId.BARRACKS) or self.super_fast_barracks:
                            if self.can_afford(UnitTypeId.BARRACKS):
                                await self.build_for_me(UnitTypeId.BARRACKS)
                            return
                        if not self.expand_for_vespene and self.can_afford(UnitTypeId.BARRACKS) \
                                and self.already_pending(UnitTypeId.BARRACKS) < 3:
                            await self.build_for_me(UnitTypeId.BARRACKS)
                            return

                    "build missile turrets to detect cloaked units."
                    if (not self.already_pending(UnitTypeId.MISSILETURRET)
                            and self.engineeringbays.ready
                            and self.can_afford(UnitTypeId.MISSILETURRET)):
                        if self.build_missile_turrets:
                            for command in self.ccANDoc:
                                if not self.structures(UnitTypeId.MISSILETURRET).closer_than(10, command):
                                    await self.build(UnitTypeId.MISSILETURRET,
                                                     near=command.position.towards(self.game_info.map_center, 5),
                                                     build_worker=self.scvs.random)
                                    return
                        if self.mineral_field_turret:
                            for command in self.ccANDoc:
                                is_in_expansion_location = False
                                for expansion in self.expansion_locations_list:
                                    if command.position.distance_to(expansion) < 3:
                                        is_in_expansion_location = True
                                        break
                                if not is_in_expansion_location:
                                    continue
                                if self.mineral_field.closer_than(10.0, command.position):
                                    mineral_line_center = self.mineral_field.closer_than(10.0, command.position).center
                                    if self.structures(UnitTypeId.MISSILETURRET).closer_than(7, mineral_line_center):
                                        continue

                                    def sorted_turret_locations(loc):
                                        return loc.distance_to(mineral_line_center)

                                    positions = await find_potential_minral_line_turret_locations(command.position)
                                    print(positions)
                                    pos = None
                                    positions.sort(key=sorted_turret_locations)
                                    print(positions)
                                    for possible_position in positions:
                                        if await self.can_place(UnitTypeId.MISSILETURRET, [possible_position]) \
                                                and not self.mines_burrowed.closer_than(2, possible_position):
                                            pos = possible_position
                                            break
                                    if pos and not self.structures(UnitTypeId.MISSILETURRET).closer_than(5, pos):
                                        worker = self.select_contractor(pos)
                                        if worker:
                                            self.do(worker.build(UnitTypeId.MISSILETURRET, position=pos))
                                            print("Building", UnitTypeId.MISSILETURRET.name)
                                        return

                    # if self.priority_tank:
                    #     return

                    can_build_starport = True
                    if not self.build_extra_factory_and_starport and self.vespene < 500:
                        can_build_starport = False
                    elif self.build_extra_factory_and_starport \
                            and self.factories.amount + self.factoriesflying.amount < self.maxfactory:
                        if self.starports:
                            can_build_starport = False
                    if self.structures(UnitTypeId.BARRACKSTECHLAB).ready and not self.ghost_academies \
                            and self.MaxGhost > 0 and self.orbitalcommand.ready.amount >= 2:
                        if self.can_afford(UnitTypeId.GHOSTACADEMY) and not self.already_pending(
                                UnitTypeId.GHOSTACADEMY):
                            await self.build_for_me(UnitTypeId.GHOSTACADEMY)
                        return
                    elif (self.engineeringbays.amount < 1
                          and (
                                  self.fast_engineeringbay and self.orbitalcommand.ready.amount >= 2 and not self.priority_raven)):
                        if self.can_afford(UnitTypeId.ENGINEERINGBAY) and not self.already_pending(
                                UnitTypeId.ENGINEERINGBAY):
                            await self.build_for_me(UnitTypeId.ENGINEERINGBAY)
                    elif (self.engineeringbays.amount < self.max_engineeringbays
                          and (self.orbitalcommand.ready.amount >= 3)):
                        if self.can_afford(UnitTypeId.ENGINEERINGBAY) and not self.already_pending(
                                UnitTypeId.ENGINEERINGBAY):
                            await self.build_for_me(UnitTypeId.ENGINEERINGBAY)
                    if self.delay_expansion:
                        return
                    if self.delay_factory:
                        if self.orbitalcommand.ready.amount > 1:
                            self.delay_factory = False
                        return

                    if self.minerals < 175 and self.factories.ready:
                        return

                    if self.barracks.ready.exists and \
                            self.factories.ready.amount + self.factoriesflying.amount + \
                            self.already_pending(UnitTypeId.FACTORY) < self.maxfactory:
                        if not self.build_extra_factory_and_starport and self.vespene < self.factories.amount * 200:
                            pass
                        elif self.build_extra_factory_and_starport and self.already_pending(UnitTypeId.FACTORY):
                            pass
                        elif (self.factories or self.factoriesflying) and self.ccANDoc.amount == 1 \
                                and not self.mech_build and not self.delay_starport:
                            pass
                        elif self.can_afford(UnitTypeId.FACTORY):
                            if self.medivacs.amount >= 1 or self.already_pending(UnitTypeId.MEDIVAC) \
                                    or self.mech_build or self.liberators or self.already_pending(UnitTypeId.LIBERATOR):
                                await self.build_for_me(UnitTypeId.FACTORY)
                                return
                            if self.factories.amount + self.factoriesflying.amount == 0:
                                await self.build_for_me(UnitTypeId.FACTORY)
                                return
                            if self.maxmedivacs == 0 and self.starports:
                                await self.build_for_me(UnitTypeId.FACTORY)
                                return
                            if self.max_starports == 0 or self.delay_starport:
                                await self.build_for_me(UnitTypeId.FACTORY)
                                return

                    max_armory = 1
                    if self.upgrade_mech and self.refineries.ready.amount >= 5:
                        max_armory = 2

                    if (self.armories.ready.amount < max_armory
                            and not self.already_pending(UnitTypeId.ARMORY)
                            and self.build_armory
                            and not self.delay_expansion
                            and self.factories.ready
                            and ((
                                         self.fast_armory and self.ccANDoc.ready.amount >= 2) or self.ccANDoc.ready.amount >= 3)):
                        if self.can_afford(UnitTypeId.ARMORY) and self.factories.ready.exists:
                            await self.build_for_me(UnitTypeId.ARMORY)
                            return

                    elif (((self.starports.amount + self.starportflying.amount) < self.max_starports)
                          and not self.delay_expansion
                          and not self.already_pending(UnitTypeId.STARPORT)
                          and not self.delay_starport
                          and can_build_starport):
                        if self.factories.ready.exists and self.can_afford(UnitTypeId.STARPORT) and self.minerals > 175:
                            await self.build_for_me(UnitTypeId.STARPORT)

                    elif (not self.fusioncores
                          and (self.upgrade_liberator and self.liberators and self.structures(
                                UnitTypeId.STARPORTTECHLAB)
                               or (self.last_phase and self.max_BC > 0))):
                        if self.structures(UnitTypeId.STARPORTTECHLAB):
                            if self.can_afford(UnitTypeId.FUSIONCORE) and not self.already_pending(
                                    UnitTypeId.FUSIONCORE):
                                await self.build_for_me(UnitTypeId.FUSIONCORE)

                    # # lift barracks or factory if threre is over 2 thors or tanks nearby
                    # if self.iteraatio % 250 == 0 and self.ccANDoc.ready.amount > 2:
                    #     for sp in (self.factories.ready | self.barracks.ready | self.starports.ready):
                    #         machinery = (self.thors | self.siegetanks)
                    #         tooClose = machinery.closer_than(7, sp)
                    #         if len(tooClose) > 1:
                    #             self.do(sp(LIFT))
                    #             print("logistic factory lift")
                    #             break

    async def landbuildings(self):
        flyingStructures = self.barracksflyings.idle
        for flyStr in flyingStructures:
            fly_str_loc = await self.find_placement_for_barracks()
            if fly_str_loc:
                self.do(flyStr(AbilityId.LAND, fly_str_loc))
                continue
        if not self.doner_location:
            for flyStr in (self.factoriesflying.idle | self.starportflying.idle):
                fly_str_loc = await self.find_placement_for_barracks()
                if fly_str_loc:
                    self.do(flyStr(AbilityId.LAND, fly_str_loc))
                    continue

    async def on_unit_created(self, unit: Unit):
        if self.reaper_haras and unit.type_id in [UnitTypeId.REAPER]:
            self.do(unit.move(self.enemy_start_location, queue=True))
        if unit.type_id in [UnitTypeId.BANSHEE]:
            self.banshee_left = self.banshee_left - 1
        if unit.type_id in [UnitTypeId.HELLION]:
            self.hellion_left = self.hellion_left - 1
        if unit.type_id in [UnitTypeId.WIDOWMINE]:
            self.mines_left = self.mines_left - 1
            # self.do(unit.move(self.enemy_start_location))
        if unit.type_id in [UnitTypeId.CYCLONE]:
            self.cyclone_left = self.cyclone_left - 1
        if unit.type_id in [UnitTypeId.RAVEN]:
            self.raven_left = self.raven_left - 1
        if unit.type_id in [UnitTypeId.LIBERATOR]:
            self.liberator_left -= 1

    async def do_research(self):
        if self.build_cc_home:
            return True
        if self.priority_tank:
            return True
        if self.priority_raven:
            return True
        if self.nuke_rush:
            return True
        if self.upgrade_mech and self.vespene > 100 and self.minerals > 100:
            for facility in self.armories.ready.idle:
                abilities = await self.get_available_abilities(facility)
                for upgrade_level in range(1, 4):
                    upgrade_armor_id = getattr(sc2.constants,
                                               "ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL" + str(
                                                   upgrade_level))
                    upgrade_vehicleweapon_id = getattr(sc2.constants,
                                                       "ARMORYRESEARCH_TERRANVEHICLEWEAPONSLEVEL" + str(
                                                           upgrade_level))
                    upgrade_shipweapon_id = getattr(sc2.constants,
                                                    "ARMORYRESEARCH_TERRANSHIPWEAPONSLEVEL" + str(
                                                        upgrade_level))
                    if (upgrade_vehicleweapon_id in abilities
                            and self.can_afford(upgrade_vehicleweapon_id)
                            and self.upgrade_vehicle_weapons):
                        self.do(facility(upgrade_vehicleweapon_id))
                        return False
                    if (upgrade_armor_id in abilities
                            and self.can_afford(upgrade_armor_id)
                            and not self.upgrade_marine_defence_and_mech_attack):
                        self.do(facility(upgrade_armor_id))
                        return False
                    if (upgrade_shipweapon_id in abilities
                            and self.can_afford(upgrade_shipweapon_id)):
                        self.do(facility(upgrade_shipweapon_id))
                        return False

        for facility in self.structures(UnitTypeId.FACTORYTECHLAB).ready.idle:
            if self.build_cc_home:
                break
            abilities = await self.get_available_abilities(facility)
            # if self.armories.ready:
            #     print(abilities)
            if self.research_blue_flame and AbilityId.RESEARCH_INFERNALPREIGNITER in abilities and self.can_afford(
                    AbilityId.RESEARCH_INFERNALPREIGNITER) \
                    and (self.units(UnitTypeId.HELLION) or self.units(UnitTypeId.HELLIONTANK)):
                self.do(facility(AbilityId.RESEARCH_INFERNALPREIGNITER))
                print("upgrade AbilityId.RESEARCH_INFERNALPREIGNITER")
                continue
            if ((self.mines.amount + self.mines_burrowed.amount + self.mines_left >= 10)
                    and self.can_afford(AbilityId.RESEARCH_DRILLINGCLAWS)
                    and self.mines
                    and AbilityId.RESEARCH_DRILLINGCLAWS in abilities):
                self.do(facility(AbilityId.RESEARCH_DRILLINGCLAWS))
                continue
            if self.cyclones.amount >= 2 and self.can_afford(
                    RESEARCH_CYCLONELOCKONDAMAGE) and AbilityId.RESEARCH_CYCLONELOCKONDAMAGE in abilities:
                self.do(facility(AbilityId.RESEARCH_CYCLONELOCKONDAMAGE))
                continue
            if self.research_servos and self.can_afford(
                    AbilityId.RESEARCH_SMARTSERVOS) and AbilityId.RESEARCH_SMARTSERVOS in abilities:
                self.do(facility(AbilityId.RESEARCH_SMARTSERVOS))
                continue
        if self.fusioncores and self.can_afford(AbilityId.RESEARCH_BATTLECRUISERWEAPONREFIT) \
                and (self.battlecruisers or self.already_pending(UnitTypeId.BATTLECRUISER)) \
                and not self.already_pending(UpgradeId.BATTLECRUISERENABLESPECIALIZATIONS):
            for facility in self.fusioncores.ready.idle:
                # abilities = await self.get_available_abilities(facility)
                # if (AbilityId.RESEARCH_BATTLECRUISERWEAPONREFIT in abilities
                self.do(facility(AbilityId.RESEARCH_BATTLECRUISERWEAPONREFIT))
                return False
        if self.upgrade_liberator and self.can_afford(RESEARCH_ADVANCEDBALLISTICS):
            for facility in self.fusioncores.ready.idle:
                abilities = await self.get_available_abilities(facility)
                if FUSIONCORERESEARCH_RESEARCHBALLISTICRANGE in abilities:
                    self.do(facility(AbilityId.FUSIONCORERESEARCH_RESEARCHBALLISTICRANGE))
                    return False
        if (not self.already_pending(SHIELDWALL)
                and self.refineries.ready.amount >= 2
                and not self.build_priority_cyclone
                and self.max_marine > 0
                and self.research_combatshield):
            for facility in self.structures(BARRACKSTECHLAB).ready.idle:
                if self.can_afford(RESEARCH_COMBATSHIELD):
                    print("upgrade COMBATSHIELD")
                    self.do(facility(AbilityId.RESEARCH_COMBATSHIELD))
                return False
        if (self.refineries.ready.amount >= 2 and self.research_stimpack and not self.build_priority_cyclone
                and (self.medivacs or self.already_pending(UnitTypeId.MEDIVAC) or self.agressive_marines)):
            if not self.already_pending(STIMPACK):
                for facility in self.structures(BARRACKSTECHLAB).ready.idle:
                    if self.can_afford(BARRACKSTECHLABRESEARCH_STIMPACK):
                        print("upgrade STIMPACK")
                        self.do(facility(AbilityId.BARRACKSTECHLABRESEARCH_STIMPACK))
                        return False
                    if self.expand_for_vespene:
                        return False
                    else:
                        return True
        if self.research_concussiveshels and (self.cyclones or self.cyclone_left <= 0):
            for facility in self.structures(BARRACKSTECHLAB).ready.idle:
                if self.can_afford(RESEARCH_CONCUSSIVESHELLS) and not self.already_pending(PUNISHERGRENADES):
                    print("upgrade CONCUSSIVESHELLS")
                    self.do(facility(AbilityId.RESEARCH_CONCUSSIVESHELLS))
                    return False

        for facility in self.engineeringbays.ready.idle:
            if not self.upgrade_marine:
                continue
            if self.build_cc_home:
                continue
            abilities = await self.get_available_abilities(facility)
            # if RESEARCH_HISECAUTOTRACKING in abilities and self.can_afford(RESEARCH_HISECAUTOTRACKING):
            #     self.do(facility(AbilityId.RESEARCH_HISECAUTOTRACKING))
            #     return False
            # if RESEARCH_TERRANSTRUCTUREARMORUPGRADE in abilities and self.can_afford(
            #         RESEARCH_TERRANSTRUCTUREARMORUPGRADE):
            #     self.do(facility(AbilityId.RESEARCH_TERRANSTRUCTUREARMORUPGRADE))
            #     return False
            # if self.minerals < 150:
            #     return False
            for upgrade_level in range(1, 4):
                if upgrade_level >= 2 and not self.armories.ready:
                    break
                upgrade_weapon_id = getattr(sc2.constants,
                                            "ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL" + str(
                                                upgrade_level))
                upgrade_weapon_research_id = getattr(sc2.constants,
                                                     "TERRANINFANTRYWEAPONSLEVEL" + str(upgrade_level))
                upgrade_armor_id = getattr(sc2.constants,
                                           "ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL" + str(
                                               upgrade_level))
                upgrade_armor_research_id = getattr(sc2.constants,
                                                    "TERRANINFANTRYARMORSLEVEL" + str(upgrade_level))
                if not self.already_pending(upgrade_armor_research_id) and not (
                        upgrade_armor_research_id in self.state.upgrades):
                    if self.can_afford(upgrade_armor_id):
                        print("upgrade", upgrade_armor_research_id)
                        self.do(facility(upgrade_armor_id))
                        return False
                    if self.expand_for_vespene:
                        return False
                    else:
                        return True
                if (not self.already_pending(upgrade_weapon_research_id)
                        and not (upgrade_weapon_research_id in self.state.upgrades)
                        and not self.upgrade_marine_defence_and_mech_attack):
                    if self.can_afford(upgrade_weapon_id):
                        print("upgrade", upgrade_weapon_research_id)
                        self.do(facility(upgrade_weapon_id))
                        if not self.build_armory:
                            self.build_armory = True
                        return False
                    if self.expand_for_vespene:
                        return False
                    else:
                        return True
            if (RESEARCH_TERRANSTRUCTUREARMORUPGRADE in abilities
                    and self.can_afford(RESEARCH_TERRANSTRUCTUREARMORUPGRADE)
                    and self.minerals > 300
                    and self.vespene > 300
                    and self.refineries.ready.amount >= 6):
                self.do(facility(AbilityId.RESEARCH_TERRANSTRUCTUREARMORUPGRADE))
                self.upgrade_marine_defence_and_mech_attack = False
                self.upgrade_mech = True
                return False

        for facility in self.ghost_academies.ready:
            if len(facility.orders) >= 1:
                continue
            if not self.ghosts and not self.already_pending(UnitTypeId.GHOST):
                continue
            abilities = await self.get_available_abilities(facility)
            if self.ghosts.amount >= self.MaxGhost:
                if not self.already_pending(PERSONALCLOAKING):
                    if RESEARCH_PERSONALCLOAKING in abilities:
                        if self.can_afford(RESEARCH_PERSONALCLOAKING):
                            self.do(facility(AbilityId.RESEARCH_PERSONALCLOAKING))
                    return False
            if self.NukesLeft > 0:
                if not self.already_pending(PERSONALCLOAKING):
                    if RESEARCH_PERSONALCLOAKING in abilities:
                        if self.can_afford(RESEARCH_PERSONALCLOAKING):
                            self.do(facility(AbilityId.RESEARCH_PERSONALCLOAKING))
                    return False
                elif BUILD_NUKE in abilities:
                    if self.can_afford(BUILD_NUKE):
                        self.do(facility(AbilityId.BUILD_NUKE))
                        self.NukesLeft = self.NukesLeft - 1
                    return False
            elif self.enemy_race == Race.Protoss:
                if GHOSTACADEMYRESEARCH_RESEARCHENHANCEDSHOCKWAVES in abilities:
                    if self.can_afford(GHOSTACADEMYRESEARCH_RESEARCHENHANCEDSHOCKWAVES):
                        self.do(facility(AbilityId.GHOSTACADEMYRESEARCH_RESEARCHENHANCEDSHOCKWAVES))
                    return False

        for facility in self.structures(STARPORTTECHLAB).ready.idle:
            abilities = await self.get_available_abilities(facility)
            # print(abilities)
            if self.upgrade_banshee_speed and not self.already_pending(
                    BANSHEESPEED) and self.banshees.amount > 0:
                if self.can_afford(RESEARCH_BANSHEEHYPERFLIGHTROTORS):
                    self.do(facility(AbilityId.RESEARCH_BANSHEEHYPERFLIGHTROTORS))
                return False
            if self.upgrade_banshee_cloak and RESEARCH_BANSHEECLOAKINGFIELD in abilities and self.banshees.amount > 1:
                if self.can_afford(RESEARCH_BANSHEECLOAKINGFIELD):
                    self.do(facility(AbilityId.RESEARCH_BANSHEECLOAKINGFIELD))
                return False
            if self.upgrade_liberator and RESEARCH_ADVANCEDBALLISTICS in abilities:
                if self.can_afford(RESEARCH_ADVANCEDBALLISTICS):
                    self.do(facility(AbilityId.RESEARCH_ADVANCEDBALLISTICS))
                return False
        return True

    def findOppId(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--OpponentId', type=str, nargs="?", help='Opponent Id')
        args, unknown = parser.parse_known_args()
        if args.OpponentId:
            return args.OpponentId
        return None

    def on_end(self, result):
        print(str(result))

def main():
    maps = [

        # AiArena season 2
        "DeathAuraLE",
        "EternalEmpireLE",
        "EverDreamLE",
        "GoldenWallLE",
        "IceandChromeLE",
        "PillarsofgoldLE",
        "SubmarineLE",

        # Probots 2020 season 3
        # "DeathAuraLE",
        # "JagannathaLE",
        # "LightshadeLE",
        # "OxideLE",
        # "PillarsofgoldLE",
        # "RomanticideLE",
        # "SubmarineLE",

        # "AcropolisLE",
        # "Bandwidth" ,
        # "CrystalCavern" ,
        # "DigitalFrontier" ,
        # "DiscoBloodbathLE" ,
        # "Ephemeron" ,
        # "EphemeronLE" ,
        # "OldSunshine" ,
        # "Opponent Stats" ,
        # "PrimusQ9",
        # "Reminiscence" ,
        # "Sanglune" ,
        # "TheTimelessVoid" ,
        # "ThunderbirdLE" ,
        # "Treachery" ,
        # "TritonLE" ,
        # "WintersGateLE" ,
        # "WorldofSleepersLE" ,
        # "Urzagol" ,
    ]
    mapname = random.choice(maps)
    opponents = [Race.Protoss, Race.Zerg, Race.Terran]
    # opponents = [Race.Protoss]
    # opponents = [Race.Zerg]
    # opponents = [Race.Terran]
    # mapname = ("DarknessSanctuaryLE")

    sc2.run_game(sc2.maps.get(mapname), [
        Bot(Race.Terran, ANIbot()),
        Computer(random.choice(opponents), Difficulty.VeryHard)
    ], realtime=False, save_replay_as="ANI.SC2Replay")


if __name__ == '__main__':
    main()
