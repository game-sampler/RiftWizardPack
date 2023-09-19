import sys
#sys.path.append('../..')

import Spells
import Upgrades
import Level
import CommonContent
import Variants
import RareMonsters
import Monsters
import random
import Upgrades
import math
import text
import Consumables

import os

class BruhMoment(Level.Spell):
    def on_init(self):
        self.name = "Bruh Moment"
        self.range = 0
        self.cool_down = 19

    def get_description(self):
        return "Teleports every enemy on the map to a random tile and deals [holy] damage to them equal to 1/5 of their current HP."

    def can_cast(self, x, y):
        enemies = [u for u in list(self.caster.level.units) if Level.are_hostile(u, self.caster)]
        return len(enemies) > 0
    
    def get_tp_points(self, unit):
        possible_points = []
        for i in range(len(self.owner.level.tiles)):
            for j in range(len(self.owner.level.tiles[i])):
                if self.owner.level.can_stand(i, j, unit):
                    possible_points.append(Level.Point(i, j))
        return possible_points
    def cast_instant(self, x, y):
        targets = [u for u in list(self.caster.level.units) if Level.are_hostile(u, self.caster)]
        for unit in targets:
            points = self.get_tp_points(unit)
            target = random.choice(points)
            dmg = math.ceil(unit.cur_hp / 5)
            self.caster.level.deal_damage(unit.x, unit.y, dmg, Level.Tags.Holy, self)
            self.caster.level.act_move(unit, target.x, target.y, teleport=True)

class SummonTroubler(Level.Spell):
    def on_init(self):
        self.name = "Conjure Trouble"
        self.range = 7
        self.max_charges = 3
        self.must_target_empty = True
        self.must_target_walkable = False

        self.minion_health = 1
        self.shields = 1
        self.minion_damage = 1
        self.teleport_distance = 4
        self.stats.append('teleport_distance')
        self.tags = [Level.Tags.Arcane, Level.Tags.Conjuration]

        self.level = 3

        self.upgrades['shields'] = (2, 2)
        self.upgrades['teleport_distance'] = (2, 3)
        self.upgrades['mobility'] = (1, 3, "Enhanced Mobility", "Troublers gain an extra 15% chance to passively teleport")
        self.upgrades['gild'] = (1, 7, "Shining Trouble", "Summons a golden troubler.\nGolden troublers are [metallic] [holy] creatures with a [blinding:holy] phase bolt attack that deals [holy] damage.", "variant")
        self.upgrades['winterize'] = (1, 7, "Troubling Winter", "Summons a wintry troubler.\nWintry Troublers are [ice] [arcane] creatures with an [ice] phase bolt that [freezes] hit units and hits in a [1_tile_burst:radius].", "variant")
    def get_description(self):
        return (
            "Summons a troubler on target tile.\n"
            "Troublers are stationary flying [arcane] units with [{minion_health}_HP:minion_health], [{shields}_SH:shields], and 100 [arcane] resist.\n"
            "Troublers have [arcane] ranged attacks which deal [{minion_damage}_damage:minion_damage] and teleport targets up to [{teleport_distance}_tiles_away:arcane].\n"
            "Troublers can also passively teleport with a range of [8_tiles:range]."
        ).format(**self.fmt_dict())

    def make_troubler(self):
        trouble = Monsters.Troubler()
        if self.get_stat('gild'):
            trouble.name = "Golden Troubler"
            trouble.asset_name = os.path.join("..","..","mods","SummonTroubler","mask_gold")
            trouble.spells[0] = CommonContent.SimpleRangedAttack(name="Troubling Light",damage=self.get_stat('minion_damage'), range=10, onhit=lambda caster, target: CommonContent.randomly_teleport(target, self.get_stat('teleport_distance')), damage_type=Level.Tags.Holy, buff=Level.BlindBuff, buff_duration=3)
            trouble.spells[0].description = "Blinds victims and teleports them up to %d tiles away" % self.get_stat('teleport_distance')
            trouble.resists = Variants.GoldHand().resists
            trouble.resists[Level.Tags.Arcane] = 100
            trouble.tags = Variants.GoldHand().tags
        elif self.get_stat('winterize'):
            trouble.name = "Wintry Troubler"
            trouble.asset_name = os.path.join("..","..","mods","SummonTroubler","mask_wintry")
            trouble.spells[0] = CommonContent.SimpleRangedAttack(name="Troubling Frost",damage=self.get_stat('minion_damage'), range=10, onhit=lambda caster, target: CommonContent.randomly_teleport(target, self.get_stat('teleport_distance')), radius=1, damage_type=Level.Tags.Ice, buff=CommonContent.FrozenBuff, buff_duration=2)
            trouble.spells[0].description = "Freezes victims and teleports them up to %d tiles away" % self.get_stat('teleport_distance')
            trouble.resists[Level.Tags.Ice] = 100
            trouble.resists[Level.Tags.Fire] = -100
            trouble.tags += [Level.Tags.Ice]
        else:
            trouble.spells[0].damage = self.get_stat('minion_damage')
            trouble.spells[0].onhit = lambda caster, target: CommonContent.randomly_teleport(target, self.get_stat('teleport_distance'))
            trouble.spells[0].description = "Teleports victims randomly up to %d tiles away" % self.get_stat('teleport_distance')
        trouble.max_hp = self.get_stat('minion_health')
        trouble.shields = self.get_stat('shields')
        if self.get_stat('mobility'):
            random_tp = trouble.get_buff(CommonContent.TeleportyBuff)
            random_tp.chance += .15
            random_tp.get_tooltip = lambda: "Each turn, %d%% chance to %s to a random tile up to %d tiles away" % (int(random_tp.chance * 100), "blink", random_tp.radius)
        return trouble
    
    def cast_instant(self, x, y):
        self.summon(self.make_troubler(), Level.Point(x, y))

Spells.all_player_spell_constructors.append(SummonTroubler)