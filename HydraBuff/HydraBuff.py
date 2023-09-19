import Spells
import Upgrades
import Level
import CommonContent
import Variants
import RareMonsters
import Monsters
import Upgrades
import text
import Game

import os, math, random

class HastenBuff(Level.Buff):
    def __init__(self, strength):
        self.strength = strength
        self.buff_type = Level.BUFF_TYPE_BLESS
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Speedrage"
        self.color = Level.Tags.Enchantment.color
        self.show_effect = False
        self.stack_type = Level.STACK_NONE
    
    def get_tooltip(self):
        return "Takes %d extra actions per turn" % (self.strength)
    
    def on_pre_advance(self):
        self.owner.haste += self.strength

class HydraNew(Level.Spell):

    def on_init(self):
        self.name = "Frostfire Hydra"
        
        self.tags = [Level.Tags.Ice, Level.Tags.Fire, Level.Tags.Dragon, Level.Tags.Conjuration]
        self.level = 3
        self.max_charges = 7

        self.minion_range = 9
        self.breath_damage = 7
        self.minion_health = 32
        self.minion_duration = 15

        self.upgrades['minion_range'] = (6, 3)
        self.upgrades['minion_duration'] = (10, 2)
        self.upgrades['breath_damage'] = (7, 4)
        self.upgrades['beamboost'] = (1, 3, "Enhanced Beams", "Beams have 1 turn of cooldown instead of 2.")
        self.upgrades['speed'] = (1, 4, "Split Heads", "The hydra can take one extra action each turn.")

        self.must_target_walkable = True
        self.must_target_empty = True

    def get_description(self):
        return ("Summon a frostfire hydra.\n"
                "The hydra has [{minion_health}_HP:minion_health], and is stationary.\n"
                "The hydra has a beam attack which deals [{breath_damage}_fire:fire] damage with a [{minion_range}_tile:minion_range] range.\n"
                "The hydra has a beam attack which deals [{breath_damage}_ice:ice] damage with a [{minion_range}_tile:minion_range] range.\n"
                "The hydra vanishes after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

    def cast_instant(self, x, y):

        unit = Level.Unit()
        unit.max_hp = self.get_stat('minion_health')

        unit.name = "Frostfire Hydra"
        unit.asset_name = 'fire_and_ice_hydra'

        fire = CommonContent.SimpleRangedAttack(damage=self.get_stat('breath_damage'), range=self.get_stat('minion_range'), damage_type=Level.Tags.Fire, beam=True)
        fire.name = "Fire"
        fire.cool_down = 2 if not self.get_stat('beamboost') else 1

        ice = CommonContent.SimpleRangedAttack(damage=self.get_stat('breath_damage'), range=self.get_stat('minion_range'), damage_type=Level.Tags.Ice, beam=True)
        ice.name = "Ice"
        ice.cool_down = 2 if not self.get_stat('beamboost') else 1

        unit.stationary = True
        unit.spells = [ice, fire]

        unit.resists[Level.Tags.Fire] = 100
        unit.resists[Level.Tags.Ice] = 100

        unit.turns_to_death = self.get_stat('minion_duration')

        unit.tags = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Dragon]
        if self.get_stat('speed'):
            unit.buffs.append(HastenBuff(1))

        self.summon(unit, Level.Point(x, y))

#Spells.all_player_spell_constructors.remove(Spells.SummonFrostfireHydra)
#Spells.all_player_spell_constructors.append(HydraNew)