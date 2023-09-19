import Spells
import Upgrades
import Level
import CommonContent
import Variants
import RareMonsters
import Monsters
import Upgrades
import Shrines
import text

import os, math, random

from copy import copy

class PlagueIdolBuff(Level.Buff):

    def __init__(self, spell):
        self.spell = spell
        self.name = "Contagion"
        Level.Buff.__init__(self)

    def on_advance(self):
        units = self.owner.level.get_units_in_los(self.owner)
        for u in units:
            if u == self.owner:
                continue
            
            if Level.are_hostile(u, self.owner):
                b = u.get_buff(CommonContent.Poison)
                if b:
                    b.turns_left += 2
                else:
                    u.apply_buff(CommonContent.Poison(), 2)

class PlagueIdol(Level.Spell):

    def on_init(self):

        self.name = "Plague Idol"
        
        self.level = 6
        self.tags = [Level.Tags.Dark, Level.Tags.Nature, Level.Tags.Conjuration]
        self.max_charges = 4

        self.minion_health = 35
        self.shields = 3
        self.minion_duration = 20

        self.upgrades['shields'] = (5, 3)
        self.upgrades['minion_duration'] = (15, 2)
        self.upgrades['minion_health'] = (20, 2)

        self.must_target_walkable = True
        self.must_target_empty = True

    def get_description(self):
        return ("Summon an Idol of Contagion.\n"
                "The idol has [{minion_health}_HP:minion_health], [{shields}_SH:shields], and is stationary.\n"
                "The idol has a passive aura which affects all enemies in line of sight of the idol each turn.\n"
                "Affected enemies are [poisoned] for 2 turns.\n"
                "Enemies that are already poisoned have their poison durations extended by the same amount instead.\n"
                "The idol vanishes after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

    def make_idol(self):
        idol = Level.Unit()
        idol.asset_name = os.path.join("..","..","mods","MiscSummons","units","plague_idol")
        idol.name = "Idol of Contagion"
        idol.max_hp = self.get_stat('minion_health')
        idol.shields = self.get_stat('shields')
        idol.stationary = True
        idol.resists[Level.Tags.Physical] = 75 
        idol.resists[Level.Tags.Poison] = 100
        idol.tags = [Level.Tags.Construct, Level.Tags.Dark, Level.Tags.Nature]
        idol.buffs.append(PlagueIdolBuff(self))
        idol.turns_to_death = self.get_stat('minion_duration')
        return idol
    
    def cast_instant(self, x, y):
        self.summon(self.make_idol(), Level.Point(x, y))

class StillIdolBuff(Level.Buff):

    def __init__(self, spell):
        self.spell = spell
        self.count = 0
        self.first_turn = True
        Level.Buff.__init__(self)

    def on_applied(self, owner):
        self.name = "Stillness"

    def on_advance(self):
        units = self.owner.level.get_units_in_los(self.owner)
        if self.count == self.spell.get_stat('freeze_cooldown'):
            for u in units:
                u.apply_buff(CommonContent.FrozenBuff(), 1)
            self.count = 0
        for u in units:
            if u == self.owner:
                continue
            
            if Level.are_hostile(u, self.owner):
                u.deal_damage(1, Level.Tags.Ice, self)
        
        self.count += 1


class StillIdol(Level.Spell):

    def on_init(self):

        self.name = "Chilling Idol"
        
        self.level = 6
        self.tags = [Level.Tags.Ice, Level.Tags.Conjuration]
        self.max_charges = 3

        self.minion_health = 40
        self.shields = 3
        self.minion_duration = 20
        self.freeze_cooldown = 4

        self.upgrades['shields'] = (3, 2)
        self.upgrades['freeze_cooldown'] = (-1, 3)
        self.upgrades['stillshot'] = (1, 4, "Strike of Stillness", "The Idol gains a [ice] beam attack.")

        self.must_target_walkable = True
        self.must_target_empty = True

    def get_description(self):
        return ("Summon an Idol of Stillness.\n"
                "The idol has [{minion_health}_HP:minion_health], [{shields}_SH:shields], 100 [ice] resist, and is stationary.\n"
                "The idol has a passive aura which affects all units in line of sight of the idol each turn.\n"
                "Affected enemies take 1 [ice] damage.\n"
                "Every [{freeze_cooldown}:duration] turns, the idol also [freezes] all units in its line of sight for 1 turn.\n"
                + text.frozen_desc +
                "\nThe idol vanishes after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

    def make_idol(self):
        idol = Level.Unit()
        idol.asset_name = os.path.join("..","..","mods","MiscSummons","units","stillness_idol")
        idol.name = "Idol of Stillness"
        idol.max_hp = self.get_stat('minion_health')
        idol.shields = self.get_stat('shields')
        idol.stationary = True
        idol.resists[Level.Tags.Physical] = 75 
        idol.resists[Level.Tags.Poison] = 100
        idol.resists[Level.Tags.Ice] = 100
        idol.tags = [Level.Tags.Construct, Level.Tags.Ice]
        if self.get_stat('stillshot'):
            skill = CommonContent.SimpleRangedAttack(name="Still Gaze", damage=10, damage_type=Level.Tags.Ice, range=8, beam=True)
            idol.spells.append(skill)
        idol.buffs.append(StillIdolBuff(self))
        idol.turns_to_death = self.get_stat('minion_duration')
        return idol
    
    def cast_instant(self, x, y):
        self.summon(self.make_idol(), Level.Point(x, y))

class EmpoweredFlies(Upgrades.Upgrade):
    def on_init(self):
        self.prereq = BugBag
        self.level = 3
        self.name = "Empowered Swarms"
        self.description = "Flies summoned through this spell gain 2 damage and 1 range to all abilities."
        self.global_triggers[Level.EventOnUnitAdded] = self.on_unit_added

    def on_unit_added(self, evt):
        if evt.unit.source == self.prereq and "Bag" not in evt.unit.name:
            for s in evt.unit.spells:
                s.damage += 2
                s.range += 1

class BugBag(Level.Spell):

    def on_init(self):

        self.name = "Bag of Bugs"
        
        self.level = 2
        self.tags = [Level.Tags.Dark, Level.Tags.Nature, Level.Tags.Conjuration]
        self.range = 7
        self.max_charges = 8
        self.num_summons = 4
        self.spawn_chance = 5
        self.minion_health = 16

        self.stats.append('spawn_chance')

        self.upgrades['spawn_chance'] = (5, 2)
        self.upgrades['num_summons'] = (4, 1)

        self.add_upgrade(EmpoweredFlies())

        self.upgrades['fire'] = (1, 4, "Fiery Bags", "Summon bags of fireflies instead.", "affinity")
        self.upgrades['electr'] = (1, 4, "Electric Bags", "Summon bags of lightning bugs instead.", "affinity")
        self.upgrades['brain'] = (1, 3, "Brain Bags", "Summon bags of brain flies instead", "affinity")

        self.must_target_walkable = True
        self.must_target_empty = True

    def get_description(self):
        return ("Summon a Bag of Bugs.\n"
                "The bag is a [dark] [construct] with [{minion_health}_HP:minion_health], 50 [dark] resist, 25 [physical] resist, and -100 [fire] resist.\n"
                "The bag has a [{spawn_chance}%_chance:nature] to spawn a fly swarm each turn.\n"
                "When the bag dies, it spawns [{num_summons}:num_summons] fly swarms."
                ).format(**self.fmt_dict())
    def custom_fly(self):
        if self.get_stat('fire'):
            u = Variants.BagOfBugsFire().get_buff(Monsters.BagOfBugsBuff).spawn()
        elif self.get_stat('electr'):
            u = Variants.BagOfBugsLightning().get_buff(Monsters.BagOfBugsBuff).spawn()
        elif self.get_stat('brain'):
            u = Variants.BagOfBugsBrain().get_buff(Monsters.BagOfBugsBuff).spawn()
        else:
            u = Monsters.BagOfBugs().get_buff(Monsters.BagOfBugsBuff).spawn()
        u.source = self
        return u
    def cast_instant(self, x, y):
        if self.get_stat('fire'):
            M = Variants.BagOfBugsFire()
        elif self.get_stat('electr'):
            M = Variants.BagOfBugsLightning()
        elif self.get_stat('brain'):
            M = Variants.BagOfBugsBrain()
        else:
            M = Monsters.BagOfBugs()
        b = M.get_buff(Monsters.BagOfBugsBuff)
        b.spawns = self.get_stat('num_summons')
        b.spawn = self.custom_fly
        c = M.get_buff(Monsters.GeneratorBuff)
        c.spawn_func = self.custom_fly
        c.spawn_chance = self.get_stat('spawn_chance') / 100
        M.max_hp = self.get_stat('minion_health')
        M.source = self
        CommonContent.apply_minion_bonuses(self, M)
        self.summon(M, Level.Point(x, y))

#phoenix

class LightningPhoenixBuff(Level.Buff):
    
    def on_init(self):
        self.color = Level.Tags.Lightning.color
        self.owner_triggers[Level.EventOnDeath] = self.on_death
        self.name = "Phoenix Lightning"

    def get_tooltip(self):
        return "On death, deals 25 lightning damage in 6 tiles.\nAlly units gain 8 damage to all spells and skills for 20 turns."

    def on_death(self, evt):

        for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, 6):
            unit = self.owner.level.get_unit_at(*p)
            if unit and not Level.are_hostile(unit, self.owner):
                b = CommonContent.GlobalAttrBonus("damage", 8)
                b.name = "Phoenix Force"
                b.color = Level.Tags.Color
                unit.apply_buff(b, 20)
            else:
                self.owner.level.deal_damage(p.x, p.y, 25, Level.Tags.Lightning, self)

def LightningPhoenix():
    u = Level.Unit()
    u.name = "Lightning Phoenix"
    u.tags = [Level.Tags.Lightning, Level.Tags.Holy]
    u.max_hp = 1
    u.cur_hp = 1
    u.flying = True
    u.asset_name = os.path.join("..","..","mods","MiscSummons","units","lightning_phoenix")
    u.resists[Level.Tags.Lightning] = 100
    u.resists[Level.Tags.Poison] = 100
    u.resists[Level.Tags.Dark] = -50
    u.spells.append(CommonContent.SimpleRangedAttack(damage=9, range=4, damage_type=Level.Tags.Lightning))
    u.buffs.append(LightningPhoenixBuff())
    u.buffs.append(CommonContent.ReincarnationBuff(1))
    return u


class SparkingRebirth(Upgrades.Upgrade):
    def on_init(self):
        self.prereq = RebirthFlare
        self.level = 5
        self.name = "Tempest Reborn"
        self.description = "Summon a lightning phoenix instead of a normal one.\nThese phoenixes are highly resistant to [lightning], have [lightning] ranged attacks, and emit a burst on death that deals [lightning] damage to enemies and grants bonus damage to allies.\nAlso, deal [lightning] damage to allies hit by this spell instead of [fire].\nThis spell will lose [fire] and gain [lightning] on purchase."
        self.exc_class = "elemental"
    
    def on_applied(self, owner):
        b = [s for s in owner.spells if s.name == self.prereq.name][0]
        b.tags[0] = Level.Tags.Lightning
        for s in b.spell_upgrades:
            s.tags[0] = Level.Tags.Lightning   

class ArcaneRebirth(Upgrades.Upgrade):
    def on_init(self):
        self.prereq = RebirthFlare
        self.level = 6
        self.name = "Void Revival"
        self.description = "Summon a void phoenix instead of a normal one.\nThese phoenixes are highly resistant to [arcane], have [arcane] ranged attacks that hit through walls, and emit a burst on death that deals [arcane] damage to enemies and grants SH to allies.\nAlso, deal [arcane] damage to allies hit by this spell instead of [fire].\nThis spell will lose [fire] and gain [arcane] on purchase."
        self.exc_class = "elemental"
    
    def on_applied(self, owner):
        b = [s for s in owner.spells if s.name == self.prereq.name][0]
        b.tags[0] = Level.Tags.Arcane
        for s in b.spell_upgrades:
            s.tags[0] = Level.Tags.Arcane 

class RebirthFlare(Level.Spell):

    def on_init(self):

        self.name = "Flames of Rebirth"
        
        self.level = 7
        self.tags = [Level.Tags.Fire, Level.Tags.Holy, Level.Tags.Sorcery, Level.Tags.Conjuration]
        self.range = 8
        self.max_charges = 2
        self.damage = 45
        self.minion_health = 85
        self.minion_damage = 9
        self.minion_range = 6
        self.lives = 1

        self.stats.append('lives')
        
        self.upgrades['minion_health'] = (25, 3)
        self.upgrades['minion_range'] = (1, 3)
        self.upgrades['lives'] = (1, 3)

        self.add_upgrade(SparkingRebirth())
        self.spell_upgrades[0].tags[0] = Level.Tags.Lightning
        self.add_upgrade(ArcaneRebirth())
        self.spell_upgrades[1].tags[0] = Level.Tags.Arcane

        for u in self.spell_upgrades:
            u.description += "\n%s can be upgraded with only 1 %s upgrade" % (self.name, u.exc_class)

    def get_description(self):
        return (
                "Immolate target ally, dealing [{damage}_fire_damage:fire].\n"
                "If target ally is [living] and dies to this damage, they are revived as a phoenix.\n"
                "The phoenix is a [holy] [fire] creature with [{minion_health}_HP:minion_health], 100 [poison] resist, and 100 [fire] resist.\n"
                "The phoenix has a ranged attack dealing [9_fire_damage:fire] with a [4-tile:range] range.\n"
                "The phoenix can reincarnate [{lives}_times:heal].\n"
                "When it dies, it creates an explosion in a [6-tile_burst:radius], dealing [25_fire_damage:fire] to enemies and healing allies."
                ).format(**self.fmt_dict())

    def can_cast(self, x, y):
        if x == self.caster.x and y == self.caster.y:
            return False
        u = self.caster.level.get_unit_at(x, y)
        return u and not Level.are_hostile(u, self.caster)
    
    def cast_instant(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        dtype = Level.Tags.Lightning if self.caster.has_buff(SparkingRebirth) else Level.Tags.Arcane if self.caster.has_buff(ArcaneRebirth) else Level.Tags.Fire
        u.deal_damage(self.get_stat('damage'), dtype, self)
        if not u.is_alive() and Level.Tags.Living in u.tags:
            if self.caster.has_buff(SparkingRebirth):
                u = LightningPhoenix()
            elif self.caster.has_buff(ArcaneRebirth):
                u = RareMonsters.VoidPhoenix()
                u.buffs.pop(2)
            else:
                u = Monsters.Phoenix()
            u.max_hp = self.get_stat('minion_health')
            u.cur_hp = u.max_hp
            u.spells[0].damage = self.get_stat('minion_damage')
            u.spells[0].range = self.get_stat('minion_range')
            b = u.get_buff(CommonContent.ReincarnationBuff)
            b.lives = self.get_stat('lives')
            b.name = "Reincarnation %d" % b.lives
            self.summon(u, Level.Point(x, y))

class EternalLifeBuff(Level.Buff):
    def __init__(self):
        Level.Buff.__init__(self)
        self.name = "Eternal Life"
        self.color = Level.Tags.Holy.color

    def on_applied(self, owner):
        owner.turns_to_death = None

class EternalLife(Level.Spell):

    def __init__(self):
        Level.Spell.__init__(self)

    def on_init(self):
        self.name = "Unending Life"
        self.description = "Make non-permanent ally permanent.\nOnly one unit can be affected at a time."
        self.range = Level.RANGE_GLOBAL
        self.requires_los = False
    
    def can_cast(self, x, y):
        if any(u.has_buff(EternalLifeBuff) for u in self.caster.level.units):
            return False
        return True

    def get_ai_target(self):
        to_redeem = [u for u in self.caster.level.units if u != self.caster and not Level.are_hostile(u, self.caster) and u.turns_to_death != None and not u.has_buff(EternalLifeBuff)]

        return random.choice(to_redeem) if to_redeem else None

    def cast(self, x, y):
        unit = self.caster.level.get_unit_at(x, y)
        if unit:
            self.caster.level.show_path_effect(self.caster, unit, Level.Tags.Holy)
            unit.apply_buff(EternalLifeBuff())
            yield

class EternityTablet(Level.Spell):

    def on_init(self):

        self.name = "Eternal Stone"
        
        self.level = 7
        self.tags = [Level.Tags.Holy, Level.Tags.Conjuration]
        self.range = 5
        self.max_charges = 2
        self.ability_cooldown = 11
        self.minion_health = 55
        self.shields = 3

        self.stats.append('ability_cooldown')

        self.upgrades['ability_cooldown'] = (-3, 3)
        self.upgrades['shields'] = (2, 3)

        self.must_target_walkable = True
        self.must_target_empty = True

    def get_description(self):
        return ("Summon a Tablet of Eternity.\n"
                "The tablet is a stationary [construct] with 50 [physical] resist, [{minion_health}_HP:minion_health], and [{shields}_SH:shield].\n"
                "The tablet has no attacks of its own.\n"
                "The tablet can grant non-permanent allies eternal life, making them permanent.\n"
                "Only one unit can be granted this status at a time.\n"
                "This ability has a [{ability_cooldown}_turn_cooldown:duration]."
                ).format(**self.fmt_dict())\

    def tablet(self):
        unit = Level.Unit()
        unit.name = "Tablet of Eternity"
        unit.tags = [Level.Tags.Construct]
        unit.resists[Level.Tags.Physical] = 50
        unit.asset_name = "tablet_regeneration"
        unit.max_hp = self.get_stat('minion_health')
        unit.shields = self.get_stat('shields')
        unit.spells.append(EternalLife())
        unit.spells[0].cool_down = self.get_stat('ability_cooldown')
        unit.stationary = True
        return unit

    def cast_instant(self, x, y):
        self.summon(self.tablet(), Level.Point(x, y))

class RebelBuff(Level.Buff):
    def __init__(self):
        Level.Buff.__init__(self)
        self.global_bonuses["radius"] = 1
        self.global_bonuses["damage"] = 4
        self.color = Level.Tags.Demon.color
        self.name = "Incursion Blessing"
        self.buff_type = Level.BUFF_TYPE_BLESS

class RebelBless(Level.Spell):

    def __init__(self, num_tgts, dur):
        self.num_tgts = num_tgts
        self.dur = dur
        Level.Spell.__init__(self)

    def on_init(self):
        self.name = "Incursion Blessing"
        self.description = "Up to %d friendly [demon] units gain +1 ability radius and +4 ability damage for %d turns" % (self.num_tgts, self.dur)
        self.range = Level.RANGE_GLOBAL
        self.requires_los = False

    def cast(self, x, y):
        to_hit = [u for u in self.caster.level.units if u != self.caster and not Level.are_hostile(u, self.caster) and Level.Tags.Demon in u.tags and not u.has_buff(RebelBuff)]
        to_hit = random.sample(to_hit, self.num_tgts) if len(to_hit) > self.num_tgts else to_hit
        if to_hit:
            for unit in to_hit:
                self.caster.level.show_path_effect(self.caster, unit, Level.Tags.Dark)
                unit.apply_buff(RebelBuff(), self.dur)
                yield

class DemonTablet(Level.Spell):

    def on_init(self):

        self.name = "Defiant Stone"
        
        self.level = 5
        self.tags = [Level.Tags.Dark, Level.Tags.Conjuration]
        self.range = 5
        self.max_charges = 2
        self.ability_cooldown = 8
        self.minion_health = 35
        self.shields = 4
        self.num_targets = 2
        self.duration = 15

        self.stats.append('ability_cooldown')

        self.upgrades['ability_cooldown'] = (-2, 3)
        self.upgrades['shields'] = (1, 1)
        self.upgrades['num_targets'] = (1, 3)
        self.upgrades['duration'] = (5, 4)

        self.must_target_walkable = True
        self.must_target_empty = True

    def get_description(self):
        return ("Summon a Tablet of Rebellion.\n"
                "The tablet is a stationary [construct] with 50 [physical] resist, [{minion_health}_HP:minion_health], and [{shields}_SH:shield].\n"
                "The tablet has no attacks of its own.\n"
                "The tablet can grant up to [{num_targets}:num_targets] [demon] allies [1_radius:radius] and [4_damage:damage] to all abilities for [{duration}_turns:duration].\n"
                "This ability has a [{ability_cooldown}_turn_cooldown:duration]."
                ).format(**self.fmt_dict())\

    def tablet(self):
        unit = Level.Unit()
        unit.name = "Tablet of Rebellion"
        unit.tags = [Level.Tags.Construct]
        unit.resists[Level.Tags.Physical] = 50
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","tablet_rebellion")
        unit.max_hp = self.get_stat('minion_health')
        unit.shields = self.get_stat('shields')
        unit.spells.append(RebelBless(self.get_stat('num_targets'), self.get_stat('duration')))
        unit.spells[0].cool_down = self.get_stat('ability_cooldown')
        unit.stationary = True
        return unit

    def cast_instant(self, x, y):
        self.summon(self.tablet(), Level.Point(x, y))

class Haze(Level.Buff):
    def __init__(self):
        Level.Buff.__init__(self)
        self.name = "Amnesia"
        self.color = Level.Tags.Arcane.color

    def on_applied(self, owner):
        for s in owner.spells:
            s.cool_down += 3
    
    def on_unapplied(self):
        for s in self.owner.spells:
            s.cool_down = max(0, s.cool_down-3)

class CursedTree(Level.Spell):

    def on_init(self):

        self.name = "Neurosapling"
        
        self.level = 6
        self.tags = [Level.Tags.Nature, Level.Tags.Arcane, Level.Tags.Conjuration]
        self.range = 5
        self.max_charges = 3
        self.minion_health = 70
        self.aura_damage = 1
        self.minion_duration = 16

        self.stats.append('aura_damage')

        self.upgrades['aura_damage'] = (1, 4)
        self.upgrades['minion_duration'] = (5, 4)
        self.upgrades['amnesia'] = (1, 5, "Haze of Memory", "Brain trees gain a [physical] ranged attack with a 3 turn cooldown that can inflict amnesia on enemy units.\nAmnesia increases cooldowns by 3 for 15 turns.")

        self.must_target_walkable = True
        self.must_target_empty = True

    def get_description(self):
        return ("Summon a Brain Tree.\n"
                "The tree is a stationary [arcane] [nature] unit with [{minion_health}_HP:minion_health], 100 [arcane] resist, 50 [physical] resist, -50 [fire] resist, and -50 [ice] resist.\n"
                "The tree has no attacks but has an aura that deals [{aura_damage}_arcane_damage:arcane] to enemies in 7 tiles of it.\n"
                "This damage cannot be increased by skills, shrines, or buffs.\n"
                "The tree lasts [{minion_duration}_turns:duration]."
                ).format(**self.fmt_dict())\

    def tree(self):
        unit = Level.Unit()
        unit.name = "Brain Tree"
        unit.tags = [Level.Tags.Arcane, Level.Tags.Nature]
        unit.resists[Level.Tags.Physical] = 50
        unit.resists[Level.Tags.Arcane] = 100
        unit.resists[Level.Tags.Ice] = -50
        unit.resists[Level.Tags.Fire] = -50
        unit.turns_to_death = self.get_stat('minion_duration')
        unit.asset_name = "brain_tree"
        unit.max_hp = self.get_stat('minion_health')
        unit.stationary = True
        unit.buffs.append(CommonContent.DamageAuraBuff(damage=self.get_stat('aura_damage'), damage_type=Level.Tags.Arcane, radius=7))
        if self.get_stat('amnesia'):
            unit.spells.append(CommonContent.SimpleRangedAttack(name="Amnestic Spore",damage=9,range=8,cool_down=3,buff=Haze,buff_duration=15))
        return unit

    def cast_instant(self, x, y):
        self.summon(self.tree(), Level.Point(x, y))

class FiendBuff(Level.Buff):

    def __init__(self, summoner, spell):
        Level.Buff.__init__(self)
        self.summoner = summoner
        self.spell = spell

    def on_init(self):
        self.name = "Bound Fiend"
        self.owner_triggers[Level.EventOnDeath] = self.on_death

    def on_death(self, evt):
        for i in range(3):
            chgs = [s.cur_charges for s in self.summoner.spells]
            if sum(chgs) <= 0:
                self.summoner.deal_damage(35, Level.Tags.Dark, self.spell)
            else:
                potentials = [s for s in self.summoner.spells if s.cur_charges > 0]
                choice = random.choice(potentials)
                choice.cur_charges -= 1

class DemonAgreement(Level.Spell):

    def on_init(self):

        self.name = "Infernal Pact"
        
        self.level = 7
        self.tags = [Level.Tags.Dark, Level.Tags.Conjuration]
        self.range = 0
        self.max_charges = 3
        self.minion_health = 80

        self.upgrades['iron'] = (1, 5, "Metal Fiends", "Replace storm and fire fiends with copper and furnace fiends, respectively.", "variant")
        self.upgrades['chaos'] = (1, 4, "Chaos Summoning", "Summon only Chaos Fiends.", "variant")
        self.upgrades['inane'] = (1, 5, "Dark Call", "Summon ash, rot, and insanity fiends instead.", "variant")

    def get_description(self):
        return (
                "Summon 2 fiends, chosen randomly from storm, fire, and iron variants.\n"
                "Each fiend has [{minion_health}_HP:minion_health] and a unique arsenal of abilities and resistances.\n"
                "Whenever a fiend dies, lose 3 spell charges randomly.\n"
                "If you have no spell charges left, take 35 [dark] damage."
                ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        if self.get_stat('iron'):
            fiend_vars = [Monsters.CopperFiend, Monsters.FurnaceFiend, Monsters.IronFiend]
        elif self.get_stat('chaos'):
            fiend_vars = [Monsters.ChaosFiend]
        elif self.get_stat('inane'):
            fiend_vars = [Monsters.RotFiend, Monsters.AshFiend, Monsters.InsanityFiend]
        else:
            fiend_vars = [Monsters.YellowFiend, Monsters.RedFiend, Monsters.IronFiend]
        for unit in random.choices(fiend_vars, k=2):
            new = unit()
            new.max_hp = self.get_stat('minion_health')
            new.cur_hp = new.max_hp
            new.buffs.append(FiendBuff(self.caster, self))
            [s for s in new.spells if type(s) == CommonContent.SimpleSummon][0].cool_down += 3
            self.summon(new, Level.Point(self.caster.x, self.caster.y))

class SafeTormenting(Upgrades.Upgrade):
    def on_init(self):
        self.prereq = NeoTormentor
        self.level = 2
        self.name = "Judicious Tormenting"
        self.description = "If you would be hit by an attack from a tormentor summoned by this spell, gain 1 SH immediately before taking damage."
        self.owner_triggers[Level.EventOnPreDamaged] = self.on_pre_damage
    
    def on_pre_damage(self, evt):
        if hasattr(evt.source, "caster"):
            if evt.source.caster.source == self.prereq and not Level.are_hostile(self.owner, evt.source.caster):
                self.owner.add_shields(1)

class NeoTormentor(Level.Spell):

    def on_init(self):

        self.name = "Frosty Tormentor"
        
        self.level = 4
        self.tags = [Level.Tags.Dark, Level.Tags.Ice, Level.Tags.Conjuration]
        self.range = 5
        self.max_charges = 6
        self.minion_health = 41
        self.minion_damage = 7
        self.leech_damage = 6
        self.radius = 3
        self.minion_range = 3
        self.minion_duration = 19
        self.stats.append('leech_damage')

        self.upgrades['radius'] = (2, 2)
        self.upgrades['minion_duration'] = (7, 2)
        self.upgrades['speed'] = (1, 3, "Swift Tormenting", "Tormentors summoned by this spell get a 1 turn cooldown reduction on their torment attacks.")
        self.upgrades['trojan'] = (1, 4, "Amalgam of Torment", "Consume 1 extra charge on cast to summon an icy tormenting mass instead.\nMasses spawn 3 frosty tormentors on death.\nTormentors that the mass spawns on death have the same minion duration as normal.", "suffering")
        self.upgrades['gigas'] = (1, 4, "Great Tormentor", "Consume 1 extra charge on cast to summon a giant frosty tormentor instead.\nGiant tormentors have twice as much HP, are permanent, and gain 4 bonus damage to all abilities.", "suffering")
        self.add_upgrade(SafeTormenting())

        self.must_target_walkable = True
        self.must_target_empty = True

    def fmt_dict(self):
        d = Level.Spell.fmt_dict(self)
        d['leech_damage'] = (d['minion_damage'] // 2) + 2
        return d

    def get_description(self):
        return (
                "Summon a frosty tormentor.\n"
                "The tormentor is an [ice] [demon] with [{minion_health}_HP:minion_health], 100 [dark] resist, 100 [ice] resist, -50 [fire] resist, and -100 [holy] resist.\n"
                "The tormentor has a burst attack dealing [{minion_damage}_ice:ice] damage with a [{radius}_tile:radius] radius.\n"
                "The tormentor has a lifesteal attack dealing [{leech_damage}_dark:dark] damage with a [{minion_range}_tile:minion_range] range.\n"
                "The tormentor vanishes after [{minion_duration}_turns:minion_duration]."
                ).format(**self.fmt_dict())
    
    def custom_tormentor(self):
        unit = Monsters.IcyTormentor()
        CommonContent.apply_minion_bonuses(self, unit)
        unit.max_hp = self.get_stat('minion_health')
        unit.spells[0].radius = self.get_stat('radius')
        unit.spells[1].damage = (self.get_stat('minion_damage') // 2) + 2
        unit.spells[1].range = self.get_stat('minion_range')
        unit.turns_to_death = self.get_stat('minion_duration') 
        unit.source = self
        if self.get_stat('speed'):
            for s in unit.spells:
                if "Torment" in s.name:
                    s.cool_down = max(0, s.cool_down-1)
        return unit 

    def custom_gigas(self):
        unit = Variants.IcyTormentorGiant()
        CommonContent.apply_minion_bonuses(self, unit)
        unit.max_hp = self.get_stat('minion_health')*2
        unit.spells[0].radius = self.get_stat('radius')
        unit.spells[0].damage = self.get_stat('minion_damage')
        unit.spells[1].damage = (self.get_stat('minion_damage') // 2) + 2
        unit.spells[1].range = self.get_stat('minion_range')
        unit.turns_to_death = None
        unit.source = self 
        for s in unit.spells:
            if self.get_stat('speed') and "Torment" in s.name:
                s.cool_down = max(0, s.cool_down-1)
            if hasattr(s, "damage"):
                s.damage += 4
        return unit   

    def custom_mass(self):
        unit = Variants.IcyTormentorMass()
        unit.asset_name = "tormentor_frosty_mass"
        CommonContent.apply_minion_bonuses(self, unit)
        unit.max_hp = self.get_stat('minion_health')
        unit.spells[0].radius = self.get_stat('radius')
        unit.spells[1].damage = (self.get_stat('minion_damage') // 2) + 2
        unit.spells[1].range = self.get_stat('minion_range')
        unit.turns_to_death = self.get_stat('minion_duration') 
        unit.source = self
        if self.get_stat('speed'):
            for s in unit.spells:
                if "Torment" in s.name:
                    s.cool_down = max(0, s.cool_down-1)
        unit.buffs[0].spawner = self.custom_tormentor
        unit.buffs[0].apply_bonuses = False
        unit.buffs[0].description = "On death, spawn %d %ss" % (unit.buffs[0].num_spawns, unit.buffs[0].spawner().name)
        return unit
    
    def cast_instant(self, x, y):
        if self.get_stat('trojan'):
            func = self.custom_mass
        elif self.get_stat('gigas'):
            func = self.custom_gigas
        else:
            func = self.custom_tormentor
        self.summon(func(), Level.Point(x, y))
        if self.get_stat('trojan') or self.get_stat('gigas'):
            self.cur_charges -= 1
            self.cur_charges = max(self.cur_charges, 0)

class PhantomBuff(Level.Buff):
    def __init__(self, spell):
        Level.Buff.__init__(self)
        self.spell = spell
        self.color = Level.Tags.Holy.color
        self.name = "Offered Spirit"
        self.dmg_counter = 0
        self.b = CommonContent.ShieldRegenBuff(10, self.spell.get_stat('shield_frequency'))
        self.b.name = "Shielding"
        self.owner_triggers[Level.EventOnDamaged] = self.on_damaged
        self.buff_type = Level.BUFF_TYPE_CURSE

    def make_phantom(self):
        unit = Monsters.Ghost()
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","ghost_holy")
        unit.name = "Sacrosanct Phantom"
        unit.shields = 1
        for s in unit.spells:
            s.damage += 1
        unit.resists[Level.Tags.Holy] = 50
        unit.tags.append(Level.Tags.Holy)
        unit.spells.insert(0, CommonContent.SimpleRangedAttack(damage=1, range=4, damage_type=Level.Tags.Holy))
        unit.source = self.spell
        unit.max_hp = 5
        unit.cur_hp = 5
        return unit
    
    def on_applied(self, owner):
        owner.apply_buff(self.b)
    
    def on_pre_advance(self):
        if not Level.are_hostile(self.owner, self.spell.caster):
            self.owner.remove_buff(self)
    
    def on_unapplied(self):
        self.owner.remove_buff(self.b)

    def on_damaged(self, evt):
        radius = 6
        self.dmg_counter += evt.damage
        while(self.dmg_counter >= self.spell.get_stat('summon_threshold')):
            self.spell.summon(self.make_phantom(), Level.Point(self.owner.x, self.owner.y), radius=radius)
            self.dmg_counter -= self.spell.get_stat('summon_threshold')
        if self.spell.get_stat('justice') and evt.damage > 15 and (Level.Tags.Demon in self.owner.tags or Level.Tags.Undead in self.owner.tags):
            self.spell.summon(self.make_phantom(), Level.Point(self.owner.x, self.owner.y), radius=radius)
            potentials = [u for u in self.spell.caster.level.get_units_in_los(self.owner) if Level.are_hostile(u, self.spell.caster) and u != self.owner]
            if potentials:
                unit = random.choice(potentials)
                self.owner.level.show_path_effect(self.owner, unit, Level.Tags.Holy, minor=True)
                unit.apply_buff(PhantomBuff(self.spell), 6)


class HolyCurse(Level.Spell):

    def on_init(self):

        self.name = "Spirit Rite"
        
        self.level = 5
        self.tags = [Level.Tags.Dark, Level.Tags.Holy, Level.Tags.Conjuration, Level.Tags.Enchantment]
        self.range = 7
        self.max_charges = 3
        self.shield_frequency = 3
        self.summon_threshold = 13
        self.duration = 18
        self.stats.append('shield_frequency')
        self.stats.append('summon_threshold')

        self.upgrades['summon_threshold'] = (-6, 4, "Fruitful Sacrifice", "This reduces the amount of damage needed to summon a phantom.")
        self.upgrades['shield_frequency'] = (1, 2)
        self.upgrades['lifekill'] = (1, 5, "Life Rip", "Deal 35 [dark] damage to [living] targets.\nIf they die from this damage, inflict Offered Spirit on enemies in 6 tiles of the target for 6 turns, ignoring line of sight.", "propagation")
        self.upgrades['justice'] = (1, 6, "Phantom Justice", "If a [demon] or [undead] unit with Offered Spirit takes more than 15 damage, summon a phantom near it and inflict Offered Spirit on a random enemy in line of sight of it for 6 turns.", "propagation")

        self.can_target_empty = False

    def can_cast(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        return u and Level.are_hostile(u, self.caster) and Level.Spell.can_cast(self, x, y)
    
    def get_description(self):
        return (
                "Target enemy gains Offered Spirit for [{duration}_turns:duration].\n"
                "Units with Offered Spirit regenerate [1_SH:shield] every [{shield_frequency}_turns:duration], to a max of 10.\n"
                "Whenever a unit with Offered Spirit takes damage, summon a sacrosanct phantom near it for every [{summon_threshold}:damage] damage dealt.\n"
                "If an affected unit becomes friendly to the Wizard, it loses Offered Spirit.\n"
                "The phantoms are [holy] [undead] with 50 [holy] resist, 50 [dark] resist, [5_HP:minion_health] and [1_SH:shield].\n"
                "The phantoms have [holy] ranged attacks and a [dark] melee attack."
                ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        if u and Level.are_hostile(u, self.caster):
            u.apply_buff(PhantomBuff(self), self.get_stat('duration'))
            if Level.Tags.Living in u.tags and self.get_stat('lifekill'):
                u.deal_damage(35, Level.Tags.Dark, self)
                if not u.is_alive():
                    for p in self.caster.level.get_points_in_ball(x, y, 6, diag=False):
                        u = self.caster.level.get_unit_at(p.x, p.y)
                        if u and Level.are_hostile(u, self.caster):
                            u.apply_buff(PhantomBuff(self), 6)

def GoldSlime():

    unit = Level.Unit()
    unit.name = "Golden Slime"
    unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","slime_gilded")
    unit.max_hp = 10
    unit.tags = [Level.Tags.Slime, Level.Tags.Holy, Level.Tags.Metallic]
    unit.spells.append(CommonContent.SimpleMeleeAttack(3, damage_type=Level.Tags.Holy))
    unit.buffs.append(Monsters.SlimeBuff(spawner=GoldSlime))
    unit.resists = Variants.GoldHand().resists
    unit.resists[Level.Tags.Poison] = 100
    unit.resists[Level.Tags.Physical] = 100

    return unit

def ChaosSlime():

    unit = Level.Unit()
    unit.name = "Chaotic Slime"
    unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","slime_chaos")
    unit.max_hp = 10
    unit.tags = [Level.Tags.Slime, Level.Tags.Chaos]
    unit.spells.append(CommonContent.SimpleRangedAttack(name="Chaos Ooze", damage=8, range=3, radius=1, damage_type=[Level.Tags.Fire, Level.Tags.Physical, Level.Tags.Lightning]))
    unit.buffs.append(Monsters.SlimeBuff(spawner=ChaosSlime))
    unit.resists[Level.Tags.Fire] = 75
    unit.resists[Level.Tags.Lightning] = 75
    unit.resists[Level.Tags.Physical] = 100

    return unit

class SlimeBlast(Level.Spell):

    def on_init(self):

        self.name = "Slime Blast"
        
        self.level = 5
        self.tags = [Level.Tags.Arcane, Level.Tags.Sorcery, Level.Tags.Conjuration]
        self.range = 8
        self.damage = 9
        self.max_charges = 4
        self.radius = 1
        self.max_hp_gain = 2
        self.stats.append('max_hp_gain')

        ex = Monsters.GreenSlime()

        self.minion_health = ex.max_hp
        self.minion_damage = ex.spells[0].damage
        self.minion_range = 3

        self.upgrades['radius'] = (1, 4)
        self.upgrades['minion_range'] = (1, 3)
        self.upgrades['max_hp_gain'] = (2, 4)
        self.upgrades['shine']  = (1, 5, "Shining Blast", "Deal 3 [holy] damage to enemies in the radius, and summon a golden slime at the center tile.\nGolden slimes are [metallic] [holy] creatures with a wide array of resistances and a [holy] melee attack.", "variant")
        self.upgrades['chaos'] = (1, 6, "Goolamity", "Deal 3 [fire], [lightning] or [physical] damage to enemies in the radius, and summon a chaotic slime at the center tile.\nChaotic slimes are [chaos] creatures that are highly resistant to [fire], [lightning] and [physical] damage.\nThey also have a powerful chaos shot attack dealing [fire], [lightning], or [physical] damage randomly.", "variant")

    def get_description(self):
        return (
            "Throw a blast of slime in a [{radius}-tile_radius:radius].\n"
            "Deal [{damage}_poison_damage:poison] to enemies in the radius.\n"
            "Friendly [slime] units are healed instead and gain [{max_hp_gain}_max_HP:heal].\n"
            "Summon slimes at empty tiles in the radius.\n"
            "Slimes have [{minion_health}_HP:minion_health], have a 50% chance each turn to gain 1 max HP, and split into two slimes upon reaching twice their starting HP.\n"
            "Slimes have a melee attack which deals [{minion_damage}_poison:poison] damage."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        points = self.caster.level.get_points_in_ball(x, y, self.get_stat('radius'))
        for p in points:
            unit = self.caster.level.tiles[p.x][p.y].unit
            if unit is None and self.caster.level.tiles[p.x][p.y].can_see and self.caster.level.tiles[p.x][p.y].can_walk    :
                if p.x == x and p.y == y and self.get_stat('shine'):
                    mon = GoldSlime()
                elif p.x == x and p.y == y and self.get_stat('chaos'):
                    mon = ChaosSlime()
                else:
                    mon = Monsters.GreenSlime()
                CommonContent.apply_minion_bonuses(self, mon)
                self.summon(mon, p)
            elif unit and Level.Tags.Slime in unit.tags and not Level.are_hostile(self.caster, unit):
                unit.max_hp += self.get_stat('max_hp_gain')
                unit.deal_damage(-self.get_stat('damage'), Level.Tags.Heal, self)
            elif unit and Level.are_hostile(unit, self.caster):
                unit.deal_damage(self.get_stat('damage'), Level.Tags.Poison, self)
                if self.get_stat('shine'):
                    unit.deal_damage(3, Level.Tags.Holy, self)
                elif self.get_stat('chaos'):
                    dtype = random.choice([Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical])
                    unit.deal_damage(3, dtype, self)
    
class ReincarnAura(Level.Buff):
    def __init__(self, spell):
        Level.Buff.__init__(self)
        self.spell = spell
        self.color = Level.Tags.Holy.color
        self.name = "Alus' Hope"
        self.turn_no = 0
    
    def get_tooltip(self):
        return "Applies a buff once every %d turns that gives [demon], [undead] and [holy] units nearby the ability to reincarnate on death for %d turns." % (self.spell.get_stat('aura_frequency'), self.spell.get_stat('reincarnation_duration'))
    
    def on_advance(self):
        self.turn_no += 1
        if self.turn_no == self.spell.get_stat('aura_frequency'):
            self.turn_no = 0
            for unit in self.owner.level.get_units_in_ball(Level.Point(self.owner.x, self.owner.y), self.spell.get_stat('radius')):
                if unit == self.owner:
                    continue
                elif unit and not Level.are_hostile(self.owner, unit):
                    acceptable_tags = [Level.Tags.Demon, Level.Tags.Holy, Level.Tags.Undead]
                    if len([t for t in unit.tags if t in acceptable_tags]) > 0:
                        unit.apply_buff(CommonContent.ReincarnationBuff(1), self.spell.get_stat('reincarnation_duration'))
            points = self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.spell.get_stat('radius'))
            points = [p for p in points if not self.owner.level.get_unit_at(p.x, p.y)]
            random.shuffle(points)
            for i in range(7):
                if not points:
                    break
                p = points.pop()
                self.owner.level.deal_damage(p.x, p.y, 0, Level.Tags.Holy, self.spell)

class JohnsIdea(Level.Spell):

    def on_init(self):

        self.name = "Saintly Call"
        
        self.level = 7
        self.tags = [Level.Tags.Dark, Level.Tags.Holy, Level.Tags.Conjuration]
        self.range = 4
        self.max_charges = 1
        self.minion_health = 90
        self.radius = 5
        self.aura_frequency = 11
        self.reincarnation_duration = 6
        self.stats.append('aura_frequency')
        self.stats.append('reincarnation_duration')

        self.upgrades['radius'] = (1, 4)
        self.upgrades['reincarnation_duration'] = (2, 4, "Buff Duration")
        self.upgrades['aura_frequency'] = (-1, 4, "Aura Frequency", "Alus' aura takes 1 less turn to activate.")
        self.upgrades['guard'] = (1, 2, "Saintly Protection", "Alus starts with [2_SH:shield].")

        self.must_target_empty = True

    def get_impacted_tiles(self, x, y):
        return [Level.Point(x, y)]

    def get_description(self):
        return (
            "Summon Alus, the Saint of Reincarnation.\n"
            "Alus is a flying [holy] [undead] with [{minion_health}_HP:minion_health], 75 [holy] resist, and 75 [dark] resist.\n"
            "Alus has an aura around him that activates every [{aura_frequency}_turns:holy] and affects allies in [{radius}_tiles:radius] of him.\n"
            "Affected [undead], [demon], and [holy] units gain a buff that grants the ability to reincarnate on death for [{reincarnation_duration}_turns:duration].\n"
            "However, Alus cannot attack on his own."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Alus, Saint of Reincarnation"
        unit.flying = True
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","alus")
        unit.max_hp = self.get_stat('minion_health')
        unit.tags = [Level.Tags.Undead, Level.Tags.Holy]
        unit.resists[Level.Tags.Holy] = 75
        unit.resists[Level.Tags.Dark] = 75
        unit.resists[Level.Tags.Ice] = 0
        unit.buffs.append(ReincarnAura(self))
        unit.is_coward = False
        if self.get_stat('guard'):
            unit.shields = 2
        return unit
    
    def cast_instant(self, x, y):
        self.summon(self.make_summon(), Level.Point(x, y))

class UndeathTowerSummon(Level.Spell):
    def __init__(self, spell):
        self.spell = spell
        Level.Spell.__init__(self)

    def on_init(self):
        self.range = 0
        self.cool_down = self.spell.get_stat('summon_cooldown')
        self.num_summons = self.spell.get_stat('num_summons')
        self.name = "Call of Undeath"
    
    def get_ai_target(self):
        if not any(Level.are_hostile(self.caster, u) for u in self.caster.level.units):
            return None
        else:
            return self.caster
    
    def get_description(self):
        return "Randomly summon ghosts or skeletons"
        
    def make_skeleton(self):
        skeleton = Level.Unit()
        skeleton.name = "Skeleton"
        skeleton.asset_name = "skeletal"
        skeleton.max_hp = 5
        skeleton.spells.append(CommonContent.SimpleMeleeAttack(5))
        skeleton.tags.append(Level.Tags.Undead)
        skeleton.team = self.caster.team
        skeleton.flying = False
        return skeleton
    
    def cast_instant(self, x, y):
        if self.spell.get_stat('ghast'):
            accepted = [self.make_skeleton, Monsters.Ghost, Monsters.GhostMass]
            acceptedw = [40, 50, 10]
        elif self.spell.get_stat('bony'):
            accepted = [self.make_skeleton, Monsters.Ghost, Monsters.BoneShambler]
            acceptedw = [50, 40, 10]
        else:
            accepted = [self.make_skeleton, Monsters.Ghost]
            acceptedw = [50, 50]
        for i in range(self.num_summons):
            mon = random.choices(accepted, acceptedw, k=1)[0]
            if mon == Monsters.BoneShambler:
                mon = mon(16)
                CommonContent.apply_minion_bonuses(self.spell, mon)
                mon.max_hp = 16
            else:
                mon = mon()
                CommonContent.apply_minion_bonuses(self.spell, mon)
            mon.turns_to_death = None
            mon.source = self.spell
            self.summon(mon, Level.Point(x, y), radius=5)

class UndeathTower(Level.Spell):

    def on_init(self):

        self.name = "Black Fulcrum"
        
        self.level = 5
        self.tags = [Level.Tags.Dark, Level.Tags.Conjuration]
        self.range = 2
        self.max_charges = 4
        self.minion_health = 35
        self.minion_duration = 18
        self.summon_cooldown = 4
        self.num_summons = 2

        self.upgrades['num_summons'] = (1, 3)
        self.upgrades['summon_cooldown'] = (-1, 4)
        self.upgrades['strong'] = (1, 3, "Iron Will", "The fulcrum becomes [metallic].")
        self.upgrades['ghast'] = (1, 5, "Ghastly Fulcrum", "The fulcrum has a 10% chance to spawn a ghostly mass instead of a skeleton.", "undeath")
        self.upgrades['bony'] = (1, 6, "King of Bones", "The fulcrum has a 10% chance to spawn a bone shambler with 16 HP instead of a ghost.", "undeath")

        self.must_target_empty = True

    def get_impacted_tiles(self, x, y):
        return [Level.Point(x, y)]

    def get_description(self):
        return (
            "Summon a Fulcrum of Undeath at target tile.\n"
            "The fulcrum is an immobile [dark] [construct] with [{minion_health}_HP:minion_health], 50 [physical] resist, and 50 [dark] resist.\n"
            "The fulcrum can summon [{num_summons}:num_summons] undead on a [{summon_cooldown}-turn_cooldown:dark], choosing from ghosts or skeletons.\n"
            "The fulcrum vanishes after [{minion_duration}_turns:minion_duration]."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Fulcrum of Undeath"
        unit.flying = True
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","undeath_fulcrum")
        unit.max_hp = self.get_stat('minion_health')
        unit.tags = [Level.Tags.Dark, Level.Tags.Construct]
        if self.get_stat('strong'):
            unit.tags.append(Level.Tags.Metallic)
        unit.resists[Level.Tags.Physical] = 50
        unit.resists[Level.Tags.Dark] = 50
        unit.turns_to_death = self.get_stat('minion_duration')
        unit.stationary = True
        unit.spells.append(UndeathTowerSummon(self))
        return unit
    
    def cast_instant(self, x, y):
        self.summon(self.make_summon(), Level.Point(x, y))

class MortalIdolBuff(Level.Buff):

    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)

    def on_applied(self, owner):
        self.name = "Necrosis"

    def on_advance(self):
        units = self.owner.level.get_units_in_los(self.owner)
        for u in units:
            if u == self.owner:
                continue
            elif Level.Tags.Undead in u.tags and not Level.are_hostile(u, self.owner):
                u.deal_damage(-2, Level.Tags.Heal, self)
            else:
                u.deal_damage(1, Level.Tags.Dark, self)

class MortalIdol(Level.Spell):

    def on_init(self):

        self.name = "Bone Idol"
        
        self.level = 6
        self.tags = [Level.Tags.Dark, Level.Tags.Conjuration]
        self.max_charges = 2

        self.minion_health = 25
        self.shields = 4
        self.minion_duration = 25

        self.upgrades['shields'] = (4, 3)
        self.upgrades['minion_duration'] = (3, 2)
        self.upgrades['ranged'] = (1, 5, "Necrotic Wrath", "The idol gains a lifesteal [dark] ranged attack.")

        self.must_target_walkable = True
        self.must_target_empty = True

    def get_description(self):
        return ("Summon an Idol of Necrosis.\n"
                "The idol has [{minion_health}_HP:minion_health], [{shields}_SH:shields], 100 [dark] resist, and is stationary.\n"
                "The idol has a passive aura which affects all units in line of sight of the idol each turn.\n"
                "Affected [undead] allies heal for 2 HP, and all other units including the caster that are not [undead] take 1 [dark] damage.\n"
                "The idol vanishes after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

    def make_idol(self):
        idol = Level.Unit()
        idol.asset_name = os.path.join("..","..","mods","MiscSummons","units","idol_necro")
        idol.name = "Idol of Necrosis"
        idol.max_hp = self.get_stat('minion_health')
        idol.shields = self.get_stat('shields')
        idol.stationary = True
        idol.resists[Level.Tags.Poison] = 100
        idol.resists[Level.Tags.Dark] = 100
        idol.tags = [Level.Tags.Construct, Level.Tags.Dark]
        idol.buffs.append(MortalIdolBuff(self))
        if self.get_stat('ranged'):
            idol.spells.append(CommonContent.SimpleRangedAttack(name="Necrotic Beam", damage=10, damage_type=Level.Tags.Dark, range=7, beam=True, drain=True))
        idol.turns_to_death = self.get_stat('minion_duration')
        return idol
    
    def cast_instant(self, x, y):
        self.summon(self.make_idol(), Level.Point(x, y))

class HonorBuff(Level.Buff):

    def __init__(self, spell):
        Level.Buff.__init__(self)
        self.name = "Honor"
        self.color = Level.Tags.Holy.color
        self.turns = 0
        self.spell = spell
        if self.spell.get_stat('glory'):
            self.global_bonuses['damage'] = 4
        self.buff_type = Level.BUFF_TYPE_BLESS
    
    def on_applied(self, owner):
        owner.resists[Level.Tags.Poison] = 100
        if self.spell.get_stat('swift'):     
            for s in owner.spells:
                s.cool_down = max(0, s.cool_down-1)

    def on_advance(self):
        if self.owner.shields >= 10:
            self.turns = 0
        else:
            self.turns += 1
            if self.turns == 3:
                self.owner.add_shields(1)
                self.turns = 0

    def on_unapplied(self):
        if self.spell.get_stat('swift'):
            for s in self.owner.spells:
                s.cool_down = max(0, s.cool_down+1)

class HonorBless(Level.Spell):

    def __init__(self, dur, source_spell):
        self.dur = dur
        self.source_spell = source_spell
        Level.Spell.__init__(self)

    def on_init(self):
        self.name = "Decoration of Honor"
        self.description = "A friendly [holy] unit or knight gains 5 max HP and regenerates 1 shield every 3 turns for %d turns" % (self.dur)
        self.range = Level.RANGE_GLOBAL
        self.requires_los = False
    
    def get_ai_target(self):
        to_hit = [u for u in self.caster.level.units if u != self.caster and not Level.are_hostile(u, self.caster) and (Level.Tags.Holy in u.tags or "Knight" in u.name) and not u.has_buff(HonorBuff)]
        return random.choice(to_hit) if to_hit else None

    def cast(self, x, y):
        unit = self.caster.level.get_unit_at(x, y)
        self.caster.level.show_path_effect(self.caster, unit, Level.Tags.Holy, minor=True)
        unit.apply_buff(HonorBuff(self.source_spell), self.dur)
        if self.source_spell.get_stat('poison_fix'):
            unit.deal_damage(-15, Level.Tags.Heal, self)
        yield

class OathTablet(Level.Spell):

    def on_init(self):

        self.name = "Venerated Stone"
        
        self.level = 4
        self.tags = [Level.Tags.Holy, Level.Tags.Conjuration]
        self.range = 3
        self.max_charges = 3
        self.ability_cooldown = 12
        self.minion_health = 35
        self.shields = 2
        self.duration = 10

        self.stats.append('ability_cooldown')

        self.upgrades['ability_cooldown'] = (-2, 4)
        self.upgrades['shields'] = (2, 2)
        self.upgrades['poison_fix'] = (1, 4, "Crusader's Repose", "The tablet also heals targets for 15 HP.", "crusade")
        self.upgrades['glory'] = (1, 4, "Crusader's Valor", "The tablet also increases ability damage by 4.", "crusade")
        self.upgrades['swift'] = (1, 5, "Rapid Crusade", "The tablet also decreases spell cooldowns by 1.", "crusade")

        self.must_target_walkable = True
        self.must_target_empty = True

    def get_description(self):
        return ("Summon a Tablet of Honor.\n"
                "The tablet is a stationary [construct] with 50 [physical] resist, 50 [holy] resist, [{minion_health}_HP:minion_health], and [{shields}_SH:shield].\n"
                "The tablet has no attacks of its own.\n"
                "The tablet can grant a friendly knight or [holy] unit 100 [poison] resist permanently, and shield regeneration for [{duration}_turns:duration].\n"
                "This ability has a [{ability_cooldown}_turn_cooldown:duration]."
                ).format(**self.fmt_dict())\

    def tablet(self):
        unit = Level.Unit()
        unit.name = "Tablet of Honor"
        unit.tags = [Level.Tags.Construct]
        unit.resists[Level.Tags.Physical] = 50
        unit.resists[Level.Tags.Holy] = 50
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","tablet_honor")
        unit.max_hp = self.get_stat('minion_health')
        unit.shields = self.get_stat('shields')
        unit.spells.append(HonorBless(self.get_stat('duration'), self))
        unit.spells[0].cool_down = self.get_stat('ability_cooldown')
        unit.stationary = True
        return unit

    def cast_instant(self, x, y):
        self.summon(self.tablet(), Level.Point(x, y))

class ClawSwing(Level.Spell):

    def on_init(self):
        self.name = "Rotting Claw"
        self.description = "Deals damage in an arc\nDeals dark, physical, and poison damage"
        self.range = 1.5
        self.melee = True
        self.can_target_self = False
        
        self.damage = 0
        self.damage_type = [Level.Tags.Physical, Level.Tags.Poison, Level.Tags.Dark]

    def get_impacted_tiles(self, x, y):
        ball = self.caster.level.get_points_in_ball(x, y, 1, diag=True)
        aoe = [p for p in ball if 1 <= Level.distance(p, self.caster, diag=True) < 2]
        return aoe

    def cast(self, x, y):
        for p in self.get_impacted_tiles(x, y):
            for dtype in self.damage_type:
                unit = self.caster.level.get_unit_at(p.x, p.y)
                if unit and not Level.are_hostile(self.caster, unit):
                    continue
                self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), dtype, self)
                yield    

class Corpseport(Level.Spell):

    def on_init(self):

        self.name = "Abandon Corpus"
        
        self.level = 5
        self.max_charges = 3
        self.tags = [Level.Tags.Dark, Level.Tags.Nature, Level.Tags.Conjuration, Level.Tags.Translocation]
        self.range = 5
        self.hp_percentage = 50
        self.minion_damage = 10
        self.stats.append("hp_percentage")

        self.upgrades['hp_percentage'] = (25, 3)
        self.upgrades['range'] = (2, 2)
        self.upgrades['plagued'] = (1, 3, "Plagued Corpus", "The body's melee attack is replaced with a claw swing dealing [dark], [physical], and [poison] damage in an arc.")

        self.must_target_walkable = True
        self.must_target_empty = True
        self.requires_los = False

    def get_description(self):
        return (
                "Shed your mortal body and reform up to [{range}_tiles_away:range].\n"
                "Your old body becomes a [living] [dark] [nature] [undead] minion with [{hp_percentage}%_of_your_max_HP:minion_health] and 100 [poison] resist.\n"
                "It has a melee attack dealing [{minion_damage}_physical_damage:physical]."
                ).format(**self.fmt_dict())

    def zombo(self):
        unit = Level.Unit()
        unit.name = "Wizombie"
        unit.tags = [Level.Tags.Living, Level.Tags.Undead, Level.Tags.Dark, Level.Tags.Nature]
        unit.resists[Level.Tags.Physical] = 0
        unit.resists[Level.Tags.Poison] = 100
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","player_zombie")
        unit.max_hp = math.ceil(self.caster.max_hp*(self.get_stat('hp_percentage')/100))
        if self.get_stat('plagued'):
            p = ClawSwing()
            p.damage = self.get_stat('minion_damage')
            unit.spells.append(p)
        else:
            unit.spells.append(CommonContent.SimpleMeleeAttack(self.get_stat('minion_damage')))
        return unit

    def cast_instant(self, x, y):
        oldpos = Level.Point(self.caster.x, self.caster.y)
        self.caster.level.act_move(self.caster, x, y, teleport=True)
        self.summon(self.zombo(), oldpos)

class VoodooLink(Level.Buff):
    def __init__(self, spell, linked):
        Level.Buff.__init__(self)
        self.name = "Voodoo Link"
        self.color = Level.Tags.Dark.color
        self.spell = spell
        self.linked = linked
        self.owner_triggers[Level.EventOnDamaged] = self.on_damage
        if spell.get_stat('twist'):
            self.owner_triggers[Level.EventOnBuffApply] = self.on_apply
            self.owner_triggers[Level.EventOnBuffRemove] = self.on_remove
        if spell.get_stat('share'):
            self.global_triggers[Level.EventOnPreDamaged] = self.share_proc
    
    def on_damage(self, evt):
        self.linked.deal_damage(evt.damage, Level.Tags.Dark, self)

    def on_apply(self, evt):
        buff = self.owner.get_buff(type(evt.buff))
        for t in buff.resists:
            if buff.resists[t] > 0:
                self.owner.resists[t] -= 2*buff.resists[t]
    
    def on_remove(self, evt):
        for t in evt.buff.resists:
            if evt.buff.resists[t] > 0:
                self.owner.resists[t] += 2*evt.buff.resists[t]
    
    def share_proc(self, evt):
        if evt.damage > 0 and not Level.are_hostile(evt.unit, self.owner) and evt.unit.name != "Voodoo Doll":
            self.owner.deal_damage(evt.damage, Level.Tags.Physical, self)

    def on_advance(self):
        if self.spell.get_stat('wicker'):
            self.linked.deal_damage(1, Level.Tags.Fire, self)
    
    def get_tooltip(self):
        return "Whenever this unit takes damage, the cursed unit takes the same amount of dark damage."


class VoodooDoll(Level.Spell):

    def on_init(self):

        self.name = "Voodoo Curse"
        
        self.level = 5
        self.max_charges = 5
        self.tags = [Level.Tags.Dark, Level.Tags.Enchantment, Level.Tags.Conjuration]
        self.range = 8

        self.upgrades['twist'] = (1, 4, "Twist Resistances", "Effects that increase the doll's resistances instead decrease them by the same amount.")
        self.upgrades['frail'] = (1, 3, "Frailty", "The doll gains -50 [dark], [physical], and [poison] resistance.")
        self.upgrades['share'] = (1, 4, "Pain Split", "Whenever a non-doll ally is hit, the doll will take the same amount of [physical] damage.\nThe amount is calculated before resistances, and the doll is damaged even if the target blocks the attack due to shield.", "cursing")
        self.upgrades['wicker'] = (1, 5, "Wicker Curse", "The target takes 1 [fire] damage every turn.", "cursing")

    def can_cast(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        return u and Level.are_hostile(u, self.caster) and Level.Spell.can_cast(self, x, y)

    def get_description(self):
        return (
                "Hex target enemy, creating a voodoo doll nearby.\n"
                "The doll has the same max HP as the target.\n"
                "Whenever the doll is damaged, the target takes that much [dark] damage."
        ).format(**self.fmt_dict())

    def zombo(self):
        unit = Level.Unit()
        unit.name = "Voodoo Doll"
        unit.tags = [Level.Tags.Construct, Level.Tags.Dark]
        unit.resists[Level.Tags.Poison] = 0
        if self.get_stat('frail'):
            for t in [Level.Tags.Physical, Level.Tags.Dark, Level.Tags.Poison]:
                unit.resists[t] = -50
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","voodoo_doll")
        unit.max_hp = 0
        unit.stationary = True
        return unit

    def cast_instant(self, x, y):
        p = self.zombo()
        u = self.caster.level.get_unit_at(x, y)
        p.max_hp, p.cur_hp = u.max_hp, u.cur_hp
        p.buffs.append(VoodooLink(self, u))
        self.summon(p, Level.Point(x, y), radius=6)

class ScrollBuff(Level.Buff):
    def __init__(self, spell, chosen):
        Level.Buff.__init__(self)
        self.color = Level.Tags.Physical.color
        self.chosen, self.spell = chosen, spell
        self.owner_triggers[Level.EventOnSpellCast] = self.on_cast
        if spell.get_stat('runic'):
            self.owner_triggers[Level.EventOnDeath] = self.on_death
    
    def on_cast(self, evt):
        self.owner.kill()
    
    def on_death(self, evt):
        candidates = [s for s in self.chosen.tags if s in [Level.Tags.Arcane, Level.Tags.Dark, Level.Tags.Holy, Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Lightning, Level.Tags.Nature, Level.Tags.Metallic]]
        candidates = [Level.Tags.Physical if item == Level.Tags.Metallic else (Level.Tags.Poison if item == Level.Tags.Nature else item) for item in candidates]
        if candidates:
            dtype = random.choice(candidates)
            for stage in Level.Burst(self.owner.level, Level.Point(self.owner.x, self.owner.y), 3):
                for point in stage:
                    u = self.owner.level.get_unit_at(point.x, point.y)
                    if u and not Level.are_hostile(u, self.owner):
                        continue
                    self.owner.level.deal_damage(point.x, point.y, 13, dtype, self)

    def get_tooltip(self):
        s = "Dies when it casts a spell"
        if self.spell.get_stat('runic'):
            s += ", dealing 13 damage of a type randomly selected from tags the scroll's chosen spell has"
        return s

class WriteIt(Level.Spell):
    def on_init(self):

        self.name = "Transcribe"
        
        self.level = 5
        self.max_charges = 1
        self.tags = [Level.Tags.Arcane, Level.Tags.Conjuration]
        self.range = 0

        self.upgrades['boost'] = (1, 3, "High Scrolls", "Level 3 spells can also be transcribed.")
        self.upgrades['max_charges'] = (1, 2)
        self.upgrades['runic'] = (1, 7, "Rune Paper", "Scrolls explode on death dealing 13 damage in a [3-tile_burst:radius].\nThe type of this damage is chosen randomly among damage types that the chosen spell had as tags.\n[Metallic] becomes [physical] and [nature] becomes [poison] when deciding.")
    
    def can_cast(self, x, y):
        candidates = [s for s in self.caster.spells if s.level <= (3 if self.get_stat('boost') else 2) and s.cur_charges > 0 and Level.Tags.Sorcery in s.tags and Level.Tags.Conjuration not in s.tags]
        return len(candidates) > 0 and Level.Spell.can_cast(self, x, y)

    def get_description(self):
        return(
            "Consume all remaining charges of a random level 2 or lower [sorcery] spell with at least 1 charge left. [Conjuration] spells cannot be transcribed.\n"
            "For each charge consumed, summon a living scroll imbued with that spell nearby.\n"
            "The scrolls have [1_HP:minion_health] and [2_SH:shield].\n"
            "The scrolls have all tags the spell has, excluding [sorcery], [enchantment] and [conjuration].\n"
            "Scrolls use their spells with all of your upgrades and bonuses."
        ).format(**self.fmt_dict())

    def make_scroll(self, spell):
        scroll = Level.Unit()
        scroll.name = "Living Scroll of %s" % spell.name
        scroll.asset_name = "living_scroll"
        scroll.max_hp = 1
        scroll.shields = 2
        scroll.flying = True
        fball = type(spell)()
        fball.statholder = self.caster
        fball.max_charges = 0
        fball.cur_charges = 0
        scroll.spells.append(fball)
        scroll.buffs.append(ScrollBuff(self, spell))
        scroll.tags = [s for s in spell.tags if s not in [Level.Tags.Sorcery, Level.Tags.Conjuration, Level.Tags.Enchantment]]
        return scroll
        
    def cast_instant(self, x, y):
        candidates = [s for s in self.caster.spells if s.level <= (3 if self.get_stat('boost') else 2) and s.cur_charges > 0 and Level.Tags.Sorcery in s.tags and Level.Tags.Conjuration not in s.tags]
        sp = random.choice(candidates)
        for i in range(sp.cur_charges):
            self.summon(self.make_scroll(sp), Level.Point(x, y), radius=7)
        sp.cur_charges = 0

class IcyHotHasteBuff(Level.Buff):
    def __init__(self, spell, power):
        Level.Buff.__init__(self)
        self.name = "Frostfire Haste %d" % power
        self.power, self.spell = power, spell
        self.color = Level.Tags.Fire.color
        self.buff_type = Level.BUFF_TYPE_BLESS

    def on_advance(self):
        for i in range(self.power):
            if self.owner and self.owner.is_alive():
                self.owner.level.leap_effect(self.owner.x, self.owner.y, random.choice([Level.Tags.Fire.color, Level.Tags.Ice.color]), self.owner)
                self.owner.advance()

class IcyHotBless(Level.Spell):

    def __init__(self, dur, source_spell):
        self.dur = dur
        self.source_spell = source_spell
        Level.Spell.__init__(self)

    def on_init(self):
        self.name = "Frostfire blessing"
        self.description = "A friendly [fire] or [ice] unit gains 1 extra action each turn for %d turns" % (self.dur)
        self.range = Level.RANGE_GLOBAL
        self.requires_los = False
    
    def get_ai_target(self):
        to_hit = [u for u in self.caster.level.units if u != self.caster and not Level.are_hostile(u, self.caster) and (Level.Tags.Fire in u.tags or Level.Tags.Ice in u.tags) and not u.has_buff(IcyHotHasteBuff)]
        return random.choice(to_hit) if to_hit else None

    def cast(self, x, y):
        unit = self.caster.level.get_unit_at(x, y)
        self.caster.level.show_path_effect(self.caster, unit, Level.Tags.Ice, minor=True)
        unit.apply_buff(IcyHotHasteBuff(self.source_spell, 1), self.dur)
        yield

class IcyHotTablet(Level.Spell):

    def on_init(self):

        self.name = "Frostfire Stone"
        
        self.level = 6
        self.tags = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Conjuration]
        self.range = 3
        self.max_charges = 3
        self.ability_cooldown = 14
        self.minion_health = 40
        self.shields = 3
        self.ability_duration = 4

        self.stats.append('ability_cooldown')

        self.upgrades['ability_duration'] = (1, 4)
        self.upgrades['ability_cooldown'] = (-3, 3)
        self.upgrades['minion_health'] = (10, 2)

        self.must_target_walkable = True
        self.must_target_empty = True

    def get_description(self):
        return (
            "Summon a Frostfire Tablet.\n"
            "The tablet is a stationary [construct] with 50 [physical] resist, 50 [fire] resist, 50 [ice] resist, [{minion_health}_HP:minion_health], and [{shields}_SH:shield].\n"
            "The tablet has no attacks of its own.\n"
            "The tablet can grant a friendly [fire] or [ice] unit an extra action each turn for [{ability_duration}_turns:duration].\n"
            "This ability has a [{ability_cooldown}_turn_cooldown:duration]."
        ).format(**self.fmt_dict())

    def tablet(self):
        unit = Level.Unit()
        unit.name = "Frostfire Tablet"
        unit.tags = [Level.Tags.Construct]
        unit.resists[Level.Tags.Fire] = 50
        unit.resists[Level.Tags.Ice] = 50
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","tablet_frostfire")
        unit.max_hp = self.get_stat('minion_health')
        unit.shields = self.get_stat('shields')
        unit.stationary = True
        unit.spells.append(IcyHotBless(self.get_stat('ability_duration'), self))
        unit.spells[0].cool_down = self.get_stat('ability_cooldown')
        return unit

    def cast_instant(self, x, y):
        self.summon(self.tablet(), Level.Point(x, y))

class SupportAuraBuff(Level.Buff):

    def __init__(self, radius):
        Level.Buff.__init__(self)
        self.color = Level.Tags.Lightning.color
        self.radius = radius

    def on_advance(self):
        units = list(self.owner.level.get_units_in_ball(Level.Point(self.owner.x, self.owner.y), self.radius))

        for unit in units:
            if not self.owner.level.are_hostile(self.owner, unit):
                continue
            buffs = list(unit.buffs)
            for b in buffs:
                if b.buff_type not in [Level.BUFF_TYPE_CURSE, Level.BUFF_TYPE_PASSIVE]:
                    unit.remove_buff(b)
                    unit.deal_damage(0, Level.Tags.Lightning, self)

    def get_tooltip(self):
        return "Removes buffs from enemies in a %d-tile radius" % self.radius


class WatcherSwapBuff(Level.Buff):
    def __init__(self, spell):
        Level.Buff.__init__(self)
        self.spell = spell
        self.activated = False
        self.color = Level.Tags.Metallic.color
        self.buff_type = Level.BUFF_TYPE_PASSIVE
        self.global_triggers[Level.EventOnSpellCast] = self.on_cast

    def on_advance(self):
        self.activated = False
    
    def on_cast(self, evt):
        for t in evt.spell.get_impacted_tiles(evt.x, evt.y):
            u = self.owner.level.get_unit_at(t.x, t.y)
            if u and u.cur_hp < u.max_hp // 2 and not Level.are_hostile(u, self.owner):
                if not self.spell.get_stat('paladin'):
                    self.activated = True
                elif self.owner.level.can_move(self.owner, u.x, u.y, True, True):
                    self.owner.level.act_move(self.owner, u.x, u.y, teleport=True, leap=False, force_swap=True)
                    return

    def get_tooltip(self):
        desc = "waps places with allies below half HP that would take damage from attacks"
        if self.spell.get_stat('paladin'):
            desc = "S" + desc
        else:
            desc = "Once per turn, s" + desc
        return desc

class JohnsOtherIdea(Level.Spell):

    def on_init(self):

        self.name = "Clockwork Guard"
        
        self.level = 5
        self.tags = [Level.Tags.Holy, Level.Tags.Metallic, Level.Tags.Conjuration]
        self.range = 0
        self.max_charges = 3
        self.minion_health = 16
        self.num_summons = 2
        self.minion_damage = 5
        self.minion_range = 5
        self.minion_duration = 25
        self.shield_frequency = 4
        self.stats.append('shield_frequency')

        self.upgrades['shield_frequency'] = (-1, 3, "Shield Frequency", "Watchers regenerate shields 1 turn faster.")
        self.upgrades['num_summons'] = (1, 3)
        self.upgrades['paladin'] = (1, 5, "Clockwork Paladins", "Watchers gain [2_SH:shield] and can swap places an unlimited number of times each turn.", "variate")
        self.upgrades['prism'] = (1, 4, "Prism Watchers", "Watchers' ranged attacks [freeze] units hit for 1 turn.", "variate")
        self.upgrades['diviner'] = (1, 5, "Clockwork Judges", "Watchers gain [lightning] and an aura that removes buffs on enemies in a [4-tile_radius:radius] of them.", "variate")

    def get_description(self):
        return (
            "Summon [{num_summons}:num_summons] clockwork watchers near the Wizard.\n"
            "Watchers are flying [holy] [metallic] [constructs:construct] with [{minion_health}_HP:minion_health] and a wide array of resistances.\n"
            "Watchers have ranged attacks dealing [{minion_damage}:damage] [holy] damage with a range of [{minion_range}_tiles:minion_range], and regenerate [1_SH:shield] every [{shield_frequency}_turns:arcane], to a max of 5.\n"
            "Watchers have advanced sensory and mobility systems that allow them to swap places with allies below half of their maximum HP that would be hit by damaging attacks once each turn.\n"
            "Watchers last [{minion_duration}_turns:minion_duration]."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Clockwork Watcher"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","watcher_clockwork")
        unit.max_hp = self.get_stat('minion_health')
        unit.tags = [Level.Tags.Holy, Level.Tags.Metallic, Level.Tags.Construct]
        unit.resists[Level.Tags.Holy] = 50
        unit.resists[Level.Tags.Dark] = -50
        atk_name = "Clockwork Bolt"
        dts = Level.Tags.Holy
        basic_atk = CommonContent.SimpleRangedAttack(name=atk_name, damage=self.get_stat('minion_damage'), damage_type=dts, range=self.get_stat('minion_range'), buff=(CommonContent.FrozenBuff if self.get_stat('prism') else None), buff_duration=(1 if self.get_stat('prism') else 0))
        unit.spells.append(basic_atk)
        unit.buffs.append(CommonContent.ShieldRegenBuff(5, self.get_stat('shield_frequency')))
        unit.buffs.append(WatcherSwapBuff(self))
        if self.get_stat('diviner'):
            unit.tags.append(Level.Tags.Lightning)
            unit.buffs.append(SupportAuraBuff(4))
        unit.turns_to_death = self.get_stat('minion_duration')
        if self.get_stat('paladin'):
            unit.shields = 2
        unit.flying = True
        return unit
    
    def cast_instant(self, x, y):
        for i in range(self.get_stat('num_summons')):
            self.summon(self.make_summon(), self.caster, radius=5)

class CrystalAuraBuff(Level.Buff):

    def __init__(self, radius, spell):
        Level.Buff.__init__(self)
        self.color = Level.Tags.Glass.color
        self.radius = radius
        self.spell = spell

    def on_advance(self):
        units = list(self.owner.level.get_units_in_ball(Level.Point(self.owner.x, self.owner.y), self.radius))
        hit = 0
        for unit in units:
            if not self.owner.level.are_hostile(self.owner, unit):
                continue
            unit.apply_buff(CommonContent.GlassPetrifyBuff(), 2)
            unit.deal_damage(1, Level.Tags.Physical, self.spell)
            hit += 1
        points = self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.radius)
        points = [p for p in points if not self.owner.level.get_unit_at(p.x, p.y)]
        random.shuffle(points)
        if 7-hit > 0:
            for i in range(7-hit):
                if not points:
                    break
                p = points.pop()
                self.owner.level.deal_damage(p.x, p.y, 0, Level.Tags.Physical, self.spell)

    def can_threaten(self, x, y):
        return Level.distance(self.owner, Level.Point(x, y)) <= self.radius
                
    def get_tooltip(self):
        return "Glassifies enemies in a %d-tile radius for 2 turns, then deals 1 [physical] damage to them." % self.radius

class CrystalBreath(Monsters.BreathWeapon):

    def on_init(self):
        self.name = "Crystal Breath"
        self.damage = 0
        self.damage_type = Level.Tags.Physical

    def get_description(self):
        return "Breathes a cone of crystals dealing %d [ice] and [physical] damage" % self.damage

    def per_square_effect(self, x, y):
        for dtype in [Level.Tags.Ice, Level.Tags.Physical]:
            self.caster.level.deal_damage(x, y, self.damage, dtype, self)

class MithrilDrake(Level.Spell):

    def on_init(self):

        self.name = "Crystal Drake"
        
        self.level = 7
        self.tags = [Level.Tags.Ice, Level.Tags.Metallic, Level.Tags.Conjuration, Level.Tags.Dragon]
        self.range = 5
        self.max_charges = 1
        self.minion_health = 99
        self.breath_damage = 10
        self.minion_damage = 8
        self.minion_range = 6

        self.must_target_empty = True

        self.upgrades['minion_health'] = (33, 3)
        self.upgrades['breath_damage'] = (9, 3)
        self.upgrades['aura'] = (1, 7, "Crystal Storm", "Crystal Drakes gain an aura that [glassifies:glass] enemies in a 5-tile radius for 2 turns and deals 1 [physical] damage to them.")

    def get_description(self):
        return (
            "Summon a crystal drake on target tile.\n"
            "Crystal drakes are [ice] [metallic] [constructs:construct] with [{minion_health}_HP:minion_health] and a variety of resistances.\n"
            "Crystal drakes have a breath weapon dealing [{breath_damage}:damage] [physical] and [ice] damage in a [{minion_range}-tile_cone:range], and a melee attack dealing [{minion_damage}_physical_damage:physical]."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Crystal Drake"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","drake_crystal")
        unit.max_hp = self.get_stat('minion_health')
        unit.flying = True
        breathe = CrystalBreath()
        breathe.damage = self.get_stat('breath_damage')
        breathe.range = self.get_stat('minion_range')
        unit.tags = [Level.Tags.Ice, Level.Tags.Metallic, Level.Tags.Construct, Level.Tags.Dragon]
        unit.spells.extend([breathe, CommonContent.SimpleMeleeAttack(self.get_stat('minion_damage'))])
        if self.get_stat('aura'):
            unit.buffs.append(CrystalAuraBuff(5, self))
        return unit
    
    def cast_instant(self, x, y):
        self.summon(self.make_summon(), Level.Point(x, y), radius=5)

class FlaminDrake(Level.Spell):

    def on_init(self):

        self.name = "Furnace Drake"
        
        self.level = 7
        self.tags = [Level.Tags.Fire, Level.Tags.Metallic, Level.Tags.Conjuration, Level.Tags.Dragon]
        self.range = 3
        self.max_charges = 1
        self.minion_health = 60
        self.breath_damage = 20
        self.minion_damage = 15
        self.minion_range = 6
        self.radius = 5

        self.must_target_empty = True

        self.upgrades['minion_health'] = (25, 2)
        self.upgrades['breath_damage'] = (13, 4)
        self.upgrades['radius'] = (3, 5)
        self.upgrades['dragon_mage'] = (1, 6, "Dragon Mage", "Summoned Furnace Drakes can cast Melt with a 5 turn cooldown.\nThis Melt gains all of your upgrades and bonuses.")

    def get_impacted_tiles(self, x, y):
        return [Level.Point(x, y)]

    def get_description(self):
        return (
            "Summon a furnace drake on target tile.\n"
            "Furnace drakes are [fire] [metallic] [constructs:construct] with [{minion_health}_HP:minion_health] and a variety of resistances.\n"
            "Furnace drakes have a breath weapon dealing [{breath_damage}:damage] [fire] damage in a [{minion_range}_tile_cone:range], and a melee attack dealing [{minion_damage}_physical_damage:physical].\n"
            "Furnace drakes also have an aura dealing [2_fire_damage:fire] to units in a [{radius}-tile_radius:radius] each turn."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Furnace Drake"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","drake_furnace")
        unit.max_hp = self.get_stat('minion_health')
        unit.flying = True
        breathe = Monsters.FireBreath()
        breathe.damage = self.get_stat('breath_damage')
        breathe.range = self.get_stat('minion_range')
        breathe.name = "Furnace Breath"
        unit.tags = [Level.Tags.Fire, Level.Tags.Metallic, Level.Tags.Construct, Level.Tags.Dragon]
        unit.resists[Level.Tags.Ice] = -50
        unit.resists[Level.Tags.Fire] = 100
        unit.spells.extend([breathe, CommonContent.SimpleMeleeAttack(self.get_stat('minion_damage'))])
        unit.buffs.append(CommonContent.DamageAuraBuff(2, Level.Tags.Fire, self.get_stat('radius')))
        if self.get_stat('dragon_mage'):
            fball = Spells.MeltSpell()
            fball.statholder = self.caster
            fball.max_charges = 0
            fball.cur_charges = 0
            fball.cool_down = 5
            unit.spells.insert(1, fball)
        return unit
    
    def cast_instant(self, x, y):
        self.summon(self.make_summon(), Level.Point(x, y), radius=5)

class AscensionBuff(Level.Buff):

    def __init__(self, spell, unit):
        Level.Buff.__init__(self)
        self.name = "Countdown to Return"
        self.color = Level.Tags.Holy.color
        self.spell = spell
        self.unit = unit
        self.buff_type = Level.BUFF_TYPE_PASSIVE
        self.stack_type = Level.STACK_INTENSITY
        self.prereq = self.spell
        self.saved = None
    
    def make_summon(self, base):
        unit = Level.Unit()
        unit.spells = base.spells
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","ghost_holy")
        unit.name = base.name + (" Spirit" if base.source != self.spell else "")
        for s in unit.spells:
            s.caster = unit
            s.statholder = unit
            if hasattr(s, "damage"):
                s.damage += self.spell.get_stat('duration')*self.spell.get_stat('damage_boost')
        unit.max_hp = base.max_hp + self.spell.get_stat('health_boost')*self.spell.get_stat('duration')
        unit.flying = base.flying
        unit.tags = (base.tags if self.spell.get_stat('tag_keep') else [])
        if Level.Tags.Undead not in base.tags:
            unit.tags += [Level.Tags.Undead]
        unit.source = self.spell
        unit.resists = base.resists
        return unit

    def on_unapplied(self):
        spirit = self.make_summon(self.unit)
        self.summon(spirit, self.owner, 5)
        if self.spell.get_stat('booned'):
            eligible = [s for s in self.owner.spells if s.range == 0 and Level.Tags.Enchantment in s.tags]
            if not eligible:
                return
            pick = type(random.choice(eligible))()
            pick.cur_charges = 1
            pick.caster = spirit
            pick.owner = spirit
            pick.statholder = self.owner
            if pick.can_cast(spirit.x, spirit.y):
                self.owner.level.act_cast(spirit, pick, spirit.x, spirit.y)

class TRANSCENDE(Level.Spell):

    def on_init(self):

        self.name = "Ascension"
        
        self.level = 7
        self.tags = [Level.Tags.Holy, Level.Tags.Conjuration]
        self.max_charges = 2
        self.range = 7
        self.duration = 7
        self.requires_los = self.can_target_empty = False
        self.damage_boost = 1
        self.health_boost = 5
        self.stats.extend(['damage_boost', 'health_boost'])

        self.upgrades['redeem'] = (1, 3, "Salvation", "Ascension can target [demon] and [undead] allies.")
        self.upgrades['damage_boost'] = (1, 5, "Damage Boost", "Killed units gain an additional 1 damage per turn of death.")
        self.upgrades['health_boost'] = (3, 3, "Health Boost", "Killed units gain an additional 3 maximum HP per turn of death.")
        self.upgrades['tag_keep'] = (1, 3, "Wise Return", "Spirits gain all tags the target had on death.")
        self.upgrades['booned'] = (1, 7, "Boon Return", "Spirits will randomly cast one of your self-targeting [enchantment] spells when they are summoned.")

    def can_cast(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        return u and (Level.Tags.Holy in u.tags or ((Level.Tags.Demon in u.tags or Level.Tags.Undead in u.tags) and self.get_stat('redeem'))) and not Level.are_hostile(self.caster, u) and Level.Spell.can_cast(self, x, y)

    def get_description(self):
        return (
            "Target [holy] ally loses all reincarnations and dies.\n"
            "After [{duration}_turns:duration], revive it as an [undead] spirit near the Wizard.\n"
            "The spirit has all spells the target knew when it died and has its resists and ability to fly.\n"
            "For every turn the unit was dead, it gains [{damage_boost}_damage:damage] and [{health_boost}_max_HP:minion_health]."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        if not u:
            return
        for b in u.buffs:
            if type(b) == CommonContent.ReincarnationBuff:
                u.remove_buff(b)   
        u.kill()
        self.owner.apply_buff(AscensionBuff(self, u), self.get_stat('duration')) 

class MercuryBless(Level.Spell):

    def __init__(self, source_spell):
        self.source_spell = source_spell
        self.accepted = [Level.Tags.Metallic]
        if self.source_spell.get_stat('dark_compat'):
            self.accepted += [Level.Tags.Demon, Level.Tags.Undead]
        if self.source_spell.get_stat('myth_compat'):
            self.accepted += [Level.Tags.Holy, Level.Tags.Arcane]
        if self.source_spell.get_stat('elem_compat'):
            self.accepted += [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Lightning]
        if self.source_spell.get_stat('life_compat'):
            self.accepted += [Level.Tags.Nature]
        Level.Spell.__init__(self)

    def on_init(self):
        self.name = "Traveler's Boon"
        self.description = "A friendly %s unit gains %d extra actions" % (' or '.join(("[" + t.name.lower() + "]") for t in self.accepted), self.source_spell.get_stat('extra_turns'))
        self.range = self.source_spell.get_stat('minion_range')
        self.requires_los = False
    
    def get_ai_target(self):
        to_hit = [u for u in self.caster.level.units if u != self.caster and not Level.are_hostile(u, self.caster) and any(t in u.tags for t in self.accepted) and Level.Spell.can_cast(self, u.x, u.y) and u != self.caster.level.player_unit]
        return random.choice(to_hit) if to_hit else None

    def cast(self, x, y):
        unit = self.caster.level.get_unit_at(x, y)
        self.caster.level.show_path_effect(self.caster, unit, Level.Tags.Physical, minor=True)
        for i in range(self.source_spell.get_stat('extra_turns')):
            if unit and unit.is_alive():
                unit.level.leap_effect(unit.x, unit.y, random.choice([t.color for t in self.accepted]), unit)
                unit.advance()
            yield

class SpeedSummon(Level.Spell):

    def on_init(self):

        self.name = "Mercury Ritual"
        
        self.level = 6
        self.tags = [Level.Tags.Metallic, Level.Tags.Conjuration, Level.Tags.Holy]
        self.range = 5
        self.max_charges = 2
        self.minion_health = 44
        self.minion_range = 6
        self.minion_damage = 4
        self.extra_turns = 1

        self.must_target_empty = True
        self.must_target_walkable = True
        
        self.upgrades['boon_speed'] = (2, 3, "Traveler's Haste", "Mercury's boon loses 2 cooldown.")
        self.upgrades['extra_turns'] = (1, 5, "Extra Action", "Mercury can grant 1 more action with his boon.")
        self.upgrades['dark_compat'] = (1, 5, "Netherworld Travel", "Mercury can also target [demon] and [undead] units.", "travel")
        self.upgrades['myth_compat'] = (1, 4, "Mythic Travel", "Mercury can also target [holy] and [arcane] units.", "travel")
        self.upgrades['elem_compat'] = (1, 6, "Triad Travel", "Mercury can also target [fire], [lightning], and [ice] units.", "travel")
        self.upgrades['life_compat'] = (1, 3, "Fauna Travel", "Mercury can also target [nature] units.", "travel")

    def get_description(self):
        return (
            "Summon Mercury on target tile.\n"
            "Mercury is a [holy] [metallic] unit with [{minion_health}_HP:minion_health] and a variety of resistances.\n"
            "Mercury has a boon that can give [{extra_turns}_extra_actions:metallic] to [metallic] allies in [{minion_range}_tiles:range] of him. This ability does not require line of sight to use.\n"
            "Mercury has a melee attack dealing [{minion_damage}_physical_damage:physical].\n"
            "Casting this spell again while Mercury is already summoned will give him 2 SH and cleanse him of debuffs."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Mercury"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","mercury_god")
        unit.max_hp = self.get_stat('minion_health')
        unit.tags = [Level.Tags.Metallic, Level.Tags.Holy]
        unit.resists[Level.Tags.Holy] = 50
        unit.resists[Level.Tags.Dark] = -50
        unit.spells.extend([MercuryBless(self), CommonContent.SimpleMeleeAttack(self.get_stat('minion_damage'))])
        unit.spells[0].cool_down = 8 - self.get_stat('boon_speed')
        return unit
    
    def cast_instant(self, x, y):
        existing = [u for u in self.caster.level.units if u.name == "Mercury"]
        if existing:
            existing[0].add_shields(2)
            for b in existing.buffs:
                if b.buff_type == Level.BUFF_TYPE_CURSE:
                    existing.remove_buff(b)
            return
        self.summon(self.make_summon(), Level.Point(x, y), radius=5)

class BatFormBuff(Level.Buff):

    def __init__(self, spell):
        Level.Buff.__init__(self)
        self.name = "Bat Form"
        self.description = "You're a bat, yay!"
        self.spell = spell
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.stack_type = Level.STACK_TYPE_TRANSFORM
        self.asset = Spells.DarknessBuff().asset
        self.transform_asset_name = os.path.join("..","..","mods","MiscSummons","units","bat_vampire_player")
        self.can_casts = {}
        self.resists[Level.Tags.Dark] = 100
        self.resists[Level.Tags.Holy] = -100
        self.resists[Level.Tags.Fire] = -50
        
    def on_applied(self, owner):
        self.casts = 0
        self.cast_this_turn = False
        self.color = Level.Tags.Dark.color
        self.owner.flying = True
    
    def on_unapplied(self):
        self.owner.flying = False
        if not self.owner.level.tiles[self.owner.x][self.owner.y].can_walk:
            self.owner.level.queue_spell(self.bat_escape())
            return
        
    def bat_escape(self):
        tiles = [t for t in self.owner.level.iter_tiles() if t.can_walk and not t.unit]
        if not tiles:
            yield
        tiles.sort(key = lambda x: Level.distance(x, self.owner))
        self.owner.level.act_move(self.owner, tiles[0].x, tiles[0].y, teleport=True)
        self.owner.apply_buff(Level.Stun(), 2)
        yield

    def on_advance(self):
        self.owner.level.queue_spell(self.summon_bats())
    
    def modify_spell(self, spell):
        if spell == self.spell or not (Level.Tags.Dark in spell.tags):
            def cannot_cast(*args, **kwargs):
                return False

            self.can_casts[spell] = spell.can_cast
            spell.can_cast = cannot_cast

    def unmodify_spell(self, spell):
        if spell in self.can_casts:
            spell.can_cast = self.can_casts[spell]

    def modify_bat(self, source_func):
        u = source_func()
        CommonContent.apply_minion_bonuses(self.spell, u)
        u.get_buff(CommonContent.MatureInto).mature_duration = self.spell.get_stat('timer')   
        old = u.get_buff(CommonContent.MatureInto).spawner 
        u.get_buff(CommonContent.MatureInto).spawner = lambda: self.modify_monster(old) 
        u.cur_hp = u.max_hp = self.spell.get_stat('minion_health')
        return u

    
    def modify_monster(self, source_func):
        u = source_func()
        CommonContent.apply_minion_bonuses(self.spell, u)
        u.max_hp += self.spell.get_stat('minion_health')
        if self.spell.get_stat('defrail'):
            u.resists[Level.Tags.Fire] = -50
            u.resists[Level.Tags.Holy] = -50
        if u.has_buff(CommonContent.RespawnAs):
            old = u.get_buff(CommonContent.RespawnAs).spawner
            u.get_buff(CommonContent.RespawnAs).spawner = lambda: self.modify_bat(old)
        return u
    

    def summon_bats(self):
        self.owner.level.show_effect(0, 0, Level.Tags.Sound_Effect, 'summon_3')
        bonus = 1 if (self.spell.get_stat('extra_bat') and random.random() > .7) else 0
        for _ in range(1 + bonus):
            v = Monsters.VampireBat()
            if self.spell.get_stat('scholar') and random.random() > .5:
                v = Monsters.VampireEye()
            elif self.spell.get_stat('guard') and random.random() > .5:
                v = Variants.ArmoredBat()
            elif self.spell.get_stat('lord') and random.random() > .5:
                v = Monsters.VampireMist()
            CommonContent.apply_minion_bonuses(self.spell, v)
            v.get_buff(CommonContent.MatureInto).mature_duration = self.spell.get_stat('timer')
            old = v.get_buff(CommonContent.MatureInto).spawner 
            v.get_buff(CommonContent.MatureInto).spawner = lambda: self.modify_monster(old)
            v.cur_hp = v.max_hp = self.spell.get_stat('minion_health')
            self.spell.summon(v, self.owner)
            yield


class BatForm(Level.Spell):

    def on_init(self):

        self.name = "Bat Form"
        
        self.level = 7
        self.tags = [Level.Tags.Dark, Level.Tags.Conjuration, Level.Tags.Enchantment]
        self.range = 0
        self.max_charges = 1
        self.duration = 7
        self.minion_health = 13
        self.minion_damage = 7
        self.timer = 13
        self.stats.append('timer')

        self.upgrades['timer'] = (-5, 2, "Incubated Bats", "Bats mature 5 turns faster.")
        self.upgrades['extra_bat'] = (1, 4, "Spacious Shadows", "Bat Form has a 30% chance to summon an additional bat each turn.")
        self.upgrades['duration'] = (3, 4)
        self.upgrades['defrail'] = (25, 5, "Solar Shields", "Summoned vampires gain 50 [fire] and [holy] resist.")
        self.upgrades['scholar'] = (1, 5, "Vampire Scholars", "Summoned bats have a 50% chance to become vampire eyes.", "bat")
        self.upgrades['guard'] = (1, 3, "Vampire Guards", "Summoned bats have a 50% chance to become armored vampire bats.", "bat")
        self.upgrades['lord'] = (1, 4, "Vampire Lords", "Summoned bats have a 50% chance to become vampiric mists.", "bat")

    def get_description(self):
        return (
            "Become a vampire bat for [{duration}_turns:duration].\n"
            "While in bat form, you can only cast [dark] spells but you can fly over chasms.\n"
            "The Wizard gains 100 [dark] resist, -100 [holy] resist, and -50 [fire] resist while in bat form.\n"
            "Each turn, summon a vampire bat with [{minion_health}_HP:minion_health] near yourself, which matures into a vampire after [{timer}_turns:dark].\n"
            "If Bat Form expires over a chasm or other unwalkable terrain, the Wizard is teleported to the nearest walkable tile and stunned for 2 turns."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        self.caster.apply_buff(BatFormBuff(self), self.get_stat('duration'))

class GoyleDream(Level.Buff):

    def on_init(self):
        self.name = "Sweet Dream"
        self.description = "Sweet dreams!"
        self.color = Level.Tags.Dark.color
        self.asset = ['status', 'purity']
        self.resists[Level.Tags.Dark] = 50
        self.resists[Level.Tags.Holy] = 50
        self.buff_type = Level.BUFF_TYPE_BLESS

    def on_applied(self, owner):
        for b in owner.buffs:
            if b.buff_type == Level.BUFF_TYPE_CURSE:
                owner.remove_buff(b)

class Darkgoyle(Level.Spell):

    def on_init(self):

        self.name = "Belfry Nightmare"
        
        self.level = 5
        self.tags = [Level.Tags.Arcane, Level.Tags.Dark, Level.Tags.Conjuration, Level.Tags.Metallic]
        self.max_charges = 2
        self.minion_health = 40
        self.minion_range = 9
        self.range = 1
        self.minion_damage = 8
        self.melee = True

        self.must_target_empty = True

        self.upgrades['minion_health'] = (20, 4)
        self.upgrades['res'] = (50, 3, "Twilight Fantasy", "Nightmare gargoyles and nightmare gargoyle statues gain 50 [holy] resist.")
        self.upgrades['nightdash'] = (1, 4, "Phantom Nightmare", "Nightmare gargoyles gain a phasing dash dealing 7 [dark] damage with the same range as a statue's beam and a 3 turn cooldown.", "gargoyle")
        self.upgrades['rouse'] = (1, 5, "Dream Watch", "Nightmare gargoyles can grant allies Sweet Dream, which cures debuffs and gives 50 [dark] and [holy] resist.", "gargoyle")
        self.upgrades['crash'] = (1, 4, "Razing Beams", "Nightmare gargoyle statue beams melt walls.", "statue")
        self.upgrades['motivate'] = (1, 4, "Motivation", "Nightmare gargoyle statues can inspire allies in 4 tiles of them, granting them 8 damage to all abilities for 3 turns.", "statue")
    
    def fmt_dict(self):
        d = Level.Spell.fmt_dict(self)
        d['statue_health'] = math.ceil(d['minion_health'] * 0.75)
        d['beam_damage'] = 2*d['minion_damage']
        return d

    def get_description(self):
        return (
            "Summon a nightmare gargoyle on target tile.\n"
            "Nightmare gargoyles are [metallic] [dark] [arcane] [constructs:construct] with [{minion_health}_HP:minion_health] and many resistances.\n"
            "Nightmare gargoyles have melee attacks dealing [{minion_damage}_physical_damage:physical].\n"
            "Whenever a nightmare gargoyle dies, it transforms into a nightmare gargoyle statue with [{statue_health}_HP:minion_health], which matures into a nightmare gargoyle after 13 turns.\n"
            "Statues are immobile but have beams dealing [{beam_damage}:damage] [dark] or [arcane] damage to enemies in [{minion_range}_tiles:minion_range]."
        ).format(**self.fmt_dict())

    def make_statue(self):
        unit = Level.Unit()
        unit.name = "Nightmare Gargoyle Statue"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","gargoyle_nightmare_statue")
        unit.max_hp = math.ceil(self.get_stat('minion_health') * 0.75)
        unit.tags = [Level.Tags.Metallic, Level.Tags.Arcane, Level.Tags.Dark, Level.Tags.Construct]
        unit.resists[Level.Tags.Dark] = 75
        unit.resists[Level.Tags.Arcane] = 50
        unit.resists[Level.Tags.Holy] = -100 + self.get_stat('res')
        unit.stationary = True
        unit.spells.append(CommonContent.SimpleRangedAttack(name="Nightmare Beam", damage=self.get_stat('minion_damage')*2, damage_type=[Level.Tags.Dark, Level.Tags.Arcane], range=self.get_stat('minion_damage'), beam=True, melt=self.get_stat('crash')))
        unit.buffs.append(CommonContent.MatureInto(self.make_goyle, 13))
        if self.get_stat('motivate'):
            def inspire():
                b = CommonContent.BloodrageBuff(8)
                b.color = Level.Tags.Arcane.color
                b.name = "Motivated"
                b.asset = ['status', 'multicast']
                return b
            s = CommonContent.SimpleCurse(lambda: inspire(), 3)
            s.name = "Inspire"
            s.range = 4
            s.cool_down = 4
            unit.spells.append(s)
        return unit

    def make_goyle(self):
        unit = Level.Unit()
        unit.name = "Nightmare Gargoyle"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","gargoyle_nightmare")
        unit.max_hp = self.get_stat('minion_health')
        unit.tags = [Level.Tags.Metallic, Level.Tags.Arcane, Level.Tags.Dark, Level.Tags.Construct]
        unit.resists[Level.Tags.Dark] = 75
        unit.resists[Level.Tags.Arcane] = 50
        unit.resists[Level.Tags.Holy] = -100 + self.get_stat('res')
        unit.buffs.append(CommonContent.RespawnAs(self.make_statue))
        unit.flying = True
        unit.spells.append(CommonContent.SimpleMeleeAttack(self.get_stat('minion_damage')))
        if self.get_stat('nightdash'):
            s = CommonContent.LeapAttack(damage=7, damage_type=Level.Tags.Dark, range=self.get_stat('minion_range'), is_ghost=True)
            s.cool_down = 3
            s.name = "Nightmare Pursuit"
            unit.spells.append(s)
        elif self.get_stat('rouse'):
            s = CommonContent.SimpleCurse(GoyleDream, 5)
            s.name = "Dream Watch"
            s.range = 6
            s.cool_down = 5
            unit.spells.append(s)
        return unit
    
    def cast_instant(self, x, y):
        self.summon(self.make_goyle(), Level.Point(x, y))

class CrowMarkBuff(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)
    
    def on_init(self):
        self.color = Level.Tags.Dark.color
        self.owner_triggers[Level.EventOnDeath] = self.on_death
        self.name = "Mark of the Crow"

    def crow(self):
        crow = Level.Unit()
        crow.flying = True
        crow.name = "Crow"
        crow.asset_name = os.path.join("..","..","mods","MiscSummons","units","crow")
        crow.tags = [Level.Tags.Living, Level.Tags.Nature, Level.Tags.Dark]
        crow.max_hp = self.spell.get_stat('minion_health')
        crow.resists[Level.Tags.Dark] = 75
        crow.resists[Level.Tags.Holy] = 0
        crow.spells.append(CommonContent.SimpleMeleeAttack(self.spell.get_stat('minion_damage')))
        crow.source = self.spell
        return crow

    def on_death(self, evt):
        base = 1
        count = 0
        while base < evt.unit.max_hp:
            count += 1
            base = (base*2)+1
        for i in range(count):
            unit = self.crow()
            unit.max_hp += evt.unit.max_hp // (count*(2-self.spell.get_stat('efficiency')))
            if evt.unit.max_hp > 40:
                s = CommonContent.LeapAttack(damage=self.spell.get_stat('minion_damage')+2, damage_type=Level.Tags.Dark, range=self.spell.get_stat('minion_range'), is_ghost=self.spell.get_stat('necroton'))
                s.name = "Black Dive"
                s.cool_down = 3
                unit.spells.append(s)
            if evt.unit.max_hp > 70 and self.spell.get_stat('spiritize'):
                unit.buffs.append(CommonContent.CloudGeneratorBuff(CommonContent.BlizzardCloud, radius=3, chance=.2))
                unit.resists[Level.Tags.Ice] = 100
            if evt.unit.max_hp > 80 and self.spell.get_stat('necroton'):
                unit.resists[Level.Tags.Physical] = 100
                unit.tags.append[Level.Tags.Undead]
            self.spell.summon(unit, evt.unit, radius=5)

class Corvus(Level.Spell):

    def on_init(self):

        self.name = "Corvus Howl"
        
        self.level = 5
        self.tags = [Level.Tags.Dark, Level.Tags.Nature, Level.Tags.Conjuration, Level.Tags.Enchantment]
        self.minion_health = 8
        self.duration = 9
        self.range = 7
        self.minion_damage = 5
        self.minion_range = 5
        self.max_charges = 3

        self.can_target_empty = False

        self.upgrades['duration'] = (4, 2)
        self.upgrades['efficiency'] = (1, 4, "Efficient Scavenging", "Crows gain the target's full max HP distributed evenly among them instead of half.")
        self.upgrades['spiritize'] = (1, 6, "Blizzard Voice", "Crows gain 100 [ice] resist and passively summon blizzards near themselves if the target had more than 70 max HP.", "voice")
        self.upgrades['necroton'] = (1, 6, "Phantom Voice", "Crows' leap attacks pass through walls, and crows gain 100 [physical] resist and [undead] if the target had more than 80 max HP.", "voice")

    def get_description(self):
        return (
            "Designate the target as prey for opportunistic scavengers, inflicting Mark of the Crow for [{duration}_turns:duration].\n"
            "When a target with Mark of the Crow dies, summon crows around it based on max HP with diminishing returns.\n"
            "Each crow starts with [{minion_health}_HP:minion_health] and a melee attack dealing [{minion_damage}_physical_damage:physical].\n"
            "Crows feed off of the target's life force, gaining half of the target's max HP, distributed evenly between them.\n"
            "Crows gain dive attacks dealing [dark] damage with [{minion_range}_range:minion_range] if the target had more than 40 max HP."
        
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        if u:
            u.apply_buff(CrowMarkBuff(self), self.get_stat('duration'))

class RespawnAsCond(Level.Buff):

    def __init__(self, spawner):
        Level.Buff.__init__(self)
        self.spawner = spawner
        self.spawn_name = None
        self.get_tooltip()
        self.name = "Respawn As %s" % self.spawn_name

    def on_init(self):
        self.owner_triggers[Level.EventOnDamaged] = self.on_damage

    def on_damage(self, evt):
        if self.owner.cur_hp <= 0 and evt.damage_type == Level.Tags.Dark:
            self.owner.kill(trigger_death_event=False)
            self.respawn()

    def respawn(self):
        new_unit = self.spawner()
        new_unit.team = self.owner.team
        new_unit.source = self.owner.source
        new_unit.parent = self.owner
        p = self.owner.level.get_summon_point(self.owner.x, self.owner.y, radius_limit=8, flying=new_unit.flying)
        if p:
            self.owner.level.add_obj(new_unit, p.x, p.y)
        

    def get_tooltip(self):
        if not self.spawn_name:
            self.spawn_name = self.spawner().name
        return "On reaching 0 hp due to [dark] damage, becomes the %s" % self.spawn_name

class MadShield(Level.Buff):
    def __init__(self, is_madness=False):
        self.is_madness = is_madness
        Level.Buff.__init__(self)
    
    def on_init(self):
        self.global_triggers[Level.EventOnDamaged] = self.on_damaged
        self.color = Level.Tags.Chaos.color
    
    def on_damaged(self, evt):
        acceptables = [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical]
        if self.is_madness:
            acceptables.append(Level.Tags.Dark)
        if Level.distance(evt.unit, self.owner) > 3 or evt.damage_type not in acceptables:
            return
        self.owner.add_shields(1)
    
    def get_tooltip(self):
        return "Gains 1 SH whenever [fire], [lightning], [physical] or %sdamage is dealt within 3 tiles" % ('' if not self.is_madness else '[dark] ')

class MadTroubler(Level.Spell):

    def on_init(self):

        self.name = "Mad Mask"
        
        self.level = 5
        self.tags = [Level.Tags.Dark, Level.Tags.Chaos, Level.Tags.Conjuration]
        self.range = 5
        self.minion_range = 7
        self.minion_damage = 1
        self.max_charges = 4
        self.shields = 2

        self.must_target_empty = True

        self.upgrades['mage'] = (1, 5, "Magely Meltdown", "The Masked Chaos can cast your Chaos Barrage spell on a 5 turn cooldown.\nThis Chaos Barrage gains all of your upgrades and bonuses.\nThe Masked Madness can cast Devour Mind in the same fashion, with an 8 turn cooldown, and this Devour Mind has 3 extra range.")
        self.upgrades['placebo'] = (1, 3, "Psychic Guard", "The Masked Madness gains 1 shield whenever [fire], [lightning], [physical], or [dark] damage is dealt within 3 tiles of it.")
        self.upgrades['grudge'] =  (3, 4, "Madness Accelerator", "The Masked Madness' leap attack gains 3 damage per square traveled.")
        self.upgrades['end'] = (1, 6, "Shade of The Mask", "Casting this spell will cause each Masked Chaos to lose all SH and take 2 [dark] damage.")
        self.upgrades['shields'] = (4, 3)

    def get_description(self):
        return (
            "Summon the Masked Chaos on target tile.\n"
            "The Masked Chaos is fixed at 1 HP, but has [{shields}_SH:shield] and a variety of resistances.\n"
            "The Masked Chaos has a phase bolt dealing [{minion_damage}:damage] [fire], [lightning], or [physical] damage randomly and teleporting hit targets to a random tile at least 4 spaces away.\n"
            "If the Masked Chaos dies to [dark] damage, it returns as the Masked Madness, retaining its abilities and gaining 100 [dark] resistance plus a rush attack dealing [dark] damage."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Masked Chaos"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","mask_chaos")
        unit.max_hp = 1
        unit.tags = [Level.Tags.Chaos]
        for d in [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical]:
            unit.resists[d] = 75
        unit.flying = True
        phasebolt = CommonContent.SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=[Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical])
        def boltport(caster, target):
            valids = [p for p in caster.level.iter_tiles() if Level.distance(target, p) > 3 and target.level.can_move(target, p.x, p.y, teleport=True)]
            if valids:
                p = random.choice(valids)
                target.level.act_move(target, p.x, p.y, teleport=True)
        if self.get_stat('mage'):
            b = Spells.ChaosBarrage()
            b.statholder = self.caster
            b.cool_down = 8
            b.cur_charges = b.max_charges = 0
            unit.spells.append(b)
        phasebolt.name = "Madbolt"
        phasebolt.description = "Teleports victims randomly at least 4 tiles away"
        phasebolt.onhit = boltport
        unit.spells.append(phasebolt)
        unit.shields = self.get_stat('shields')
        unit.buffs.extend([CommonContent.TeleportyBuff(chance=.2, radius=10), RespawnAsCond(self.make_madness)])
        unit.stationary = True
        return unit
    
    def make_madness(self):
        unit = Level.Unit()
        unit.name = "Masked Madness"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","mask_dark")
        unit.max_hp = 1
        unit.tags = [Level.Tags.Chaos, Level.Tags.Dark]
        for d in [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical]:
            unit.resists[d] = 75
        unit.resists[Level.Tags.Dark] = 100
        unit.flying = True
        phasebolt = CommonContent.SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=[Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical, Level.Tags.Dark])
        def boltport(caster, target):
            valids = [p for p in caster.level.iter_tiles() if Level.distance(target, p) > 4 and target.level.can_move(target, p.x, p.y, teleport=True)]
            if valids:
                p = random.choice(valids)
                target.level.act_move(target, p.x, p.y, teleport=True)
        if self.get_stat('mage'):
            b = Spells.MindDevour()
            b.range += 3
            b.statholder = self.caster
            b.cool_down = 8
            b.cur_charges = b.max_charges = 0
            unit.spells.append(b)
        phasebolt.name = "Madbolt"
        phasebolt.description = "Teleports victims randomly at least 5 tiles away"
        phasebolt.onhit = boltport
        leap = CommonContent.LeapAttack(damage=self.get_stat('minion_damage')+3, damage_type=Level.Tags.Dark, range=self.get_stat('minion_range')+2, is_ghost=True, charge_bonus=self.get_stat('grudge'))
        leap.cool_down = 4
        leap.name = "Madness Drive"
        unit.spells.extend([leap, phasebolt])
        unit.shields = self.get_stat('shields') + self.get_stat('madshield')
        unit.buffs.append(CommonContent.TeleportyBuff(chance=.2, radius=10))
        if self.get_stat('placebo'):
            unit.buffs.append(MadShield(is_madness=True))
        unit.stationary = True
        return unit
    
    def cast_instant(self, x, y):
        if self.get_stat('end'):
            for u in [m for m in self.caster.level.units if m.name == "Masked Chaos"]:
                u.shields = 0
                u.deal_damage(2, Level.Tags.Dark, self)
        self.summon(self.make_summon(), Level.Point(x, y))

                

class GlassMeltBuff(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Glass Heat"
        self.color = Level.Tags.Glass.color
        self.buff_type = Level.BUFF_TYPE_CURSE
    
    def on_advance(self):
        self.owner.deal_damage(self.spell.get_stat('glass_damage'), Level.Tags.Fire, self.spell)

    def on_unapplied(self):
        b = CommonContent.GlassPetrifyBuff()
        self.owner.apply_buff(b, (self.spell.get_stat('duration')))

class Glassoid(Level.Spell):

    def on_init(self):

        self.name = "Glass Cube"
        
        self.level = 5
        self.tags = [Level.Tags.Fire, Level.Tags.Arcane, Level.Tags.Conjuration]
        self.range = 3
        self.minion_health = 33
        self.minion_range = 4
        self.minion_damage = 5
        self.duration = 4
        self.glass_damage = 2
        self.max_charges = 2
        self.stats.extend(['glass_damage'])

        self.must_target_empty = True
        self.must_target_walkable = True

        self.upgrades['rush'] = (2, 3, "Throw Efficacy", "Glass cubes can throw glass without cooldown.")
        self.upgrades['hardened'] = (100, 4, "Molten Pyrex", "The cubes gain 100 [physical] resist.")
        self.upgrades['minion_health'] = (22, 4)
        self.upgrades['glass_damage'] = (1, 2, "Heat Bonus", "Glass Heat deals 1 extra damage each turn.")

    def get_description(self):
        return (
            "Summon a sentient cube of molten glass on target tile.\n"
            "The cube has [{minion_health}_HP:minion_health] and a variety of resistances. The cube also splits like a [slime].\n"
            "The cube can throw molten glass from itself at enemies in [{minion_range}_tiles:range], dealing [{minion_damage}_fire_damage:fire] and inflicting Glass Heat for [{duration}_turns:duration]. This ability has a 2 turn cooldown.\n"
            "Glass Heat deals [{glass_damage}_fire_damage:fire] each turn, inflicting [{duration}_turns:duration] of [glassify:glass] when it expires."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Glass Cube"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","melt_glass_cube")
        unit.max_hp = self.get_stat('minion_health')
        unit.tags = [Level.Tags.Fire, Level.Tags.Glass, Level.Tags.Slime]
        unit.resists[Level.Tags.Fire] = 100
        unit.resists[Level.Tags.Physical] = -100 + self.get_stat('hardened')
        unit.buffs.append(Monsters.SlimeBuff(self.make_summon, "glass cubes"))
        unit.spells.append(CommonContent.SimpleRangedAttack(name="Glass Toss", damage=self.get_stat('minion_damage'), damage_type=Level.Tags.Fire, range=self.get_stat('minion_range'), cool_down=2-self.get_stat('rush'), buff=lambda: GlassMeltBuff(self), buff_duration=self.get_stat('duration')))
        unit.spells.append(CommonContent.SimpleMeleeAttack(self.get_stat('minion_damage')+3))
        unit.source = self
        return unit
    
    def cast_instant(self, x, y):
        self.summon(self.make_summon(), Level.Point(x, y))

class BatteryDonate(Level.Spell):

    def __init__(self, source_spell):
        self.source_spell = source_spell
        Level.Spell.__init__(self)

    def on_init(self):
        self.name = "Plasma Transfusion"
        self.description = "Kills the caster to restore an ally, healing it and removing debuffs"
        self.range = Level.RANGE_GLOBAL
        self.requires_los = False
    
    def get_ai_target(self):
        to_hit = [u for u in self.caster.level.units if u != self.source_spell.caster and not Level.are_hostile(u, self.caster) and u.source != self.source_spell]
        to_hit.sort(key=lambda x: -x.cur_hp if x.has_buff(CommonContent.Poison) else x.cur_hp)
        return to_hit[0] if to_hit else None

    def cast(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        if not u:
            return
        for b in u.buffs:
            if b.buff_type == Level.BUFF_TYPE_CURSE:
                u.remove_buff(b)
        u.deal_damage(-self.owner.cur_hp, Level.Tags.Heal, self)
        if self.source_spell.get_stat('defense'):
            u.add_shields(1)
        self.caster.kill()
        yield

class SplitBooster(Level.Buff):
    def __init__(self, quant):
        self.quant = quant
        Level.Buff.__init__(self)

    def on_init(self):
        self.color = Level.Tags.Slime.color
        self.buff_type = Level.BUFF_TYPE_PASSIVE
    
    def on_advance(self):
        b = self.owner.get_buff(Monsters.SlimeBuff)
        if b:
            for i in range(self.quant):
                b.on_advance()

class HealBattery(Level.Spell):

    def on_init(self):

        self.name = "Plasmule"
        
        self.level = 3
        self.tags = [Level.Tags.Nature, Level.Tags.Conjuration]
        self.range = 5
        self.minion_health = 24
        self.minion_damage = 3
        self.max_charges = 10

        self.must_target_empty = True
        self.must_target_walkable = True

        self.upgrades['splitboost'] = (1, 4, "Split Boost", "Globules have 3 chances to gain max HP each turn instead of 1.")
        self.upgrades['defense'] = (1, 3, "Plasma Barrier", "Allies healed by a globule gain 1 SH.")
        self.upgrades['max_charges'] = (4, 2)
    
    def get_description(self):
        return (
            "Summon a sentient globule of blood plasma on target tile.\n"
            "It has [{minion_health}_HP:minion_health], 100 [poison] resist, 75 [physical] resist, and splits like a [slime].\n"
            "Globules can supply their plasma to allies in need, healing them for an amount equal to the globule's current HP and dispelling debuffs, at the cost of the globule's life.\n"
            "Globules will prioritize [poisoned:poison] allies, followed by those with low HP, and will not heal other globules.\n"
            "They also have melee attacks dealing [{minion_damage}_physical_damage:physical]."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Plasma Globule"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","plasma_slime")
        unit.max_hp = self.get_stat('minion_health')
        unit.tags = [Level.Tags.Nature, Level.Tags.Slime]
        unit.resists[Level.Tags.Physical] = 75
        unit.resists[Level.Tags.Poison] = 100
        unit.buffs.append(Monsters.SlimeBuff(self.make_summon, "plasma globules"))
        unit.spells.append(BatteryDonate(self))
        unit.spells.append(CommonContent.SimpleMeleeAttack(self.get_stat('minion_damage')))
        if self.get_stat('splitboost'):
            unit.buffs.append(SplitBooster(2))
        unit.source = self
        return unit
    
    def cast_instant(self, x, y):
        self.summon(self.make_summon(), Level.Point(x, y))

class MetalCleaner(Level.Spell):
    def __init__(self, source_spell):
        self.source_spell = source_spell
        Level.Spell.__init__(self)

    def on_init(self):
        self.name = "Fluid Wash"
        self.description = "Cleans a [metallic] ally, granting debuff immunity for 3 turns\nCosts 2 max HP to use"
        self.requires_los = True
        self.range = self.source_spell.get_stat('minion_range')
        self.cool_down = 2
    
    def get_ai_target(self):
        to_hit = [u for u in self.caster.level.units if u != self.caster and not Level.are_hostile(u, self.caster) and Level.Tags.Metallic in u.tags and self.can_cast(u.x, u.y)]
        return random.choice(to_hit) if to_hit else None

    def can_cast(self, x, y):
        return Level.Spell.can_cast(self, x, y) and self.caster.max_hp > 2 and self.caster.cur_hp > 2

    def cast(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        if not u:
            return
        self.caster.level.show_path_effect(self.caster, u, Level.Tags.Physical, minor=True)
        self.caster.max_hp -= 2
        self.caster.cur_hp -= 2
        b = Spells.PurityBuff()
        b.color = Level.Tags.Metallic.color
        b.name = "Washed"
        u.apply_buff(b, 3)
        yield

class MetalMover(Level.Spell):
    def __init__(self, source_spell):
        self.source_spell = source_spell
        Level.Spell.__init__(self)

    def on_init(self):
        self.name = "Lubricate"
        self.description = "Target [metallic] ally becomes mobile and immediately gets a turn\nCosts 3 max HP to use"
        self.requires_los = True
        self.range = self.source_spell.get_stat('minion_range')
        self.cool_down = 4
    
    def get_ai_target(self):
        to_hit = [u for u in self.caster.level.units if u != self.caster and not Level.are_hostile(u, self.caster) and Level.Tags.Metallic in u.tags and self.can_cast(u.x, u.y)]
        return random.choice(to_hit) if to_hit else None

    def can_cast(self, x, y):
        return Level.Spell.can_cast(self, x, y) and self.caster.max_hp > 3 and self.caster.cur_hp > 3

    def cast(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        if not u:
            return
        self.caster.level.show_path_effect(self.caster, u, Level.Tags.Physical, minor=True)
        self.caster.max_hp -= 3
        self.caster.cur_hp -= 3
        if u.stationary:
            u.stationary = False
        if u.is_alive():
            self.owner.level.leap_effect(u.x, u.y, Level.Tags.Physical.color, u)
            self.owner.advance()
        yield

class LubricantFunny(Level.Spell):

    def on_init(self):

        self.name = "Slime Model 40"
        
        self.level = 3
        self.tags = [Level.Tags.Nature, Level.Tags.Conjuration]
        self.range = 7
        self.max_charges = 6
        self.minion_range = 7

        self.must_target_empty = True
        self.must_target_walkable = True
        
        self.upgrades['minion_range'] = (2, 2)
        self.upgrades['range'] = (2, 1)
        self.upgrades['phaser'] = (1, 4, "Phasing Fluid", "The slimes' support abilities no longer require line of sight to use.")

    def get_description(self):
        return (
            "Summon a slime made of specially formulated fluid with fixed [10_HP:minion_health] and 50 [physical] resist.\n"
            "It has no attacks but has 2 chances to split each turn and can support [metallic] allies in a variety of ways.\n"
            "The slimes can use some of their fluid to clean and protect [metallic] allies, making them immune to debuffs for 3 turns.\n"
            "Additionally, the fluid is an excellent lubricant and can be applied to [metallic] allies, letting them immediately act once and making them permanently mobile.\n"
            "These actions can target allies in [{minion_range}_tiles:range], and will cause the slime to lose maximum HP."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Slime Model 40"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","slime_wd40")
        unit.max_hp = 10
        unit.tags = [Level.Tags.Slime]
        unit.resists[Level.Tags.Physical] = 50
        unit.buffs.extend([SplitBooster(1), Monsters.SlimeBuff(self.make_summon)])
        unit.source = self
        unit.spells.extend([MetalMover(self), MetalCleaner(self)])
        if self.get_stat('phaser'):
            for s in unit.spells:
                s.requires_los = False
        return unit
    
    def cast_instant(self, x, y):
        self.summon(self.make_summon(), Level.Point(x, y))

class Immortality(Level.Buff):
    def __init__(self):
        Level.Buff.__init__(self)
        self.owner_triggers[Level.EventOnDamaged] = self.on_self_damage
        self.name = "Immortality"
        self.color = Level.Tags.Holy.color

    def get_buff_tooltip(self):
        return "Cannot die."

    def on_self_damage(self, damage):
        if self.owner.cur_hp <= 0:
            self.owner.cur_hp = 1

class AstroCall(Level.Spell):

    def on_init(self):

        self.name = "Astral Beckon"
        
        self.level = 6
        self.tags = [Level.Tags.Dark, Level.Tags.Holy, Level.Tags.Arcane, Level.Tags.Conjuration]
        self.range = 0
        self.max_charges = 2
        self.minion_health = 75
        self.minion_range = 3
        self.minion_damage = 7
        self.shields = 2

        self.upgrades['max_charges'] = (2, 3)
        self.upgrades['minion_health'] = (40, 3)
        self.upgrades['shields'] = (1, 3)
        self.upgrades['twicast'] = (1, 5, "Twilight Convergence", "Casting this spell while the twilight knight is alive will grant it immortality for 5 turns.", "convergence")
        self.upgrades['enercast'] = (1, 5, "Energy Convergence", "Casting this spell while the energy knight is alive will restore its health fully and let it instantly attack.", "convergence")

    def can_cast(self, x, y):
        existing = [u for u in self.caster.level.units if u.source == self]        
        if existing:
            return (x == existing[0].x and y == existing[0].y)
        return Level.Spell.can_cast(self, x, y)

    def get_description(self):
        return (
            "Summon a twilight knight and an energy knight.\n"
            "Each knight has [{minion_health}_HP:minion_health] and a variety of abilities and resistances.\n"
            "Casting this spell again while the knights are alive will remove [poison] from them and give them [{shields}_SH:shield] to a max of 5."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        if any(u.source == self for u in self.caster.level.units):
            for u in [i for i in self.caster.level.units if i.source == self]:
                if (b := u.get_buff(CommonContent.Poison)):
                    u.remove_buff(b)
                if u.name == "Twilight Knight" and self.get_stat('twicast'):
                    u.apply_buff(Immortality(), 5)
                if u.name == "Energy Knight" and self.get_stat('enercast'):
                    u.deal_damage(-u.max_hp, Level.Tags.Heal, self) 
                    self.caster.level.leap_effect(u.x, u.y, Level.Tags.Arcane.color, u)
                    u.advance()
                if u.shields < 5:
                    u.shields = min(5, u.shields+self.get_stat('shields'))
            return
        summons = [Monsters.TwilightKnight(), Monsters.EnergyKnight()]
        for s in summons:
            CommonContent.apply_minion_bonuses(self, s)
            s.max_hp = self.get_stat('minion_health')
            self.summon(s, Level.Point(x, y))

class HopeBuffSpell(Level.Spell):

    def on_init(self):
        self.name = "Belief in Victory"
        self.description = "All allies excluding the Wizard gain a stack of belief, which increases all damage by 8 for 5 turns"
        self.cool_down = 18
        self.range = 0
    
    def get_ai_target(self):
        return self.caster

    def cast(self, x, y):
        valids = [u for u in self.caster.level.units if u != self.caster.level.player_unit and not Level.are_hostile(u, self.caster)]
        for v in valids:
            b = CommonContent.BloodrageBuff(8)
            b.asset = None
            b.name = "Belief"
            b.color = Level.Tags.Holy.color
            v.apply_buff(b, 5)
        yield

class HopeRegenSpell(Level.Spell):

    def on_init(self):
        self.name = "Hope's Respite"
        self.description = "All allies in 4 tiles, including self and excluding the Wizard, gain Regeneration 5 for 7 turns"
        self.cool_down = 7
        self.range = 0
    
    def get_ai_target(self):
        if list(self.caster.level.get_units_in_ball(self.caster, 4)):
            return self.caster
        return None

    def cast(self, x, y):
        valids = [u for u in self.caster.level.get_units_in_ball(self.caster, 4) if u != self.caster.level.player_unit and not Level.are_hostile(u, self.caster)]
        for v in valids:
            v.apply_buff(CommonContent.RegenBuff(5), 7)
        yield

class JusticeFlash(Level.Spell):

    def on_init(self):
        self.name = "Karmic Blaze"
        self.description = "Deals fire damage in a burst, hitting [demon] and [undead] units twice and not harming allies"
        self.requires_los = True
        self.radius = 7
        self.damage = 0
        self.range = 0
        self.cool_down = 10
    
    def get_ai_target(self):
        for p in self.get_impacted_tiles(self.caster.x, self.caster.y):
            u = self.caster.level.get_unit_at(p.x, p.y)
            if u and Level.are_hostile(u, self.caster):
                return self.caster
        return None

    def cast(self, x, y):
        for stage in Level.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for point in stage:
                u = self.caster.level.get_unit_at(point.x, point.y)
                times = 1
                if u:
                    if not Level.are_hostile(u, self.caster):
                        continue
                    times = 2 if (Level.Tags.Demon in u.tags or Level.Tags.Undead in u.tags) else 1
                for _ in range(times):
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Fire, self)
        yield

class HopeShield(Level.Buff):

    def __init__(self):
        self.turn_count = 0
        self.radius = 5
        Level.Buff.__init__(self)
    
    def on_init(self):
        self.name = "Hopeshield"
        self.color = Level.Tags.Holy.color

    def on_advance(self):
        self.turn_count += 1
        if self.turn_count % 2 == 0:
            units = self.owner.level.get_units_in_ball(self.owner, self.radius)
            for u in units:
                if u == self.owner or Level.are_hostile(u, self.owner) or u.shields >= 3:
                    continue    
                u.add_shields(1)  

    def get_tooltip(self):
        return "Every 2 turns, all allies in %d tiles gain 1 shield, to a max of 3" % self.radius  

class TombDeathSummon(Level.Buff):

    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)
    
    def on_init(self):
        self.color = Level.Tags.Eye.color
        self.owner_triggers[Level.EventOnDeath] = self.on_death
        self.name = "Tomb Call"

    def on_death(self, evt):
        if evt.damage_event != None:
            self.owner.level.queue_spell(self.summon_ghosts())

    def summon_ghosts(self):
        summons = [self.hope(), self.justice(), self.courage()]
        for s in summons:
            s.flying = True
            self.summon(s, self.owner)
        yield

    def get_tooltip(self):
        return "On death, summons the spirits of [hope:holy], [justice:fire], and [courage:arcane] nearby."

    def hope(self):
        unit = Level.Unit()
        unit.name = "Hope"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","ghost_hope")
        unit.max_hp = 30
        unit.tags = [Level.Tags.Undead, Level.Tags.Holy]
        unit.resists[Level.Tags.Holy] = 100
        unit.resists[Level.Tags.Physical] = 100
        b = HopeShield()
        b.radius += self.spell.get_stat('unique')
        unit.buffs.extend([HopeShield(), CommonContent.TeleportyBuff(3, .25)])
        unit.spells.extend([HopeBuffSpell(), HopeRegenSpell()])
        unit.source = self.spell
        return unit
    
    def justice(self):
        unit = Level.Unit()
        unit.name = "Justice"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","ghost_justice")
        unit.max_hp = 30
        unit.tags = [Level.Tags.Undead, Level.Tags.Fire]
        unit.resists[Level.Tags.Fire] = 100
        unit.resists[Level.Tags.Physical] = 100
        unit.source = self.spell
        bolt = CommonContent.SimpleRangedAttack(name="Justice Bolt", damage=self.spell.get_stat('minion_damage')*2, range=self.spell.get_stat('minion_range'), damage_type=Level.Tags.Fire)
        (flash := JusticeFlash()).damage = self.spell.get_stat('minion_damage')
        flash.radius += self.spell.get_stat('unique')
        unit.spells.extend([flash, bolt])
        unit.buffs.extend([CommonContent.DamageAuraBuff(damage=2, radius=5+self.spell.get_stat('unique'), damage_type=Level.Tags.Fire), CommonContent.TeleportyBuff(3, .25)])
        return unit
    
    def courage(self):
        unit = Level.Unit()
        unit.name = "Courage"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","ghost_courage")
        unit.max_hp = 30
        unit.tags = [Level.Tags.Undead, Level.Tags.Arcane]
        unit.resists[Level.Tags.Arcane] = 100
        unit.resists[Level.Tags.Physical] = 100
        unit.shields = 5 + self.spell.get_stat('unique')
        unit.source = self.spell
        unit.buffs.extend([CommonContent.ShieldRegenBuff(10, 3), CommonContent.TeleportyBuff(3, .25)])
        bolt = CommonContent.SimpleRangedAttack(name="Courageous Strike", damage=self.spell.get_stat('minion_damage'), range=self.spell.get_stat('minion_range'), damage_type=Level.Tags.Arcane)
        unit.spells.extend([bolt])
        return unit

class VirtueGhosts(Level.Spell):

    def on_init(self):

        self.name = "Tomb of Legend"
        
        self.level = 7
        self.tags = [Level.Tags.Fire, Level.Tags.Holy, Level.Tags.Arcane, Level.Tags.Conjuration]
        self.range = 7
        self.minion_range = 7
        self.minion_damage = 12
        self.max_charges = 2

        self.must_target_empty = True
        self.must_target_walkable = True

        self.upgrades['max_charges'] = (2, 3)
        self.upgrades['minion_damage'] = (7, 2)
        self.upgrades['minion_range'] = (2, 3)
        self.upgrades['unique'] = (2, 5, "Legendary Spirits", "Hope's shield aura gains [2_radius:radius], Courage starts with [2_extra_SH:shield], and Justice's damage aura and Karmic Blaze both gain [2_radius:radius]")

    def can_cast(self, x, y):
        existing = [u for u in self.caster.level.units if u.source == self]        
        if existing:
            return (x == existing[0].x and y == existing[0].y)
        return Level.Spell.can_cast(self, x, y)

    def get_description(self):
        return (
            "Summon the Saintly Tomb on target tile.\n"
            "It is a stationary [holy] [construct] with fixed [50_HP:minion_health].\n"
            "When the Tomb dies, it summons the spirits of hope, justice, and courage near itself.\n"
            "Each spirit is a ghost with fixed [30_HP:minion_health] and a variety of resistances and abilities.\n"
            "Casting this spell while the tomb is alive will kill it, and casting the spell while any spirits are alive will give them 1 reincarnation permanently."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Saintly Tomb"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","box_of_energy")
        unit.max_hp = 50
        unit.source = self
        unit.tags = [Level.Tags.Holy, Level.Tags.Construct]
        unit.resists[Level.Tags.Holy] = 100
        unit.resists[Level.Tags.Physical] = 50
        unit.stationary = True
        unit.buffs.append(TombDeathSummon(self))
        return unit
    
    def cast_instant(self, x, y):
        existing = [u for u in self.caster.level.units if u.source == self]
        if not existing:
            self.summon(self.make_summon(), Level.Point(x, y))
        else:
            for u in existing:
                if "Tomb" not in u.name:
                    u.apply_buff(CommonContent.ReincarnationBuff(1))
                else:
                    self.caster.level.event_manager.raise_event(Level.EventOnDeath(u, Level.EventOnDamaged(u, 999, Level.Tags.Construct, u)), u)
                    u.kill()

def laced_onhit(caster, target):
    if (b := target.get_buff(CommonContent.Poison)):
        b.turns_left += 1
    else:
        target.apply_buff(CommonContent.Poison(), 1)
            
class BallistaMen(Level.Spell):

    def on_init(self):

        self.tags = [Level.Tags.Nature, Level.Tags.Conjuration]
        self.name = "Archer Corps"
        self.level = 2
        self.num_summons = 2
        self.max_charges = 3
        self.max_channel = 4

        ex = Monsters.Kobold()
        self.minion_health = ex.max_hp
        self.minion_range = ex.spells[0].range

        self.upgrades['minion_health'] = (5, 2)
        self.upgrades['num_summons'] = (1, 2)
        self.upgrades['max_channel'] = (3, 3)
        self.upgrades['ballistic'] = (1, 3, "Ballisticians", "Additionally, summon a Kobold Siege Mechanic.", "elite")
        self.upgrades['sniper'] = (1, 2, "Snipers", "Additionally, summon a Kobold Longbowman.", "elite")
        self.upgrades['tipped_poison'] = (1, 3, "Laced Arrows", "Each shot from a kobold applies 1 turn of poison to its target, or extends the target's poison duration by 1 if they are already poisoned. Does not affect kobolds from elite upgrades.", "effect")
        self.upgrades['tipped_frenzy'] = (1, 5, "Arrow Frenzy", "Each shot from a kobold applies a stack of bloodrage to the kobold for 10 turns, increasing all damage by 1. Does not affect kobolds from elite upgrades.", "effect")

    def get_description(self):
        return (
            "Call in a squad of [{num_summons}:num_summons] kobolds equipped with bows.\n"
            "Each kobold has [{minion_health}_HP:minion_health] and a bow attack with [{minion_range}_range:minion_range] dealing 1 damage.\n"
            "This spell can be channeled for [{max_channel}_turns:duration]."
        ).format(**self.fmt_dict())

    def cast(self, x, y, channel_cast=False):
        if not channel_cast:
            self.caster.apply_buff(Level.ChannelBuff(self.cast, Level.Point(x, y)), self.get_stat('max_channel'))
            return
        
        summons = [Monsters.Kobold() for i in range(self.get_stat('num_summons'))]
        if self.get_stat('ballistic'):
            summons.append(Variants.KoboldSiegeOperator())
        if self.get_stat('sniper'):
            summons.append(Variants.KoboldLongbow())
        random.shuffle(summons)
        for u in summons:
            if u.name == "Kobold":
                if self.get_stat('tipped_poison'):
                    u.spells[0].onhit = laced_onhit
                    u.spells[0].description += "Poisons hit units for 1 turn or extends existing poison by 1 turn"
                elif self.get_stat('tipped_frenzy'):
                    u.spells[0].onhit = CommonContent.bloodrage(1)
                    u.spells[0].description += "Gain +1 damage for 10 turns with each attack"
            u.max_hp = self.get_stat('minion_health', base=u.max_hp)
            for s in u.spells:
                if hasattr(s, 'range') and s.range >= 2:
                    s.range = self.get_stat('minion_range', base=s.range)
            self.summon(u, Level.Point(x, y))
            yield

class DreamerBuffModular(Level.Buff):

    def __init__(self, spell):
        self.chance = spell.get_stat('teleport_chance') / 100
        self.dist = spell.get_stat('teleport_distance')
        self.spell = spell
        Level.Buff.__init__(self)

    def on_init(self):
        self.color = Level.Tags.Translocation.color

    def get_tooltip(self):
        return "%d%% chance to teleport each enemy unit up to %d squares away each turn" % (self.chance*100, self.dist)

    def on_advance(self):
        level = self.owner.level
        for u in [u for u in level.units if Level.are_hostile(self.owner, u)]:

            if random.random() < self.chance:
                targets = [t for t in level.iter_tiles() if level.can_stand(t.x, t.y, u) and Level.distance(t, u) < self.dist]
                if targets:
                    teleport_target = random.choice(targets)
                    level.flash(u.x, u.y, Level.Tags.Translocation.color)
                    level.act_move(u, teleport_target.x, teleport_target.y, teleport=True)
                    level.flash(u.x, u.y, Level.Tags.Translocation.color)

class EyeGrab(Level.Spell):

    def on_init(self):
        self.name = "Dream Vision"
        self.description = "Casts one of the Wizard's eye spells on self"
        self.cool_down = 5
        self.range = 0
    
    def get_ai_target(self):
        valids = [s for s in self.caster.level.player_unit.spells if Level.Tags.Eye in s.tags and s.range == 0]
        if valids:
            return self.caster
        return None

    def cast(self, x, y):
        valids = [s for s in self.caster.level.player_unit.spells if Level.Tags.Eye in s.tags and s.range == 0]
        spell = type(random.choice(valids))()
        spell.caster = self.caster
        spell.owner = self.caster
        spell.statholder = self.caster
        self.caster.level.act_cast(self.caster, spell, self.caster.x, self.caster.y, pay_costs=False)
        yield
        

class DreamerCall(Level.Spell):

    def on_init(self):

        self.name = "Ocular Dream"
        
        self.level = 7
        self.tags = [Level.Tags.Eye, Level.Tags.Arcane, Level.Tags.Conjuration]
        self.range = 7
        self.max_charges = 1
        ex = RareMonsters.Dreamer()
        self.minion_damage = ex.spells[0].damage
        self.minion_range = ex.spells[0].range
        self.shields = ex.shields - 2
        self.teleport_chance = 25
        self.teleport_distance = 4
        self.stats.extend(['teleport_chance', 'teleport_distance'])

        self.must_target_empty = True

        self.upgrades['teleport_chance'] = (25, 2)
        self.upgrades['teleport_distance'] = (2, 2)
        self.upgrades['minion_damage'] = (8, 3)
        self.upgrades['max_charges'] = (1, 2)
        self.upgrades['immortal'] = (1, 5, "Undying Dream", "The Dreamer regenerates 1 SH every turn to a max of 20.")


    def get_description(self):
        return (
            "Summon the Dreamer on target tile.\n"
            "It has 1 fixed HP, [{shields}_SH:shield], and a [{teleport_chance}%_chance:arcane] to teleport each enemy unit up to [{teleport_distance}_tiles_away:translocation] each turn.\n"
            "It also has a ranged attack dealing [{minion_damage}_arcane_damage:arcane] with a [{minion_range}-tile_range:range].\n"
            "Every 5 turns, the Dreamer will cast one of the Wizard's eye spells with 0 range on itself."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = RareMonsters.Dreamer()
        CommonContent.apply_minion_bonuses(self, unit)
        unit.shields = self.get_stat('shields')
        unit.max_hp = 1
        unit.buffs.clear()
        unit.buffs.append(DreamerBuffModular(self))
        unit.spells.insert(0, EyeGrab())
        if self.get_stat('light_dream'):
            unit.tags.append(Level.Tags.Holy)
            unit.resists[Level.Tags.Holy] = 100
        if self.get_stat('immortal'):
            unit.buffs.append(CommonContent.ShieldRegenBuff(20, 1))
        return unit
    
    def cast_instant(self, x, y):
        self.summon(self.make_summon(), Level.Point(x, y))

def bonus_bush(unit, spell):
    def inner():
        u = unit()
        CommonContent.apply_minion_bonuses(spell, u)
        u.source = spell   
        if spell.get_stat('ironroot'):
            u.resists[Level.Tags.Fire] = 50
            u.buffs.append(CommonContent.Thorns(3))
        return u
    return inner

class Dreadforce(Upgrades.Upgrade):

    def on_init(self):
        self.name = "Starfire"
        self.conversions[Level.Tags.Physical][Level.Tags.Dark] = .3
        self.conversions[Level.Tags.Ice][Level.Tags.Dark] = .3
        self.color = Level.Tags.Dark.color

    def get_tooltip(self):
        return "Redeals one-quarter of all [physical] or [ice] damage as dark damage."

class SproutDeadBuff(Level.Buff):

    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)

    def on_init(self):
        self.global_triggers[Level.EventOnDamaged] = self.on_damaged
        self.name = "Sprout Curse"
        self.color = Level.Tags.Nature.color	

    def on_damaged(self, damage_event):
        if damage_event.unit.cur_hp > 0 or not self.owner.level.are_hostile(self.owner, damage_event.unit) or damage_event.unit.has_been_raised:
            return
        if Level.Tags.Living in damage_event.unit.tags or Level.Tags.Nature in damage_event.unit.tags:
            self.owner.level.queue_spell(self.raise_skeleton(damage_event.unit))
        if (Level.Tags.Dark in damage_event.unit.tags or Level.Tags.Demon in damage_event.unit.tags or Level.Tags.Undead in damage_event.unit.tags) and self.spell.get_stat('dreadlord'):
            self.owner.level.queue_spell(self.dreadize(damage_event.unit))

    def raise_skeleton(self, unit):
        bush = Monsters.IcySpriggan() if self.spell.get_stat('zero') else (Variants.ToxicSpriggan() if self.spell.get_stat('poison') else Monsters.Spriggan())
        bush.source = self.spell
        if self.spell.get_stat('ironroot'):
            bush.resists[Level.Tags.Fire] = 50
        treespawn = bush.get_buff(CommonContent.RespawnAs)
        treespawner = treespawn.spawner
        treespawn.spawner = bonus_bush(treespawner, self.spell)
        CommonContent.apply_minion_bonuses(self.spell, bush)
        self.summon(bush, Level.Point(unit.x, unit.y))
        yield

    def dreadize(self, unit):
        dread_candidates = [u for u in self.owner.level.units if Level.distance(u, unit) <= 4 and u.source == self.spell and not Level.are_hostile(u, self.spell.caster)]
        for s in dread_candidates:
            s.apply_buff(Dreadforce())
        yield

class SprigganCall(Level.Spell):

    def on_init(self):

        self.name = "Sprout Curse"
        
        self.level = 3
        self.tags = [Level.Tags.Nature, Level.Tags.Enchantment, Level.Tags.Conjuration]
        self.range = 0
        self.max_charges = 4
        self.duration = 10
        ex = Monsters.Spriggan()
        self.minion_health = ex.max_hp
        self.minion_damage = ex.spells[0].damage

        self.upgrades['minion_damage'] = (3, 1)
        self.upgrades['duration'] = (8, 3)
        self.upgrades['ironroot'] = (1, 4, "Ironroot", "Spriggans and spriggan bushes summoned by this spell have their fire resist set to 50. Spriggan bushes additionally gain melee retaliation dealing 3 [physical] damage.")
        self.upgrades['rooting'] = (1, 4, "Rapid Germination", "If you do not already have Sprout Curse when casting this spell, deal [physical] damage to all enemies equal to twice the Spriggan's melee damage.")
        self.upgrades['zero'] = (1, 5, "Seed of Hoarfrost", "Summon icy spriggans instead of regular ones.", "variant")
        self.upgrades['poison'] = (1, 4, "Seed of Mire", "Summon toxic spriggans instead of regular ones.", "variant")
        self.upgrades['dreadlord'] = (1, 5, "Dread Leech", "Whenever a [dark], [demon], or [undead] unit dies while Sprout Curse is active, each spriggan in a [4-tile_radius:radius] of the target gains a buff letting it redeal 30%% of its [physical] or [ice] damage as [dark] damage.")

    def get_description(self):
        return (
            "For [{duration}_turns:duration], whenever a [living] or [nature] enemy dies, summon a spriggan near its location.\n"
            "Spriggans have [{minion_health}_HP:minion_health] and melee attacks dealing [{minion_damage}_physical_damage:physical].\n"
            "When spriggans die, they respawn as stationary bushes."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        didnt_have = not self.caster.has_buff(SproutDeadBuff)
        self.caster.apply_buff(SproutDeadBuff(self), self.get_stat('duration'))
        if didnt_have and self.get_stat('rooting'):
            for e in [u for u in self.caster.level.units if self.caster.level.are_hostile(u, self.caster)]:
                e.deal_damage(2*self.get_stat('minion_damage'), Level.Tags.Physical, self)

class DeathTract(Level.Buff):

    def __init__(self, spell):
        self.spell = spell
        self.overkill = 0
        Level.Buff.__init__(self)

    def on_init(self):
        self.owner_triggers[Level.EventOnDeath] = self.on_death
        self.owner_triggers[Level.EventOnPreDamaged] = self.track_overkill
        self.name = "Soul Contract"
        self.color = Level.Tags.Demon.color	
        self.global_bonuses['damage'] = 5
        self.global_bonuses['range'] = 2

    def on_applied(self, owner):
        owner.tags.append(Level.Tags.Demon)

    def on_unapplied(self):
        if Level.Tags.Demon in self.owner.tags:
            self.owner.tags.remove(Level.Tags.Demon)

    def on_death(self, evt):
        if evt.damage_event:
            print(evt.damage_event.damage)
            self.owner.level.queue_spell(self.thrall(evt.damage_event))

    def track_overkill(self, evt):
        multiplier = (100 - evt.unit.resists[evt.damage_type]) / 100.0
        if(evt.damage*multiplier) > self.owner.cur_hp:
            self.overkill = (evt.damage*multiplier)-self.owner.cur_hp

    def thrall(self, damage):
        ghost = Level.Unit()
        ghost.name = "Soul Thrall"
        ghost.asset_name = os.path.join("..","..","mods","MiscSummons","units","soul_thrall")
        ghost.max_hp = math.ceil(self.owner.max_hp*(self.spell.get_stat('hp_ratio')/100))
        ghost.tags = [Level.Tags.Dark, Level.Tags.Undead]
        ghost.resists[Level.Tags.Physical] = 100
        if damage.damage_type not in ghost.tags and self.spell.get_stat('heritance'):
            ghost.tags += [damage.damage_type]
        for s in self.owner.spells:
            s.caster = s.owner = s.statholder = ghost
            ghost.spells.append(s)
        if self.spell.get_stat('overkiller') and self.overkill:
            ghost.max_hp += self.overkill
        if self.spell.get_stat('ink_holy') and damage.damage_type == Level.Tags.Holy:
            ghost.resists[Level.Tags.Holy] = 100
            atk = CommonContent.SimpleRangedAttack(name="Heaven Bolt", damage=7, damage_type=Level.Tags.Holy, range=6, cool_down=4)
            def heaven_heal(caster, target):
                for i in [u for u in caster.level.get_units_in_ball(target, 2) if not Level.are_hostile(u, caster) and u != caster.level.player_unit]:
                    i.deal_damage(-4, Level.Tags.Heal, caster)
            atk.onhit = heaven_heal
            atk.description += "Heals allies in 2 tiles of the target for 4 HP"
            ghost.spells.insert(0, atk)
        if self.spell.get_stat('ink_poison') and damage.damage_type == Level.Tags.Poison:
            acid = CommonContent.SimpleRangedAttack(name="Acid Stream", damage=3, damage_type=Level.Tags.Poison, range=7, cool_down=1, buff=CommonContent.Acidified, buff_duration=5)
            acid.can_redeal = lambda target, already_checked = []: True
            ghost.spells.insert(0, acid)
        if self.spell.get_stat('ink_dark') and damage.damage_type == Level.Tags.Dark:
            ghost.max_hp = math.ceil(ghost.max_hp*1.3)
            for s in ghost.spells:
                if hasattr(s, 'damage'):
                    s.damage += 5
        if self.spell.get_stat('ink_arc') and damage.damage_type == Level.Tags.Arcane:
            ghost.buffs.append(CommonContent.ShieldRegenBuff(4, 3))
        if self.spell.get_stat('ink_element') and damage.damage_type in [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Lightning]:
            ghost.resists[damage.damage_type] = 100
            ghost.spells.insert(0, CommonContent.SimpleRangedAttack(name="%s Shot" % damage.damage_type.name, damage=10, damage_type=damage.damage_type, range=8, radius=1, cool_down=4))
        ghost.spells.sort(key=lambda x: x.cool_down, reverse=True)
        self.spell.summon(ghost, Level.Point(self.owner.x, self.owner.y))
        if Level.Tags.Demon in self.owner.tags:
            self.owner.tags.remove(Level.Tags.Demon)
        yield

class Contractual(Level.Spell):

    def on_init(self):

        self.name = "Possessor's Trade"
        
        self.level = 4
        self.tags = [Level.Tags.Dark, Level.Tags.Enchantment, Level.Tags.Conjuration]
        self.range = 7
        self.max_charges = 4
        self.duration = 13
        self.hp_ratio = 60

        self.stats.extend(['hp_ratio'])

        self.upgrades['hp_ratio'] = (20, 2, "HP Ratio")
        self.upgrades['duration'] = (5, 2)
        self.upgrades['overkiller'] = (1, 3, "Crimson Pen", "Whenever a unit with Soul Contract dies from damage, if that damage was greater than the target's current HP, the thrall gains maximum HP equal to the difference.\nThis applies before the Fell Ink bonus.")
        self.upgrades['heritance'] = (1, 3, "Imbued Soul", "Soul Thralls gain the damage type they died to as a tag.")
        self.upgrades['ink_holy'] = (1, 5, "Aural Ink", "If a unit with Soul Contract dies to [holy] damage, the thrall gains 100 [holy] resist and a holy bolt that heals allies around the target.", "ink")
        self.upgrades['ink_poison'] = (1, 4, "Vitrolic Ink", "If a unit with Soul Contract dies to [poison] damage, the thrall gains an attack that deals [poison] damage and acidifies hit targets for 5 turns.", "ink")
        self.upgrades['ink_dark'] = (1, 4, "Fell Ink", "If a unit with Soul Contract dies to [dark] damage, the thrall gains 30% extra max HP and 5 [damage] to all abilities. This HP gain stacks multiplicatively with the base percentage.", "ink")
        self.upgrades['ink_arc'] = (1, 4, "Mystic Ink", "If a unit with Soul Contract dies to [arcane] damage, the thrall gains the ability to regenerate [1_SH:shield] every 3 turns, to a max of 4.", "ink")
        self.upgrades['ink_element'] = (1, 6, "Elemental Ink", "If a unit with Soul Contract dies to [fire], [lightning], or [ice] damage, the thrall gains 100 resistance to that element and a ranged attack of that element with 1 radius.", "ink")
    def can_cast(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        return u and all(i not in [Level.Tags.Demon, Level.Tags.Dark, Level.Tags.Undead] for i in u.tags) and Level.Spell.can_cast(self, x, y)

    def get_description(self):
        return (
            "Target unit gains [demon], [5_damage:damage] and [2_range:range] to all abilities, and is teleported as close as possible to you.\n"
            "Enemies teleported in this way are stunned for 1 turn.\n"
            "The target gains Soul Contract for [{duration}_turns:duration].\n"
            "Whenever a unit with Soul Contract dies, it becomes a friendly Soul Thrall with [{hp_ratio}_percent:heal] of the target's max HP.\n"
            "Soul Thralls are [dark] [undead] with knowledge of the victim's spells.\n"
            "[Dark], [demon], and [undead] units cannot be targeted by this spell."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        if not u:
            return
        u.apply_buff(DeathTract(self), self.get_stat('duration'))
        valids = [t for t in self.caster.level.iter_tiles() if self.caster.level.can_stand(t.x, t.y, u)]
        if valids:
            valids.sort(key=lambda x: Level.distance(x, self.caster))
            self.caster.level.flash(u.x, u.y, Level.Tags.Translocation.color)
            self.caster.level.act_move(u, valids[0].x, valids[0].y, teleport=True)
            self.caster.level.flash(u.x, u.y, Level.Tags.Translocation.color)
            if Level.are_hostile(u, self.caster):
                u.apply_buff(Level.Stun(), 1)

class SuperStormCloud(CommonContent.StormCloud):

    def __init__(self, owner, damage=10):
        CommonContent.StormCloud.__init__(self, owner, damage)
        self.strikechance = 1.0
        self.name = "Enhanced Storm Cloud"
        self.source = None
        self.asset_name = 'thunder_cloud'

    def get_description(self):
        return "Each turn, deals [%d_lightning:lightning] damage to any enemy unit standing inside of it.\nExpires in %d turns." % (self.damage, self.duration)

    def on_advance(self):
        u = self.level.get_unit_at(self.x, self.y)
        if not(u and not Level.are_hostile(u, self.owner)):
            self.level.deal_damage(self.x, self.y, self.damage, Level.Tags.Lightning, self.source or self)

class WildfireSparkBuff(Level.Buff):
    def __init__(self, spell):
        Level.Buff.__init__(self)
        self.spell = spell
        self.color = Level.Tags.Fire.color
        self.name = "Wild Sparkblaze"
        self.rad = self.spell.get_stat('radius')
    
    def get_tooltip(self):
        return "Deals 2 fire damage to enemy units and creates enhanced storm clouds in a %d-tile radius." % self.rad
    
    def on_advance(self):
        for unit in self.owner.level.get_units_in_ball(Level.Point(self.owner.x, self.owner.y), self.rad):
            if unit and Level.are_hostile(self.owner, unit):
                unit.deal_damage(2, Level.Tags.Fire, self.spell)
        points = [p for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.spell.get_stat('radius'))]
        random.shuffle(points)
        for p in points:
            if random.random () < .10:
                storm = SuperStormCloud(self.owner, 4+self.spell.get_stat('cloudboost'))
                storm.source = self.spell
                storm.duration = 4+self.spell.get_stat('cloudboost')
                self.owner.level.add_obj(storm, p.x, p.y)

class Wildfire(Level.Spell):

    def on_init(self):

        self.name = "Wildfire Spark"
        
        self.level = 5
        self.tags = [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Conjuration]
        self.range = 5
        self.max_charges = 1
        self.minion_health = 39
        self.minion_damage = 10
        self.minion_range = 7
        self.radius = 5

        self.upgrades['radius'] = (2, 3)
        self.upgrades['recall'] = (1, 2, "Roads of Haze", "Casting Wildfire Spark while the spirit is alive will also teleport it to the target tile if possible and give it 1 extra [SH:shield].", "recasting")
        self.upgrades['auraforce'] = (3, 4, "Mana Charge", "Casting Wildfire Spark while the spirit is alive will activate its aura 3 additional times.", "recasting")
        self.upgrades['cloudboost'] = (4, 4, "Spark Mastery", "The spirit's clouds last twice as long and deal twice as much damage.")
        self.upgrades['minion_health'] = (22, 3)

    def can_cast(self, x, y):
        existing = [u for u in self.caster.level.units if u.source == self]        
        if existing:
            return (x == existing[0].x and y == existing[0].y)
        return Level.Spell.can_cast(self, x, y)

    def get_description(self):
        return (
            "Summon a wildfire spirit on target tile.\n"
            "The wildfire spirit is a flying [fire] [lightning] unit with [{minion_health}_max_HP:minion_health] and a blast dealing [{minion_damage}:minion_damage] [fire] or [lightning] damage with [{minion_range}-tile_range:range].\n"
            "The wildfire spirit has an aura dealing 2 fixed [fire] damage to enemies and creating enhanced thunderclouds lasting 4 turns in a [{radius}-tile_radius:radius] each turn. These clouds always strike, dealing 4 damage, and do not harm allies.\n"
            "Casting this spell while a spirit exists will give it [1_SH:shield] and activate its aura once."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.flying = True
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","spirit_wildfire")
        unit.tags = [Level.Tags.Fire, Level.Tags.Lightning]
        unit.name = "Wildfire Spirit"
        unit.max_hp = self.get_stat('minion_health')
        unit.resists[Level.Tags.Fire] = 100
        unit.resists[Level.Tags.Lightning] = 100
        unit.buffs.append(WildfireSparkBuff(self))
        unit.spells.extend([CommonContent.SimpleRangedAttack(name='Wildfire Blast', damage=self.get_stat('minion_damage'), damage_type=[Level.Tags.Fire, Level.Tags.Lightning], range=self.get_stat('minion_range'))])
        return unit
    
    def cast_instant(self, x, y):
        existing = [u for u in self.caster.level.units if u.source == self]
        if existing:
            u = existing[0]
            if self.get_stat('recall') and self.caster.level.can_move(u, x, y, teleport=True):
                self.caster.level.show_effect(u.x, u.y, Level.Tags.Translocation)
                self.caster.level.act_move(u, x, y, teleport=True)
            aura = u.get_buff(WildfireSparkBuff)
            for _ in range(1+self.get_stat('auraforce')):
                aura.on_advance()
            u.add_shields(1+self.get_stat('recall'))
            return
        else:
            self.summon(self.make_summon(), Level.Point(x, y))

class TrooperBomb(Level.Buff):
    def __init__(self, spell):
        Level.Buff.__init__(self)
        self.spell = spell
        self.color = Level.Tags.Fire.color
        self.name = "Shock Strike"
        self.owner_triggers[Level.EventOnUnitAdded] = self.bomb_queue

    def get_tooltip(self):
        return "When summoned, deals %d%% of maximum HP as fire or lightning damage in a %d-tile burst to %d enemies in 5 tiles." % (self.spell.get_stat('munition_ratio'), self.spell.get_stat('radius'), self.spell.get_stat('num_targets'))
    
    def bomb_queue(self, evt):
        self.owner.level.queue_spell(self.bomb())

    def bomb(self):
        if self.spell.get_stat('force'):
            targets = [u for u in self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('munition_range')) if Level.are_hostile(u, self.owner)]
        else:
            targets = [u for u in self.owner.level.get_units_in_los(self.owner) if Level.distance(self.owner, u) < self.spell.get_stat('munition_range') and Level.are_hostile(u, self.owner)]
        dmg = math.ceil((self.owner.max_hp/10)*(self.spell.get_stat('munition_ratio')/100))
        if targets:
            finals = random.choices(targets, k=self.spell.get_stat('num_targets'))
            for u in finals:
                for stage in Level.Burst(self.owner.level, u, self.spell.get_stat('radius'), ignore_walls=self.spell.get_stat('force')):
                    for point in stage:
                        u = self.owner.level.get_unit_at(point.x, point.y)
                        if u and not Level.are_hostile(u, self.owner) and self.spell.get_stat('helpful'):
                            if (Level.Tags.Fire in u.tags or Level.Tags.Lightning in u.tags) and u.source != self.spell and u.is_alive():
                                self.owner.level.leap_effect(u.x, u.y, random.choice([Level.Tags.Fire.color, Level.Tags.Lightning.color]), u)
                                u.advance()
                            continue
                        if self.owner.level.tiles[point.x][point.y].is_wall() and self.spell.get_stat('force'):
                            self.owner.level.make_floor(point.x, point.y)
                        self.owner.level.deal_damage(point.x, point.y, dmg, random.choice([Level.Tags.Fire, Level.Tags.Lightning]), self.spell)
        yield

    def on_pre_advance(self):
        self.owner.level.queue_spell(self.hp_slice())
    
    def hp_slice(self):
        self.owner.max_hp //= (10-self.spell.get_stat('division'))
        self.owner.cur_hp = self.owner.max_hp
        yield

class ShockTroopers(Level.Spell):

    def on_init(self):

        self.name = "Golem Assault"
        self.level = 4
        self.tags = [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Metallic, Level.Tags.Conjuration]
        self.max_charges = 2
        self.minion_health = 10
        self.minion_damage = 5
        self.num_summons = 3
        self.num_targets = 4
        self.radius = 1
        self.munition_ratio = 20
        self.munition_range = 5
        self.stats.extend(['munition_ratio', 'munition_range'])

        self.must_target_walkable = self.must_target_empty = True

        self.upgrades['munition_ratio'] = (10, 2, "Improved Munitions", "Shock troopers deal an extra 10% of their maximum HP as damage when summoned.")
        self.upgrades['minion_health'] = (10, 4)
        self.upgrades['munition_range'] = (2, 3, "Advanced Targeting", "Shock trooper munitions can hit enemies 2 tiles further away.")
        self.upgrades['division'] = (5, 3, "Launch Refactoring", "Shock troopers have their maximum HP divided by 5 instead of 10 after firing.")
        self.upgrades['force'] = (1, 4, "Disruption Mortars", "Shock trooper munitions destroy walls in the area and can launch at units not in LOS.", "variation")
        self.upgrades['helpful'] = (1, 6, "Vitalizing Launchers", "Allies that would be hit by shock trooper munitions do not take damage. [Fire] and [lightning] allies that would be hit instead use the projectile's energy to instantly act once.", "variation")

    def fmt_dict(self):
        d = Level.Spell.fmt_dict(self)
        d['golem_hp'] = d['minion_health']*10
        return d

    def get_description(self):
        return (
            "Summon a group of [{num_summons}:num_summons] golem shock troopers with [{golem_hp}_HP_each:minion_health]. Shock troopers benefit ten times from [minion_health:minion_health] bonuses.\n"
            "When golem shock troopers are summoned, they launch heavy munitions at [{num_targets}:num_targets] enemies in LOS within [{munition_range}_tiles:range], dealing [{munition_ratio}%:fire] of their maximum HP as [fire] or [lightning] damage in a [{radius}-tile_burst:radius].\n"
            "Before the start of their turn, their maximum HP is divided by 10, and their current HP is set to their new maximum.\n"
            "Golem shock troopers also have a melee attack dealing [{minion_damage}_fire_damage:fire]."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","golem_shock_trooper")
        unit.tags = [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Construct, Level.Tags.Metallic]
        unit.name = "Golem Shock Trooper"
        unit.max_hp = self.get_stat('minion_health')*10
        unit.spells.append(CommonContent.SimpleMeleeAttack(self.get_stat('minion_damage'), damage_type=Level.Tags.Fire))
        unit.buffs.append(TrooperBomb(self))
        return unit
    
    def cast_instant(self, x, y):
        for _ in range(self.get_stat('num_summons')):
            self.summon(self.make_summon(), Level.Point(x, y))

class EmeraldBound(Level.Buff):
    def __init__(self, spell, summoner):
        Level.Buff.__init__(self)
        self.spell = spell
        self.summoner = summoner
        self.color = Level.Tags.Nature.color
        self.name = "Gem Binding"
        self.global_triggers[Level.EventOnPreDamaged] = self.on_damage

    def get_tooltip(self):
        return "Will automatically move near its summoner if more than 3 tiles away from it, and will protect its summoner from damage if within 3 tiles by sacrificing 10 HP."

    def on_pre_advance(self):
        if Level.distance(self.owner, self.summoner) > 3:
            points = [p for p in self.owner.level.get_points_in_ball(self.summoner.x, self.summoner.y, 3) if not self.owner.level.tiles[p.x][p.y].unit and self.owner.level.can_stand(p.x, p.y, self.owner)]
            if points:
                p = random.choice(points)
                self.owner.level.flash(self.owner.x, self.owner.y, Level.Tags.Translocation.color)
                self.owner.level.act_move(self.owner, p.x, p.y, teleport=True)
                self.owner.level.flash(self.owner.x, self.owner.y, Level.Tags.Translocation.color)

    def on_damage(self, evt):
        if evt.unit == self.summoner and Level.distance(self.owner, self.summoner) <= 3 and self.owner.cur_hp > 10:
            foe = evt.source.owner if isinstance(evt.source.owner, Level.Unit) else evt.source
            self.owner.cur_hp -= 0 if ((Level.distance(foe, self.summoner) > 5 and self.spell.get_stat('blocker') and Level.are_hostile(self.summoner, foe)) or (not Level.are_hostile(foe, self.owner) and self.spell.get_stat('ally')) or foe == self.owner) else 10
            self.summoner.add_shields(1)

class EmeraldBoi(Level.Spell):

    def on_init(self):

        self.name = "Emerald Golem"
        self.level = 6
        self.tags = [Level.Tags.Nature, Level.Tags.Metallic, Level.Tags.Conjuration]
        self.max_charges = 2
        self.minion_health = 140
        self.minion_damage = 10

        self.must_target_walkable = self.must_target_empty = True

        self.upgrades['minion_health'] = (40, 2)
        self.upgrades['max_charges'] = (2, 2)
        self.upgrades['minion_damage'] = (9, 3)
        self.upgrades['beam'] = (1, 3, "Emerald Beam", "The golem's melee attack is replaced by an emerald beam with 6 range that deals [poison] or [physical] damage.")
        self.upgrades['blocker'] = (1, 6, "Reactive Protection", "If an enemy damages you from more than 5 tiles away, emerald golems will not lose HP when giving you SH, but they must still have 10 or more HP to do so.", "guard")
        self.upgrades['ally'] = (1, 6, "Empathic Shield", "Emerald golems will not lose HP when giving you SH if the damage came from an ally, but they must still have 10 or more HP to do so.", "guard")

    def can_cast(self, x, y):
        existing = [u for u in self.caster.level.units if u.source == self]       
        if existing:
            return (x == existing[0].x and y == existing[0].y)
        return Level.Spell.can_cast(self, x, y)

    def get_description(self):
        return (
            "Summon an immobile emerald golem near you with [{minion_health}_HP:minion_health] and many resistances. It is unhealable except with this spell.\n"
            "When possible, the golem will move near you before acting if it is more than 3 tiles away.\n"
            "When you would take damage, if the golem is in 3 tiles and has more than 10 HP, the golem will lose 10 HP and give you 1 SH. The golem will not lose HP when protecting you from its own attacks.\n"
            "The golem has a melee attack dealing [{minion_damage}_physical_damage:physical].\n"
            "Casting this spell while an emerald golem exists will heal it for [30_HP:heal]."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","golem_emerald")
        unit.tags = [Level.Tags.Nature, Level.Tags.Metallic, Level.Tags.Construct]
        unit.name = "Emerald Golem"
        unit.max_hp = self.get_stat('minion_health')
        unit.resists[Level.Tags.Arcane] = unit.resists[Level.Tags.Fire] = 75
        unit.resists[Level.Tags.Poison] = 100
        unit.resists[Level.Tags.Heal] = 100
        unit.stationary = True
        if not self.get_stat('beam'):
            unit.spells.append(CommonContent.SimpleMeleeAttack(self.get_stat('minion_damage')))
        else:
            unit.spells.append(CommonContent.SimpleRangedAttack(name="Emerald Beam", damage=self.get_stat('minion_damage'), damage_type=[Level.Tags.Poison, Level.Tags.Physical], range=6, beam=True))
        unit.buffs.append(EmeraldBound(self, self.caster))
        return unit
    
    def cast_instant(self, x, y):
        existing = [u for u in self.caster.level.units if u.source == self]
        if existing:
            u = existing[0]
            u.cur_hp = min(u.cur_hp+30, u.max_hp)
            return
        self.summon(self.make_summon(), Level.Point(x, y))

class BurningForce(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)
        self.name = "Burning Power"
        self.color = Level.Tags.Fire.color
        self.global_triggers[Level.EventOnDamaged] = self.on_damage
    
    def on_damage(self, evt):
        if Level.are_hostile(evt.unit, self.owner):
            if evt.source.owner == self.owner or evt.source == self.owner:
                evt.unit.apply_buff(Shrines.BurningBuff(evt.damage // 2), 1)

    def get_tooltip(self):
        return "Whenever this unit deals damage to an enemy, that enemy takes half of that damage again as fire damage on their next turn"

class NothingBuff(Level.Buff):
    def __init__(self):
        Level.Buff.__init__(self)
        self.name = "Nothingness"
        self.color = Level.Tags.Dark.color
        self.buff_type = Level.BUFF_TYPE_CURSE

    def get_tooltip(self):
        return "Does nothing"

class DarkAuraBuff(Level.Buff):

    def on_init(self):
        self.radius = 5
        self.color = Level.Tags.Dark.color
        self.name = "Essence of Darkness"

    def on_advance(self):
        for unit in self.owner.level.get_units_in_ball(Level.Point(self.owner.x, self.owner.y), self.radius):
            if Level.are_hostile(self.owner, unit) or Level.Tags.Dark not in unit.tags or unit == self.owner:
                continue
            if unit.turns_to_death:
                unit.turns_to_death += 1
    
    def get_tooltip(self):
        return "Dark allies in %d tiles have their durations extended by 1 each turn" % self.radius

class ShrineBone(Level.Spell):

    def on_init(self):

        self.name = "Charbone Call"
        
        self.level = 6
        self.tags = [Level.Tags.Fire, Level.Tags.Dark, Level.Tags.Conjuration]
        self.range = 6
        self.minion_range = 7
        self.minion_health = 66
        self.minion_damage = 9
        self.max_charges = 1

        self.must_target_empty = True
        self.must_target_walkable = True

        self.upgrades['minion_health'] = (33, 3)
        self.upgrades['lanky'] = (1, 2, "Telescoping Staff", "Charbone ascetics can use their staff at a distance.")
        self.upgrades['witchy'] = (1, 7, "Hexed Soul", "Ascetics' quarterstaffs gain [dark] and benefit from two instances of the Faewitch shrine effect in addition to the Wizard's active shrines, and inflict Nothingness permanently on the target, which has no function.\nAscetics extend the duration of temporary [dark] allies in 5 tiles by 1 turn each turn.", "path")
        self.upgrades['frostfire'] = (1, 6, "Crackling Force", "Ascetics gain 50 [lightning] resist.\nTheir quarterstaffs gain [lightning] and benefit from the Thunder shrine effect in addition to the Wizard's active shrines.", "path")
        self.upgrades['chaos'] = (1, 7, "Chaotic Flame", "Ascetics gain [chaos] and 75 [physical] resist. Additionally, their staffs gain 1 level and [chaos].\nAscetics benefit from the Chaos Imp shrine effect in addition to the Wizard's active shrines.", "path")

    def can_cast(self, x, y):
        return False if any(u.source == self for u in self.caster.level.units) else Level.Spell.can_cast(self, x, y)

    def get_description(self):
        return (
            "Summon a charbone ascetic on target tile.\n"
            "Charbone ascetics are [fire] [undead] with [{minion_health}_max_HP:minion_health], fixed [2_SH:shield] and a wide range of resistances.\n"
            "Charbone ascetics redeal half of all damage they do as [fire] damage on the next turn.\n"
            "Charbone ascetics have a quarterstaff attack dealing [{minion_damage}_dark_damage:dark]. This attack is treated as a level 2 [fire] [sorcery] spell and benefits from all applicable shrines the Wizard currently has on their spells.\n"
            "You can only have 1 charbone ascetic at a time."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Charbone Ascetic"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","charbone")
        unit.max_hp = self.get_stat('minion_health')
        unit.shields = 2
        unit.source = self
        unit.tags = [Level.Tags.Undead, Level.Tags.Fire, Level.Tags.Dark]
        if self.get_stat('chaos'):
            unit.tags.append(Level.Tags.Chaos)
            unit.resists[Level.Tags.Physical] = 75
        unit.resists[Level.Tags.Fire] = 100
        unit.buffs.append(BurningForce(self))
        staff = CommonContent.SimpleMeleeAttack(self.get_stat('minion_damage'), damage_type=Level.Tags.Dark)
        if self.get_stat('lanky'):
            staff = CommonContent.SimpleRangedAttack(damage=self.get_stat('minion_damage'), damage_type=Level.Tags.Dark, range=self.get_stat('minion_range'))
        staff.tags = [Level.Tags.Fire, Level.Tags.Sorcery]
        staff.level = 2
        if self.get_stat('witchy'):
            staff.buff = NothingBuff
            staff.tags.append(Level.Tags.Dark)
            staff.description += "Permanently applies Nothingness"
        if self.get_stat('frostfire'):
            unit.resists[Level.Tags.Lightning] = 50
            staff.tags.append(Level.Tags.Lightning)
        if self.get_stat('chaos'):
            staff.level += 1
            staff.tags.append(Level.Tags.Chaos)
        staff.name = "Quarterstaff" if not self.get_stat('lanky') else "Staff Strike"
        unit.spells.append(staff)
        shrinebuffs = [b for b in self.caster.buffs if hasattr(b, "shrine_name") and b.shrine_name != None and b.buff_type == Level.BUFF_TYPE_PASSIVE]
        all_shrines = [s[0] for s in Shrines.new_shrines]
        for s in shrinebuffs:
            target_shrines = [h for h in all_shrines if h().name == s.shrine_name]
            if target_shrines:
                target_shrine = target_shrines[0]()
                if target_shrine.can_enhance(staff):
                    buff = target_shrine.get_buff(staff)
                    buff.description = ''
                    unit.buffs.append(buff)
        if self.get_stat('witchy'):
            for _ in range(2):
                s = Shrines.FaewitchShrine()
                if s.can_enhance(staff):
                    b = s.get_buff(staff)
                    b.description = ''
                    unit.buffs.append(b)
            unit.buffs.append(DarkAuraBuff())
        if self.get_stat('frostfire'):
            s = Shrines.ThunderShrine()
            if s.can_enhance(staff):
                b = s.get_buff(staff)
                b.description = ''
                unit.buffs.append(b)
        if self.get_stat('chaos'):
            s = Shrines.ImpShrine()
            if s.can_enhance(staff):
                b = s.get_buff(staff)
                b.description = ''
                unit.buffs.append(b)
        return unit
    
    def cast_instant(self, x, y):
        self.summon(self.make_summon(), Level.Point(x, y))

class AfterscrollBuff(Level.Buff):
    def __init__(self, spell):
        Level.Buff.__init__(self)
        self.color = Level.Tags.Physical.color
        self.spell = spell
        self.owner_triggers[Level.EventOnSpellCast] = self.on_cast
    
    def on_cast(self, evt):
        self.owner.kill()

    def get_tooltip(self):
        return "Dies when it casts a spell"

class WriteAfterscrolls(Level.Spell):

    def __init__(self, spell):
        self.spell = spell
        Level.Spell.__init__(self)
        self.name = "Afterwrite"
        self.description = "Summon %d radiance or dismay scrolls" % self.spell.get_stat('num_summons')
        self.range = 0
        self.cool_down = 5

    def get_ai_target(self):
        return self.caster

    def can_cast(self, x, y):
        return True

    def cast(self, x, y):

        for i in range(self.spell.get_stat('num_summons')):
            scroll_str = 'dark' if self.spell.get_stat('dismay') else ('radiant' if self.spell.get_stat('radiant') else random.choice(['dark', 'radiant']))
            unit = self.spell.scroll(scroll_str)
            unit.source = self.spell
            self.summon(unit, radius=6, sort_dist=True)
            yield

class RealQuill(Level.Spell):

    def on_init(self):

        self.name = "Twilight Scribe"
        self.level = 5
        self.tags = [Level.Tags.Dark, Level.Tags.Holy, Level.Tags.Conjuration]
        self.max_charges = 3
        self.minion_health = 10
        self.shields = 1
        self.minion_duration = 20
        self.num_summons = 3
        self.lawcopy = False

        self.must_target_empty = True

        self.upgrades['num_summons'] = (3, 4)
        self.upgrades['speed'] = (2, 4, "Godspeed", "The Afterwriter's summoning ability loses 2 cooldown.")
        self.upgrades['dismay'] = (1, 2, "Dusk Scriptures", "Afterwriters will only summon scrolls of dismay.", "alignment")
        self.upgrades['radiant'] = (1, 3, "Dawn Scriptures", "Afterwriters will only summon scrolls of radiance.", "alignment")
        self.upgrades['premade'] = (1, 4, "Script Collection", "Whenever you cast this spell, if an Afterwriter does not exist, the newly summoned Afterwriter immediately activates its summoning ability twice.", "scripting")
        self.upgrades['scrollite'] = (1, 3, "Afterwrite Shades", "Whenever you cast this spell while an Afterwriter exists, it activates its summoning ability once.", "scripting")
        self.upgrades['lastcast'] = (1, 5, "Final Testament", "Casting the last charge of this spell while an Afterwriter exists will copy it X+1 times, where X is this spell's max charges. Copies do not trigger this effect.", "scripting")

    def can_cast(self, x, y):
        existing = [u for u in self.caster.level.units if type(u.source) == RealQuill and u.name == "The Afterwriter"]        
        if existing:
            return (x == existing[0].x and y == existing[0].y)
        return Level.Spell.can_cast(self, x, y)
    def get_description(self):
        return (
            "Summon the Afterwriter, a [dark] [holy] phantom quill with [{minion_health}_HP:minion_health] and [{shields}_SH:shield] lasting [{minion_duration}_turns:duration].\n"
            "The Afterwriter can summon [{num_summons}:num_summons] scrolls of radiance and dismay with fixed [1_SH:shield], which can kill themselves to cast your Death Bolt and Heavenly Blast respectively. This ability has a 5 turn cooldown.\n"
            "Casting this spell while an Afterwriter exists will extend its duration by [{minion_duration}_turns:duration] and give it [2_SH:shield]."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","afterlife_quill")
        unit.tags = [Level.Tags.Dark, Level.Tags.Holy, Level.Tags.Construct]
        unit.name = "The Afterwriter"
        unit.max_hp = self.get_stat('minion_health')
        unit.shields = self.get_stat('shields')
        unit.flying = True
        unit.resists[Level.Tags.Arcane] = 100
        unit.resists[Level.Tags.Dark] = unit.resists[Level.Tags.Holy] = 100
        unit.spells.append(WriteAfterscrolls(self))
        unit.spells[0].cool_down -= self.get_stat('speed')
        unit.turns_to_death = self.get_stat('minion_duration')
        return unit
    
    def scroll(self, string):
        unit = Level.Unit()
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","scroll_%s" % string)
        unit.name = "Scroll of %s" % ("Dismay" if string == "dark" else "Radiance")
        unit.shields = 1
        unit.max_hp = 1
        unit.flying = True
        fball = Spells.DeathBolt() if string == "dark" else Spells.HolyBlast()
        fball.statholder = self.caster
        fball.max_charges = 0
        fball.cur_charges = 0
        unit.spells.append(fball)
        unit.buffs.append(AfterscrollBuff(self))
        return unit
    
    def cast_instant(self, x, y):
        existing = [u for u in self.caster.level.units if type(u.source) == RealQuill and u.name == "The Afterwriter"]
        if existing:
            u = existing[0]
            u.turns_to_death += self.get_stat('minion_duration')
            u.add_shields(2)
            spell = [s for s in u.spells if type(s) == WriteAfterscrolls][0]
            if self.get_stat('scrollite'):
                self.caster.level.act_cast(u, spell, u.x, u.y, pay_costs=False)
            if not self.cur_charges and not self.lawcopy and self.get_stat('lastcast'):
                copied = copy(self)
                copied.lawcopy = True
                for _ in range(self.get_stat('max_charges')+1):
                    self.caster.level.act_cast(self.caster, copied, x, y, pay_costs=False)
        else:
            u = self.make_summon()
            self.summon(u, Level.Point(x, y))
            if self.get_stat('premade'):
                spell = [s for s in u.spells if type(s) == WriteAfterscrolls][0]
                self.caster.level.act_cast(u, spell, u.x, u.y, pay_costs=False)
                self.caster.level.act_cast(u, spell, u.x, u.y, pay_costs=False)


class Egg(Level.Spell):

    def on_init(self):

        self.name = "Wyrmbreed"
        self.level = 6
        self.tags = [Level.Tags.Dragon, Level.Tags.Conjuration]
        self.max_charges = 2
        self.range = 6
        
        ex = Monsters.FireWyrm()
        self.minion_health = ex.max_hp
        self.minion_damage = ex.spells[1].damage
        self.breath_damage = ex.spells[0].damage
        self.minion_range = ex.spells[0].range

        self.upgrades['minion_range'] = (2, 3)
        self.upgrades['breath_damage'] = (8, 4)
        self.upgrades['weakegg'] = (1, 2, "Brittle Eggs", "Eggs spawn with half of their max HP and -100 [physical] resist.")
        self.upgrades['spreader'] = (1, 3, "Spreading Breath", "Wyrms breathe at a 120 degree angle.")
        self.upgrades['chaotic'] = (1, 6, "Chaotic Lineage", "Wyrm breaths do not deal damage of their corresponding element and are instead picked randomly from all damage types excluding [poison] and [physical].\nWyrms gain 100 resistance to that damage type if they do not already have 100 or more resistance to it.\nIce wyrm breath attacks retain their freezing ability.")

    def get_description(self):
        return (
            "Summon a fire or ice wyrm egg randomly on target tile with fixed 14 HP, which will hatch into a wyrm of the corresponding type with [{minion_health}_HP:minion_health] when killed.\n"
            "Wyrms have [{minion_health}_HP:minion_health], regenerate [8_fixed_HP:heal] each turn, have melee attacks dealing [{minion_damage}_physical_damage:physical], and breath attacks dealing [{breath_damage}_damage:damage] of their element in a [{minion_range}-tile_cone:range].\n"
            "Ice wyrm breaths also freeze hit enemies for 2 turns."
        ).format(**self.fmt_dict())

    def make_egg(self):
        unit = random.choice([Monsters.FireWyrmEgg, Monsters.IceWyrmEgg])()
        if unit.name == "Fire Wyrm Egg":
            unit.get_buff(CommonContent.RespawnAs).spawner = lambda: self.make_wyrm('fire')
        else:
            unit.get_buff(CommonContent.RespawnAs).spawner = lambda: self.make_wyrm('ice')
        if self.get_stat('weakegg'):
            unit.resists[Level.Tags.Physical] = -100
            unit.cur_hp = unit.max_hp // 2
        return unit

    def make_wyrm(self, typing):
        wyrm = Monsters.FireWyrm() if typing == 'fire' else Monsters.IceWyrm()
        CommonContent.apply_minion_bonuses(self, wyrm)
        wyrm.spells[0].damage = self.get_stat('breath_damage')
        if self.get_stat('spreader'):
            wyrm.spells[0].angle = math.pi/3
        if self.get_stat('chaotic'):
            wyrm.spells[0].damage_type = random.choice([Level.Tags.Arcane, Level.Tags.Holy, Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Dark, Level.Tags.Lightning])  
            wyrm.spells[0].name = "Chaotic Breath"
            if wyrm.name == "Ice Wyrm":
                old = wyrm.spells[0].get_description 
                wyrm.spells[0].get_description = lambda: old().replace('ice', wyrm.spells[0].damage_type.name.lower())
            if wyrm.resists[wyrm.spells[0].damage_type] < 100:
                wyrm.resists[wyrm.spells[0].damage_type] = 100
        return wyrm
    
    def cast_instant(self, x, y):
        self.summon(self.make_egg(), Level.Point(x, y))

class EldenForce(Level.Buff):
    def __init__(self):
        Level.Buff.__init__(self)
        self.name = "Elden Force"
        self.color = Level.Tags.Ice.color
        self.global_bonuses['damage'] = 1
        self.global_bonuses['range'] = 1
        self.stack_type = Level.STACK_INTENSITY

class FlagInspireBuff(Level.Buff):
    def __init__(self, spell):
        Level.Buff.__init__(self)
        self.color = Level.Tags.Ice.color
        self.spell = spell
        self.global_triggers[Level.EventOnSpellCast] = self.on_cast

    def on_pre_advance(self):
        if self.spell.get_stat('elden'):    
            leveled_units = [u for u in self.owner.level.units if not Level.are_hostile(self.owner, u) and hasattr(u.source, "level") and u != self.owner]
            if leveled_units:
                maxlv = max(u.source.level for u in leveled_units)
                leveled_units = [u for u in leveled_units if u.source.level == maxlv]
                for u in leveled_units:
                    for _ in range(u.source.level):
                        u.apply_buff(EldenForce(), 2)
        elif self.spell.get_stat('honor'):
            eligibles = [u for u in self.owner.level.units if not Level.are_hostile(self.owner, u) and u != self.owner and (Level.Tags.Ice in u.tags or Level.Tags.Lightning in u.tags or "knight" in u.name.lower())]
            for e in eligibles:
                for s in e.spells:
                    e.cool_downs[s] = 0
    
    def on_cast(self, evt):
        if evt.caster == self.spell.caster and Level.Tags.Conjuration in evt.spell.tags:
            if (self.owner.level.can_see(self.owner.x, self.owner.y, evt.x, evt.y) or self.spell.get_stat('blind')) and Level.distance(self.owner, Level.Point(evt.x, evt.y)) < self.spell.get_stat('radius')+2:
                self.owner.level.act_cast(self.owner, evt.spell, evt.x, evt.y, pay_costs=False)

    def get_tooltip(self):
        buff_str = "Copies [conjuration] spells cast in %d tiles of it" % (self.spell.get_stat('radius')+2)
        if self.spell.get_stat('elden'):
            buff_str += " and gives the allies summoned by the highest level spells or skills 1 damage and range to all abilities per source level for 2 turns each turn"
        if self.spell.get_stat('honor'):
            buff_str += " and resets the cooldown of all ice, [lightning], and knight allies' abilities to 0 before acting"
        return buff_str

class StormFlag(Level.Spell):

    def on_init(self):

        self.name = "Storm Command"
        
        self.level = 6
        self.tags = [Level.Tags.Lightning, Level.Tags.Ice, Level.Tags.Conjuration]
        self.range = 6
        self.radius = 4
        self.minion_health = 55
        self.max_charges = 2

        self.must_target_empty = True
        self.must_target_walkable = True

        self.upgrades['radius'] = (2, 3)
        self.upgrades['blind'] = (1, 4, "Blind Devotion", "The flag no longer requires line of sight to copy spells.")
        self.upgrades['sheer'] = (1, 3, "Sheer Force", "The flag's aura gains 1 damage.")
        self.upgrades['elden'] = (1, 6, "Elden Command", "Each turn, the allies summoned by the highest level spells or skills you have gain 1 damage and range to all abilities per level for 2 turns.", "militant")
        self.upgrades['honor'] = (1, 7, "Blizzardly Honor", "[Ice] allies, [lightning] allies, or allies with \"knight\" in their names have their cooldowns instantly reset before the flag's turn starts.", "militant")

    def can_cast(self, x, y):
        return False if any(u.source == self for u in self.caster.level.units) else Level.Spell.can_cast(self, x, y)

    def fmt_dict(self):
        d = Level.Spell.fmt_dict(self)
        d['inspire_rad'] = d['radius']+2
        return d

    def get_description(self):
        return (
            "Summon a stationary storm flag with [{minion_health}_HP:minion_health] and a variety of resistances.\n"
            "The flag has no attacks but has an aura dealing 1 fixed [ice] or [lightning] damage to units in [{radius}_tiles:radius].\n"
            "Whenever the Wizard casts a [conjuration] spell in line of sight of the flag within [{inspire_rad}_tiles:radius] of it, the flag will cast it as well on the same tile.\n"
            "You may only have one flag at a time."
        ).format(**self.fmt_dict())

    def make_summon(self):
        unit = Level.Unit()
        unit.name = "Storm Flag"
        unit.asset_name = os.path.join("..","..","mods","MiscSummons","units","storm_flag")
        unit.max_hp = self.get_stat('minion_health')
        unit.source = self
        unit.buffs.append(CommonContent.DamageAuraBuff(1+self.get_stat('sheer'), [Level.Tags.Lightning, Level.Tags.Ice], self.get_stat('radius')))
        unit.buffs.append(FlagInspireBuff(self))
        unit.stationary = True
        unit.resists[Level.Tags.Lightning] = 100
        unit.resists[Level.Tags.Ice] = 100
        unit.resists[Level.Tags.Physical] = 50
        return unit
    
    def cast_instant(self, x, y):
        self.summon(self.make_summon(), Level.Point(x, y))

Spells.all_player_spell_constructors.extend([PlagueIdol, StillIdol, BugBag, RebirthFlare, EternityTablet, DemonTablet, CursedTree, DemonAgreement, NeoTormentor, HolyCurse, SlimeBlast, JohnsIdea, UndeathTower, MortalIdol, OathTablet])
Spells.all_player_spell_constructors.extend([Corpseport, VoodooDoll, WriteIt, IcyHotTablet, JohnsOtherIdea])
Spells.all_player_spell_constructors.extend([MithrilDrake, FlaminDrake])
Spells.all_player_spell_constructors.extend([TRANSCENDE, SpeedSummon])
Spells.all_player_spell_constructors.extend([BatForm])
Spells.all_player_spell_constructors.extend([Darkgoyle, Corvus, MadTroubler, Glassoid, HealBattery, LubricantFunny, AstroCall, VirtueGhosts, BallistaMen, DreamerCall, SprigganCall, Contractual, Wildfire, ShockTroopers, EmeraldBoi, ShrineBone, RealQuill, Egg, StormFlag])