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

Temporal = Level.Tag("Temporal", Level.Color(181, 126, 220))
Modred.add_tag_keybind(Temporal, 'p')
Modred.add_tag_tooltip(Temporal)

Level.Tags.elements.append(Temporal)

class HastenBuff(Level.Buff):
    def __init__(self, strength):
        self.strength = strength
        self.buff_type = Level.BUFF_TYPE_BLESS
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Hasten %d" % self.strength
        self.color = Level.Tags.Temporal.color
        self.show_effect = False
        self.stack_type = Level.STACK_NONE
        self.description = "Take %d extra actions per turn" % (self.strength)
    
    def get_tooltip(self):
        return "Takes %d extra actions per turn" % (self.strength)
    
    def on_pre_advance(self):
        self.owner.haste += self.strength

class LightningBow(Upgrades.Upgrade):

    def on_init(self):
        self.prereq = MetalBallista
        self.name = "Teravolt Ballistae"
        self.description = "Allows ballistae to shoot [lightning] arrows instead of conventional ones, and grants them one extra action that stacks with Enhanced Reloading.\nAdds the [lightning] tag to this spell on purchase."
        self.level = 5
        self.exc_class = "elemental"
    
    def on_applied(self, owner):
        self.prereq.tags.append(Level.Tags.Lightning)

class EnchantBow(Upgrades.Upgrade):

    def on_init(self):
        self.prereq = MetalBallista
        self.exc_class = "elemental"
        self.name = "Enchanted Ballistae"
        self.description = "Allows ballistae to shoot [arcane] arrows instead of conventional ones.\nArcane arrows deal double damage compared to normal arrows.\nAdds the [arcane] tag to this spell on purchase."
        self.level = 5
    
    def on_applied(self, owner):
        self.prereq.tags.append(Level.Tags.Arcane)

class MetalBallista(Level.Spell): 
    def on_init(self):
        self.name = "Ballista"
        self.level = 3
        self.max_charges = 4
        self.range = 3
        self.minion_damage = 5
        self.minion_range = 14
        self.minion_health = 15
        self.minion_duration = 20
        self.must_target_empty = True
        self.must_target_walkable = True
        self.tags = [Level.Tags.Metallic, Level.Tags.Conjuration]

        self.upgrades['minion_damage'] = (4, 2)
        self.upgrades['minion_health'] = (10, 1)
        self.upgrades['autoload'] = (1, 3, "Enhanced Reloading", "Allows the ballista to fire 2 extra times each turn.")
        self.add_upgrade(LightningBow())
        self.spell_upgrades[0].tags.append(Level.Tags.Lightning)
        self.add_upgrade(EnchantBow())
        self.spell_upgrades[1].tags.append(Level.Tags.Arcane)
        for u in self.spell_upgrades:
            u.description += "\n%s can be upgraded with only 1 %s upgrade" % (self.name, u.exc_class)
    def get_description(self):
        return (
            "Summons a stationary [metallic] ballista on target tile.\n"
            "Ballistae have a ranged attack dealing [{minion_damage}:minion_damage] [physical] damage with a range of [{minion_range}_tiles:minion_range].\n"
            "Ballistae last [{minion_duration}_turns:minion_duration].\n"
        ).format(**self.fmt_dict())

    def make_ballista(self):
        hasten_val = 0
        ballista = Variants.KoboldBallista()
        ballista.name = "Ballista"
        ballista.tags += [Level.Tags.Metallic]
        ballista.max_hp = self.get_stat('minion_health')
        ballista.spells[0] = CommonContent.SimpleRangedAttack(name="Ballista Bolt", damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), proj_name="kobold_arrow")
        ballista.resists[Level.Tags.Fire] = 50
        if self.get_stat('autoload'):
            hasten_val += 2
        if self.caster.get_buff(LightningBow):
            hasten_val += 1 
            ballista.spells[0] = CommonContent.SimpleRangedAttack(name="Sky Bolt", damage=self.get_stat('minion_damage'), damage_type = Level.Tags.Lightning, range=self.get_stat('minion_range'), radius=1, proj_name="kobold_arrow")
        if self.caster.get_buff(EnchantBow):
            ballista.spells[0] = CommonContent.SimpleRangedAttack(name="Arcana Bolt", damage=self.get_stat('minion_damage')*2, damage_type = Level.Tags.Arcane, range=self.get_stat('minion_range'), proj_name="kobold_arrow")
        ballista.turns_to_death = self.get_stat('minion_duration')
        if hasten_val:
            ballista.buffs.append(HastenBuff(hasten_val))
        return ballista

    def cast_instant(self, x, y):
        self.summon(self.make_ballista(), Level.Point(x, y))

class Celerity(Level.Spell):
    def on_init(self):
        self.name = "Celerity"
        self.level = 6
        self.max_charges = 3
        self.range = 3
        self.bonus_actions = 2
        self.duration = 2
        self.stats.append('bonus_actions')
        self.tags = [Level.Tags.Temporal]

        self.upgrades['bonus_actions'] = (1, 4)
        self.upgrades['range'] = (1, 3)

    def get_description(self):
        return "Target ally gains [{bonus_actions}_extra_actions:temporal] per turn for [{duration}_turns:duration].".format(**self.fmt_dict())

    def can_cast(self, x, y):
        unit = self.caster.level.get_unit_at(x, y)
        return unit and unit != self.caster and not self.caster.level.are_hostile(unit, self.caster)

    def cast_instant(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        u.apply_buff(HastenBuff(self.get_stat('bonus_actions')), self.get_stat('duration'))

class Haste(Level.Spell):
    def on_init(self):
        self.name = "Haste"
        self.level = 5
        self.max_charges = 2
        self.range = 0
        self.bonus_actions = 1
        self.duration = 4
        self.stats.append('bonus_actions')
        self.tags = [Level.Tags.Temporal]

        self.upgrades['max_charges'] = (2, 3)
        self.upgrades['bonus_actions'] = (1, 4)

    def get_description(self):
        return "The Wizard gains [{bonus_actions}_extra_actions:temporal] per turn for [{duration}_turns:duration].".format(**self.fmt_dict())

    def cast_instant(self, x, y):
        self.caster.apply_buff(HastenBuff(self.get_stat('bonus_actions')), self.get_stat('duration'))

class TimeSummon(Level.Spell): 
    def on_init(self):
        self.name = "Chronolacrum"
        self.level = 7
        self.max_charges = 2
        self.range = 6
        self.num_spells = 3
        self.max_spell_level = 3
        self.requires_los = False
        self.tags = [Level.Tags.Temporal, Level.Tags.Conjuration]
        self.stats.append('num_spells')
        self.stats.append('max_spell_level')

        self.upgrades['max_spell_level'] = (1, 4)
        self.upgrades['range'] = (2, 1)

    def get_description(self):
        return (
            "Summons a copy of the Wizard from a different timeline.\n"
            "This clone has the same health as the original.\n"
            "The clone can use up to [{num_spells}_sorcery:sorcery] spells from your spellbook which are level [{max_spell_level}:enchantment] or lower.\n"
            "Copied spells gain all of your upgrades and bonuses.\n"
            "If you own no valid spells for the clone to copy, it will gain Magic Missile without your upgrades or bonuses.\n"
            "Spells copied have cooldowns equal to 3 times their spell level."
        ).format(**self.fmt_dict())

    def make_player(self):
        copy = Level.Unit()
        copy.max_hp = self.caster.max_hp
        copy.asset_name = os.path.join("..","..","rl_data","char","player")
        copy.name = "Wizard Alter"
        potentialspells = [s for s in self.caster.spells if s.level <= self.get_stat('max_spell_level') and s.name != "Cheat" and Level.Tags.Sorcery in s.tags]
        if not potentialspells:
            copy.spells.append(Spells.MagicMissile())
        else:
            if len(potentialspells) > 3:
                potentialspells = random.sample(potentialspells, 3)
            for p in potentialspells:
                n = type(p)()
                n.max_charges = 0
                n.cur_charges = 0
                n.statholder = self.caster
                n.cool_down = n.level*3
                copy.spells.append(n)
        return copy

    def cast_instant(self, x, y):
        self.summon(self.make_player(), Level.Point(x, y))

class DecelerateBuff(Level.Buff):
    def __init__(self, freq):
        Level.Buff.__init__(self)
        self.freq = freq
        self.cur = 0
        self.name = "Time Slip %d" % self.freq
        self.buff_type = Level.BUFF_TYPE_CURSE

    def on_init(self):
        self.color = Level.Tags.Temporal.color
        self.show_effect = False
        self.stack_type = Level.STACK_DURATION
    
    def on_advance(self):
        if self.cur == self.freq:
            self.owner.apply_buff(Level.Stun(), 1)
            self.cur = 0
        else:
            self.cur += 1

class Decelerate(Level.Spell):
    def on_init(self):
        self.name = "Decelerate"
        self.level = 3
        self.max_charges = 5
        self.range = 6
        self.duration = 20
        self.can_target_empty = False
        self.tags = [Level.Tags.Temporal, Level.Tags.Enchantment]

        self.upgrades['requires_los'] = (-1, 2, "Blindcasting", "Decelerate can be cast without line of sight.")
        self.upgrades['ultraslow'] = (1, 4, "Decelerate Attack", "Add a permanent 2 cooldown to target's spell with the lowest cooldown when casting Decelerate.")

    def get_description(self):
        return (
            "Curse target enemy with Time Slip, causing them to be stunned for 1 turn once every 2 turns.\n"
            "This curse lasts [{duration}_turns:duration]."
        ).format(**self.fmt_dict())

    def can_cast(self, x, y):
        unit = self.caster.level.get_unit_at(x, y)
        return unit and unit != self.caster and self.caster.level.are_hostile(unit, self.caster)

    def cast_instant(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        self.caster.level.show_effect(u.x, u.y, Level.Tags.Translocation)
        u.apply_buff(DecelerateBuff(1), self.get_stat('duration'))
        if self.get_stat('ultraslow') and u.spells:
            container = u.spells
            container.sort(key=lambda x:x.cool_down)
            u.spells[u.spells.index(container[0])].cool_down += 2

class Timehole(Level.Spell):
    def on_init(self):
        self.name = "Time Marker"
        self.level = 7
        self.max_charges = 2
        self.range = 0
        self.can_target_empty = False
        self.tags = [Level.Tags.Temporal]

        self.upgrades['max_charges'] = (2, 3)
    
    def get_description(self):
        return "Place a copy of the Wizard in the past, granting the Wizard the ability to reincarnate on death once."

    def cast_instant(self, x, y):
        self.caster.apply_buff(CommonContent.ReincarnationBuff(1))

Spells.all_player_spell_constructors.append(MetalBallista)
Spells.all_player_spell_constructors.append(Celerity)
Spells.all_player_spell_constructors.append(Haste)
Spells.all_player_spell_constructors.append(Decelerate)
Spells.all_player_spell_constructors.append(TimeSummon)
Spells.all_player_spell_constructors.append(Timehole)
