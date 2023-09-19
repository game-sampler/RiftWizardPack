import Spells
import Upgrades
import Level
import CommonContent
import Variants
import RareMonsters
import Monsters
import random
import mods.API_Universal.Modred as Modred
import Upgrades
import math
import text
import Game
import os

class PouchBuff(Level.Buff):
    def __init__(self, spell, unit):
        self.spell = spell
        self.c_buffs = unit.buffs
        self.c_resists = unit.resists
        self.c_mhp = unit.max_hp
        self.c_curhp = unit.cur_hp
        self.c_asset = unit.asset
        self.c_assetname = unit.asset_name
        self.c_spells = unit.spells
        self.c_name = unit.name
        self.c_tags = unit.tags
        self.c_flying = unit.flying
        self.c_tod = unit.turns_to_death
        self.c_sh = unit.shields
        Level.Buff.__init__(self)
        self.owner_triggers[Level.EventOnUnitAdded] = self.on_unit_added
    
    def on_init(self):
        self.name = "Pouch (%s)" % self.c_name
        self.color = Level.Tags.Conjuration.color
        self.show_effect = False
        self.stack_type = Level.STACK_NONE
    
    def copy(self):
        c = Level.Unit()
        c.buffs = self.c_buffs
        c.resists = self.c_resists
        c.max_hp = self.c_mhp
        c.cur_hp = self.c_curhp
        c.asset = self.c_asset
        c.asset_name = self.c_assetname
        c.spells = self.c_spells
        c.name = self.c_name
        c.tags = self.c_tags
        c.flying = self.c_flying
        c.turns_to_death = self.c_tod
        c.shields = self.c_sh
        if self.spell.get_stat('comfort'):
            c.cur_hp = c.max_hp
        elif self.spell.get_stat('training'):
            for s in c.spells:
                s.damage += 3
            c.shields += 1
        return c
    
    def on_unit_added(self, evt):
        if evt.unit != self.owner:
            return
        p = self.owner.level.get_summon_point(self.owner.x, self.owner.y)
        unit = self.copy()
        self.summon(unit, p)
        self.owner.remove_buff(self)
        
class Pouch(Level.Spell):
    def on_init(self):
        self.name = "Summon Pouch"
        self.level = 5
        self.max_charges = 4
        self.range = 7
        self.hp_cap = 45
        self.stats.append('hp_cap')
        self.tags = [Level.Tags.Arcane, Level.Tags.Conjuration, Level.Tags.Enchantment]

        self.upgrades['blindcasting'] = (-1, 3, "Blindcasting", "Summon Pouch can be cast without line of sight")
        self.upgrades['hp_cap'] = (25, 4)

        self.upgrades['comfort'] = (1, 4, "Comfort Pouch", "The pouch has extra bean bag chairs and a pool table.\nWhen the contained ally is summoned, it is fully healed.", "amenities")
        self.upgrades['training'] = (1, 5, "Training Pouch", "The pouch has some punching bags and exercise equipment.\nWhen the contained ally is summoned, it gains [3_damage:damage] to all of its spells, as well as [1_SH:shield].", "amenities")
        
    def get_description(self):
        return (
            "Place target ally with [{hp_cap}:heal] or less maximum HP in a magic pouch to save for later.\n"
            "The ally retains its current and maximum HP, tags, spells, resistances, shields, and buffs.\n"
            "When entering a new realm, summon the affected ally on a random tile within 5 tiles of the Wizard."
        ).format(**self.fmt_dict())

    def can_cast(self, x, y):
        unit = self.caster.level.get_unit_at(x, y)
        return unit and unit != self.caster and not self.caster.level.are_hostile(unit, self.caster) and unit.max_hp <= self.get_stat('hp_cap') 

    def cast_instant(self, x, y):
        unit = self.caster.level.get_unit_at(x, y)
        self.caster.apply_buff(PouchBuff(self, unit))
        unit.kill()

Spells.all_player_spell_constructors.extend([Pouch])
