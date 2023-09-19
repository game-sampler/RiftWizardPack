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

import os

def ElecSlime():
    slime = Monsters.GreenSlime()
    slime.spells[0] = CommonContent.SimpleRangedAttack(damage=3, damage_type=Level.Tags.Lightning, range=3)
    slime.asset_name = os.path.join("..","..","mods","SummonSlime","lightning_slime")
    slime.name = "Lightning Slime"
    slime.tags.insert(0, Level.Tags.Lightning)
    slime.resists[Level.Tags.Lightning] = 100
    slime.buffs[0].spawner = ElecSlime
    return slime

def HolySlime():
    slime = Monsters.GreenSlime()
    slime.spells[0] = CommonContent.SimpleRangedAttack(damage=3, damage_type=Level.Tags.Holy, range=3)
    slime.asset_name = os.path.join("..","..","mods","SummonSlime","holy_slime")
    slime.name = "Holy Slime"
    slime.tags.insert(0, Level.Tags.Holy)
    slime.resists[Level.Tags.Holy] = 100
    slime.buffs[0].spawner = HolySlime
    return slime

def DarkSlime():
    slime = Monsters.GreenSlime()
    slime.spells[0] = CommonContent.SimpleRangedAttack(damage=3, damage_type=Level.Tags.Dark, range=3)
    slime.asset_name = os.path.join("..","..","mods","SummonSlime","dark_slime")
    slime.name = "Dark Slime"
    slime.tags.insert(0, Level.Tags.Dark)
    slime.resists[Level.Tags.Dark] = 100
    slime.buffs[0].spawner = DarkSlime
    return slime

class Quest(Upgrades.Upgrade):
    def on_init(self):
        self.cur_level = -1
        self.prereq = SlimeSummon
        self.level = 7
        self.name = "Vengeance Quest"
        self.description = "Automatically cast Summon Slime on empty tiles around you whenever you enter a rift that has at least 1 [living] or [nature] unit.\nWhen entering realms 10 and above, cast it in empty tiles in 2 tiles of you instead.\nCan only be purchased if Judgment Slimes has been purchased for this spell."
        self.owner_triggers[Level.EventOnUnitAdded] = self.on_unit_added
    
    def get_nature_or_living(self):
        for unit in self.owner.level.units:
            if Level.Tags.Nature in unit.tags or Level.Tags.Living in unit.tags:
                return True
        return False

    def on_unit_added(self, evt):
        if evt.unit != self.owner:
            return
        rad = 1 if self.cur_level < 9 else 2
        self.cur_level += 1
        target = Level.Point(self.owner.x, self.owner.y)
        if self.get_nature_or_living():
            for spread in CommonContent.Burst(self.owner.level, target, rad):
                for point in spread:
                    if point != target and (self.owner.level.tiles[point.x][point.y].can_walk and not self.owner.level.get_unit_at(point.x, point.y)):
                        choices = [Monsters.VoidSlime, DarkSlime, HolySlime]
                        choice = random.choice(choices)
                        self.summon(self.prereq.make_slime(choice), point)
            return
    
    def on_applied(self, owner):
        summon_slime = [s for s in self.owner.spells if type(s) == SlimeSummon][0]
        if not summon_slime.get_stat('judgment'):
            self.owner.xp += self.level
            return Level.ABORT_BUFF_APPLY
        if self.cur_level == -1:
            self.cur_level = self.owner.level.level_no

class Championism(Upgrades.Upgrade):
    def on_init(self):
        self.prereq = SlimeSummon
        self.level = 7
        self.name = "Noble Journey"
        self.description = "Slimes gain a damage aura that deals 4 damage to units in 3 tiles. This aura has the same element as the slime's ranged attack, and its damage is fixed.\nWhen Summon Slime is cast in realms 10 and above, summoned slimes gain +10 ability damage and this spell has a 20% chance to not consume a charge.\nCan only be purchased if Elemental Slimes has been purchased for this spell."

    def on_applied(self, owner):
        summon_slime = [s for s in self.owner.spells if type(s) == SlimeSummon][0]
        if not summon_slime.get_stat('elements'):
            self.owner.xp += self.level
            return Level.ABORT_BUFF_APPLY

class Mitosis(Upgrades.Upgrade):
    def on_init(self):
        self.prereq = SlimeSummon
        self.level = 5
        self.name = "Mitotic Assistance"
        self.description = "Slimes gain 2 max HP gain."
        self.global_triggers[Level.EventOnUnitAdded] = self.on_unit_add
    def on_unit_add(self, evt):
        if not self.owner.level.are_hostile(self.owner, evt.unit) and Level.Tags.Slime in evt.unit.tags and evt.unit.source == self.prereq:
            split = evt.unit.get_buff(Monsters.SlimeBuff)
            split.growth += 2
            split.description = "50%% chance to gain %d hp and max hp per turn.  Upon reaching %d HP, splits into 2 %s." % (split.growth, split.to_split, split.spawner_name)

class SlimeSummon(Level.Spell):
    def on_init(self):
        self.asset = ["SummonSlime", "smug_slime"]

        ex = Monsters.GreenSlime()
        self.minion_damage = ex.spells[0].damage
        self.minion_health = ex.max_hp
        self.minion_range = 3

        self.must_target_walkable = True
        self.must_target_empty = True

        self.name = "Summon Slime"
        self.level = 1
        self.tags = [Level.Tags.Nature, Level.Tags.Arcane, Level.Tags.Conjuration]
        self.max_charges = 9
        self.range = 7

        self.upgrades['minion_health'] = (10, 1)
        self.upgrades['minion_damage'] = (4, 3)
        self.upgrades['minion_range'] = (2, 2)
        self.upgrades['judgment'] = (1, 5, "Judgment Slimes", "Randomly summon holy, void, or dark slimes instead of green slimes.", "color")
        self.add_upgrade(Quest())
        self.upgrades['elements'] = (1, 5, "Elemental Slimes", "Randomly summon fire, ice, or lightning slimes instead of green slimes.", "color")
        self.add_upgrade(Championism())
        self.add_upgrade(Mitosis())
    def get_description(self):
        return (
                "Summon a friendly slime at target tile.\n"
                "Slimes have [{minion_health}_HP:minion_health], have a [50_%:slime] chance each turn to gain max HP, and split into two slimes upon reaching twice their starting HP.\n"
                "Slimes also have a melee attack dealing [{minion_damage}_poison_damage:poison].\n"
                "Slime types with non-melee attacks can use them with a range of [{minion_range}_tiles:minion_range]"
                ).format(**self.fmt_dict())
    def make_slime(self, base):
        slime = base()
        slime.max_hp = self.get_stat('minion_health')
        slime.spells[0].damage = self.get_stat('minion_damage')
        slime.buffs[0].spawner = lambda: self.make_slime(base)
        if not slime.spells[0].melee:
            slime.spells[0].range = self.get_stat('minion_range')
        if self.caster.get_buff(Championism):
            tag = [t for t in slime.tags if t != Level.Tags.Slime][0]
            slime.buffs.append(CommonContent.DamageAuraBuff(damage_type=tag, damage=4, radius=3, friendly_fire=False))
            if self.caster.level.level_no >= 10:
                slime.spells[0].damage += 10
        slime.source = self
        return slime
    def cast_instant(self, x, y):
        choices = [Monsters.GreenSlime]
        if self.get_stat('judgment'):
            choices = [Monsters.VoidSlime, DarkSlime, HolySlime]
        elif self.get_stat('elements'):
            choices= [Monsters.RedSlime, ElecSlime, Monsters.IceSlime]
        choice = random.choice(choices)
        self.summon(self.make_slime(choice), Level.Point(x, y))
        if self.caster.get_buff(Championism) and random.random() < .2 and self.caster.level.level_no > 10:
            self.cur_charges = min(self.get_stat('max_charges'), self.cur_charges+1)

Spells.all_player_spell_constructors.append(SlimeSummon)