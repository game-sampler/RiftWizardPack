from re import L
import Spells
import Upgrades
import Level
import CommonContent
import Variants
import RareMonsters
import Monsters
import mods.API_Universal.Modred as Modred
import Upgrades
import text

import random, math, os

class FryingPan(Level.Spell):

    def on_init(self):
        self.name = "Frying Pan"
        self.max_charges = 15
        self.damage = 9
        self.range = 1
        self.level = 1
        self.melee = True
        self.tags = [Level.Tags.Metallic, Level.Tags.Fire, Level.Tags.Sorcery]

        self.upgrades['damage'] = (4, 2)
        self.upgrades['max_charges'] = (10, 3)
    
    def get_description(self):
        return (
            "Smacks target enemy with a frying pan, dealing [{damage}:damage] [physical] and [fire] damage."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        dtypes = [Level.Tags.Physical, Level.Tags.Fire]
        for dtype in dtypes:
            self.caster.level.deal_damage(x, y, self.get_stat('damage'), dtype, self)

class SeasonBuff(Level.Buff):
    def __init__(self, spell, caster):
        self.spell = spell
        self.caster = caster
        Level.Buff.__init__(self)
        self.buff_type = Level.BUFF_TYPE_CURSE
        self.stack_type = Level.STACK_NONE
        self.color = Level.Tags.Nature.color
        self.name = "Seasoned"
        self.owner_triggers[Level.EventOnDeath] = self.on_death

    def on_applied(self, owner):
        if Level.Tags.Living not in owner.tags and (self.spell.get_stat('garlic') and Level.Tags.Undead not in owner.tags and Level.Tags.Demon not in owner.tags):
            return Level.ABORT_BUFF_APPLY

    def on_advance(self):
        if self.spell.get_stat('chili'):
            self.owner.deal_damage(4, Level.Tags.Fire, self.spell)
        if self.spell.get_stat('garlic') and (Level.Tags.Dark in self.owner.tags or Level.Tags.Demon in self.owner.tags or Level.Tags.Undead in self.owner.tags):
            self.owner.deal_damage(3, Level.Tags.Holy, self.spell)

    def on_death(self, evt):
        heal = -min(self.spell.heal_limit, (self.owner.max_hp // 2))
        self.caster.deal_damage(heal, Level.Tags.Heal, self.spell)


class Season(Level.Spell):
    def on_init(self):
        self.name = "Season"
        self.max_charges = 8
        self.range = 10
        self.level = 2
        self.heal_limit = 10
        self.stats.append("heal_limit")
        self.tags = [Level.Tags.Nature, Level.Tags.Enchantment]
        
        self.upgrades['heal_limit'] = (15, 2)
        self.upgrades['chili'] = (1, 3, "Chili Powder", "Seasoned enemies take [4_fire_damage:fire] each turn while seasoned.", "flavoring")
        self.upgrades['garlic'] = (1, 5, "Garlic Powder", "Seasoned [dark], [demon], or [undead] units take [3_holy_damage:holy] each turn while seasoned.\n[Undead] and [demon] units can also be seasoned.", "flavoring")

    def get_description(self):
        return (
            "Season target enemy with various spices, making it more appetizing.\n"
            "When it dies, the Wizard heals for half of its maximum HP, up to [{heal_limit}:nature] points.\n"
            "Only [living] enemies can be seasoned."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        for spread in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for point in spread:
                u = self.caster.level.get_unit_at(point.x, point.y)
                if u and self.caster.level.are_hostile(u, self.caster):
                    u.apply_buff(SeasonBuff(self, self.caster))

class Potluck(Level.Spell):
    def on_init(self):
        self.name = "Potluck"
        self.level = 5
        self.max_charges = 5
        self.damage = 17
        self.range = 7
        self.radius = 4
        self.max_allies = 3
        self.heal_limit = 20
        self.stats.append('max_allies')
        self.stats.append('heal_limit')
        self.tags = [Level.Tags.Fire, Level.Tags.Sorcery]

        self.upgrades['max_charges'] = (2, 3)
        self.upgrades['max_allies'] = (1, 2)
        self.upgrades['bone_flavor'] = (1, 4, "Bone Broth", "If an [undead] unit dies to this spell's damage, each participant heals an extra 5 HP.\nThis extra healing can bypass the normal limit.\nHowever, at least one [living] unit must be killed in order for allies to heal.", "culinary")
        self.upgrades['blaze'] = (1, 5, "Nether Spices", "If a [fire] or [demon] unit dies to this spell's damage, participants gain a buff increasing spell and skill damage by [5:damage] for [10_turns:duration].\nAt least one [living] unit must be killed for this to take effect.", "culinary")
        self.upgrades['herbal'] = (1, 6, "Natural Ingredients", "If a [nature] unit dies to this spell's damage, each participant gains 1 SH.\n[Nature] units killed count towards the amount healed.", "culinary")

    def get_description(self):
        return (
            "Host a potluck, cooking enemies in a [{radius}-tile_burst:radius].\n"
            "Enemies in range take [{damage}_fire_damage:damage].\n"
            "The caster heals for an amount equal to the sum of the max HP of all [living] enemies that died to this spell's damage, split evenly between it and up to [{max_allies}:conjuration] allies in line of sight.\n"
            "Each participant can heal for a maximum of [{heal_limit}_HP:nature]."
        ).format(**self.fmt_dict())

    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]
    
    def cast_instant(self, x, y):
        broth_active = False
        living_died = False
        blaze_active = False
        herbal_active = False
        heal_pool = 0
        for spread in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for point in spread:
                u = self.caster.level.get_unit_at(point.x, point.y)
                if u and self.caster.level.are_hostile(u, self.caster):
                    u.deal_damage(self.get_stat('damage'), Level.Tags.Fire, self)
                    if not u.is_alive():
                        if Level.Tags.Living in u.tags or (Level.Tags.Nature in u.tags and self.get_stat('herbal')):
                            heal_pool += u.max_hp
                            living_died = True
                        if Level.Tags.Undead in u.tags:
                            broth_active = True
                        if Level.Tags.Demon in u.tags or Level.Tags.Fire in u.tags:
                            blaze_active = True
                        if Level.Tags.Nature in u.tags:
                            herbal_active = True
        targets = [self.caster] + [u for u in self.caster.level.get_units_in_los(self.caster) if u != self.caster and not self.caster.level.are_hostile(u, self.caster)]
        participants = self.get_stat('max_allies')+1
        targets = targets[:participants] if len(targets) > participants else targets
        per_target_heal = min(heal_pool // len(targets), self.heal_limit)
        if broth_active and self.get_stat('bone_flavor'):
            per_target_heal += 5
        if per_target_heal > 0 and living_died:
            for t in targets:
                t.deal_damage(-per_target_heal, Level.Tags.Heal, self)
                if blaze_active and self.get_stat('blaze'):
                    print("blaze upgrade active")
                    buff = CommonContent.GlobalAttrBonus('damage', 5)
                    buff.name = "Nether Spices"
                    buff.stack_type = Level.STACK_NONE
                    buff.color = Level.Tags.Fire.color
                    t.apply_buff(buff, 10)
                if herbal_active and self.get_stat('herbal'):
                    t.add_shields(1)

class PotCookingBuff(Level.Buff):

    def __init__(self, spell):
        self.spell = spell
        self.buff_type = Level.BUFF_TYPE_BLESS
        Level.Buff.__init__(self)
        self.hit_units = []
        self.turns_active = 0
        self.healpool = 0

    def on_init(self):
        self.name = "Cooking"
        self.color = Level.Tags.Fire.color
        self.show_effect = False
        self.global_triggers[Level.EventOnDamaged] = self.on_damaged
        self.stack_type = Level.STACK_NONE
    
    def get_tooltip(self):
        string = "Cooks using any target Pot Spill "
        if self.spell.get_stat('electr'):
            string += "or Pot Zap hits.\n"
        else:
            string += "hits.\n"
        return string
    
    def on_damaged(self, evt):
        if evt.source.name in ["Pot Spill", "Pot Zap"] and self.owner.level.are_hostile(evt.unit, self.owner) and evt.unit not in self.hit_units:
            self.hit_units.append(evt.unit)
    
    def on_applied(self, owner):
        self.owner_triggers[Level.EventOnDeath] = self.on_death
        self.owner.level.show_effect(self.owner.x, self.owner.y, Level.Tags.Buff_Apply, Level.Tags.Fire.color)

    def on_advance(self):
        self.turns_active += 1

    def on_death(self, evt):
        self.healpool = 0
        for u in self.hit_units:
            if Level.Tags.Living in u.tags:
                self.healpool += self.spell.get_stat('heal_power')
        los_units = [u for u in self.owner.level.get_units_in_los(self.owner) if u != self.owner and not self.owner.level.are_hostile(u, self.owner)]
        for l in los_units:
            if Level.Tags.Living in l.tags:
                l.deal_damage(-self.healpool, Level.Tags.Heal, self.spell)
            if self.spell.get_stat('slow'):
                sh = min(self.turns_active // 3, 3)
                l.add_shields(sh)

class PotSummon(Level.Spell):
    def on_init(self):
        self.name = "Magic Pot"
        self.level = 4
        self.max_charges = 7
        self.range = 6
        self.radius = 3
        self.minion_health = 55
        self.minion_damage = 7
        self.minion_duration = 16
        self.minion_range = 6
        self.heal_power = 4
        self.stats.append('heal_power')
        self.must_target_walkable = True
        self.must_target_empty = True
        self.tags = [Level.Tags.Metallic, Level.Tags.Fire, Level.Tags.Conjuration]

        self.upgrades['minion_duration'] = (6, 1)
        self.upgrades['radius'] = (1, 2)
        self.upgrades['heal_power'] = (2, 3, "Healthy Pot")
        self.upgrades['electr'] = (1, 4, "Electric Pot", "The pot gains a second ranged attack that deals [lightning] damage.", "utility")
        self.upgrades['slow'] = (1, 4, "Slow Cooker", "Allies affected by the pot's healing gain [1_SH:shield] for every 3 turns the pot was alive, rounded down, up to a max of 3.", "utility")

    def get_impacted_tiles(self, x, y):
        return [Level.Point(x, y)]
    
    def get_description(self):
        return (
            "Summon a magic pot on target tile.\n"
            "The pot is a [metallic] [fire] [construct] with [{minion_health}_HP:minion_health].\n"
            "The pot has an aura dealing 1 unboostable [fire] or [physical] damage to enemies in [{radius}_tiles:radius].\n"
            "The pot also has a ranged attack dealing [{minion_damage}:damage] [fire] damage to units in [{minion_range}_tiles:minion_range].\n"
            "When the pot dies, [living] allies in line of sight heal [{heal_power}_HP:heal] for each unique [living] unit hit.\n"
            "The pot vanishes after [{minion_duration}_turns:minion_duration]."
        ).format(**self.fmt_dict())
    
    def make_pot(self):
        potpath = os.path.join("..","..","mods","CookingWizard","unit_sprites","magic_pot")
        pot = Level.Unit()
        pot.name = "Magic Pot"
        pot.turns_to_death = self.get_stat('minion_duration')
        pot.asset_name = potpath
        pot.tags = [Level.Tags.Metallic, Level.Tags.Construct, Level.Tags.Fire]
        pot.resists[Level.Tags.Fire] = 100
        pot.max_hp = self.get_stat('minion_health')
        pot.spells.append(CommonContent.SimpleRangedAttack(name="Pot Spill", damage=self.get_stat('minion_damage'), damage_type=Level.Tags.Fire, range=self.get_stat('minion_range'), cool_down=2))
        if self.get_stat('electr'):
            pot.spells.append(CommonContent.SimpleRangedAttack(name="Pot Zap", damage=self.get_stat('minion_damage'), damage_type=Level.Tags.Lightning, range=self.get_stat('minion_range'), cool_down=2))
        pot.buffs.append(CommonContent.DamageAuraBuff(1, [Level.Tags.Fire, Level.Tags.Physical], self.get_stat('radius')))
        pot.buffs.append(PotCookingBuff(self))
        return pot

    def cast_instant(self, x, y):
        self.summon(self.make_pot(), Level.Point(x, y))

class CutleryStorm(Level.Spell):
    def on_init(self):
        self.name = "Cutlery Storm"
        self.max_charges = 10
        self.level = 2
        self.num_targets = 4
        self.damage = 8
        self.range = 0
        self.tags = [Level.Tags.Metallic, Level.Tags.Sorcery]

        self.upgrades['damage'] = (6, 2)
        self.upgrades['num_targets'] = (2, 3)
        self.upgrades['glass'] = (1, 4, "Glass Cutlery", "Inflicts [glassification:glassify] on hit targets for [2_turns:duration].")
    
    def get_description(self):
        return(
            "Throw expensive silverware at the nearest [{num_targets}:num_targets] units in line of sight, dealing [{damage}_physical_damage:physical]."
        ).format(**self.fmt_dict())
    
    
    def get_tgts(self):
        potential_targets = [u for u in self.caster.level.get_units_in_los(self.owner) if self.caster.level.are_hostile(u, self.caster)]
        potential_targets = sorted(potential_targets, key=lambda u: Level.distance(u, self.caster))
        potential_targets = potential_targets[:self.get_stat('num_targets')] if len(potential_targets) > self.get_stat('num_targets') else potential_targets
        return potential_targets
    
    def get_impacted_tiles(self, x, y):
        return [Level.Point(u.x, u.y) for u in self.get_tgts()]
    
    def cast_instant(self, x, y):
        for p in self.get_tgts():
            p.deal_damage(self.get_stat('damage'), Level.Tags.Physical, self)
            if self.get_stat('glass'):
                p.apply_buff(CommonContent.GlassPetrifyBuff(), 2)

class SearWord(Level.Spell):
    def on_init(self):
        self.name = "Word of Searing"
        self.tags = [Level.Tags.Fire, Level.Tags.Word]
        self.level = 7
        self.max_charges = 1
        self.range = 0
        self.damage = 50

        self.upgrades['max_charges'] = (1, 2)
    
    def get_description(self):
        return(
            "Invoke the secret words of cooking meat.\n"
            "All [living] and [nature] units except the caster take [{damage}:damage] [fire] damage.\n"
            "All [fire] units have their current and maximum HP doubled.\n"
            "All [undead] and [ice] units with less than half of their maximum HP remaining immediately die."
        ).format(**self.fmt_dict())

    def get_impacted_tiles(self, x, y):
        return [u for u in self.caster.level.units if u != self.caster]
    
    def cast_instant(self, x, y):
        units = list(self.caster.level.units)
        random.shuffle(units)
        for unit in units:
            if unit == self.caster:
                continue
            if (Level.Tags.Undead in unit.tags or Level.Tags.Ice in unit.tags) and unit.cur_hp < (unit.max_hp // 2):
                unit.kill()
            if Level.Tags.Fire in unit.tags:
                unit.max_hp *= 2
                unit.deal_damage(-unit.cur_hp, Level.Tags.Heal, self)
            if Level.Tags.Living in unit.tags or Level.Tags.Nature in unit.tags:
                unit.deal_damage(self.get_stat('damage'), Level.Tags.Fire, self)

class StuffedBuff(Level.Buff):

    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)
        self.turns_active = 0

    def on_init(self):
        self.color = Level.Tags.Nature.color
        self.name = "Stuffed"
        self.asset = ['status', 'rot']

    def on_advance(self):
        self.turns_active += 1
        if self.turns_active == 13 and self.spell.get_stat('perish'):
            self.owner.apply_buff(CommonContent.Poison())

    def on_applied(self, owner):
        owner.tags.append(Level.Tags.Living) 
        if Level.Tags.Undead in self.owner.tags:
            owner.tags.remove(Level.Tags.Undead)
        multiple = 1 + (self.spell.get_stat('max_HP_gain')/100)
        owner.max_hp = math.ceil(owner.max_hp * multiple)
        if not self.spell.get_stat('min'):
            owner.cur_hp = math.ceil(owner.cur_hp * multiple)
        if self.spell.get_stat('preseasoned'):
            s_spell = Season()
            s_spell.statholder = self.spell.caster
            s_spell.caster = self.spell.caster
            owner.apply_buff(SeasonBuff(s_spell, self.spell.caster))
                
class Stuff(Level.Spell):
    def on_init(self):
        self.name = "Stuff"
        self.tags = [Level.Tags.Nature, Level.Tags.Enchantment]
        self.level = 4
        self.max_charges = 5
        self.range = 7
        self.radius = 2
        self.max_HP_gain = 20
        self.stats.append('max_HP_gain')

        self.upgrades['radius'] = (2, 4)
        self.upgrades['max_HP_gain'] = (10, 2)
        self.upgrades['min'] = (1, 2, "Fake Ingredients", "Stuffed targets no longer gain current HP.\n")

        self.upgrades['perish'] = (1, 4, "Perishable Stuffing", "Stuffed targets will be permanently [poisoned] after 13 turns.", "style")
        self.upgrades['preseasoned'] = (1, 5, "Seasoned Stuffing", "Stuffed targets are automatically seasoned.\nThis version of season gains all of your upgrades and bonuses.", "style")


    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]
    
    def get_description(self):
        return (
            "Stuff units in a [{radius}-tile_burst:radius] with tasty living matter, giving them the appearance of being alive.\n"
            "Affected units gain [living], lose [undead], and gain an additional [{max_HP_gain}%:heal] current and max HP."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        for spread in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for point in spread:
                u = self.caster.level.get_unit_at(point.x, point.y)
                if u and u != self.caster:
                    u.apply_buff(StuffedBuff(self))

class Jello(Level.Spell):
    def on_init(self):
        self.name = "Jell-O"
        self.tags = [Level.Tags.Arcane, Level.Tags.Nature, Level.Tags.Enchantment]
        self.level = 2
        self.max_charges = 7
        self.range = 8
        self.heal_power = 32
        self.stats.append('heal_power')
        self.can_target_empty = True

        self.upgrades['batch'] = (1, 4, "Jell-O Fabrication", "Jell-O affects all allies in LOS of the caster in addition to the target unit.")

        self.upgrades['mango'] = (1, 3, "Mango Flavor", "Affected units gain [1_SH:shield].\nAffected [slime] units gain 50 [fire] and [ice] resist.", "flavor")
        self.upgrades['blk_cherry'] = (1, 3, "Black Cherry Flavor", "Affected units gain 100 [fire] resist.\nAffected [slime] units gain an aura dealing [1_fire_damage:fire] to units in [2_tiles:radius].", "flavor")
        self.upgrades['lemon'] = (1, 3, "Lemon Flavor", "Affected units gain 100 [lightning] resist.\nAffected [slime] units gain 6 spell and skill damage for [6_turns:duration].")
    
    def get_description(self):
        return(
            "Give some Jell-O to target unit.\n"
            "If the unit is an ally, it heals [{heal_power}_HP:heal], and if it is a [slime], it immediately splits.\n"
            "Enemies are unaffected."
        ).format(**self.fmt_dict())
    
    def get_impacted_tiles(self, x, y):
        targets = [Level.Point(x, y)]
        if self.get_stat('batch'):
            targets = targets + [Level.Point(u.x, u.y) for u in self.caster.level.get_units_in_los(self.owner) if u != self.caster and not self.caster.level.are_hostile(u, self.caster)]
        return targets

    def cast_instant(self, x, y):
        targets = [self.caster.level.get_unit_at(x, y)]
        if self.get_stat('batch'):
            targets = targets + [u for u in self.caster.level.get_units_in_los(self.owner) if u != self.caster and not self.caster.level.are_hostile(u, self.caster)]
        for u in targets:
            if u and not self.caster.level.are_hostile(u, self.caster):
                self.caster.level.show_effect(u.x, u.y, Level.Tags.Buff_Apply, Level.Tags.Enchantment.color)
                u.deal_damage(-self.get_stat('heal_power'), Level.Tags.Heal, self)
                if self.get_stat('mango'):
                    u.add_shields(1)
                elif self.get_stat('blk_cherry'):
                    u.resists[Level.Tags.Fire] += 100
                elif self.get_stat('lemon'):
                    u.resists[Level.Tags.Lightning] += 100
                if Level.Tags.Slime in u.tags:
                    if self.get_stat('mango'):
                        u.resists[Level.Tags.Fire] += 50
                        u.resists[Level.Tags.Ice] += 50
                    elif self.get_stat('blk_cherry'):
                        b = CommonContent.DamageAuraBuff(damage=1, damage_type=Level.Tags.Fire, radius=2)
                        u.apply_buff(b)
                    elif self.get_stat('lemon'):
                        b = CommonContent.GlobalAttrBonus('damage', 6)
                        b.name = "Lemon Power"
                        b.color = Level.Tags.Lightning.color
                        u.apply_buff(b, 6)
                    slime_buff = u.get_buff(Monsters.SlimeBuff)
                    if slime_buff != None:
                        u.max_hp, u.cur_hp = slime_buff.to_split, slime_buff.to_split
                        p = self.caster.level.get_summon_point(u.x, u.y)
                        if p:
                            u.max_hp //= 2
                            u.cur_hp //= 2
                            unit = slime_buff.spawner()
                            unit.team = u.team
                            self.caster.level.add_obj(unit, p.x, p.y)

class TenderizeDebuff(Level.Buff):
    def __init__(self, mul, restypes, spell):
        self.mul = mul
        self.buff_type = Level.BUFF_TYPE_CURSE
        self.spell = spell
        self.restypes = restypes
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Tenderized"
        self.color = Level.Tags.Physical.color
        self.show_effect = False
        self.stack_type = Level.STACK_INTENSITY if self.spell.get_stat('chain') else Level.STACK_NONE
    
    def on_applied(self, owner):
        reduct = -(60 - self.mul*5)
        if Level.Tags.Living in owner.tags or (Level.Tags.Undead in owner.tags and self.spell.get_stat('zombozo')) or (Level.Tags.Nature in owner.tags and self.spell.get_stat('nature')):
            reduct *= 2
        for r in self.restypes:
            self.resists[r] = min(-10, reduct)
    

class Tenderize(Level.Spell):
    def on_init(self):
        self.name = "Tenderize"
        self.level = 3
        self.max_charges = 5
        self.damage = 9
        self.range = 9
        self.duration = 12
        self.can_target_empty = False
        self.tags = [Level.Tags.Metallic, Level.Tags.Sorcery]
        self.upgrades['damage'] = (9, 3)
        
        self.upgrades['chain'] = (1, 5, "Multi-Tenderize", "The resist reduction from Tenderized now stacks.")

        self.upgrades['zombozo'] = (1, 3, "Bone Breaker", "[Undead] units are also doubly affected.", "specialization")
        self.upgrades['nature'] = (1, 3, "Nature Slayer", "[Nature] units are also doubly affected.", "specialization")
        
        self.upgrades['dark'] = (1, 3, "Nefarious Swings", "Tenderize also removes [dark] resist.", "element")
        self.upgrades['holy'] = (1, 3, "Sacred Swings", "Tenderize also removes [holy] resist.", "element")
        self.upgrades['arcane'] = (1, 3, "Mystic Swings", "Tenderize also removes [arcane] resist.", "element")
    
    def get_description(self):
        return (
            "Hit targets with a tenderizer, dealing [{damage}_physical_damage:physical].\n"
            "Damaged units lose [fire], [ice], and [lightning] resist based on how close they were to the caster, to a minimum of 10.\n"
            "[Living] units lose twice as much resist.\n"
            "The debuff lasts for [{duration}_turns:duration]."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        res_lost = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Lightning]
        if self.get_stat('dark'):
            res_lost += [Level.Tags.Dark]
        if self.get_stat('holy'):
            res_lost += [Level.Tags.Holy]
        if self.get_stat('arcane'):
            res_lost += [Level.Tags.Arcane]
        u = self.caster.level.get_unit_at(x, y)
        if u:
            if u.deal_damage(self.get_stat('damage'), Level.Tags.Physical, self) > 0:
                dist = math.ceil(Level.distance(u, self.caster))
                debuff = TenderizeDebuff(dist, res_lost, self)
                u.apply_buff(debuff, self.get_stat('duration')) 

allspells = [FryingPan, Season, Potluck, PotSummon, CutleryStorm, SearWord, Stuff, Jello, Tenderize]
Spells.all_player_spell_constructors.extend(allspells)