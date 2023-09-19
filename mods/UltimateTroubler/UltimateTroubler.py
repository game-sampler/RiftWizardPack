# Add the base directory to sys.path for testing- allows us to run the mod directly for quick testing
import sys
#sys.path.append('../..')

import Spells
import Level
import CommonContent
import Monsters
import Variants
import RareMonsters
import random
import os

class VulgatesPower(Level.Buff):

    def on_init(self):
        self.turns = 0
        self.resists[Level.Tags.Lightning] = 50
        self.name = "Vulgate's Power"
        self.color = Level.Tags.Lightning.color
        spell = CommonContent.SimpleRangedAttack(damage=5, range=16, damage_type=Level.Tags.Lightning)
        spell.name = "Thunderbolt"
        self.spells = [spell]
        self.asset = ['status', '%s_eye' % Level.Tags.Lightning.name.lower()]

    def on_advance(self):
        if self.owner.shields >= 3:
            self.turns = 0
        else:
            self.turns += 1
            if self.turns == 2:
                self.owner.add_shields(1)
                self.turns = 0

class TurboTroubleTrick(Level.Spell):
    def on_init(self):
        self.name = "Turbo Troubletrick"
        self.range = 0
        self.cool_down = 18
        self.requires_los = True
    def get_description(self):
        return "Summons 4 Iron Troublers on random tiles. All Troublers gain a long-range [lightning] attack, 50 [lightning] resist, and passive SH generation."
    def cast(self, x, y):
        potentialspots = [t for t in self.caster.level.iter_tiles() if t.can_walk and not t.unit]
        finalspots = random.sample(potentialspots, 4)
        for spot in finalspots:
            irontroubler = Variants.TroublerIron()
            irontroubler.team = self.caster.team
            self.caster.level.add_obj(irontroubler, spot.x, spot.y)
        candidates = [u for u in self.caster.level.units if not Level.are_hostile(u, self.caster) and not u.has_buff(VulgatesPower)]
        for unit in candidates:
            if "Troubler" in unit.name:
                unit.apply_buff(VulgatesPower())
                yield

                
        

class WarpChain(Level.Spell):
    def on_init(self):
        self.name = "Warp Chain"
        self.range = 0
        self.cool_down = 5
        self.requires_los = True
    def get_description(self):
        return "Teleports the Wizard to 5 random tiles, dealing 1 [arcane] damage to units in a 2 tile burst centered on him each time. Troublers in range gain 2 SH.".format(**self.fmt_dict())
    def cast(self, x, y):
        dtype = Level.Tags.Arcane
        for i in range(5):
            old_loc = Level.Point(self.caster.level.player_unit.x, self.caster.level.player_unit.y)
            choices = [t for t in self.caster.level.iter_tiles() if t.can_walk and not t.unit]
            if choices:
                target = random.choice(choices)
                yield self.caster.level.act_move(self.caster.level.player_unit, target.x, target.y, teleport=True)
            burstpoint = Level.Point(self.caster.level.player_unit.x, self.caster.level.player_unit.y)
            for stage in CommonContent.Burst(self.caster.level, burstpoint, 2):
                for point in stage:
                    unit = self.caster.level.get_unit_at(point.x, point.y)
                    if unit and "Troubler" in unit.name:
                        unit.add_shields(2)
                    self.caster.level.deal_damage(point.x, point.y, 1, dtype, self)
            yield
    def can_cast(self, x, y):
        return True



def Vulgate():
    unit = Level.Unit()
    unit.name = "Vulgate, Lightspeed Troubler"
    unit.asset_name = os.path.join("..","..","mods","UltimateTroubler","troubler_turbo")

    unit.max_hp = 100
    unit.shields = 10
    unit.buffs.append(CommonContent.TeleportyBuff(chance=.7, radius=99))

    unit.resists[Level.Tags.Arcane] = 100
    unit.resists[Level.Tags.Dark] = 50
    unit.resists[Level.Tags.Lightning] = 75
    unit.resists[Level.Tags.Poison] = 0

    unit.tags = [Level.Tags.Arcane, Level.Tags.Lightning, Level.Tags.Dark]
    unit.spells.append(TurboTroubleTrick())
    unit.spells.append(WarpChain())

    unit.flying=True
    unit.stationary=True

    return unit

#Monsters.spawn_options.append((Vulgate, 1))