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

class RainbowShot(Level.Spell):
    def on_init(self):
        self.name = "Rainbow Shot"
        self.damage = 3
        self.range = 13
        self.radius = 2
        self.cool_down = 2
        self.requires_los = True
    def get_description(self):
        return "Deals [fire], [ice], [lightning], [dark], and [holy] damage in a [{radius}_tile:radius] burst.".format(**self.fmt_dict())
    def cast(self, x, y):
        dtypes = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Lightning, Level.Tags.Dark, Level.Tags.Holy]
        burstpoint = Level.Point(x, y)
        for stage in CommonContent.Burst(self.caster.level, burstpoint, self.get_stat('radius')):
            for point in stage:
                for dtype in dtypes:
                    self.caster.level.deal_damage(point.x, point.y, 3, dtype, self)
        for i in range(4):
            yield

class RainbowBreath(Monsters.BreathWeapon):
    def __init__(self):
        Monsters.BreathWeapon.__init__(self)
        self.name = "Scourge Breath"
        self.range = 8
        self.damage = 8
        self.requires_los = True
        self.ignore_walls = False
    def get_description(self):
        return "Breathes a cone of multicolored energy dealing [fire], [ice], [lightning], [dark], and [holy] damage.".format(**self.fmt_dict())
    def cast(self, x, y):
        yield from Monsters.BreathWeapon.cast(self, x, y)
    def per_square_effect(self, x, y):
        for dtype in [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Lightning, Level.Tags.Dark, Level.Tags.Holy]:
            self.caster.level.deal_damage(x, y, self.damage, dtype, self)

class Starfall(Level.Spell):
    def on_init(self):
        self.name = "Starfall"
        self.damage = 4
        self.range = 0
        self.radius = 3
        self.cool_down = 20
        self.requires_los = False
    def get_description(self):
        return "Summons 15 energy blasts at random tiles that deal [fire], [ice], [lightning], [dark], and [holy] damage in a [{radius}_tile:radius] tile burst and destroy walls.".format(**self.fmt_dict())
    def cast(self, x, y):
        dtypes = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Lightning, Level.Tags.Dark, Level.Tags.Holy]
        potentialtargets = [t for t in self.caster.level.iter_tiles() if t.can_walk and not t.unit]
        targets = random.sample(potentialtargets, 15)
        for target in targets:
            for stage in CommonContent.Burst(self.caster.level, target, self.get_stat('radius'), ignore_walls=True):
                for point in stage:
                    for dtype in dtypes:
                        self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)
                    if self.caster.level.tiles[point.x][point.y].is_wall():
                        self.caster.level.make_floor(point.x, point.y)
                for i in range(4):
                    yield




def RainbowDrg():
    unit = Level.Unit()
    unit.name = "Rainbow Drake"
    unit.asset_name = os.path.join("..","..","mods","RainbowDrake","rainbow_drake")
    unit.max_hp = 1350
    unit.shields = 1

    unit.spells = [RainbowShot(), Starfall(), RainbowBreath()]
    unit.tags = [Level.Tags.Dragon, Level.Tags.Living]

    for resist in [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Lightning, Level.Tags.Dark, Level.Tags.Holy]:
        unit.resists[resist] = 50
    unit.flying = True
    return unit
#Monsters.spawn_options.append((RainbowDrg, 1))