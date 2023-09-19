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
class MysticRadius(Level.Spell):
    def on_init(self):
        self.name = "Mystic Envelopment"
        self.level = 5
        self.tags = [Level.Tags.Arcane, Level.Tags.Enchantment]
        self.max_charges = 3
        self.strength = 1
        self.duration = 13
        self.range = 0
        self.stats.append('strength')
        self.upgrades['duration'] = (8, 3)
        self.upgrades['strength'] = (1, 5, "Radius Boost", "Increases the [radius] of spells by 1 extra tile.")
        self.upgrades['max_charges'] = (2, 3)
    def get_description(self):
        return "Increase the radius of all your spells by [{strength}_tiles:radius] for [{duration}_turns:duration].".format(**self.fmt_dict())
    def cast_instant(self, x, y):
        buff = CommonContent.GlobalAttrBonus('radius', self.get_stat('strength'))
        buff.name = "Mystic Envelopment"
        self.caster.apply_buff(buff, self.get_stat('duration'))

Spells.all_player_spell_constructors.append(MysticRadius)