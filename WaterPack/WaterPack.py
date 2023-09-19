import Spells
import Upgrades
import Level
import CommonContent
import Variants
import RareMonsters
import Monsters
import mods.API_Universal.Modred as Modred
import Upgrades
import text
import Game

import os, math, random

Aqua = Level.Tag("Aqua", Level.Color(0, 113, 255))
Modred.add_tag_keybind(Aqua, 'q')
Modred.add_tag_tooltip(Aqua)
Level.Tags.elements.append(Aqua)
Modred.add_shrine_option(Aqua, 1)

#resist things, remove quotes to implement resists to the aqua element
set_default_resistances_old = Level.Level.set_default_resitances

def __set_default_resistances_new(self, unit):
    set_default_resistances_old(self, unit)

    if Level.Tags.Fire in unit.tags:
        unit.resists.setdefault(Level.Tags.Aqua, -75)

    if Level.Tags.Metallic in unit.tags and "Iron" in unit.name:
        unit.resists.setdefault(Level.Tags.Aqua, -50)

    if "Toad" in unit.name or Level.Tags.Lightning in unit.tags or Level.Tags.Ice in unit.tags:
        unit.resists.setdefault(Level.Tags.Aqua, 100)

Level.Level.set_default_resitances = __set_default_resistances_new

Modred.add_tag_effect_simple(Level.Tags.Aqua, os.path.join('mods','WaterPack','water_vfx'))

#spells

class Watergun(Level.Spell): 
    def on_init(self):
        self.name = "Watergun"
        self.level = 1
        self.max_charges = 13
        self.range = 7
        self.damage = 8      
        self.resist_loss = 50
        self.tags = [Level.Tags.Aqua, Level.Tags.Sorcery]

        self.upgrades['max_charges'] = (8, 1)
        self.upgrades['damage'] = (11, 3)
        self.upgrades['resist_loss'] = (25, 2)

    def get_description(self):
        return "Deals [{damage}:damage] [aqua] damage to the target.\nThe target loses {resist_loss} [lightning] resist.".format(**self.fmt_dict())

    def cast_instant(self, x, y):
        self.caster.level.deal_damage(x, y, self.get_stat('damage'), Level.Tags.Aqua, self)
        u = self.caster.level.get_unit_at(x, y)
        if u and self.caster.level.are_hostile(u, self.caster):
            u.resists[Level.Tags.Lightning] -= 50

class Aquaball(Level.Spell): 
    def on_init(self):
        self.name = "Waterball"
        self.level = 2
        self.max_charges = 8
        self.range = 6
        self.radius = 3
        self.damage = 10      
        self.resist_loss = 25
        self.tags = [Level.Tags.Aqua, Level.Tags.Sorcery]
        self.stats.append('resist_loss')

        self.upgrades['range'] = (4, 2)
        self.upgrades['salt'] = (1, 4, "Salt Ball", "[Metallic] units are stunned for [2_turns:duration] and lose half of their current HP.\n[Ice] units lose 25 [ice] and [aqua] resist.", "affinity")
        self.upgrades['light'] = (1, 4, "Brilliant Ball", "[Demon] and [undead] units take additional [holy] damage.\n", "affinity")

    def get_description(self):
        return "Deals [{damage}:damage] [aqua] damage in a [{radius}_tile_burst:radius].\nHit units lose {resist_loss} [lightning] resist.".format(**self.fmt_dict())

    def cast_instant(self, x, y):
        for spread in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for point in spread:
                u = self.caster.level.get_unit_at(point.x, point.y)
                if u and self.caster.level.are_hostile(u, self.caster):
                    u.resists[Level.Tags.Lightning] -= 25
                    if self.get_stat('salt'):
                        if Level.Tags.Metallic in u.tags:
                            u.apply_buff(Level.Stun(), 2)
                            u.cur_hp //= 2
                        if Level.Tags.Ice in u.tags:
                            u.resists[Level.Tags.Aqua] -= 25
                            u.resists[Level.Tags.Ice] -= 25
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Aqua, self)
                    if self.get_stat('light') and (Level.Tags.Demon in u.tags or Level.Tags.Undead in u.tags):
                        self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Holy, self)

class Eel(Level.Spell): 
    def on_init(self):
        self.name = "Lightning Eel"
        self.level = 4
        self.max_charges = 3
        self.range = 7
        self.minion_damage = 6
        self.minion_range = 5
        self.melee_damage = 8
        self.minion_health = 25
        self.minion_duration = 30
        self.tags = [Level.Tags.Aqua, Level.Tags.Lightning, Level.Tags.Nature, Level.Tags.Conjuration]
        self.stats.append('melee_damage')

        self.upgrades['minion_health'] = (15, 2)
        self.upgrades['self_charging'] = (1, 4, "Enhanced Charging", "Eels' ranged attacks no longer have a cooldown.", "static")
        self.upgrades['black'] = (1, 5, "Black Eels", "Summon black eels instead of normal eels. Black eels have 100 [dark] and -100 [holy] resistance in addition to their normal resistances.\nTheir ranged attacks gain the lifesteal property and deal [dark] and [lightning] damage.", "static")

    def make_eel(self):
        eeltype = "eel_black" if self.get_stat('black') else "eel"
        eel = Level.Unit()
        eel.name = "Black Eel" if self.get_stat('black') else "Lightning Eel"
        eel.asset_name = os.path.join("..","..","mods","WaterPack",eeltype)
        eel.max_hp = self.get_stat('minion_health')
        eel.tags = [Level.Tags.Aqua, Level.Tags.Lightning, Level.Tags.Nature] + ([Level.Tags.Dark] if self.get_stat('black') else [])
        eel.resists[Level.Tags.Aqua] = 75
        eel.resists[Level.Tags.Lightning] = 75
        eel.resists[Level.Tags.Fire] = 50
        if self.get_stat('black'):
            eel.spells.append(CommonContent.SimpleRangedAttack(name="Necrostatic Ball", damage=self.get_stat('minion_damage'), damage_type=[Level.Tags.Dark, Level.Tags.Lightning], range=self.get_stat('minion_range'), radius=1, drain=True))
        else:
            eel.spells.append(CommonContent.SimpleRangedAttack(name="Hydrostatic Ball", damage=self.get_stat('minion_damage'), damage_type=[Level.Tags.Aqua, Level.Tags.Lightning], range=self.get_stat('minion_range'), radius=1))
        eel.spells[0].cool_down = 0 if self.get_stat('self_charging') else 4
        eel.spells.append(CommonContent.SimpleMeleeAttack(damage=self.get_stat('melee_damage')))
        eel.spells[1].name = "Bite"
        return eel
    
    def get_description(self):
        return (
            "Summons a lightning eel on target tile. Lightning eels have [{minion_health}_HP:heal], 50 [aqua] resist, 50 [lightning] resist, and 75 [fire] resist.\n"
            "Lightning eels have a melee attack that deals [{melee_damage}_physical_damage:physical] and a ranged attack that randomly deals [{minion_damage}:minion_damage] [aqua] or [lightning] damage in a [1_tile_burst:radius] with a 4 turn cooldown.\n"
            "Eels can use their ranged attacks with a range of [{minion_range}_tiles:minion_range].\n"
            "Eels last [{minion_duration}_turns:minion_duration].\n"
        ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        self.summon(self.make_eel(), Level.Point(x, y))

class Hotspring(Level.Spell): 
    def on_init(self):
        self.name = "Hot Spring"
        self.level = 3
        self.max_charges = 5
        self.range = 8
        self.radius = 3
        self.damage = 10   
        self.tags = [Level.Tags.Aqua, Level.Tags.Fire, Level.Tags.Sorcery]

        self.upgrades['max_charges'] = (5, 1)
        self.upgrades['damage'] = (10, 3)

    def get_description(self):
        return "Deals [{damage}:damage] [aqua] and [fire] damage to enemies in a [{radius}_tile_burst:radius].\nAllies in range are healed for [{damage}_HP:heal] instead.".format(**self.fmt_dict())
    
    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]

    def cast_instant(self, x, y):
        dtypes = [Level.Tags.Fire, Level.Tags.Aqua]
        for spread in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for point in spread:
                u = self.caster.level.get_unit_at(point.x, point.y)
                if u and not self.caster.level.are_hostile(self.caster, u):
                    self.caster.level.deal_damage(point.x, point.y, -self.get_stat('damage'), Level.Tags.Heal, self)
                else:
                    for dtype in dtypes:
                        self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)

class Sleet(Level.Spell): 
    def on_init(self):
        self.name = "Sleet"
        self.level = 3
        self.max_charges = 8
        self.range = 7
        self.radius = 3
        self.damage = 10
        self.num_targets = 10   
        self.tags = [Level.Tags.Aqua, Level.Tags.Ice, Level.Tags.Sorcery]

        self.upgrades['requires_los'] = (-1, 2, "Blindcasting", "Sleet can be cast without line of sight")
        self.upgrades['num_targets'] = (14, 3)

    def get_description(self):
        return "Rains sleet on [{num_targets}_random_tiles:num_targets] in a [{radius}_tile_burst:radius], dealing [{damage}:damage] [aqua] and [ice] damage.".format(**self.fmt_dict())

    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]

    def cast(self, x, y):
        dtypes = [Level.Tags.Ice, Level.Tags.Aqua]
        for i in range(self.get_stat('num_targets')):
            tile = random.choice([t for t in self.get_impacted_tiles(x, y) if not self.caster.level.tiles[t.x][t.y].is_wall()])
            for dtype in dtypes:
                self.caster.level.deal_damage(tile.x, tile.y, self.get_stat('damage'), dtype, self)
            for j in range(3):
                yield



class WordWaves(Level.Spell):
    def on_init(self):
        self.name = "Word of Flooding"
        self.level = 7
        self.tags = [Level.Tags.Word, Level.Tags.Aqua]
        self.max_charges = 1
        self.range = 0
        self.damage = 60

        self.upgrades['max_charges'] = (1, 2)
    def get_description(self):
        metal_damage = self.get_stat('damage') // 2
        all_damage = self.get_stat('damage') // 4
        return (
                "Deal [{damage}:damage] [aqua] damage to all [fire] units and move them 1 tile in directions away from the Wizard, if possible.\n"
                "Each [metallic] unit loses all resistances, loses an additional 50 [aqua] resist, and takes [%d:damage] [aqua] damage.\n"
                "All [ice] and [lightning] units gain 1 SH.\n" 
                "All other units take [%d:damage] [aqua] damage" % (metal_damage, all_damage)
                ).format(**self.fmt_dict())
    
    def get_impacted_tiles(self, x, y):
        return [u for u in self.caster.level.units if u != self.caster]

    def find_loc(self, unit):
        for point in self.owner.level.get_points_in_ball(unit.x, unit.y, 1, diag=True):
            if self.caster.level.can_stand(point.x, point.y, unit):
                if Level.distance(point, Level.Point(self.caster.level.player_unit.x, self.caster.level.player_unit.x)) > Level.distance(Level.Point(unit.x, unit.y), Level.Point(self.caster.level.player_unit.x, self.caster.level.player_unit.x)):
                    return point
        return "NF"
            
    def cast_instant(self, x, y):
        for unit in [u for u in self.caster.level.units if u != self.caster]:
            if Level.Tags.Fire in unit.tags:
                self.caster.level.deal_damage(unit.x, unit.y, self.get_stat('damage'), Level.Tags.Aqua, self)
                spot = self.find_loc(unit)
                if spot != "NF":
                    self.caster.level.act_move(unit, spot.x, spot.y, teleport=True)
                    self.caster.level.show_effect(unit.x, unit.y, Level.Tags.Translocation)
            elif Level.Tags.Metallic in unit.tags:
                for r in list(unit.resists.keys()):
                    if unit.resists[r] > 0:
                        unit.resists[r] = 0
                unit.resists[Level.Tags.Aqua] -= 50
                self.caster.level.deal_damage(unit.x, unit.y, self.get_stat('damage') // 2, Level.Tags.Aqua, self)
            elif Level.Tags.Ice in unit.tags or Level.Tags.Lightning in unit.tags:
                unit.add_shields(1)
            else:
                self.caster.level.deal_damage(unit.x, unit.y, self.get_stat('damage') // 4, Level.Tags.Aqua, self)



class RainAcid(Level.Spell): 
    def on_init(self):
        self.name = "Acid Rain"
        self.level = 5
        self.max_charges = 5
        self.range = 9
        self.radius = 3
        self.damage = 13   
        self.tags = [Level.Tags.Aqua, Level.Tags.Nature, Level.Tags.Sorcery]
        self.max_channel = 6

        self.upgrades['radius'] = (2, 4)
        self.upgrades['damage'] = (5, 2)
        self.upgrades['requires_los'] = (-1, 2, "Blindcasting", "Acid Rain can be cast without line of sight")

    def get_description(self):
        return "Deals [{damage}:damage] [aqua] and [poison] damage to enemies in a [{radius}_tile_burst:radius].\nAcid Rain can be channeled for up to [{max_channel}_turns:duration].".format(**self.fmt_dict())

    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]

    def cast(self, x, y, channel_cast=False):
        if not channel_cast:
            self.caster.apply_buff(Level.ChannelBuff(self.cast, Level.Point(x, y)), self.get_stat('max_channel'))
            return
            
        dtypes = [Level.Tags.Poison, Level.Tags.Aqua]
        for spread in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for point in spread:
                for dtype in dtypes:
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)
        yield

class GhostShipBallSpell(Level.Spell):
    def on_init(self):
        self.name = "Call Crew"
        self.radius = 2
        self.range = 0
        self.cool_down = 1

    def get_ai_target(self):
        for p in self.get_impacted_tiles(self.caster.x, self.caster.y):
            u = self.caster.level.get_unit_at(p.x, p.y)
            if not u:
                return self.caster
        return None

    def get_description(self):
        return "Summons ghosts in a radius around the caster"

    def cast_instant(self, x, y):
        points = self.caster.level.get_points_in_ball(x, y, self.get_stat('radius'))
        for point in points:
            unit = self.caster.level.tiles[point.x][point.y].unit
            if unit is None and self.caster.level.tiles[point.x][point.y].can_see:
                ghost = Monsters.Ghost()
                CommonContent.apply_minion_bonuses(self, ghost)
                self.summon(ghost, point)

class VoidPiracyBuff(Level.Buff):
    def __init__(self, magnitude, healing):
        Level.Buff.__init__(self)
        self.name = "Void Piracy"
        self.magnitude = magnitude
        self.healing = healing
        self.color = Level.Tags.Arcane.color
    def on_applied(self, owner):
        self.global_triggers[Level.EventOnDamaged] = self.on_damaged
    def get_tooltip(self):
        return "Gains %d SH and regenerates %d HP every time it kills an enemy" % (self.magnitude, self.healing)
    def regen(self):
        self.owner.level.deal_damage(self.owner.x, self.owner.y, -self.magnitude, Level.Tags.Heal, self)
        self.owner.shields += self.magnitude
    def on_damaged(self, damage_event):
        if self.owner.level.are_hostile(self.owner, damage_event.unit) and damage_event.unit.cur_hp <= 0:
            if hasattr(damage_event.source, 'owner'):
                if damage_event.source.owner == self.owner:
                    self.regen()
            elif hasattr(damage_event.source, 'caster'):
                if damage_event.source.caster == self.owner:
                    self.regen()
            elif damage_event.source == self.owner:
                self.regen()

class GhostShip(Level.Spell): 
    def on_init(self):
        self.name = "Ghost Ship"
        self.level = 6
        self.max_charges = 3
        self.range = 5
        self.minion_damage = 8
        self.minion_range = 6
        self.shields = 2
        self.minion_health = 50
        self.tags = [Level.Tags.Aqua, Level.Tags.Dark, Level.Tags.Conjuration]

        self.upgrades['shields'] = (1, 3)
        self.upgrades['crew'] = (1, 5, "Extra Crew", "The ship has reduced cooldown on its cannon and summon abilities, and its cannon gains 1 radius.", "buccaneering")
        self.upgrades['piracy'] = (1, 6, "Void Piracy", "Each time a Ghost Ship kills an enemy, it gains [1_SH:shield] and recovers [5_HP:heal].\nGhost ships also gain a long-range cannon that deals [arcane] damage.", "buccaneering")

    def make_ship(self):
        ship = Level.Unit()
        ship.max_hp = self.get_stat('minion_health')
        ship.shields = self.get_stat('shields')
        ship.asset_name = os.path.join("..","..","mods","WaterPack","clay-ship-1")
        ship.flying = True
        ship.name = "Ghost Ship"
        for dtype in [Level.Tags.Dark, Level.Tags.Physical, Level.Tags.Poison]:
            ship.resists[dtype] = 100
        ship.resists[Level.Tags.Aqua] = 75
        ship.resists[Level.Tags.Holy] = -100
        ship.tags = [Level.Tags.Aqua, Level.Tags.Dark, Level.Tags.Construct]
        summon = GhostShipBallSpell()
        summon.cool_down = 4 if self.get_stat('crew') else 10
        ship.spells.append(summon)
        cannon = CommonContent.SimpleRangedAttack(name="Cannon", damage=self.get_stat('minion_damage'), damage_type=Level.Tags.Fire, range=self.get_stat('minion_range'), radius=2)
        if self.get_stat('crew'):
            cannon.radius += 1
        cannon.cool_down = 2 if self.get_stat('crew') else 6
        ship.spells.append(cannon)
        ship.buffs.append(CommonContent.TeleportyBuff(5, .2))
        if self.get_stat('piracy'):
            super_cannon = CommonContent.SimpleRangedAttack(name="Void Cannon", damage=self.get_stat('minion_damage'), damage_type=Level.Tags.Arcane, range=14, radius=2)
            super_cannon.cool_down = 8
            ship.spells.append(super_cannon)
            ship.buffs.append(VoidPiracyBuff(1, 5))
        return ship
    
    def get_description(self):
        return (
            "Summons a ghost ship on target tile. These ships have [{minion_health}_HP:minion_health], [{shields}_SH:shield], 75 [aqua] resist, 100 [dark] resist, 100 [physical] resist, passively blink, and can fly.\n"
            "Ships have a cannon attack that deals [{minion_damage}:damage] [fire] damage in a [2_tile_burst:radius] with a [{minion_range}_tile_range:minion_range].\n"
            "Ghost ships can also summon ghosts in empty tiles in 2 tiles around themselves.\n"
        ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        self.summon(self.make_ship(), Level.Point(x, y))


class Waterjet(Level.Spell): 
    def on_init(self):
        self.name = "Waterjet"
        self.level = 3
        self.max_charges = 13
        self.range = 7
        self.damage = 22    
        self.tags = [Level.Tags.Aqua, Level.Tags.Sorcery]

        self.upgrades['damage'] = (8, 2)
        self.upgrades['icy'] = (1, 3, "Arctic Water", "Waterjet deals [ice] damage and freezes hit units for [2_turns:duration].", "boost")
        self.upgrades['splashy'] = (1, 4, "Splitjet", "Waterjet will also cast itself on the closest 3 enemies in 5 tiles of the target tile.", "boost")

    def get_description(self):
        return "Deals [{damage}:damage] [aqua] damage to enemies in a beam.".format(**self.fmt_dict())

    def get_impacted_tiles(self, x, y):
        start = Level.Point(self.caster.x, self.caster.y)
        target = Level.Point(x, y)
        return list(CommonContent.Bolt(self.caster.level, start, target))

    def cast_instant(self, x, y, chained=False):
        dtypes = [Level.Tags.Aqua]
        if self.get_stat('icy'):
            dtypes.append(Level.Tags.Ice)
        start, target = Level.Point(self.caster.x, self.caster.y), Level.Point(x, y)
        for point in CommonContent.Bolt(self.caster.level, start, target):
            for dtype in dtypes:
                self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)
            u = self.caster.level.get_unit_at(x, y)
            if u and self.caster.level.are_hostile(u, self.caster) and self.get_stat('icy'):
                u.apply_buff(CommonContent.FrozenBuff(), 2)
        if not chained and self.get_stat('splashy'):
            targets = []
            for spread in CommonContent.Burst(self.caster.level, Level.Point(x, y), 5):
                for point in spread:
                    u = self.caster.level.get_unit_at(point.x, point.y)
                    if u and self.caster.level.are_hostile(u, self.caster):
                        targets.append(u)
            targets = targets[:3]
            if targets:
                for targeted in targets:
                    self.cast_instant(targeted.x, targeted.y, True)

class AquaBreath(Monsters.BreathWeapon):

    def __init__(self):
        Monsters.BreathWeapon.__init__(self)
        self.name = "Aqua Breath"
        self.damage = 9
        self.damage_type = Level.Tags.Aqua
        self.requires_los = False
        self.ignore_walls = False

    def get_description(self):
        return "Breathes a cone of water dealing aqua damage"

    def per_square_effect(self, x, y):
        self.caster.level.deal_damage(x, y, self.damage, Level.Tags.Aqua, self)

class WaterDrake(Level.Spell): 
    def on_init(self):
        self.name = "Aqua Drake"
        self.range = 4
        self.max_charges = 2
        self.tags = [Level.Tags.Aqua, Level.Tags.Conjuration, Level.Tags.Dragon]
        self.level = 5

        self.minion_health = 45
        self.minion_damage = 9
        self.breath_damage = 8
        self.minion_range = 7

        self.upgrades['minion_range'] = (2, 2)
        self.upgrades['breath_damage'] = (3, 2)
        self.upgrades['dragon_mage'] = (1, 5, "Dragon Mage", "Summoned Aqua Drakes can cast Waterjet with a 9 turn cooldown.\nThis Waterjet gains all of your upgrades and bonuses.")

    def make_drake(self):
        drake = Level.Unit()
        drake.name = "Aqua Drake"
        drake.team = self.caster.team
        drake.max_hp = self.get_stat('minion_health')
        drake.asset_name = os.path.join("..","..","mods","WaterPack","water_drake")
        breathe = AquaBreath()
        breathe.range = self.get_stat('minion_range')
        breathe.damage = self.get_stat('breath_damage')
        drake.spells.append(breathe)
        drake.spells.append(CommonContent.SimpleMeleeAttack(self.get_stat('minion_damage')))
        drake.tags = [Level.Tags.Dragon, Level.Tags.Living, Level.Tags.Aqua]
        drake.resists[Level.Tags.Poison] = 0
        drake.resists[Level.Tags.Aqua] = 100
        if self.get_stat('dragon_mage'):
            jet = Waterjet()
            jet.statholder = self.caster
            jet.max_charges = 0
            jet.cur_charges = 0
            jet.cool_down = 8
            drake.spells.insert(1, jet)
        return drake
    
    def get_description(self):
        return (
            "Summons an aqua drake on target tile.\n"
            "Aqua drakes have [{minion_health}_HP:minion_health], 100 [aqua] resist, and can fly.\n"
            "Aqua drakes have a breath weapon that deals [{breath_damage}_aqua_damage:aqua] damage, and a melee attack that deals [{minion_damage}_physical_damage:damage]"
        ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        self.summon(self.make_drake(), Level.Point(x, y))

class SquidJet(Monsters.BreathWeapon):
    def get_description(self):
        return "Sprays a cone of ink, blinding enemies in range"
    def per_square_effect(self, x, y):
        self.caster.level.show_effect(x, y, Level.Tags.Dark, minor=True)
        u = self.caster.level.get_unit_at(x, y)
        if u and self.caster.level.are_hostile(u, self.caster):
            u.apply_buff(Level.BlindBuff(), 2)

class Squiddy(Level.Spell): 
    def on_init(self):
        self.name = "Marine Call"
        self.range = 5
        self.max_charges = 3
        self.tags = [Level.Tags.Aqua, Level.Tags.Conjuration, Level.Tags.Nature]
        self.level = 7
        self.num_summons = 3
        self.max_channel = 4
        self.must_target_walkable = True
        self.must_target_empty = True

        self.minion_health = 33
        self.minion_damage = 13
        self.minion_range = 4
        self.multi_hit = 2
        self.stats.append('multi_hit')

        self.upgrades['num_summons'] = (1, 4)
        self.upgrades['minion_health'] = (10, 2)
        self.upgrades['max_channel'] = (3, 3)
        self.upgrades['multi_hit'] = (1, 2)
        self.upgrades['squizards'] = (1, 8, "Squizardry", "Squids can cast Waterball with a 7 turn cooldown. This Waterball gains all of your upgrades and bonuses", "aquatic")
        self.upgrades['gilded'] = (1, 9, "Gilded Crabs", "Summons golden crabs which have a variety of resistances and a [aqua] bolt attack.", "aquatic")
    
    def fmt_dict(self):
        d = Level.Spell.fmt_dict(self)
        d['crab_hp'] = self.get_stat('minion_health') // 2
        d['crab_dmg'] = self.get_stat('minion_damage') + (self.get_stat('minion_damage') // 5)
        return d

    def get_description(self):
        return (
            "Summons a group of [{num_summons}:num_summons] crabs and squids.\n"
            "Crabs have [{crab_hp}_HP:minion_health], 50 [physical] resist, 100 [aqua] resist, and a melee attack dealing [{crab_dmg}:minion_damage] [physical] damage.\n"
            "Squids have [{minion_health}_HP:minion_health], 100 [aqua] resist, and an inkjet attack that inflicts [blind] on enemies in a [{minion_range}_tile_cone:minion_range] for 2 turns.\n"
            "Squids also have a multihit melee attack dealing [{minion_damage}:minion_damage] [physical] damage and hitting [{multi_hit}_times:aqua].\n"
            "This spell can be channeled for [{max_channel}_turns:duration]."
        ).format(**self.fmt_dict())

    def make_squid(self):
        squid = Level.Unit()
        squid.name = "Squid"
        squid.team = self.caster.team
        squid.max_hp = self.get_stat('minion_health')
        squid.asset_name = os.path.join("..","..","mods","WaterPack","squid")
        if self.get_stat('squizards'):
            squid.asset_name = os.path.join("..","..","mods","WaterPack","squid_wiz")
        squid.resists[Level.Tags.Aqua] = 100
        squid.tags = [Level.Tags.Aqua, Level.Tags.Nature, Level.Tags.Living]
        jet = SquidJet()
        jet.cool_down = 3
        jet.name = "Ink Jet"
        jet.range = self.get_stat('minion_range')
        melee = CommonContent.SimpleMeleeAttack(damage=self.get_stat('minion_damage'), attacks=self.get_stat('multi_hit'))
        melee.name = "Tentacle"
        squid.spells = [jet, melee]
        if self.get_stat('squizards'):
            ball = Aquaball()
            ball.statholder = self.caster
            ball.max_charges = 0
            ball.cur_charges = 0
            ball.cool_down = 7
            squid.spells = [ball] + squid.spells
        return squid
    
    def make_crab(self):
        crab = Level.Unit()
        crab.name = "Crab"
        crab.team = self.caster.team
        crab.max_hp = self.get_stat('minion_health') // 2
        crab.asset_name = os.path.join("..","..","mods","WaterPack","crab")
        crab.resists[Level.Tags.Aqua] = 100
        crab.tags = [Level.Tags.Aqua, Level.Tags.Nature, Level.Tags.Living]
        if self.get_stat('gilded'):
            crab.asset_name = os.path.join("..","..","mods","WaterPack","crab_gold")
            crab.resists = Variants.GoldHand().resists
            crab.tags.append(Level.Tags.Metallic)
            crab.name = "Golden " + crab.name
            bolt = CommonContent.SimpleRangedAttack(name="Water Bolt", damage=(self.get_stat('minion_damage') // 4), damage_type=Level.Tags.Aqua, range=self.get_stat('minion_range'), cool_down=2)
            crab.spells.append(bolt)
        else:
            crab.resists[Level.Tags.Physical] = 50
        crab.resists [Level.Tags.Aqua] = 100
        dmg = self.get_stat('minion_damage') + (self.get_stat('minion_damage') // 5)
        melee = CommonContent.SimpleMeleeAttack(damage=dmg)
        melee.name = "Claw"
        crab.spells.append(melee)
        return crab
    
    def cast(self, x, y, channel_cast=False):
        if not channel_cast:
            self.caster.apply_buff(Level.ChannelBuff(self.cast, Level.Point(x, y)), self.get_stat('max_channel'))
            return
        for s in range(self.get_stat('num_summons')):
            r = random.random()
            if r < 0.3:
                unit = self.make_squid()
            else:
                unit = self.make_crab()
            self.summon(unit, Level.Point(x, y), 4, sort_dist=False)
            yield

# skills

class AquaLord(Upgrades.Upgrade):
    def on_init(self):
        self.name = "Arch Aquamancer"
        self.tags = [Level.Tags.Aqua]
        self.level = 7
        self.tag_bonuses[Level.Tags.Aqua]['max_charges'] = 2
        self.tag_bonuses[Level.Tags.Aqua]['damage'] = 4
        self.tag_bonuses[Level.Tags.Aqua]['range'] = 2

class PoisonSupply(Upgrades.Upgrade):
    def on_init(self):
        self.name = "Poisoned Supply"
        self.tags = [Level.Tags.Aqua, Level.Tags.Nature]
        self.level = 6
        self.conversions[Level.Tags.Aqua][Level.Tags.Poison] = .5
    
    def get_description(self):
        return "Half of all [aqua] damage you or your minions deal is redealt as [poison] damage."

class Waveride(Upgrades.Upgrade):
    def on_init(self):
        self.name = "Waveride"
        self.tags = [Level.Tags.Aqua, Level.Tags.Translocation]
        self.level = 5
        self.damage = 8
        self.owner_triggers[Level.EventOnSpellCast] = self.on_spell_cast

    def get_description(self):
        return "Whenever you cast a translocation spell, deal [{damage}:damage] [aqua] damage in a [2_tile_burst:radius] around the target tile.".format(**self.fmt_dict())

    def on_spell_cast(self, evt):
        if Level.Tags.Translocation in evt.spell.tags:
            for spread in CommonContent.Burst(self.owner.level, Level.Point(evt.x, evt.y), 2):
                for point in spread:
                    self.owner.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Aqua, self)

class HydroconductAquaStack(Level.Buff):

    def __init__(self, range):
        Level.Buff.__init__(self)
        self.name = "Electroconductance"
        self.color = Level.Tags.Lightning.color
        self.stack_type = Level.STACK_NONE
        self.tag_bonuses[Level.Tags.Lightning]['range'] = range

class HydroconductLightningStack(Level.Buff):

    def __init__(self, damage):
        Level.Buff.__init__(self)
        self.name = "Aquaconductance"
        self.color = Level.Tags.Aqua.color
        self.stack_type = Level.STACK_NONE
        self.tag_bonuses[Level.Tags.Aqua]['damage'] = damage

class Hydroconduct(Upgrades.Upgrade):
    def on_init(self):
        self.name = "Hydroconductance"
        self.tags = [Level.Tags.Aqua, Level.Tags.Lightning, Level.Tags.Enchantment]
        self.level = 5
        self.duration = 5
        self.owner_triggers[Level.EventOnSpellCast] = self.on_spell_cast
        self.last_cast = None

    def get_description(self):
        return "If you cast an [aqua] spell last turn, [lightning] spells and skills gain 2 range.\nIf you cast a [lightning] spell last turn, [aqua] spells and skills gain 4 damage.\nThese effects last [{duration}_turns:duration].\nThis bonus does not stack.".format(**self.fmt_dict())
    
    def on_spell_cast(self, evt):
        self.last_cast = evt.spell
        if Level.Tags.Lightning in self.last_cast.tags:
            self.owner.apply_buff(HydroconductLightningStack(4), self.get_stat('duration'))
        elif Level.Tags.Aqua in self.last_cast.tags:
            self.owner.apply_buff(HydroconductAquaStack(2), self.get_stat('duration'))

class WaterCycle(Upgrades.Upgrade):

    def on_init(self):
        self.owner_triggers[Level.EventOnSpellCast] = self.on_spell_cast
        self.name = "Water Cycle"
        self.tags = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Aqua]
        self.level = 7

    def on_spell_cast(self, evt):
        if Level.Tags.Fire in evt.spell.tags or Level.Tags.Ice in evt.spell.tags:
            if evt.spell.cur_charges == 0:
                chance = .5
                for spell in self.owner.spells:
                    if Level.Tags.Aqua in spell.tags and spell.cur_charges == 0 and random.random() < chance:
                        spell.cur_charges += 1
                self.owner.level.show_effect(self.owner.x, self.owner.y, Level.Tags.Aqua)

    def get_description(self):
        return ("Whenever you cast your last charge of a [fire] or [ice] spell, each of your [aqua] spells with no charges left has a 50% chance of gaining a charge.\n")

class Snowcast(Upgrades.Upgrade):
    def on_init(self):
        self.name = "Snowcasting"
        self.tags = [Level.Tags.Aqua, Level.Tags.Ice]
        self.level = 5
        self.owner_triggers[Level.EventOnSpellCast] = self.on_spell_cast
    
    def on_spell_cast(self, evt):
        if Level.Tags.Aqua in evt.spell.tags:
            cloud = CommonContent.BlizzardCloud(self.owner)
            cloud.damage += self.get_stat('damage')

            if not self.owner.level.tiles[evt.x][evt.y].cloud:
                self.owner.level.add_obj(cloud, evt.x, evt.y)
            else:
                possible_points = self.owner.level.get_points_in_ball(evt.x, evt.y, 1, diag=True)
                def can_cloud(p):
                    tile = self.owner.level.tiles[p.x][p.y]
                    if tile.cloud:
                        return False
                    if tile.is_wall():
                        return False
                    return True

                possible_points = [p for p in possible_points if can_cloud(p)]
                if possible_points:
                    point = random.choice(possible_points)
                    self.owner.level.add_obj(cloud, point.x, point.y)
    
    def get_description(self):
        return ("Whenever you cast an [aqua] spell, create a blizzard near the target tile.\n")

# constructors

Spells.all_player_spell_constructors.extend([Watergun, Aquaball, Waterjet, Eel, Hotspring, Sleet, WordWaves, RainAcid, GhostShip, WaterDrake, Squiddy])
Upgrades.skill_constructors.extend([WaterCycle, AquaLord, Waveride, Hydroconduct, PoisonSupply, Snowcast])
    
