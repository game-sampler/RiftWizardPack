import sys
import random
import math

# Add the base directory to sys.path for testing- allows us to run the mod
# directly for quick testing
sys.path.append('../..')


import CommonContent
import Consumables
# import Game
import Level
import Monsters
import Mutators
import RareMonsters
import Spells
import Upgrades
import Shrines

class Shrineless(Mutators.Mutator):
    def __init__(self):
        Mutators.Mutator.__init__(self)
        self.description = "No shrines"
    def on_levelgen_pre(self, levelgen):
            levelgen.num_shrines = 0

class SnipeOff(Mutators.Mutator):
    def __init__(self):
        Mutators.Mutator.__init__(self)
        self.description = "Every enemy gains a ranged attack of a random element"
        self.global_triggers[Level.EventOnUnitAdded] = self.on_enemy_added
    def on_enemy_added(self, evt):
        self.modify_unit(evt.unit)
    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)
    def modify_unit(self, unit):
        if unit.team != Level.TEAM_ENEMY or unit.is_lair:
            return
        potentialtypes = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Lightning, Level.Tags.Arcane, Level.Tags.Poison, Level.Tags.Physical, Level.Tags.Dark, Level.Tags.Holy]
        finaltype = random.choice(potentialtypes)
        buff = CommonContent.TouchedBySorcery(finaltype)
        buff.resists[finaltype] = 0
        buff.buff_type = Level.BUFF_TYPE_PASSIVE
        unit.apply_buff(buff)

class SpellLevelRestriction(Mutators.Mutator):

    def __init__(self, level):
        Mutators.Mutator.__init__(self)
        self.level = level
        self.description = "Only level %d spells" % self.level

    def on_generate_spells(self, spells):
        allowed = [s for s in spells if s.level == self.level]
        spells.clear()
        spells.extend(allowed)

class NoHearts(Mutators.Mutator):
    def __init__(self):
        Mutators.Mutator.__init__(self)
        self.description = "No ruby hearts"
    def on_levelgen_pre(self, levelgen):
            if levelgen.shrine == Level.HeartDot or isinstance(levelgen.shrine, Level.HeartDot):
                levelgen.shrine = Shrines.library()

class ExtraSP(Mutators.Mutator):
    def __init__(self, extra):
        Mutators.Mutator.__init__(self)
        self.extra = extra
        self.description = "Start with %d extra SP" % extra
    def on_game_begin(self, game):
        game.p1.xp += self.extra

class LibrarianBuff(Level.Buff):
    def __init__(self, numspells, allspells):
        Level.Buff.__init__(self)
        self.numspells = numspells
        self.allspells = allspells
        self.owner_triggers[Level.EventOnUnitAdded] = self.on_unit_added
        self.name = "Librarian"
        self.description = "Get a random %d spells on entering a rift" % self.numspells
    def gen_rand_spells(self):
        self.owner.spells.clear()
        potentialspells = random.sample(self.allspells, self.numspells-1) 
        finals = potentialspells + [random.choice([s for s in self.allspells if s.get_stat('damage') and s not in potentialspells])]
        for spell in finals:
            self.owner.add_spell(spell)
    def on_applied(self, owner):
        self.gen_rand_spells()
    def on_unit_added(self, evt):
        if evt.unit != self.owner:
            return
        else:
            self.gen_rand_spells()

class Librarian(Mutators.Mutator):
    def __init__(self, numspells):
        Mutators.Mutator.__init__(self)
        self.numspells = numspells
        self.allspells = None
        self.description = "Get %d random spells on entering a rift, with at least one damaging spell included" % self.numspells
    def on_generate_spells(self, spells):
        self.allspells = spells
        return
    def on_game_begin(self, game):
        game.p1.apply_buff(LibrarianBuff(self.numspells, self.allspells))

class StartingHPMod(Mutators.Mutator):
    def __init__(self, newamt):
        Mutators.Mutator.__init__(self)
        self.newamt = newamt
        self.description = "The Wizard starts with %d HP" % self.newamt
    def on_game_begin(self, game):
        game.p1.cur_hp = self.newamt
        game.p1.max_hp = self.newamt

class LimitMovementBuff(Level.Buff):
    def __init__(self, freq):
        Level.Buff.__init__(self)
        self.freq = freq
        self.cur = 0
        self.description = "The Wizard is stunned for 1 turn once every %d turns" % (self.freq+1)
        self.name = "Time Slip"
    def on_advance(self):
        if self.cur == self.freq:
            self.owner.apply_buff(Level.Stun(), 1)
            self.cur = 0
        else:
            self.cur += 1

class LimitMovement(Mutators.Mutator):
    def __init__(self, freq):
        Mutators.Mutator.__init__(self)
        self.freq = freq
        self.description = "The Wizard is stunned for 1 turn once every %d turns" % (self.freq+1)
    def on_game_begin(self, game):
        game.p1.apply_buff(LimitMovementBuff(self.freq))

class DamageUp(Mutators.Mutator):
    def __init__(self, number):
        Mutators.Mutator.__init__(self)
        self.number = number
        self.description = "All enemy spells deal %d%% more damage" % ((self.number-1)*100)
        self.global_triggers[Level.EventOnUnitAdded] = self.on_enemy_added
    def on_enemy_added(self, evt):
        self.modify_unit(evt.unit)
    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)
    def modify_unit(self, unit):
        if unit.team != Level.TEAM_ENEMY or unit.is_lair:
            return
        for s in unit.spells:
            if s.get_stat('damage'):
                s.damage = math.ceil(s.damage*self.number)

class DamageUpTag(Mutators.Mutator):
    def __init__(self, number, tag):
        Mutators.Mutator.__init__(self)
        self.number = number
        self.tag = tag
        self.description = "All %s enemy spells deal %d%% more damage" % (self.tag.name.lower(), (self.number-1)*100)
        self.global_triggers[Level.EventOnUnitAdded] = self.on_enemy_added
    def on_enemy_added(self, evt):
        self.modify_unit(evt.unit)
    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)
    def modify_unit(self, unit):
        if unit.team != Level.TEAM_ENEMY or unit.is_lair or self.tag not in unit.tags:
            return
        for s in unit.spells:
            if s.get_stat('damage'):
                s.damage = math.ceil(s.damage*self.number)

class ExtraDragons(Mutators.Mutator):

    def __init__(self, num):
        Mutators.Mutator.__init__(self)
        self.num = num
        self.description = "Each level beyond the first has %d extra drakes" % self.num

    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty == 1:
            return
        for i in range(self.num):
            levelgen.bosses.append(random.choice([Monsters.StormDrake(), Monsters.FireDrake(), Monsters.VoidDrake(), Monsters.GoldDrake(), Monsters.IceDrake()]))

class AllTag(Mutators.Mutator):
    def __init__(self, tag):
        Mutators.Mutator.__init__(self)
        self.tag = tag
        self.description = "All enemies become %s" % self.tag.name.lower()
        self.global_triggers[Level.EventOnUnitAdded] = self.on_enemy_added
    def on_enemy_added(self, evt):
        self.modify_unit(evt.unit)
    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)
    def modify_unit(self, unit):
        if unit.team != Level.TEAM_ENEMY or unit.is_lair:
            return
        unit.tags.append(self.tag)
        unit.level.set_default_resitances(unit)

class StartWith(Mutators.Mutator):
    def __init__(self, spell):
        Mutators.Mutator.__init__(self)
        self.description = "Start with %s" % (spell().name)
        self.spell = spell
    def on_game_begin(self, game):
        s = self.spell()
        s.caster = game.p1
        game.p1.spells.append(s)

class StartWithChargeMult(Mutators.Mutator):
    def __init__(self, spell, mult):
        Mutators.Mutator.__init__(self)
        self.mult = mult
        self.description = "Start with %s that has %d%% max charges" % (spell().name, self.mult*100)
        self.spell = spell
    def on_game_begin(self, game):
        s = self.spell()
        s.caster = game.p1
        s.max_charges = math.ceil(s.max_charges*self.mult)
        s.cur_charges = s.max_charges
        game.p1.spells.append(s)

class RandomTorment(Mutators.Mutator):
    def __init__(self):
        Mutators.Mutator.__init__(self)
        self.description = "All enemies have a random torment attack"
        self.global_triggers[Level.EventOnUnitAdded] = self.on_enemy_added
    def on_enemy_added(self, evt):
        self.modify_unit(evt.unit)
    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)
    def modify_unit(self, unit):
        if unit.team != Level.TEAM_ENEMY or unit.is_lair:
            return
        names = {
            Level.Tags.Fire: "Fiery",
            Level.Tags.Ice: "Frosty",
            Level.Tags.Dark: "Dark",
            Level.Tags.Arcane: "Mystery",
            Level.Tags.Lightning: "Shocking",
            Level.Tags.Holy: "Radiant",
            Level.Tags.Poison: "Noxious"
        }
        dts = [Level.Tags.Arcane, Level.Tags.Dark, Level.Tags.Ice, Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Holy, Level.Tags.Poison]
        dt = random.choice(dts)
        burst = CommonContent.SimpleBurst(damage=7, damage_type=dt, cool_down=5, radius=4)
        burst.name = names[dt] + " Torment"
        burst.caster = unit
        unit.spells.append(burst)

def DespairRegen():
    b = CommonContent.ShieldRegenBuff(3, 3)
    b.name = "Shield Regeneration"
    return b

class NoSpells(Mutators.Mutator):

    def __init__(self):
        Mutators.Mutator.__init__(self)		
        self.description = "No spells can be learned"

    def on_generate_spells(self, spells):
        spells.clear()

class FMLItems(Mutators.Mutator):
    def __init__(self):
        Mutators.Mutator.__init__(self)
        self.description = "Each realm has an extra healing potion and bag of spikes\nEach realm above 5 has an additional bag of spikes"
    def on_levelgen_pre(self, levelgen):
        levelgen.items.extend([Consumables.heal_potion(), Consumables.bag_of_spikes()])
        if levelgen.difficulty > 5:
            levelgen.items.extend([Consumables.bag_of_spikes()])

class RestrictedSkills(Mutators.Mutator):

    def __init__(self, skillList):
        Mutators.Mutator.__init__(self)		
        self.skillList = skillList
        self.description = "The only skills are %s" % ' and '.join(s().name for s in self.skillList)

    def on_generate_skills(self, skills):
        skills.clear()
        skills.extend([s() for s in self.skillList])

class StartWithSkills(Mutators.Mutator):

    def __init__(self, skillList):
        Mutators.Mutator.__init__(self)		
        self.skillList = skillList
        self.description = "Start with %s" % ' and '.join(s().name for s in self.skillList)
    
    def on_game_begin(self, game):
        for s in self.skillList:
            game.p1.apply_buff(s())

class StartWithBuff(Mutators.Mutator):

    def __init__(self, buff):
        Mutators.Mutator.__init__(self)		
        self.buff = buff
        self.description = "Start with %s" % buff().name

    def on_game_begin(self, game):
        game.p1.apply_buff(self.buff())


Mutators.all_trials.clear()
#Set 1
Mutators.all_trials.append(Mutators.Trial("Gods' Ire", [Shrineless(), Mutators.SpellTagRestriction(Level.Tags.Dark)]))
Mutators.all_trials.append(Mutators.Trial("Snipe-Off", [SnipeOff(), Mutators.SpellTagRestriction(Level.Tags.Arcane)]))
Mutators.all_trials.append(Mutators.Trial("Level 1 Run", [SpellLevelRestriction(1), NoHearts()]))
Mutators.all_trials.append(Mutators.Trial("Mo's Garden", [Mutators.EnemyBuff(lambda: CommonContent.DamageAuraBuff(1, Level.Tags.Ice, 2)), Mutators.OnlySpell("Prison of Thorns"), StartWith(Spells.ThornyPrisonSpell)]))
Mutators.all_trials.append(Mutators.Trial("Nature's Wrath", [DamageUp(1.7), Mutators.EnemyShields(1), Mutators.SpellTagRestriction(Level.Tags.Nature)]))
#Set 2
Mutators.all_trials.append(Mutators.Trial("One-Hit Wonder", [NoHearts(), StartingHPMod(1)]))
Mutators.all_trials.append(Mutators.Trial("Lazy Wizard", [LimitMovement(3), Mutators.RandomSpellRestriction(0.6)]))
Mutators.all_trials.append(Mutators.Trial("Steel Resolve", [Mutators.MonsterHPMult(1.8), Mutators.SpellTagRestriction(Level.Tags.Metallic), ExtraSP(1), Mutators.SpPerLevel(2)]))
Mutators.all_trials.append(Mutators.Trial("Crimp", Mutators.SpPerLevel(1)))
Mutators.all_trials.append(Mutators.Trial("Despair", [LimitMovement(4), Mutators.EnemyBuff(DespairRegen), Mutators.EnemyBuff(lambda: CommonContent.RegenBuff(8))]))
#Set 3
Mutators.all_trials.append(Mutators.Trial("Dragon Destiny", [Mutators.SpellTagRestriction(Level.Tags.Dragon), ExtraDragons(3), DamageUpTag(2, Level.Tags.Dragon)]))
Mutators.all_trials.append(Mutators.Trial("Wire Engineer", [AllTag(Level.Tags.Metallic), Mutators.SpellTagRestriction(Level.Tags.Lightning), StartWithChargeMult(Spells.ConductanceSpell, 1.5)]))
Mutators.all_trials.append(Mutators.Trial("Eternal Torment", RandomTorment()))
Mutators.all_trials.append(Mutators.Trial("Zombieman", [AllTag(Level.Tags.Undead), Mutators.EnemyBuff(lambda: CommonContent.RegenBuff(12))]))
Mutators.all_trials.append(Mutators.Trial("World of Chaos", [Mutators.SpellTagRestriction(Level.Tags.Chaos), Mutators.SpellChargeMultiplier(0.7), Mutators.RandomSkillRestriction(0.4)]))
#A special little something
Mutators.all_trials.append(Mutators.Trial("FML Mode", [NoSpells(), FMLItems()]))
Mutators.all_trials.append(Mutators.Trial("Bookkeeper", [ExtraSP(-1), Mutators.SpPerLevel(0), Librarian(4)]))