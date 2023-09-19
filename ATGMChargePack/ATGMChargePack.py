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
import mods.API_ChargedSpells.API_ChargedSpells as API_ChargedSpells
import mods.API_Universal.Modred as Modred
import Upgrades
import math
import text

import os

Fixation = Level.Tag("Fixation", Level.Color(15, 76, 189))
Modred.add_tag_keybind(Fixation, 'x')
Modred.add_tag_tooltip(Fixation)

Invocation = Level.Tag("Invocation", Level.Color(99, 7, 7))
Modred.add_tag_keybind(Invocation, 'v')
Modred.add_tag_tooltip(Invocation)

Sanguine = Level.Tag("Sanguine", Level.Color(101, 28, 50))
Modred.add_tag_keybind(Sanguine, 'g')
Modred.add_tag_tooltip(Sanguine)

Level.Tags.elements.append(Sanguine)
Level.Tags.elements.append(Fixation)
Level.Tags.elements.append(Invocation)

Modred.add_shrine_option(Fixation, 3)
Modred.add_shrine_option(Invocation, 3)
Modred.add_shrine_option(Sanguine, 1)

Modred.add_tag_effect_simple(Level.Tags.Sanguine, os.path.join('mods','ATGMChargePack','sanguine_effect'))



Modred.add_attr_color('health_sacrifice', Sanguine.color)
Modred.add_attr_color('max_charge', Fixation.color)
Modred.add_attr_color('required_charge', Invocation.color)

#uncomment to enable default sanguine resist generation
set_default_resistances_old = Level.Level.set_default_resitances

def __set_default_resistances_new(self, unit):
    set_default_resistances_old(self, unit)

    if Level.Tags.Undead in unit.tags or "Blood" in unit.name:
        unit.resists.setdefault(Level.Tags.Sanguine, 100)

    if Level.Tags.Metallic in unit.tags:
        unit.resists.setdefault(Level.Tags.Sanguine, 50)

Level.Level.set_default_resitances = __set_default_resistances_new

class ChaosRay(API_ChargedSpells.PowerupSpell):

    def on_init(self):
        super(ChaosRay, self).on_init()
        self.name = "Ray of Chaos"
        self.radius = 1
        self.damage = 9
        self.can_target_self = False
        self.level = 5
        self.tags = [Level.Tags.Chaos, Level.Tags.Sorcery, Level.Tags.Dark, Level.Tags.Arcane, Level.Tags.Fixation]
        self.range = 10
        self.max_charges = 5
        self.max_charge = 10 # this is how many turns the spell can charge for
        self.is_chargeable = True
        self.charging_effect_color = Level.Tags.Fire.color
        self.stats.append('max_charge')

        self.upgrades['radius'] = (1, 3, "Radius")
        self.upgrades['damage'] = (7, 4, "Damage")
        self.upgrades['powered'] = (1, 6, "Manapower", "When you cast ray of chaos, consume all charges of it and add that number to the turns spent charging. This bonus can go over the normal channeling cap.")
        self.upgrades['guard'] = (1, 1, "Guard", "Prevents Ray of Chaos from damaging you.")
    def on_cast(self, x, y, turns_charged):
        if self.get_stat('powered'):
            turns_charged = turns_charged + self.cur_charges + 1
            self.cur_charges = 0
        start = Level.Point(self.caster.x, self.caster.y)
        target = Level.Point(x, y)
        dtypes = [Level.Tags.Fire, Level.Tags.Dark, Level.Tags.Lightning, Level.Tags.Physical]
        if turns_charged >= 7:
            dtypes.append(Level.Tags.Arcane)
        for dtype in dtypes:
            for point in CommonContent.Bolt(self.caster.level, start, target):
                for spread in CommonContent.Burst(self.caster.level, point, (self.get_stat('radius') + (turns_charged // 3))):
                    for point in spread:
                        if self.get_stat('guard') and self.caster.level.get_unit_at(point.x, point.y) == self.caster:
                            continue
                        self.caster.level.deal_damage(point.x, point.y, (self.get_stat('damage') + turns_charged // 2), dtype, self)
                    if turns_charged >= 10:
                        unit = self.caster.level.get_unit_at(point.x, point.y)
                        if unit and Level.are_hostile(self.caster, unit):
                            tpspots = [t for t in self.caster.level.iter_tiles() if t.can_walk and not t.unit]
                            tpspot = random.choice(tpspots)
                            yield self.caster.level.act_move(unit, tpspot.x, tpspot.y, teleport=True)
                            unit.apply_buff(Level.Stun(), 1)
            yield
                
    
    def get_description(self):
        return ("Charge a ray of chaos for up to [{max_charge}_turns:max_charge].\n"
                "The ray deals [{damage}:damage] [dark], [fire], [lightning] and [physical] damage.\n"
                "Gains different effects depending on how long you charge it for.\n"
                "Gains 1 radius every 3 turns and 1 damage every 2 turns.\n"
                "At 7 channeling turns, deals [arcane] damage in addition to its normal types. \n"
                "At full channeling, teleports hit units to random tiles and stuns them for 1 turn.").format(**self.fmt_dict())

class GravityWell(API_ChargedSpells.DualEffectSpell):
    def on_init(self):
        super(GravityWell, self).on_init()
        self.name = "Gravity Well"

        self.can_target_self = False
        self.level = 3
        self.tags = [Level.Tags.Arcane, Level.Tags.Sorcery, Level.Tags.Fixation]
        self.range = 10
        self.damage = 14
        self.pull_damage = 10
        
        self.radius = 4

        self.max_charges = 4
        self.max_charge = 3 # this is how many turns the spell can charge for
        self.stats.append('max_charge')
        self.is_chargeable = False
        self.charging_effect_color = Level.Tags.Arcane.color

        self.upgrades['pull_damage'] = (5, 2, "Pull Damage", "This damage applies while charging")
        self.upgrades['max_charge'] = (4, 2)
        self.upgrades['radius'] = (1, 2, "Radius")
        self.upgrades['endothermic'] = (1, 4, "Endothermic Well", "The well creates blizzards that last 5 turns and deals [ice] damage when exploding, and units being pulled in are [frozen] for 2 turns.", "elemental")
        self.upgrades['exothermic'] = (1, 4, "Exothermic Well", "The well deals [fire] damage to units being pulled into it equal to twice the explosion damage", "elemental")
    def get_description(self):
        return "Summons a gravity well at target tile that pulls in units in range.\nUnits within [{radius}_tiles:radius] of the well are pulled in and take [{pull_damage}_arcane:arcane] damage each turn.\nOn recast, the well explodes dealing [{damage}_arcane:arcane] and [{damage}_physical:physical] damage.\nThe well can be charged for up to [{max_charge}_turns:max_charge]".format(**self.fmt_dict())
    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]
    def on_cast1(self, x, y, turns_charged, turns_remaining):
        target = Level.Point(x, y)
        points = [p for stage in CommonContent.Burst(self.caster.level, target, self.get_stat('radius')) for p in stage]
        units =  [self.caster.level.get_unit_at(p.x, p.y) for p in points if self.caster.level.get_unit_at(p.x, p.y) and self.caster.level.get_unit_at(p.x, p.y) != self.caster]
        random.shuffle(units)
        units.sort(key=lambda u: Level.distance(u, target))
        for u in units:
            if not Level.are_hostile(u, self.caster):
                continue
            if self.get_stat('endothermic'):
                u.apply_buff(CommonContent.FrozenBuff(), 2)
            for p in self.caster.level.get_points_in_line(target, u):
                self.caster.level.show_effect(p.x, p.y, Level.Tags.Arcane, minor=True)
                self.caster.level.deal_damage(p.x, p.y, self.get_stat('pull_damage'), Level.Tags.Arcane, self)
                if self.get_stat('exothermic'):
                    self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage')*2, Level.Tags.Fire, self)
                CommonContent.pull(u, target, 3, find_clear=False)
        yield
    def on_cast2(self, x, y, turns_charged):
        target = Level.Point(x, y)
        for spread in CommonContent.Burst(self.caster.level, target, self.get_stat('radius')):
            for point in spread:
                self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Arcane, self)
                self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Physical, self)
                if self.get_stat('endothermic'):
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Ice, self)
                    cloud = CommonContent.BlizzardCloud(self.caster)
                    cloud.duration = 5
                    cloud.damage = 12
                    cloud.source = self
                    self.caster.level.add_obj(cloud, point.x, point.y)
            yield

#start of moves exclusively for the chaos inscription

class ChaosShot(Level.Spell):
    def on_init(self):
        self.name = "Chaos Shot"
        self.damage = 4
        self.range = 9
        self.radius = 0
        self.requires_los = True
    def get_description(self):
        return "Deals [fire], [lightning], and [physical] damage.".format(**self.fmt_dict())
    def cast(self, x, y):
        dtypes = [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical]
        burstpoint = Level.Point(x, y)
        for stage in CommonContent.Burst(self.caster.level, burstpoint, self.get_stat('radius')):
            for point in stage:
                for dtype in dtypes:
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)
        for i in range(4):
            yield

class ChaosWave(Monsters.BreathWeapon):
    def on_init(self):
        self.name = "Chaos Wave"
        self.damage = 7
        self.range = 7
        self.cool_down = 3
        self.requires_los = True
    def get_description(self):
        return "Deals [fire], [lightning], and [physical] damage in a cone.".format(**self.fmt_dict())
    def per_square_effect(self, x, y):
        dtypes = [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical]
        for dtype in dtypes:
            self.caster.level.deal_damage(x, y, self.get_stat('damage'), dtype, self)
    def cast(self, x, y):
        yield from Monsters.BreathWeapon.cast(self, x, y)

class RadiantBurst(Level.Spell):
    def on_init(self):
        self.name = "Radiance"
        self.damage = 7
        self.radius = 6
        self.range = 0
        self.cool_down = 4
    def get_ai_target(self):
        for p in self.get_impacted_tiles(self.caster.x, self.caster.y):
            u = self.caster.level.get_unit_at(p.x, p.y)
            if u and self.caster.level.are_hostile(u, self.caster):
                return self.caster
        return None
    def get_impacted_tiles(self, x, y):
        for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for p in stage:
                yield p
    def get_description(self):
        return "Deals [holy] damage to enemies and heals allies"
    def cast(self, x, y):
        burstpoint = Level.Point(self.caster.x, self.caster.y)
        for stage in CommonContent.Burst(self.caster.level, burstpoint, self.get_stat('radius')):
                for point in stage:
                    unit = self.caster.level.get_unit_at(point.x, point.y)
                    if unit:
                        if unit.is_player_controlled:
                            continue
                        if self.caster.level.are_hostile(unit, self.caster):
                            self.caster.level.deal_damage(point.x, point.y, -self.get_stat('damage'), Level.Tags.Heal, self)
                    else:
                        self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Holy, self)
                yield

class NecroShot(Level.Spell):

    def on_init(self):
        self.name = "Necrotic Bolt"
        self.range = 9
        self.damage = 9
        self.arc_range = 6
        self.num_cascades = 3
        self.cool_down = 7
        self.minion_damage = self.num_cascades
        self.minion_health = self.arc_range

    def cast(self, x, y):

        prev = self.caster
        target = self.caster.level.get_unit_at(x, y) or Level.Point(x, y)
        already_hit = set()
        current_cascades = 0

        while (target or prev == self.caster) and current_cascades < self.num_cascades:

            self.caster.level.deal_damage(target.x, target.y, self.get_stat('damage'), Level.Tags.Dark, self)
            yield

            already_hit.add(target)
            current_cascades += 1

            def can_arc(u, prev):
                if not self.caster.level.are_hostile(self.caster, u):
                    return False
                if u in already_hit:
                    return False
                if not self.caster.level.can_see(prev.x, prev.y, u.x, u.y):
                    return False
                return True

            units = [u for u in self.caster.level.get_units_in_ball(target, self.arc_range) if can_arc(u, target)]
            
            prev = target
            if units:
                target = random.choice(units)
            else:
                target = None	
            yield
        yield
    def get_description(self):
        return "Cascades up to {minion_damage} times with a cascade range of {minion_health}".format(**self.fmt_dict())

class VoidBarrage(Level.Spell):
    def on_init(self):
        self.name = "Void Rain"
        self.range = 8
        self.radius = 2
        self.damage = 14
        self.range = 5
        self.num_targets = 3
        self.cool_down = 6
    def get_description(self):
        return "Fires at up to [{num_targets}_targets:conjuration] in LOS, dealing damage in [{radius}_tiles:radius] of them".format(**self.fmt_dict())
    def cast(self, x, y):
        candidates = [u for u in self.caster.level.get_units_in_ball(Level.Point(self.caster.x, self.caster.y), self.get_stat('range')) if self.caster.level.can_see(self.caster.x, self.caster.y, u.x, u.y) and Level.are_hostile(self.caster, u)]
        if len(candidates) >= self.get_stat('num_targets'):
            candidates = random.sample(candidates, self.get_stat('num_targets'))
        for target in candidates:
            for spread in CommonContent.Burst(self.caster.level, Level.Point(target.x, target.y), self.get_stat('radius')):
                for point in spread:
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Arcane, self)
            for i in range(3):
                yield

#end of moves exclusively for the chaos inscription

class ChaosTome(API_ChargedSpells.PowerupSpell):
    def on_init(self):
        super(ChaosTome, self).on_init()
        self.level = 8
        self.range = 8
        self.max_charges = 3
        self.name = "Chaos Inscription"
        self.minion_duration = 25
        self.max_charge = 9
        self.minion_health = 30
        self.tags = [Level.Tags.Chaos, Level.Tags.Conjuration, Level.Tags.Fixation]
        self.must_target_empty = True
        self.must_target_walkable = False
        self.is_chargeable = True
        self.charging_effect_color = Level.Tags.Holy.color
        self.stats.append('max_charge')

        self.upgrades['max_charges'] = (2, 4, "Max Charges")
        self.upgrades['max_charge'] = (3, 3)
        self.upgrades['binding'] = (1, 3, "Binding", "Chaos Inscription gains 3 duration per turn charged.\nThe inscription's duration is capped at 50 turns.")
        self.upgrades['radiance'] = (1, 6, "Glyph of Radiance", "After 7 turns of charging, the inscription gains 100 [holy] resistance, a [holy] burst that heals allies in range, and an aura that deals [holy] damage to enemies in a wide range. \n The aura's damage and range, and the burst's damage and radius increase as the spell is charged.", "glyph")
        self.upgrades['shadow'] = (1, 6, "Glyph of Shadows", "After 7 turns of charging, the inscription gains 100 [dark] resistance, a lifesteal bolt, and a cascading [dark] blast. \n The lifesteal bolt's damage  and radius increase as you charge the spell, as well as the blast's damage and number of cascade targets.", "glyph")
        self.upgrades['insight'] = (1, 6, "Glyph of Insight", "After 7 turns of charging, the inscription gains 100 [arcane] resistance, passive teleportation, shield generation, and an [arcane] barrage that increases in damage, range and number of targets as the spell is charged. \n Grants 4 free charge turns. This bonus can exceed the normal channeling cap.", "glyph")
    def get_description(self):
        return "Summons an inscription of chaos.\nThe inscription starts with [{minion_health}_HP:minion_health] and a chaos shot attack, and becomes stronger the longer you charge this spell.\nAt 5 or more charge turns, gains a powerful chaos wave attack.\nThe inscription vanishes after [{minion_duration}_turns:minion_duration], and can be channeled for up to [{max_charge}_turns:max_charge].".format(**self.fmt_dict())
    def on_cast(self, x, y, turns_charged):
        if self.get_stat('insight'):
            turns_charged += 4
        Inscription = Level.Unit()
        Inscription.name = "Chaos Inscription"
        Inscription.asset_name = os.path.join("..","..","mods","ATGMChargePack","scroll_chaos")
        Inscription.max_hp = min(200, self.get_stat('minion_health') + 8*turns_charged)
        Inscription.shields = min(4, turns_charged // 2 + 1)
        Inscription.stationary = False
        Inscription.flying = True
        Inscription.team = self.caster.team
        if self.get_stat('radiance') and turns_charged >= 7:
            holywave = RadiantBurst()
            holywave.radius += turns_charged // 2
            holywave.damage += turns_charged
            aura = CommonContent.DamageAuraBuff(damage_type=Level.Tags.Holy, damage=6, radius=4)
            aura.damage += turns_charged // 3
            aura.radius += turns_charged // 3
            Inscription.buffs.append(aura)
            Inscription.spells.append(holywave)
            Inscription.resists[Level.Tags.Holy] = 100
        if self.get_stat('shadow') and turns_charged >= 7:
            sapbolt = CommonContent.SimpleRangedAttack(name="Mass Drain", damage=9, damage_type=Level.Tags.Dark, range=5, radius=1, drain=True)
            sapbolt.cool_down = 2
            sapbolt.damage += turns_charged
            sapbolt.radius += min(2, turns_charged // 3)
            necroshot = NecroShot()
            necroshot.num_cascades += turns_charged // 3
            necroshot.minion_damage += turns_charged // 3
            necroshot.damage += turns_charged + 3
            Inscription.spells.append(necroshot)
            Inscription.spells.append(sapbolt)
            Inscription.resists[Level.Tags.Dark] = 100
        if self.get_stat('insight') and turns_charged >= 7:
            Inscription.buffs.append(CommonContent.ShieldRegenBuff(4, 2))
            Inscription.buffs.append(CommonContent.TeleportyBuff(7, .25))
            voidbarr = VoidBarrage()
            voidbarr.num_targets += turns_charged // 2
            voidbarr.range += turns_charged
            voidbarr.damage += turns_charged // 2
            Inscription.spells.append(voidbarr)
            Inscription.resists[Level.Tags.Arcane] = 100
        for dtype in [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical, Level.Tags.Poison]:
            Inscription.resists[dtype] = 100
        Inscription.resists[Level.Tags.Ice] = 50
        CW = ChaosWave()
        CS = ChaosShot()
        CW.damage += turns_charged // 2 + 4
        CW.range += min(4, turns_charged // 2 + 1)
        CS.radius += min(3, turns_charged // 3)
        CS.damage += turns_charged + 2
        Inscription.turns_to_death = self.get_stat('minion_duration')
        if turns_charged >= 5:
            Inscription.spells.append(CW)
        Inscription.spells.append(CS)
        if self.get_stat('binding'):
            Inscription.turns_to_death = min((Inscription.turns_to_death + 3*turns_charged), 50)
        Inscription.tags = [Level.Tags.Chaos, Level.Tags.Construct]
        self.summon(Inscription, Level.Point(x, y))
        yield

class IceMelt(API_ChargedSpells.DualEffectSpell):
    def on_init(self):
        super(IceMelt, self).on_init()
        self.name = "Melting Ice"
        self.tags = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Sorcery, Level.Tags.Fixation]
        self.radius = 3
        self.range = 9
        self.damage = 20
        self.level = 4
        self.max_charges = 6
        self.max_charge = 5
        self.duration = 2
        self.cur_frozen = 0
        self.is_chargeable = True
        self.bonus_per_frozen = 4
        self.charging_effect_color = Level.Tags.Ice.color
        self.stats.append('max_charge')

        self.upgrades['max_charges'] = (3, 3, "Max Charges")
        self.upgrades['damage'] =  (12, 2, "Damage", "This upgrade affects the base recast damage only.")
        self.upgrades['radius'] = (2, 3, "Radius")
        self.upgrades['optimized'] = (1, 6, "Temperature Dynamic", "The ice wave refreezes enemies on recast, and the spell's bonus per frozen unit also applies to the melting wave's fire damage.")
    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]
    def get_description(self):
        return "While charging, continuously create waves of ice in [{radius}_tiles:radius] that [freeze] enemies for [{duration}_turns:duration]. This effect can be charged for up to [{max_charge}_turns:max_charge].\nOn recast, melt this ice dealing [{damage}_fire:fire] damage to enemies plus an extra 4 [ice] damage for each enemy that was frozen while charging.".format(**self.fmt_dict())
    def on_cast1(self, x, y, turns_charged, turns_remaining):
        target = Level.Point(x, y)
        for spread in CommonContent.Burst(self.caster.level, target, self.get_stat('radius')):
            for point in spread:
                self.caster.level.show_effect(point.x, point.y, Level.Tags.Ice, minor=False)
                u = self.caster.level.get_unit_at(point.x, point.y)
                if u and not Level.are_hostile(u, self.caster):
                    continue
                elif u:
                    u.apply_buff(CommonContent.FrozenBuff(), self.get_stat('duration'))
                    self.cur_frozen += 1
            yield
    def on_cast2(self, x, y, turns_charged):
        target = Level.Point(x, y)
        icedamage = self.cur_frozen*self.bonus_per_frozen
        realdamage = self.get_stat('damage')
        for spread in CommonContent.Burst(self.caster.level, target, self.get_stat('radius')):
            for point in spread:
                if self.get_stat('optimized'):
                    realdamage += icedamage
                self.caster.level.deal_damage(point.x, point.y, realdamage, Level.Tags.Fire, self)
                self.caster.level.deal_damage(point.x, point.y, icedamage, Level.Tags.Ice, self)
                if self.get_stat('optimized'):
                    u = self.caster.level.get_unit_at(point.x, point.y)
                    if u:
                        u.apply_buff(CommonContent.FrozenBuff(), self.get_stat('duration'))
        self.cur_frozen = 0
        yield

class LeyDraw(API_ChargedSpells.PowerupSpell):
    def on_init(self):
        super(LeyDraw, self).on_init()
        self.name = "Ley Draw"
        self.level = 6
        self.tags = [Level.Tags.Arcane, Level.Tags.Enchantment, Level.Tags.Fixation]
        self.max_charges = 5
        self.range = 0
        self.max_charge = 7
        self.stats.append('max_charge')

        self.upgrades['max_charges'] = (2, 1, "Max Charges")
        self.upgrades['max_charge'] = (2, 3)
        self.upgrades['refresh'] = (1, 5, "Arcane Recovery", "If Ley Draw is cast fully charged, gain 2 charges of a random [sorcery] spell that has no charges left.", "enhancement")
        self.upgrades['empower'] = (1, 4, "Ley Focus", "If Ley Draw is cast fully charged, gain a buff that increases the [damage] of all spells by 7 for 15 turns.", "enhancement")
    def get_description(self):
        return "Spend up to [{max_charge}_turns:max_charge] charging this spell.\nWhen recast, gain a buff that temporarily increases the maximum charge time of your next [fixation] spell that is not Ley Draw by the number of turns you charged for.\nCasting Ley Draw again will not increase the strength of the buff.".format(**self.fmt_dict())
    def on_cast(self, x, y, turns_charged):
        self.caster.apply_buff(LeyBuff(turns_charged))
        if self.get_stat('empower') and turns_charged == self.max_charge:
            buff = CommonContent.GlobalAttrBonus('damage', 7)
            buff.name = "Ley Power"
            buff.stack_type = Level.STACK_INTENSITY
            buff.color = Level.Tags.Dragon.color
            self.caster.apply_buff(buff, 15)
        if self.get_stat('refresh') and turns_charged == self.max_charge:
            choices = [s for s in self.caster.spells if Level.Tags.Sorcery in s.tags and s.cur_charges == 0]
            if choices:
                choice = random.choice(choices)
                choice.cur_charges = min(choice.cur_charges + 2, choice.get_stat('max_charges'))
        yield

class LeyBuff(Level.Buff):

    def __init__(self, strength):
        self.strength = strength
        self.buff_type = Level.BUFF_TYPE_BLESS
        Level.Buff.__init__(self)

    def on_init(self):
        self.affected_spell = None
        self.name = "Ley Channeling %d" % self.strength
        self.color = Level.Tags.Fixation.color
        self.show_effect = False
        self.tag_bonuses[Level.Tags.Fixation]['max_charge'] = self.strength
        self.owner_triggers[Level.EventOnSpellCast] = self.on_spell_cast
        self.description = "Increase the maximum charge of the next [fixation] spell by %d" % self.strength
        self.stack_type = Level.STACK_NONE
    
    def on_spell_cast(self, evt):
        if type(evt.spell) == LeyDraw:
            self.owner.remove_buff(self.owner.get_buff(LeyBuff))
        self.affected_spell = evt.spell
    
    def on_advance(self):
        b = self.owner.get_buff(LeyBuff)
        if b and self.affected_spell:
            if not self.owner.has_buff(API_ChargedSpells.ChargingBuff) or self.affected_spell.turns_charged == self.affected_spell.get_stat('max_charge'):
                self.owner.remove_buff(b)

class SoulSuck(API_ChargedSpells.DualEffectSpell):
    def on_init(self):
        super(SoulSuck, self).on_init()
        self.name = "Soul Offering"
        self.tags = [Level.Tags.Dark, Level.Tags.Holy, Level.Tags.Sorcery, Level.Tags.Fixation]
        self.radius = 5
        self.range = 9
        self.damage = 22
        self.level = 8
        self.max_charges = 1
        self.max_charge= 5
        self.duration = 2
        self.num_targets = 4
        self.num_targets_death_bonus = 1
        self.cur_bonus = 0
        self.is_chargeable = True
        self.charging_effect_color = Level.Tags.Physical.color
        self.stats.append('max_charge')

        self.upgrades['num_targets'] = (3, 3)
        self.upgrades['radius'] = (1, 2)
        self.upgrades['shadowshot'] = (1, 5, "Shadow Judgment", "The rays fired on recast deal dark damage")
    def get_description(self):
        return "Deals [{damage}_dark:dark] and [{damage}_holy:holy] damage to units in range each turn while charging. Recast to release rays on up to {num_targets} random enemies on the map that deal [{damage}_holy:holy] damage, plus an additional ray for each enemy that died to this spell while charging.\nSoul Offering can be charged for up to [{max_charge}_turns:max_charge]".format(**self.fmt_dict())
    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]
    def on_cast1(self, x, y, turns_charged, turns_remaining):
        target = Level.Point(x, y)
        for spread in CommonContent.Burst(self.caster.level, target, self.get_stat('radius')):
            for point in spread:
                for dtype in [Level.Tags.Holy, Level.Tags.Dark]:
                    unit = self.caster.level.get_unit_at(point.x, point.y)
                    self.caster.level.show_effect(point.x, point.y, dtype, minor=True)
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)
                    if unit and not unit.is_alive():
                        self.cur_bonus += 1
            yield
    def on_cast2(self, x, y, turns_charged):
        units = list(self.caster.level.units)
        if len(units) > self.num_targets + self.cur_bonus:
            units = random.sample(units, self.num_targets + self.cur_bonus)
        if units:
            for u in units:
                if not Level.are_hostile(u, self.caster):
                    continue
                if self.get_stat('shadowshot'):
                    self.caster.level.show_effect(u.x, u.y, Level.Tags.Dark, minor=False)
                    self.caster.level.deal_damage(u.x, u.y, self.get_stat('damage')*2, Level.Tags.Holy, self)
                self.caster.level.show_effect(u.x, u.y, Level.Tags.Holy, minor=False)
                self.caster.level.deal_damage(u.x, u.y, self.get_stat('damage')*2, Level.Tags.Holy, self)
            self.cur_bonus = 0
            yield

class DracoPillar(API_ChargedSpells.PowerupSpell):
    def on_init(self):
        super(DracoPillar, self).on_init()
        self.level = 7
        self.range = 8
        self.max_charges = 2
        self.name = "Draconic Pillar"
        self.minion_duration = 20
        self.max_charge = 6
        self.minion_health = 75
        self.minion_range = 3
        self.shields = 2
        self.tags = [Level.Tags.Dragon, Level.Tags.Conjuration, Level.Tags.Fixation]
        self.must_target_empty = True
        self.must_target_walkable = True
        self.num_summons = 2
        self.charging_effect_color = Level.Tags.Fire.color
        self.stats.append('max_charge')

        self.upgrades['minion_duration'] = (10, 3)
        self.upgrades['minion_health'] = (40, 3)
        self.upgrades['awakened'] = (1, 6, "Awakened Pillar", "The pillar's dragons gain additional HP and SH based on turns spent charging the pillar. The dragons also gain range and damage bonuses to their breath attack and a damage bonus to melee attacks, both based on how long this spell charged.", "imbuement")
        self.upgrades['enchanted'] = (1, 8, "Enchanted Pillar", "The pillar gains the ability to heal all allied dragons excluding itself for 10 HP, and can enlighten them with the power of a random element, giving them 100 resistance to that element and a ranged attack of that element", "imbuement")
        self.upgrades['swarm'] = (1, 7, "Scourge Pillar", "The pillar's bonus to number of summons as it charges increases, and its cooldown decreases by 2.", "imbuement")
    def get_description(self):
        return "Channel this spell for up to [{max_charge}_turns:max_charge]. On recast, summon a draconic pillar. The pillar has [{minion_health}_HP:minion_health], [{shields}_SH:shields], and a variety of resistances.\nThe pillar can summon dragons in 5 tiles of itself. It can intially summon [{num_summons}:num_summons] dragons.\nAs the spell charges, the number of dragons it can summon at a time increases.\nThe pillar vanishes after [{minion_duration}_turns:minion_duration].\nYou can only summon 1 pillar at a time, and the pillar can only be summoned while enemies exist in the current rift.".format(**self.fmt_dict())
    def can_cast(self, x, y):
        allies = [u for u in list(self.caster.level.units) if u.name == "Draconic Pillar" and not Level.are_hostile(u, self.caster)]
        enemies = [u for u in list(self.caster.level.units) if Level.are_hostile(u, self.caster)]
        return Level.Spell.can_cast(self, x, y) and len(allies) == 0 and len(enemies) > 0
    def on_cast(self, x, y, turns_charged):
        DracoPillar = Level.Unit()
        DracoPillar.name = "Draconic Pillar"
        DracoPillar.max_hp = self.get_stat('minion_health')
        DracoPillar.shields = self.get_stat('shields')
        DracoPillar.stationary = True
        DracoPillar.flying = False
        DracoPillar.team = self.caster.team
        DracoPillar.tags = [Level.Tags.Dragon, Level.Tags.Construct]
        for dtype in [Level.Tags.Ice, Level.Tags.Lightning, Level.Tags.Fire, Level.Tags.Arcane, Level.Tags.Poison]:
            DracoPillar.resists[dtype] = 75
        DracoPillar.asset_name = os.path.join("..","..","mods","ATGMChargePack","draco_pillar")
        pillar_summon = DracoPillarSummon()
        pillar_summon.num_summons = self.get_stat('num_summons') + ((turns_charged+1) // 3)
        DracoPillar.spells.append(pillar_summon)
        if self.get_stat('awakened'):
            pillar_summon.summon_awakened = True
            pillar_summon.pillar_charged_for = turns_charged + 1
        if self.get_stat('enchanted'):
            DracoPillar.spells.append(PillarHeal())
            DracoPillar.spells.append(PillarGrantSorcery())
        if self.get_stat('swarm'):
            pillar_summon.num_summons += (turns_charged + 1) // 2
            pillar_summon.cool_down -= 2
        DracoPillar.turns_to_death = self.get_stat('minion_duration')
        self.summon(DracoPillar, Level.Point(x, y))
        yield

class PillarHeal(Level.Spell):

    def on_init(self):
        self.name = "Mend Scales"
        self.cool_down = 4
        self.range = 0
        self.description = "Heal all dragon allies for 10"

        self.tags = [Level.Tags.Heal]

    def cast_instant(self, x, y):
        for u in self.caster.level.units:
            if not Level.are_hostile(u, self.caster) and Level.Tags.Dragon in u.tags and u.name != "Draconic Pillar":
                u.deal_damage(-10, Level.Tags.Heal, self)

class PillarTouchedBySorcery(Level.Buff):

    def __init__(self, element):
        self.element = element
        Level.Buff.__init__(self)

    def on_init(self):
        self.resists[self.element] = 100
        self.name = "Enlightened by %s" % self.element.name
        self.color = self.element.color
        spell = CommonContent.SimpleRangedAttack(damage=11, range=9, radius=2, damage_type=self.element)
        spell.name = "Dracosorcery"
        self.spells = [spell]

class PillarGrantSorcery(Level.Spell):

    def on_init(self):
        self.name = "Grant Draconic Sorcery"
        self.range = 99
        self.requires_los = False

    def get_description(self):
        return "Grants a ranged attack of a random element to a random dragon ally, along with immunity to that element."

    def get_ai_target(self):
        candidates = [u for u in self.caster.level.units if not Level.are_hostile(u, self.caster) and not u.has_buff(PillarTouchedBySorcery) and Level.Tags.Dragon in u.tags and u.name != "Draconic Pillar"]
        if not candidates:
            return None
        return random.choice(candidates)

    def can_cast(self, x, y):
        return True

    def cast_instant(self, x, y):

        unit = self.caster.level.get_unit_at(x, y)
        if not unit:
            return

        element = random.choice([Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Ice, Level.Tags.Dark, Level.Tags.Holy, Level.Tags.Arcane, Level.Tags.Poison, Level.Tags.Physical])

        buff = PillarTouchedBySorcery(element)
        unit.apply_buff(buff)

        self.caster.level.show_path_effect(self.caster, unit, element, minor=True)

class DracoPillarSummon(Level.Spell):
    def on_init(self):
        self.name = "Call Kin"
        self.range = 0
        self.cool_down = 9
        self.num_summons = 0
        self.summon_awakened = False
        self.pillar_charged_for = 0
    def get_description(self):
        return "Summons {num_summons} random drakes".format(**self.fmt_dict())
    def cast_instant(self, x, y):
        for i in range(self.num_summons):
            p = self.caster.level.get_summon_point(self.caster.x, self.caster.y, radius_limit=5, sort_dist=False, flying=True)
            if p:
                drake = random.choice([Monsters.FireDrake, Monsters.StormDrake, Monsters.VoidDrake, Monsters.GoldDrake, Monsters.IceDrake])
                drake = drake()
                if self.summon_awakened:
                    drake.max_hp += 8*self.pillar_charged_for
                    drake.shields += min(2, self.pillar_charged_for // 3)
                    drake.spells[0].range += self.pillar_charged_for // 2
                    drake.spells[0].damage += math.floor(self.pillar_charged_for*1.75)
                    drake.spells[1].damage += self.pillar_charged_for*2
                drake.team = self.caster.team
                self.caster.level.add_obj(drake, p.x, p.y)

class DarkDragon(API_ChargedSpells.IncantationSpell):
    def on_init(self):
        super(DarkDragon, self).on_init()
        self.name = "Dark Dragon"
        self.range = 8
        self.max_charges = 1
        self.level = 8
        self.required_charge = 5
        self.tags = [Level.Tags.Dark, Level.Tags.Conjuration, Level.Tags.Dragon, Level.Tags.Invocation]
        self.minion_health = 80
        self.minion_range = 8
        self.minion_damage = 18
        self.must_target_empty = True
        self.must_target_walkable = False
        self.charging_effect_color = Level.Tags.Dark.color
        self.stats.append('required_charge')

        self.upgrades['minion_damage'] = (14, 2)
        self.upgrades['minion_health'] = (20, 3)
        self.upgrades['minion_range'] = (3, 3)
        self.upgrades['energy'] = (1, 5, "Energy Reap", "Each time the dark dragon kills an enemy, all of its abilities gain 2 damage and the dragon gains 5 max HP.", "dark arts")
        self.upgrades['mortal'] = (1, 6, "Timeless Secrets", "The dark dragon can grant dragon allies excluding itself immortality that prevents them from dying as long as the dragon is alive.", "dark arts")
    def get_description(self):
        return "Channel the spell for [{required_charge}_turns:required_charge], then summon a powerful [dark] [dragon].\nThe dragon has [{minion_health}_HP:minion_health] and a [dark] breath attack that deals [{minion_damage}_damage:minion_damage] and raises slain units as skeletons, and a melee attack dealing [{minion_damage}_damage:minion_damage].\nYou can only summon 1 dark dragon at a time, and the dragon can only be summoned while enemies exist in the current rift.".format(**self.fmt_dict())
    def can_cast(self, x, y):
        allies = [u for u in list(self.caster.level.units) if u.name == "Dark Dragon" and not Level.are_hostile(u, self.caster)]
        enemies = [u for u in list(self.caster.level.units) if Level.are_hostile(u, self.caster)]
        return Level.Spell.can_cast(self, x, y) and len(allies) == 0 and len(enemies) > 0
    def on_cast(self, x, y):
        DarkDraco = Monsters.Dracolich()
        DarkDraco.name = "Dark Dragon"
        DarkDraco.max_hp = self.get_stat('minion_health')
        DarkDraco.spells.pop(0)
        DarkDraco.spells[0].damage = self.get_stat('minion_damage')
        DarkDraco.spells[0].range = self.get_stat('minion_range')
        DarkDraco.spells[1].damage = self.get_stat('minion_damage')
        if self.get_stat('energy'):
            DarkDraco.buffs.append(EnergyReapBuff(2, 5))
        if self.get_stat('mortal'):
            DarkDraco.spells.append(DracoImmortality())
        self.summon(DarkDraco, Level.Point(x, y))
        yield

class EnergyReapBuff(Level.Buff):
    def __init__(self, magnitude, healing):
        Level.Buff.__init__(self)
        self.name = "Energy Harvestry"
        self.magnitude = magnitude
        self.healing = healing
    def on_applied(self, owner):
        self.global_triggers[Level.EventOnDamaged] = self.on_damaged
    def get_tooltip(self):
        return "Gains %d damage to all abilities and %d max HP every time an enemy dies" % (self.magnitude, self.healing)
    def on_damaged(self, damage_event):
        if self.owner.level.are_hostile(self.owner, damage_event.unit) and damage_event.unit.cur_hp <= 0:
            self.owner.max_hp += self.healing
            self.owner.cur_hp += self.healing
            for ability in self.owner.spells:
                if ability.get_stat('damage'):
                    ability.damage += self.magnitude

class DracoImmortality(Level.Spell):

    def on_init(self):
        self.name = "Draconic Immortality"
        self.range = 99

    def get_description(self):
        return "A dragon ally cannot die until this unit is destroyed."

    def get_ai_target(self):
        candidates = [u for u in self.caster.level.units if not Level.are_hostile(u, self.caster) and not u.has_buff(CommonContent.Soulbound) and Level.Tags.Dragon in u.tags and u.name != "Dark Dragon"]
        candidates = [u for u in candidates if self.can_cast(u.x, u.y)]
        
        if not candidates:
            return None
        return random.choice(candidates)

    def cast(self, x, y):

        for p in self.caster.level.get_points_in_line(self.caster, Level.Point(x, y), find_clear=True)[1:-1]:
            self.caster.level.deal_damage(p.x, p.y, 0, Level.Tags.Dark, self)
            yield

        unit = self.caster.level.get_unit_at(x, y)
        if not unit:
            return
        
        buff = CommonContent.Soulbound(self.caster)
        buff.name = "Protected by Darkness"
        unit.apply_buff(buff)

class SummonJormungandr(API_ChargedSpells.IncantationSpell):
    def on_init(self):
        super(SummonJormungandr, self).on_init()
        self.name = "Ragnarok"
        self.range = 8
        self.max_charges = 1
        self.level = 8
        self.required_charge = 9
        self.tags = [Level.Tags.Chaos, Level.Tags.Conjuration, Level.Tags.Dragon, Level.Tags.Invocation]
        self.minion_health = 130
        self.minion_damage = 36
        self.damage = 29
        self.radius = 2
        self.num_targets = 15
        self.chaos_buff_targets = 3
        self.must_target_empty = True
        self.must_target_walkable = True
        self.charging_effect_color = Level.Tags.Physical.color
        self.stats.append('required_charge')
        self.stats.append('chaos_buff_targets')

        self.upgrades['chaos_buff_targets'] = (3, 3, "Chaos Force", "Jormungandr's passive damage buff can target an additional 3 enemies.")
        self.upgrades['tongue']  = (1, 7, "Mighty Tongue", "Jormungandr gains the Word of Atrocity ability.\nWord of Atrocity deals 30 [dark] damage to all [holy] enemies, 30 [holy] damage to all [dark] enemies, and randomly deals 30 [fire], [lightning] or [physical] damage to all other enemies and stuns all enemies for 3 turns.")
        self.upgrades['required_charge'] = (-3, 5, "Faster Summoning", "Ragnarok charges 3 turns faster.")
    def get_description(self):
        return ("Channel this spell for [{required_charge}_turns:required_charge].\n"
        "When charging finishes, rains balls of chaos on [{num_targets}_tiles:num_targets], dealing [{damage}:damage] [fire], [lightning], or [physical] damage in [{radius}_tiles:radius].\n"
        "Afterwards, summons Jormungandr, the wyrm of chaos, on a random empty tile. Jormungandr has [{minion_health}_HP:minion_health] and can breathe chaotic energy dealing [{minion_damage}:minion_damage], [fire], [lightning], or [physical] damage.\n"
        "Jormungandr also has a buff that passively deals [fire], [lightning], or [physical] damage to the [{chaos_buff_targets}:num_targets] nearest enemies equal to half of his breath damage.\n"
        "Jormungandr also passively regenerates 14 HP per turn.").format(**self.fmt_dict())
    def on_cast(self, x, y):
        spots = [t for t in self.caster.level.iter_tiles() if not self.caster.level.tiles[t.x][t.y].is_wall()]
        zones = random.sample(spots, self.get_stat('num_targets'))
        for z in zones:
            for stage in CommonContent.Burst(self.caster.level, z, self.get_stat('radius')):
                for point in stage:
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), random.choice([Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical]), self)
        Jormungandr = Level.Unit()
        Jormungandr.name = "Jormungandr, Wyrm of Chaos"
        Jormungandr.asset_name = os.path.join("..","..","mods","ATGMChargePack","jormungandr")
        Jormungandr.max_hp = self.get_stat('minion_health')
        Jormungandr.resists[Level.Tags.Fire] = 100
        Jormungandr.resists[Level.Tags.Physical] = 100
        Jormungandr.resists[Level.Tags.Lightning] = 100
        Jormungandr.resists[Level.Tags.Ice] = 100
        Jormungandr.tags = [Level.Tags.Chaos, Level.Tags.Dragon, Level.Tags.Living]
        if self.get_stat('tongue'):
            Jormungandr.spells.append(WordOfAtrocity())
        breath = JormungandrWave()
        breath.damage = self.get_stat('minion_damage')
        breath.range = 9
        breath.cool_down = 3
        Jormungandr.spells.append(breath)
        Jormungandr.buffs.append(JormungandrChaosBuff((self.get_stat('minion_damage') // 2), self.get_stat('chaos_buff_targets')))
        Jormungandr.buffs.append(CommonContent.RegenBuff(14))
        spots = [s for s in spots if self.caster.level.can_stand(s.x, s.y, Jormungandr)]
        spot = random.choice(spots)
        self.summon(Jormungandr, Level.Point(spot.x, spot.y))
        yield

class JormungandrWave(Monsters.BreathWeapon):
    def on_init(self):
        self.name = "End Breath"
        self.damage = 0
        self.range = 10
        self.cool_down = 2
        self.requires_los = True
    def get_description(self):
        return "Deals [fire], [lightning], or [physical] damage in a cone.".format(**self.fmt_dict())
    def per_square_effect(self, x, y):
        dtypes = [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical]
        dtype = random.choice(dtypes)
        self.caster.level.deal_damage(x, y, self.get_stat('damage'), dtype, self)
    def cast(self, x, y):
        yield from Monsters.BreathWeapon.cast(self, x, y)

class WordOfAtrocity(Level.Spell):
    def on_init(self):
        self.name = "Word of Atrocity"
        self.damage = 30
        self.cool_down = 22
        self.range = 0
        self.requires_los = False
    def cast(self, x, y):
        for u in [u for u in list(self.caster.level.units) if Level.are_hostile(u, self.caster)]:
            if Level.Tags.Holy in u.tags:
                self.caster.level.deal_damage(u.x, u.y, self.get_stat('damage'), Level.Tags.Dark, self)
            elif Level.Tags.Dark in u.tags:
                self.caster.level.deal_damage(u.x, u.y, self.get_stat('damage'), Level.Tags.Holy, self)
            else:
                self.caster.level.deal_damage(u.x, u.y, self.get_stat('damage'), random.choice([Level.Tags.Fire, Level.Tags.Physical, Level.Tags.Lightning]), self)
            u.apply_buff(Level.Stun(), 3)
            yield
    def get_description(self):
        return "Deals 30 [dark] damage to all [holy] enemies, 30 [holy] damage to all [dark] enemies, and randomly deals 30 [fire], [lightning] or [physical] damage to all other enemies and stuns all enemies for 3 turns."

class JormungandrChaosBuff(Level.Buff):
    def __init__(self, strength, targets):
        Level.Buff.__init__(self)
        self.name = "Chaos Force"
        self.strength = strength
        self.targets = targets
        self.cur_targets = 0
    def get_tooltip(self):
        return "Each turn, deals %d fire, lightning, or physical damage to the %d nearest enemies" % (self.strength, self.targets)
    def on_advance(self):
        tiles = [t for t in self.owner.level.iter_tiles()]
        random.shuffle(tiles)
        tiles.sort(key=lambda u: Level.distance(self.owner, u))
        for t in tiles:
            u = self.owner.level.get_unit_at(t.x, t.y)
            if u and Level.are_hostile(u, self.owner):
                if self.cur_targets < self.targets:
                    dtype = random.choice([Level.Tags.Fire, Level.Tags.Physical])
                    self.owner.level.deal_damage(u.x, u.y, self.strength, dtype, self)
                    self.cur_targets += 1
        self.cur_targets = 0

class SpiritBladeDebuff(Level.Buff):
    def __init__(self, dpt, spell):
        Level.Buff.__init__(self)
        self.stack_type = Level.STACK_DURATION
        self.damage = dpt
        self.spell = spell
        self.color = Level.Color(240, 98, 146)
        self.name = "Spirit Drain"
        self.buff_type = Level.BUFF_TYPE_CURSE
        self.global_triggers[Level.EventOnDeath] = self.on_death
        self.description = "Takes %d [arcane] damage each turn" % self.damage

    def on_advance(self):
        self.owner.deal_damage(self.damage, Level.Tags.Arcane, self)
        if self.spell.get_stat('sorrows'):
            self.owner.deal_damage(self.damage, Level.Tags.Dark, self)
            self.owner.deal_damage(self.damage, Level.Tags.Physical, self)

    def on_applied(self, owner):
        self.global_triggers[Level.EventOnDeath] = self.on_death
    
    def on_death(self, evt):
        if evt.unit != self.owner:
            return
        if self.spell.get_stat('shackle'):
            haunter = Monsters.VampireMist()
            haunter.name = "Aether Ghost"
            haunter.max_hp = 20
            haunter.team = self.owner.level.player_unit.team
            haunter.is_coward = False
            aura = CommonContent.DamageAuraBuff(damage=4, damage_type=[Level.Tags.Arcane, Level.Tags.Physical], radius=3)
            aura.name = "Aether Aura"
            haunter.buffs.clear()
            haunter.resists[Level.Tags.Arcane] = 100
            haunter.resists[Level.Tags.Fire] = 0
            haunter.buffs.append(aura)
            haunter.buffs.append(CommonContent.ReincarnationBuff(1))
            haunter.spells.clear()
            if len(evt.unit.spells) > 0:
                haunter.spells.insert(0, evt.unit.spells[0])
            p = self.owner.level.get_summon_point(evt.unit.x, evt.unit.y, radius_limit=5, sort_dist=False, flying=True)
            if p:
                self.owner.level.add_obj(haunter, p.x, p.y)
        elif self.spell.get_stat('crusader'):
            for spell in [s for s in self.owner.level.player_unit.spells if Level.Tags.Holy in s.tags]:
                if random.random() < .1 and spell.cur_charges < spell.get_stat('max_charges'):
                    spell.cur_charges += 1   
        elif self.spell.get_stat('sorrows'):
            if random.random() < .2 and self.spell.cur_charges < self.spell.get_stat('max_charges') :
                self.spell.cur_charges += 1
        
class SpiritBlade(API_ChargedSpells.PowerupSpell):
    def on_init(self):
        super(SpiritBlade, self).on_init()
        self.name = "Spirit Blade"
        self.level = 4
        self.tags = [Level.Tags.Metallic, Level.Tags.Arcane, Level.Tags.Sorcery, Level.Tags.Fixation]
        self.max_charges = 6
        self.max_charge = 6
        self.damage = 10
        self.range = 8
        self.spirit_drain_damage = 3
        self.damage_charge_bonus = 3
        self.duration = 6
        self.stats.append('max_charge')
        self.stats.append('spirit_drain_damage')
        self.stats.append('damage_charge_bonus')

        self.upgrades['damage'] = (7, 3)
        self.upgrades['spirit_drain_damage'] = (3, 4)
        self.upgrades['shackle'] = (1, 6, "Aether Shackle", "Whenever an enemy dies to Spirit Blade, summon an Aether Ghost near the target tile.\nAether Ghosts have 20 HP, reincarnate once, and know the slain enemy's first spell if it has any.\nAether Ghosts also have an aura around them that deals 4 [arcane] or [physical] damage to units in 3 tiles.", "empowerment")
        self.upgrades['crusader'] = (1, 6, "Crusader's Sword", "Deal [holy] damage in a 2 tile burst around the target tile.\nSpirit Drain also deals [holy] damage in addition to its [arcane] damage.\nWhenever an enemy dies to Spirit Blade, each of your [holy] spells has a 10% chance to regain a charge.".format(**self.fmt_dict()), "empowerment")
        self.upgrades['sorrows'] = (1, 6, "Cursed Sword", "Spirit Drain deals [dark] and [physical] damage in addition to [arcane]. Spirit Blade has a 20% chance to regain a charge whenever an enemy dies to Spirit Drain.", "empowerment")

    def get_description(self):
        return ("Charge this spell for up to [{max_charge}_turns:max_charge].\n"
                "Spirit Blade gains [{damage_charge_bonus}_damage:damage] per turn charged.\n"
                "On recast, throw an enchanted sword at target enemy dealing [{damage}_arcane:arcane] and [{damage}_physical:physical] damage.\n"
                "Additionally, inflict Spirit Drain, dealing [{spirit_drain_damage}_arcane:arcane] damage per turn to the target for [{duration}_turns:duration].").format(**self.fmt_dict())
    def on_cast(self, x, y, turns_charged):
        for p in self.caster.level.get_points_in_line(Level.Point(x, y), Level.Point(self.caster.x, self.caster.y)):
            self.caster.level.show_effect(p.x, p.y, Level.Tags.Arcane, minor=True)
        dmg = self.get_stat('damage') + turns_charged*self.get_stat('damage_charge_bonus')
        u = self.caster.level.get_unit_at(x, y)
        self.caster.level.deal_damage(x, y, dmg, Level.Tags.Arcane, self)
        self.caster.level.deal_damage(x, y, dmg, Level.Tags.Physical, self)
        if self.get_stat('crusader'):
            for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), 2):
                for point in stage:
                    self.caster.level.deal_damage(point.x, point.y, dmg, Level.Tags.Holy, self)
        if u and Level.are_hostile(u, self.caster):
            if not u.is_alive() and self.get_stat('shackle'):
                haunter = Monsters.VampireMist()
                haunter.name = "Aether Ghost"
                haunter.max_hp = 20
                haunter.team = self.owner.team
                haunter.is_coward = False
                aura = CommonContent.DamageAuraBuff(damage=4, damage_type=[Level.Tags.Arcane, Level.Tags.Physical], radius=3)
                aura.name = "Aether Aura"
                haunter.buffs.clear()
                haunter.buffs.append(aura)
                haunter.buffs.append(CommonContent.ReincarnationBuff(1))
                haunter.spells.clear()
                if len(u.spells) > 0:
                    haunter.spells.insert(0, u.spells[0])
                else:
                    haunter.spells.append(CommonContent.SimpleMeleeAttack(4, damage_type=Level.Tags.Arcane))
                haunter.resists[Level.Tags.Arcane] = 100
                haunter.resists[Level.Tags.Fire] = 0
                p = self.owner.level.get_summon_point(u.x, u.y, radius_limit=5, sort_dist=False, flying=True)
                if p:
                    self.owner.level.add_obj(haunter, p.x, p.y)
                yield
            elif not u.is_alive() and self.get_stat('crusader'):
                for spell in [s for s in self.caster.spells if Level.Tags.Holy in s.tags]:
                    if random.random() < .1 and spell.cur_charges < spell.get_stat('max_charges'):
                        spell.cur_charges += 1   
            else:
                u.apply_buff(SpiritBladeDebuff(self.get_stat('spirit_drain_damage'), self))
        yield

class MagicDagger(API_ChargedSpells.IncantationSpell):
    def on_init(self):
        super(MagicDagger, self).on_init()
        self.name = "Magic Dagger"
        self.level = 1
        self.tags = [Level.Tags.Sorcery, Level.Tags.Metallic, Level.Tags.Invocation]
        self.damage = 8
        self.required_charge = 1
        self.range = 0
        self.max_charges = 16
        self.stats.append('required_charge')

        self.upgrades['damage'] = (12, 3)
        self.upgrades['required_charge'] = (-1, 2, "Instant Throwing", "Magic Dagger can be used instantly")
        self.upgrades['storm'] = (1, 8, "Dagger Storm", "Magic Dagger hits every enemy on the map")
    def get_description(self):
        return "Charge this spell for [{required_charge}_turns:required_charge], then magically stab the nearest enemy dealing [{damage}_physical:physical] damage.".format(**self.fmt_dict())
    def on_cast(self, x, y):
        tiles = [t for t in self.caster.level.iter_tiles()]
        random.shuffle(tiles)
        tiles.sort(key=lambda u: Level.distance(self.caster, u))
        for t in tiles:
            u = self.caster.level.get_unit_at(t.x, t.y)
            if u and Level.are_hostile(u, self.caster):
                self.caster.level.deal_damage(u.x, u.y, self.get_stat('damage'), Level.Tags.Physical, self)
                if self.get_stat('mithril'):
                    self.caster.level.deal_damage(u.x, u.y, (self.get_stat('damage') // 2), Level.Tags.Arcane, self)
                if not self.get_stat('storm'):
                    break
        yield

class IceTempest(Level.Cloud):
    def __init__(self, owner, duration, spell, radius, damage=5, freezedur=2):
        Level.Cloud.__init__(self)
        self.owner = owner
        self.duration = duration
        self.damage = damage
        self.color = Level.Color(100, 100, 100)
        self.name = "Ice Tempest"
        self.asset_name = "ice_cloud"
        self.freezedur = freezedur
        self.spell = spell
        self.radius = radius
        self.source = spell
    def get_description(self):
        return "Deals %d [ice] and [lightning] damage to enemy units inside and in a %d tile burst, and has a 75%% chance of freezing enemies inside for %d turns." % (self.damage, self.radius, self.freezedur)
    def on_advance(self):
        dtypes = [Level.Tags.Lightning, Level.Tags.Ice]
        u = self.level.get_unit_at(self.x, self.y)
        if u and Level.are_hostile(self.owner, u):
            for stage in CommonContent.Burst(self.level, Level.Point(self.x, self.y), self.radius):
                for point in stage:
                    for dtype in dtypes:
                        u = self.level.get_unit_at(point.x, point.y)
                        if not u:
                            self.level.deal_damage(point.x, point.y, self.damage, dtype, self.source or self)
                            continue
                        elif Level.are_hostile(self.owner, u):
                            self.level.deal_damage(point.x, point.y, self.damage, dtype, self.source or self)
                        else:
                            continue


class InvokeStorm(API_ChargedSpells.IncantationSpell):
    def on_init(self):
        super(InvokeStorm, self).on_init()
        self.name = "Grand Hail"
        self.level = 5
        self.tags = [Level.Tags.Ice, Level.Tags.Lightning, Level.Tags.Enchantment, Level.Tags.Invocation]
        self.damage = 4
        self.required_charge = 4
        self.radius = 3
        self.cloud_radius = 1
        self.freeze_duration = 3
        self.duration = 12
        self.range = 8
        self.max_charges = 4
        self.stats.append('required_charge')
        self.stats.append('cloud_radius')
        self.stats.append('freeze_duration')

        self.upgrades['cloud_radius'] = (1, 4, "Tempest Radius", "Tempests deal damage in a larger area.")
        self.upgrades['can_be_bound'] = (1, 4, "Cloud Carry", "Grand Hail can be cast anytime after being charged.")
        self.upgrades['duration'] = (6, 3)
        self.upgrades['radius'] = (1, 2)
    def get_description(self):
        return(
                "Charge this spell for [{required_charge}_turns:required_charge].\n"
                "When cast, summons ice tempests in [{radius}_tiles:radius].\n"
                "Ice tempests are enhanced blizzards that have a 75% chance to [freeze] enemies inside for [{freeze_duration}_turns:duration], and do not harm allies.\n"
                "These tempests deal {damage} [ice] and [lightning] damage to enemies inside and within a [{cloud_radius}_tile:radius] burst.\n"
                "Tempests last [{duration}_turns:duration]."
                ).format(**self.fmt_dict())
    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]
    def on_cast(self, x, y):
        for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for point in stage:
                cloud = IceTempest(self.caster, self.get_stat('duration'), self, self.get_stat('cloud_radius'), self.get_stat('damage'), self.get_stat('freeze_duration'))
                cloud.duration = self.get_stat('duration')
                self.caster.level.add_obj(cloud, point.x, point.y)
        yield


class BuildAmoeba(Level.Spell):
    def __init__(self, originspell):
        Level.Spell.__init__(self)
        self.originspell = originspell
    def on_init(self):
        self.name = "Construct Amoeba"
        self.cool_down = 0
        self.range = 0
        self.required_drops_to_build = 7
        self.radius = 6
    def get_description(self):
        return "Takes in %d droplets within %d tiles of this unit, including this unit, and constructs an amoeba from them on this unit's tile." % (self.required_drops_to_build, self.radius)
    def can_cast(self, x, y):
        points = [p for stage in CommonContent.Burst(self.caster.level, Level.Point(self.caster.x, self.caster.y), self.get_stat('radius')) for p in stage]
        units = [self.caster.level.get_unit_at(p.x, p.y) for p in points]
        units = [u for u in units if u]
        units = [u for u in units if not self.caster.level.are_hostile(self.caster, u) and u.name == "Amoeba Droplet"]
        return len(units) >= self.required_drops_to_build and len([u for u in self.caster.level.units if self.caster.level.are_hostile(self.caster, u)]) > 0
    def cast(self, x, y):
        deathcount = 0
        points = [p for stage in CommonContent.Burst(self.caster.level, Level.Point(self.caster.x, self.caster.y), self.get_stat('radius')) for p in stage]
        units = [self.caster.level.get_unit_at(p.x, p.y) for p in points]
        units = [u for u in units if u]
        units = [u for u in units if not self.caster.level.are_hostile(self.caster, u) and u.name == "Amoeba Droplet"]
        for unit in units:
            unit.kill()
            deathcount += 1
        amoeba = self.originspell.make_amoeba(deathcount)
        self.summon(amoeba, Level.Point(x, y))
        deathcount = 0
        yield


class DropletGenBuff(Level.Buff):

    def __init__(self, spawn_chance, originspell):
        Level.Buff.__init__(self)
        self.spawn_chance = spawn_chance
        self.originspell = originspell

    def on_advance(self):
        if random.random() < self.spawn_chance:
            open_points = list(self.owner.level.get_adjacent_points(Level.Point(self.owner.x, self.owner.y), check_unit=True))
            if not open_points:
                return
            p = random.choice(open_points)
            if self.originspell.get_stat('propagate'):
                new_monster = self.originspell.make_drop(True)
                new_monster.is_coward = False
            else:
                new_monster = self.originspell.make_drop()
            self.owner.level.add_obj(new_monster, p.x, p.y)

    def get_tooltip(self):
        return "Has a %d%% chance each turn to spawn a %s" % (int(100 * self.spawn_chance), self.originspell.make_drop().name)       




class AmoebaFuse(API_ChargedSpells.DualEffectSpell):
    def on_init(self):
        super(AmoebaFuse, self).on_init()
        self.name = "Amoeba Fusion"
        self.level = 2
        self.tags = [Level.Tags.Nature, Level.Tags.Conjuration, Level.Tags.Fixation]
        self.max_charges = 4
        self.max_charge = 4
        self.num_summons = 2
        self.minion_damage = 6
        self.minion_health = 14
        self.minion_range = 6
        self.hp_per_droplet = 2
        self.damage_per_droplet = 1
        self.deathcount = 0
        self.stats.append('max_charge')
        self.stats.append('damage_per_droplet')
        self.stats.append('hp_per_droplet')

        self.upgrades['hp_per_droplet'] = (3, 2)
        self.upgrades['num_summons'] = (1, 3)
        self.upgrades['propagate'] = (1, 7, "Self-Propagation", "Amoebae passively spawn droplets each turn at a 60% chance.\nSpawned droplets have group awareness and will automatically build themselves into an amoeba provided enough other droplets are nearby.")
    def get_description(self):
        return (
                "Charge this spell for up to [{max_charge}_turns:max_charge].\n"
                "While charging, summon [{num_summons}:num_targets] amoeba droplets in 3 tiles of target tile. These droplets have 1 HP and flee from enemies.\n"
                "On recast, kill all allied amoeba droplets and summon an amoeba in their place. The amoeba starts with [{minion_health}_HP:minion_health], [{minion_damage}_ability_damage:minion_damage], and [{minion_range}_ability_range:minion_range].\n"
                "The amoeba gains [{hp_per_droplet}_HP:heal] and [{damage_per_droplet}_ability_damage:damage] per droplet that was killed.\n"
                "The amoeba has a [poison] trampling melee attack as well as a ranged [physical] attack."
                ).format(**self.fmt_dict())
    def make_drop(self, propagator=False):
        drop = Level.Unit()
        drop.name = "Amoeba Droplet"
        drop.max_hp = 1
        drop.is_coward = True
        drop.team = self.caster.team
        drop.flying = False
        drop.asset_name = os.path.join("..","..","mods","ATGMChargePack","amoeba_gel")
        if propagator:
            drop.spells.append(BuildAmoeba(self))
        return drop
    def make_amoeba(self, modifier):
        amoeba = Level.Unit()
        amoeba.name = "Amoeba"
        amoeba.max_hp = self.get_stat('minion_health') + modifier*self.get_stat('hp_per_droplet')
        amoeba.team = self.caster.team
        amoeba.flying = False
        amoeba.asset_name = os.path.join("..","..","mods","ATGMChargePack","amoeba")
        dmg = self.get_stat('minion_damage') + modifier*self.get_stat('damage_per_droplet')
        melee = CommonContent.SimpleMeleeAttack(damage=dmg, buff=CommonContent.Poison, buff_duration=18, damage_type=Level.Tags.Poison, trample=True)
        melee.name = "Engulf"
        ranged = CommonContent.SimpleRangedAttack(name="Matter Ejection", damage=dmg, range=self.get_stat('minion_range'), beam=True, radius=2)
        amoeba.spells = [melee, ranged]
        if self.get_stat('propagate'):
            amoeba.buffs.append(DropletGenBuff(.6, self))
        return amoeba
    def on_cast1(self, x, y, turns_charged, turns_remaining):
        t = self.caster.level.get_summon_point(x, y, radius_limit=3, sort_dist=False, flying=False)
        for i in range(self.get_stat('num_summons')):
            self.summon(self.make_drop(), t)
            yield
    def on_cast2(self, x, y, turns_charged):
        t = self.caster.level.get_summon_point(x, y, radius_limit=3, sort_dist=False, flying=False)
        for unit in [u for u in self.caster.level.units if not self.caster.level.are_hostile(u, self.caster) and u.name == "Amoeba Droplet"]:
            unit.kill()
            self.deathcount += 1
        self.summon(self.make_amoeba(self.deathcount), t)
        self.deathcount = 0
        yield

class ImpBurningBuff(Level.Buff):

    def __init__(self, damage, originspell):
        self.damage = damage
        self.originspell = originspell
        self.buff_type = Level.BUFF_TYPE_CURSE
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Burning (%d)" % self.damage
        self.description = "At end of this units turn, it takes %d damage and burning expires."
        self.asset = ['status', 'burning']

    def on_advance(self):
        self.owner.deal_damage(self.damage, Level.Tags.Fire, self)
        self.owner.remove_buff(self)

class CoalSwarm(API_ChargedSpells.PowerupSpell):
    def on_init(self):
        super(CoalSwarm, self).on_init()
        self.name = "Coal Imp Call"
        self.level = 4
        self.tags = [Level.Tags.Fire, Level.Tags.Dark, Level.Tags.Conjuration, Level.Tags.Fixation]
        self.max_charges = 2
        self.max_charge = 3
        self.num_summons = 3
        self.bonus_imps = 1
        self.minion_damage = 4
        self.minion_health = 5
        self.minion_range = 5
        self.minion_duration = 15
        self.stats.append('max_charge')
        self.stats.append('bonus_imps')

        self.upgrades['bonus_imps'] = (1, 4)
        self.upgrades['minion_range'] = (2, 3)
        self.upgrades['minion_damage'] = (2, 2)
        self.upgrades['fiend'] = (1, 9, "Coal Leadership", "Summons a coal fiend in addition to coal imps.\nThis fiend has [82_HP:minion_health], a [dark] ranged attack, a stronger coal attack, and can summon additional coal imps.\nThe fiend is also a permanent summon.")
    def make_imp(self):
        imp = Level.Unit()
        imp.name = "Coal Imp"
        imp.max_hp = self.get_stat('minion_health')
        imp.team = self.caster.team
        imp.flying = True
        imp.turns_to_death = self.get_stat('minion_duration')
        imp.asset_name = os.path.join("..","..","mods","ATGMChargePack","imp_coal")
        impshot = CommonContent.SimpleRangedAttack(name="Hot Coal", damage=self.get_stat('minion_damage'), damage_type=Level.Tags.Fire, range=self.get_stat('minion_range'))
        impshot.onhit = lambda caster, target: target.apply_buff(ImpBurningBuff(self.get_stat('minion_damage')//2, self))
        impshot.get_description = lambda: "Redeals half of this spell's damage again at the end of the target's next turn as [fire] damage."
        imp.spells.append(impshot)
        imp.resists[Level.Tags.Fire] = 100
        imp.resists[Level.Tags.Dark] = 75
        imp.resists[Level.Tags.Ice] = -100
        imp.resists[Level.Tags.Poison] = 0
        imp.tags = [Level.Tags.Fire, Level.Tags.Dark, Level.Tags.Demon]
        return imp
    def make_fiend(self):
        imp = Level.Unit()
        imp.name = "Coal Fiend"
        imp.max_hp = 82
        imp.team = self.caster.team
        imp.flying = False
        imp.asset_name = os.path.join("..","..","mods","ATGMChargePack","fiend_coal")
        impshot = CommonContent.SimpleRangedAttack(name="Coal Flare", damage=14, damage_type=Level.Tags.Fire, range=8, radius=2)
        impshot.onhit = lambda caster, target: target.apply_buff(ImpBurningBuff(self.get_stat('minion_damage'), self))
        impshot.get_description = lambda: "Redeals this spell's damage again at the end of the target's next turn as [fire] damage."
        darkbolt = CommonContent.SimpleRangedAttack(name="Black Gaze", damage=8, damage_type=Level.Tags.Dark, range=17, beam=True)
        impcall = CommonContent.SimpleSummon(spawn_func=self.make_imp, num_summons=3, cool_down=8, duration=self.get_stat('minion_duration'))
        imp.spells = [impcall, impshot, darkbolt]
        imp.resists[Level.Tags.Fire] = 100
        imp.resists[Level.Tags.Dark] = 75
        imp.resists[Level.Tags.Ice] = -100
        imp.resists[Level.Tags.Poison] = 0
        imp.tags = [Level.Tags.Fire, Level.Tags.Dark, Level.Tags.Demon]
        return imp
    def get_description(self):
        return (
                "Charge this spell for up to [{max_charge}_turns:max_charge].\n"
                "On recast, summon [{num_summons}:num_targets] coal imps plus [{bonus_imps}_extra_imps:num_targets] per turn charged.\n"
                "Coal imps have [{minion_health}_HP:minion_health], and a [{minion_range}_range:minion_range] coal attack that deals [{minion_damage}:damage] [fire] damage and half of that again at the end of the target's turn.\n"
                "These imps also have 100 [fire] resist, 75 [dark] resist, -100 [ice] resist and can fly.\n"
                "All imps expire after [{minion_duration}_turns:minion_duration]."   
                ).format(**self.fmt_dict())
    def on_cast(self, x, y, turns_charged):
        num_imps = self.get_stat('num_summons') + turns_charged*self.get_stat('bonus_imps')
        if self.get_stat('fiend'):
            t = self.caster.level.get_summon_point(x, y, radius_limit=6, sort_dist=False, flying=False)
            self.summon(self.make_fiend(), t)
        for i in range(num_imps):
            t = self.caster.level.get_summon_point(x, y, radius_limit=6, sort_dist=False, flying=True)
            self.summon(self.make_imp(), t)
            yield
            
class VoidFlare(API_ChargedSpells.BoundSpell):
    def on_init(self):
        super(VoidFlare, self).on_init()
        self.name = "Void Flare"
        self.level = 3
        self.tags = [Level.Tags.Arcane, Level.Tags.Fire, Level.Tags.Sorcery, Level.Tags.Invocation]
        self.damage = 9
        self.required_charge = 4
        self.range = 7
        self.bound_range = 7
        self.radius = 3
        self.max_charges = 6
        self.requires_los = False
        self.walls_destroyed = 0
        self.stats.append('required_charge')

        self.upgrades['damage'] = (4, 2)
        self.upgrades['required_charge'] = (-2, 3)
        self.upgrades['range'] = (4, 2)
        self.upgrades['hungry'] = (1, 5, "Hungry Fire", "Each wall destroyed by Void Flare adds 1 damage to the next casting. Every 5 walls destroyed adds 1 radius to the next casting, up to a maximum of 3.")
    def get_impacted_tiles(self, x, y):
        radius = self.get_stat('radius')
        if self.get_stat('hungry'):
            radius = min((radius + (self.get_stat('walls_destroyed')//4)), (radius + 3))
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), radius, ignore_walls=True) for p in stage]
    def get_description(self):
        return(
                "Charge this spell for [{required_charge}_turns:required_charge]. Can be recast anytime after fully charging.\n"
                "On cast, creates a magical fire in the targeted area dealing [{damage}_arcane:arcane] and [{damage}_fire:fire] damage in a [{radius}_tile:radius] burst.\n"
                "This fire melts walls in the targeted area."
                ).format(**self.fmt_dict())
    def cast_bound(self, x, y, turns_charged):
        dtypes = [Level.Tags.Fire, Level.Tags.Arcane]
        radius = self.get_stat('radius')
        dmg = self.get_stat('damage')
        if self.get_stat('hungry'):
            dmg += self.get_stat('walls_destroyed')
            radius = min((radius + (self.get_stat('walls_destroyed')//4)), (radius + 3))
            self.walls_destroyed = 0
        for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), radius, ignore_walls=True):
            for point in stage:
                for dtype in dtypes:
                    self.caster.level.deal_damage(point.x, point.y, dmg, dtype, self)
                if self.caster.level.tiles[point.x][point.y].is_wall():
                    self.caster.level.make_floor(point.x, point.y)
                    self.walls_destroyed += 1
            yield

class SilverStream(API_ChargedSpells.IncantationSpell):
    def on_init(self):
        super(SilverStream, self).on_init()
        self.name = "Silver Stream"
        self.tags = [Level.Tags.Fire, Level.Tags.Holy, Level.Tags.Sorcery, Level.Tags.Metallic, Level.Tags.Invocation]
        self.range = 5
        self.required_charge = 4
        self.level = 2
        self.max_charges = 9
        self.damage = 6
        self.duration = 3
        self.angle = math.pi / 6.0
        self.can_target_self = False
        self.stats.append('required_charge')
        
        self.upgrades['lead'] = (1, 4, "Toxic Alloy", "Affected units take [poison] damage and are poisoned for [15_turns:duration].", "alloy")
        self.upgrades['gold'] = (1, 5, "Sacred Alloy", "All units take holy damage instead of just [demon] and [undead] units.", "alloy")
        self.upgrades['range'] = (2, 3)
        self.upgrades['required_charge'] = (-2, 4)
    def get_description(self):
        return (
                "Charge this spell for [{required_charge}_turns:required_charge].\n"
                "Deals [{damage}_fire:fire] and [{damage}_physical:physical] damage in a cone.\n"
                "[Demon] and [undead] units are dealt additional [holy] damage.\n"
                "[Stun] all affected units for [{duration}_turns:duration].\n"
                + text.stun_desc
                ).format(**self.fmt_dict())
    def get_impacted_tiles(self, x, y):
        return [p for stage in self.aoe(x, y) for p in stage]
    def aoe(self, x, y):
        origin = Level.get_cast_point(self.caster.x, self.caster.y, x, y)
        target = Level.Point(x, y)
        return CommonContent.Burst(self.caster.level, 
                    Level.Point(self.caster.x, self.caster.y), 
                    self.get_stat('range'), 
                    burst_cone_params=Level.BurstConeParams(target, self.angle), 
                    ignore_walls=self.get_stat('melt_walls'))
    def on_cast(self, x, y):
        dtypes = [Level.Tags.Fire, Level.Tags.Physical]
        if self.get_stat('lead'):
            dtypes.append(Level.Tags.Poison)
        if self.get_stat('gold'):
            dtypes.append(Level.Tags.Holy)
        for stage in self.aoe(x, y):
            for point in stage:
                u = self.caster.level.get_unit_at(point.x, point.y)
                if u:
                    u.apply_buff(Level.Stun(), self.get_stat('duration'))
                    if self.get_stat('lead'):
                        u.apply_buff(CommonContent.Poison(), 15)
                        self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Poison, self)
                    if Level.Tags.Demon in u.tags or Level.Tags.Undead in u.tags:
                        if not self.get_stat('sacred'):
                            self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Holy, self)
                for dtype in dtypes:
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)
                yield

#a test

class MagmaWeb(CommonContent.SpiderWeb):

    def __init__(self):
        CommonContent.SpiderWeb.__init__(self)
        self.name = "Magma Web"
        self.description = "Any non-spider unit entering the web takes [7_fire_damage:fire] and is stunned for 2 turns.\nThis destroys the web."
        self.duration = 20

        self.asset_name = 'web'

    def on_unit_enter(self, unit):
        if Level.Tags.Spider not in unit.tags:
            unit.apply_buff(Level.Stun(), 3)
            self.level.deal_damage(self.x, self.y, 7, Level.Tags.Fire, self.source or self)
            self.kill()

    def on_damage(self, dtype):
        pass

class MagmaWebs(API_ChargedSpells.IncantationSpell):
    def on_init(self):
        super(MagmaWebs, self).on_init()
        self.cool_down = 7
        self.name = "Magma Webs"
        self.tags = [Level.Tags.Fire]
        self.damage = 10
        self.required_charge = 4
        self.range = 7
        self.bound_range = 7
        self.radius = 4
        self.stats.append('required_charge')
    def get_description(self):
        return "Turns chasms into floors, then deals fire damage and summons magma webs in empty tiles in radius.\nMust be charged for [{required_charge}_turns:required_charge]."
    def on_cast(self, x, y):
        for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for point in stage:
                if self.caster.level.tiles[point.x][point.y].is_chasm:
                    self.caster.level.make_floor(point.x, point.y)
                self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Fire, self)
                unit = self.caster.level.get_unit_at(point.x, point.y)
                if not (unit or not self.caster.level.tiles[point.x][point.y].can_walk):
                    web = MagmaWeb()
                    web.owner = self.caster
                    web.source = self
                    self.caster.level.add_obj(web, point.x, point.y)
        yield

class SummonClay(API_ChargedSpells.IncantationSpell):
    def on_init(self):
        super(SummonClay, self).on_init()
        self.name = "Summon Clay"
        self.range = 4
        self.max_charges = 3
        self.level = 5
        self.required_charge = 4
        self.tags = [Level.Tags.Nature, Level.Tags.Conjuration, Level.Tags.Invocation]
        self.minion_health = 50
        self.minion_damage = 9
        self.must_target_empty = True
        self.must_target_walkable = True
        self.charging_effect_color = Level.Tags.Physical.color

        self.upgrades['minion_health'] = (20, 2)
        self.upgrades['api'] = (1, 6, "API Integration", "Clay gains access to Magma Webs.\nMagma Webs is a [invocation:invocation] spell that Clay must charge for [4_turns:invocation].\nMagma Webs turns chasms into floors, then deals [fire] damage and creates Magma Webs in a [4_tile_burst:radius] around the target.\nMagma Webs are immune to fire damage, deal [7_fire_damage:fire] on entry, and stun their victims for [2_turns:duration].")

    def get_description(self):
        return (
        "Charge this spell for [{required_charge}_turns:required_charge].\n"
        "When charging ends, summons Clay.\n"
        "He has [{minion_health}_HP:minion_health], 50 [fire] resist, 50 [physical] resist, and 75 [lightning] resist, regenerates [6_HP_per_turn:heal], and has [1_SH:shields].\n"
        "However, Clay cannot weave webs on his own like other spiders.\n"
        "He also has a trampling melee attack that deals [{minion_damage}_physical_damage:physical]."
        ).format(**self.fmt_dict())

    def make_clay(self):
        clay = Level.Unit()
        clay.asset_name = os.path.join("..","..","mods","ATGMChargePack","clay_spider")
        clay.name = "Clay"
        clay.max_hp = self.get_stat('minion_health')
        clay.shields = 1
        clay.tags = [Level.Tags.Living, Level.Tags.Spider]
        clay.resists[Level.Tags.Physical] = 50
        clay.resists[Level.Tags.Fire] = 50
        clay.resists[Level.Tags.Lightning] = 75
        clay.spells.append(CommonContent.SimpleMeleeAttack(damage=self.get_stat('minion_damage'), trample=True))
        clay.buffs.append(CommonContent.RegenBuff(6))
        if self.get_stat('api'):
            clay.spells.insert(0, MagmaWebs())
        return clay

    def on_cast(self, x, y):
        self.summon(self.make_clay(), Level.Point(x, y))
        yield

class PyroCloud(Level.Cloud):
    def __init__(self, owner, duration, spell, damage=5):
        Level.Cloud.__init__(self)
        self.owner = owner
        self.duration = duration
        self.damage = damage
        self.color = Level.Color(100, 100, 100)
        self.name = "Pyrostatic Cloud"
        self.asset_name = "fire_cloud"
        self.spell = spell
        self.source = spell
    def get_description(self):
        return "Deals %d [fire] and [lightning] damage to enemy units inside." % self.damage
    def on_advance(self):
        dtypes = [Level.Tags.Lightning, Level.Tags.Fire]
        u = self.level.get_unit_at(self.x, self.y)
        if u and Level.are_hostile(self.owner, u):
            for dtype in dtypes:
                self.level.deal_damage(u.x, u.y, self.damage, dtype, self.source or self)

class PyrostaticStorm(API_ChargedSpells.PowerupSpell):
    def on_init(self):
        super(PyrostaticStorm, self).on_init()
        self.name = "Pyrostatic Storm"
        self.level = 6
        self.tags = [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Enchantment, Level.Tags.Fixation]
        self.max_charges = 3
        self.max_charge = 3
        self.duration = 20
        self.range = 6
        self.radius = 1
        self.cloud_damage = 6
        self.max_charge = 4
        self.stats.append('max_charge')
        self.stats.append('cloud_damage')

        self.upgrades['max_charge'] = (2, 3)
        self.upgrades['radius'] = (1, 2)
        self.upgrades['cloud_damage'] = (2, 3)
        
    def get_description(self):
        return (
            "Summons pyrostatic clouds in a square extending [{radius}_tiles:radius] from the target point.\n"
            "The square extends an extra [1_tile:radius] away from the target point for every 3 turns charged.\n"
            "This spell can be charged for up to [{max_charge}_turns:max_charge].\n"
            "Pyrostatic clouds deal [{cloud_damage}:damage] [fire] and [lightning] damage to enemies standing in them.\n"
            "This damage is fixed and cannot be modified by skills, shrines, or spells.\n"
            "Pyrostatic clouds last [{duration}_turns:duration]."
            ).format(**self.fmt_dict())    
    def get_impacted_tiles(self, x, y):
        return self.owner.level.get_points_in_ball(x, y, self.get_stat('radius'), diag=True)
    def on_cast(self, x, y, turns_charged):
        rad = self.get_stat('radius') + (turns_charged // 3)
        for p in self.owner.level.get_points_in_ball(x, y, rad, diag=True):
            cloud = PyroCloud(self.caster, self.get_stat('duration'), self, self.get_stat('cloud_damage'))
            self.caster.level.add_obj(cloud, p.x, p.y)
        yield

#cheater stuff

class CheatSpell(Level.Spell):

    def on_init(self):
        self.range = 0
        self.max_charges = 99
        self.name = "Cheat"
        self.duration = 8

        self.tags = [Level.Tags.Sorcery]
        self.level = 1

        self.upgrades['max_charges'] = (1, 1)
        
    def cast_instant(self, x, y):
        self.caster.xp += 99

    def get_description(self):
        return ("Gain 99 SP.\n").format(**self.fmt_dict())

#blood magic

class NetherPact(API_ChargedSpells.IncantationSpell):
    def on_init(self):
        super(NetherPact, self).on_init()
        self.name = "Nether Pact"
        self.num_summons = 2
        self.health_sacrifice = 90
        self.tags = [Level.Tags.Sanguine, Level.Tags.Conjuration, Level.Tags.Invocation]
        self.minion_health = 47
        self.minion_damage = 10
        self.range = 5
        self.required_charge = 4
        self.level = 7
        self.max_charges = 3
        self.must_target_empty = True
        self.must_target_walkable = True
        self.stats.append('health_sacrifice')

        self.upgrades['minion_damage'] = (3, 2)
        self.upgrades['health_sacrifice'] = (-20, 3)
        self.upgrades['required_charge'] = (-1, 3)
    def get_description(self):
        return (
                "Sacrifice [{health_sacrifice}_HP:health_sacrifice] and charge this spell for [{required_charge}_turns:required_charge].\n"
                "When charging ends, summon [{num_summons}:num_summons] each of chillgrave knights, dread knights, and knight officiants in 4 tiles of target tile.\n"
                "Each knight is a [sanguine] creature with a variety of resistances and abilities.\n"
                "All knights have [{minion_health}_HP:minion_health] and most of their abilities deal [{minion_damage}_damage:minion_damage]."
                ).format(**self.fmt_dict())
    def make_knight(self, knightname):
        knight = Level.Unit()
        knight.max_hp = self.get_stat('minion_health')
        knight.team = self.caster.team
        knight.resists[Level.Tags.Sanguine] = 100
        if knightname == "dread":
            knight.name = "Dread Knight"
            knight.asset_name = os.path.join("..","..","mods","ATGMChargePack","dread_knight")
            leap = CommonContent.LeapAttack(damage=self.get_stat('minion_damage'), range=6, damage_type=Level.Tags.Sanguine, is_ghost=False)
            leap.name = "Blood Charge"
            bolt = CommonContent.SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=8, damage_type=Level.Tags.Sanguine, beam=True, radius=1, drain=True)
            bolt.name = "Crimson Tide"
            bolt.cool_down = 3
            knight.tags = [Level.Tags.Dark, Level.Tags.Sanguine, Level.Tags.Living]
            knight.spells = [bolt, leap]
            for dtype in [Level.Tags.Dark, Level.Tags.Poison, Level.Tags.Holy]:
                knight.resists[dtype] = 50
            knight.buffs.append(CommonContent.DamageAuraBuff(damage=5, damage_type=[Level.Tags.Dark], radius=5))
        elif knightname == "chillgrave":
            knight.name = "Chillgrave Knight"
            knight.asset_name = os.path.join("..","..","mods","ATGMChargePack","chillgrave")
            knight.buffs.append(Monsters.NecromancyBuff())
            leap = CommonContent.LeapAttack(damage=self.get_stat('minion_damage'), range=15, damage_type=Level.Tags.Dark, charge_bonus=1, is_ghost=True)
            leap.cool_down = 4
            leap.name = "Death Flash"
            bolt = CommonContent.SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=5, damage_type=[Level.Tags.Ice, Level.Tags.Sanguine], radius=2)
            bolt.name = "Cold Blood"
            knight.spells = [leap, bolt]
            knight.tags = [Level.Tags.Ice, Level.Tags.Dark, Level.Tags.Sanguine, Level.Tags.Living]
            for dtype in [Level.Tags.Dark, Level.Tags.Ice, Level.Tags.Poison]:
                knight.resists[dtype] = 75
            knight.resists[Level.Tags.Holy] = -50
        elif knightname == "officiant":
            knight.name = "Knight Officiant"
            knight.asset_name = os.path.join("..","..","mods","ATGMChargePack","officiant")
            knight.buffs.append(CommonContent.RegenBuff(7))
            burst = RadiantBurst()
            burst.radius = 7
            burst.cool_down = 2
            burst.damage = self.get_stat('minion_damage')
            leap = CommonContent.LeapAttack(damage=self.get_stat('minion_damage'), range=8, damage_type=Level.Tags.Holy, charge_bonus=3, is_ghost=False)
            leap.name = "Lordly Charge"
            leap.cool_down = 3
            knight.spells = [burst, leap]
            knight.tags = [Level.Tags.Holy, Level.Tags.Sanguine, Level.Tags.Living]
            for dtype in [Level.Tags.Dark, Level.Tags.Holy, Level.Tags.Poison]:
                knight.resists[dtype] = 100
        knight.resists[Level.Tags.Physical] = 50
        return knight
    def on_cast(self, x, y):
        for knight in ["dread", "chillgrave", "officiant"]:
            for i in range(self.get_stat('num_summons')):
                t = self.caster.level.get_summon_point(x, y, radius_limit=5, sort_dist=False, flying=False)
                knightmade = self.make_knight(knight)
                self.summon(knightmade, t)
        self.caster.cur_hp -= self.get_stat('health_sacrifice')
        yield

class Bloodball(API_ChargedSpells.PowerupSpell):
    def on_init(self):
        super(Bloodball, self).on_init()
        self.name = "Bloodball"
        self.radius = 3
        self.damage = 6
        self.level = 1
        self.tags = [Level.Tags.Sanguine, Level.Tags.Sorcery, Level.Tags.Fixation]
        self.range = 8
        self.max_charges = 13
        self.health_sacrifice = 3
        self.max_charge = 5 # this is how many turns the spell can charge for
        self.charging_effect_color = Level.Tags.Fire.color
        self.damage_per_turn_charged = 2
        self.stats.append('max_charge')
        self.stats.append('health_sacrifice')
        self.stats.append('damage_per_turn_charged')

        self.upgrades['health_sacrifice'] = (-2, 1)
        self.upgrades['damage_per_turn_charged'] = (1, 1, "Charging Damage")
        self.upgrades['radius'] = (1, 2)
    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]
    def get_description(self):
        return(
                "Siphon your own life force for up to [{max_charge}_turns:max_charge], losing [{health_sacrifice}_HP:health_sacrifice] per turn.\n"
                "On recast, throw a ball of blood dealing [{damage}_sanguine:sanguine] damage in [{radius}_tiles:radius].\n"
                "Gains [{damage_per_turn_charged}_damage:damage] per turn charged."
                ).format(**self.fmt_dict())
    def on_cast(self, x, y, turns_charged):
        self.caster.cur_hp -= turns_charged*self.get_stat('health_sacrifice')
        dmg = self.get_stat('damage') + self.damage_per_turn_charged*turns_charged
        for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for point in stage:
                self.caster.level.deal_damage(point.x, point.y, dmg, Level.Tags.Sanguine, self)
            yield

class AltarBuff(Level.Buff):
    def __init__(self, trigger, caster, strength, frenzydur, spell):
        Level.Buff.__init__(self)
        self.name = "Gore"
        self.trigger = trigger
        self.caster = caster
        self.strength = strength
        self.frenzydur = frenzydur
        self.spell = spell
        self.global_triggers[Level.EventOnDamaged] = self.on_damage
        self.cur_trigger = 0
    def get_tooltip(self):
        return "Whenever %d damage has been dealt to enemies that this unit can see, frenzy the caster, increasing damage by %d for %d turns" % (self.trigger, self.strength, self.frenzydur)
    def on_damage(self, evt):
        if not self.owner.level.are_hostile(self.caster, evt.unit) and self.owner.level.can_see(self.owner.x, self.owner.y, evt.unit.x, evt.unit.y):
            return
        self.cur_trigger += evt.damage
        while self.cur_trigger >= self.trigger:
            self.cur_trigger -= self.trigger
            if self.spell.get_stat('harmony'):
                for unit in [u for u in list(self.caster.level.units) if not Level.are_hostile(u, self.caster)]:
                    unit.apply_buff(CommonContent.BloodrageBuff(self.strength), self.frenzydur)
            else:
                self.caster.apply_buff(CommonContent.BloodrageBuff(self.strength), self.frenzydur)
            if self.spell.get_stat('torment'):
                unit = random.choice([Variants.DeathchillTormentor(), Monsters.GhostfireTormentor(), Monsters.FrostfireTormentor()])
                unit.max_hp = math.ceil(unit.max_hp*1.5)
                for s in unit.spells:
                    s.damage *= 2
                    if s.get_stat('radius'):
                        s.radius += 2
                        s.cool_down -=1
                    if "Soul Suck" in s.name:
                        s.range += 3
                        s.damage += 5
                unit.buffs.append(CommonContent.BloodrageBuff(self.strength))
                self.summon(unit)
            if self.spell.get_stat('judgment'):
                for unit in [u for u in list(self.caster.level.units) if Level.are_hostile(u, self.caster)]:
                    self.owner.level.deal_damage(unit.x, unit.y, 5, Level.Tags.Holy, self)

class BattleAltar(API_ChargedSpells.IncantationSpell):
    def on_init(self):
        super(BattleAltar, self).on_init()
        self.name = "Crimson Altar"
        self.level = 5
        self.tags = [Level.Tags.Sanguine, Level.Tags.Conjuration, Level.Tags.Invocation]
        self.max_charges = 7
        self.health_sacrifice = 66
        self.required_charge = 3 # this is how many turns the spell can charge for
        self.minion_health = 66
        self.minion_damage = 3
        self.shields = 2
        self.duration = 15
        self.required_damage_to_trigger = 75
        self.charging_effect_color = Level.Tags.Sanguine.color
        self.frenzy_strength = 7
        self.stats.append('required_charge')
        self.stats.append('health_sacrifice')
        self.stats.append('required_damage_to_trigger')
        self.stats.append('frenzy_strength')

        self.upgrades['required_damage_to_trigger'] = (-15, 3, "Altar Efficacy")
        self.upgrades['health_sacrifice'] = (-33, 3)
        self.upgrades['torment'] = (1, 6, "Pact of Torment", "When fully charged, the altar will summon a ghostfire, frostfire, or deathchill tormentor.\nThese tormentors are stronger than normal.", "pact")
        self.upgrades['harmony'] = (1, 5, "Pact of Harmony", "When fully charged, the altar will give the frenzy buff to all allies as well as the caster.", "pact")
        self.upgrades['judgment'] = (1, 5, "Pact of Judgment", "When fully charged, the altar will deal 5 [holy] damage to all enemies on the map.", "pact")
    def get_description(self):
        return(
                "Sacrifice [{health_sacrifice}_HP:health_sacrifice] and charge this spell for [{required_charge}_turns:required_charge].\n"
                "On cast, summons a blood altar. The altar has [{minion_health}_HP:minion_health] and [{shields}_SH:shields].\n"
                "Whenever an enemy that the altar can see takes damage, the altar charges for that amount.\n"
                "When [{required_damage_to_trigger}_damage:damage] has been dealt to enemies, the altar loses all charge.\n"
                "The caster is frenzied for [{duration}_turns:duration], increasing damage by [{frenzy_strength}:sanguine]."
                ).format(**self.fmt_dict())
    def on_cast(self, x, y):
        target = Level.Point(x, y)
        Altar = Level.Unit()
        Altar.asset_name = os.path.join("..","..","mods","ATGMChargePack","gore_altar")
        Altar.name = "Blood Altar"
        Altar.max_hp = self.get_stat('minion_health')
        Altar.shields = self.get_stat('shields')
        Altar.tags = [Level.Tags.Sanguine, Level.Tags.Construct]
        Altar.stationary = True
        for tag in [Level.Tags.Physical, Level.Tags.Dark, Level.Tags.Sanguine]:
            Altar.resists[tag] = 75
        Altar.buffs.append(AltarBuff(self.get_stat('required_damage_to_trigger'), self.caster, self.get_stat('frenzy_strength'), self.get_stat('duration'), self))
        self.caster.cur_hp -= self.get_stat('health_sacrifice')
        self.summon(Altar, target)
        yield

class WordSacrifice(API_ChargedSpells.IncantationSpell):
    def on_init(self):
        super(WordSacrifice, self).on_init()
        self.name = "Word of Sacrifice"
        self.level = 7
        self.tags = [Level.Tags.Word, Level.Tags.Sanguine, Level.Tags.Invocation]
        self.max_charges = 1
        self.range = 0
        self.health_remaining = 1
        self.required_charge = 2
        self.charging_effect_color = Level.Tags.Sanguine.color
        self.stats.append('health_remaining')
        self.stats.append('required_charge')

        self.upgrades['max_charges'] = (1, 2)
    def get_description(self):
        return (
                "Sacrifice all but [{health_remaining}:sanguine] of your HP and charge this spell for [{required_charge}_turns:required_charge].\n"
                "When charging ends, deal half of the HP you lost as [sanguine] damage to all enemies.\n"
                "This spell cannot be cast if you are at 1 HP, but it will always deal at least 1 damage."
                ).format(**self.fmt_dict())
    def can_cast(self, x, y):
        return self.caster.cur_hp > 1
    def get_impacted_tiles(self, x, y):
        return [u for u in self.caster.level.units if u != self.caster and self.caster.level.are_hostile(u, self.caster)]
    def on_cast(self, x, y):
        dmg = (self.caster.cur_hp - 1) // 2
        if dmg <= 0:
            dmg += 1
        for unit in [u for u in self.caster.level.units if u != self.caster and self.caster.level.are_hostile(u, self.caster)]:
            self.caster.level.deal_damage(unit.x, unit.y, dmg, Level.Tags.Sanguine, self)
        self.caster.cur_hp = 1
        yield

class SoulSever(API_ChargedSpells.PowerupSpell):
    def on_init(self):
        super(SoulSever, self).on_init()
        self.name = "Soul Sever"
        self.level = 5
        self.tags = [Level.Tags.Sorcery, Level.Tags.Sanguine, Level.Tags.Fixation]
        self.max_charges = 7
        self.range = 7
        self.max_charge = 5
        self.damage = 5
        self.health_sacrifice = 6
        self.charging_effect_color = Level.Tags.Sanguine.color
        self.stats.append('max_charge')
        self.stats.append('health_sacrifice')

        self.upgrades['health_sacrifice'] = (-2, 1)
        self.upgrades['max_charges'] = (3, 3)
        self.upgrades['transfusion'] = (1, 4, "Transfusion", "Gives the removed spell to a random ally.\nThen, sorts their spells in order of highest cooldown to lowest.", "power")
        self.upgrades['crackdown'] = (1, 4, "Crackdown", "Reduces the damage of the enemy's other spells by 4.", "power")
    def get_description(self):
        return (
                "Charge this spell for up to [{max_charge}_turns:max_charge].\n"
                "On recast, sacrifice [{health_sacrifice}_HP:health_sacrifice] per turn charged and remove the enemy's first spell.\n"
                "Also, deal [{damage}:damage] [sanguine] damage to the enemy per turn charged."
                ).format(**self.fmt_dict())
    def on_cast(self, x, y, turns_charged):
        u = self.caster.level.get_unit_at(x, y)
        self.caster.level.deal_damage(u.x, u.y, (self.get_stat('damage')*turns_charged), Level.Tags.Sanguine, self)
        if u:
            if len(u.spells) > 0 and Level.are_hostile(u, self.caster):
                removed = u.spells.pop(0)
            else:
                removed = None
            if self.get_stat('crackdown') and removed:
                for s in u.spells:
                    if s.get_stat('damage'):
                        s.damage -= 4
            if self.get_stat('transfusion') and removed:
                ally = random.choice([u for u in self.caster.level.units if not Level.are_hostile(self.caster, u) and u != self.caster])
                ally.spells.append(removed)
                ally.spells.sort(reverse=True, key=lambda x: x.cool_down)
        self.caster.cur_hp -= self.get_stat('health_sacrifice')
        yield

class VariableCopy(Level.Buff):
    def __init__(self, spell, tags, name, statstr):
        self.spell = spell
        self.affected_tags = tags
        self.statstr = statstr
        self.set_name = name
        self.color = tags[0].color
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.asset = ['status', 'multicast']
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = self.set_name
        self.can_copy = True
        self.description = "Copy spells from the following tags:\n"
        for tag in self.affected_tags:
            self.description += "%s\n" % tag.name
        self.owner_triggers[Level.EventOnSpellCast] = self.on_spell_cast

    def on_spell_cast(self, evt):
        if evt.spell.item:
            return
        common = [t for t in evt.spell.tags if t in self.affected_tags]
        if self.can_copy and len(common) > 0:
            self.can_copy = False
            for i in range(self.spell.get_stat(self.statstr)):
                if evt.spell.can_cast(evt.x, evt.y) and evt.spell.can_pay_costs():
                    evt.caster.level.act_cast(evt.caster, evt.spell, evt.x, evt.y, pay_costs=False)
            evt.caster.level.queue_spell(self.reset())

    def reset(self):
        self.can_copy = True
        yield

class BloodSimulacrum(API_ChargedSpells.IncantationSpell):
    def on_init(self):
        super(BloodSimulacrum, self).on_init()
        self.name = "Sanguine Simulacrum"
        self.level = 6
        self.tags = [Level.Tags.Enchantment, Level.Tags.Sanguine, Level.Tags.Invocation]
        self.max_charges = 1
        self.range = 0
        self.required_charge = 6
        self.health_sacrifice = 50
        self.num_copies = 1
        self.duration = 2
        self.charging_effect_color = Level.Tags.Sanguine.color
        self.stats.append('required_charge')
        self.stats.append('health_sacrifice')

        self.upgrades['num_copies'] = (1, 3)
        self.upgrades['duration'] = (2, 3)
        self.upgrades['health_sacrifice'] = (-10, 3)
    def get_description(self):
        return (
                "Sacrifice [{health_sacrifice}_HP:sanguine] and charge this spell for [{required_charge}_turns:required_charge].\n"
                "When charging ends, gain a buff which copies [conjuration] spells you cast.\n"
                "This buff lasts for [{duration}_turns:duration]."
                ).format(**self.fmt_dict())
    def on_cast(self, x, y):
        self.caster.apply_buff(VariableCopy(self, [Level.Tags.Conjuration], "Simulacrum", 'num_copies'), self.get_stat('duration'))
        self.caster.cur_hp -= self.get_stat('health_sacrifice')
        yield

class BloodWave(Level.Spell):
    def on_init(self):
        self.name = "Bloody Wave"
        self.damage = 7
        self.radius = 1
        self.range = 0
    def get_ai_target(self):
        for p in self.get_impacted_tiles(self.caster.x, self.caster.y):
            u = self.caster.level.get_unit_at(p.x, p.y)
            if u and self.caster.level.are_hostile(u, self.caster):
                return self.caster
        return None
    def get_impacted_tiles(self, x, y):
        for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for p in stage:
                yield p
    def get_description(self):
        return "Deals [sanguine] damage to enemies in a burst around the caster.\nKills the caster."
    def cast(self, x, y):
        burstpoint = Level.Point(self.caster.x, self.caster.y)
        for stage in CommonContent.Burst(self.caster.level, burstpoint, self.get_stat('radius')):
                for point in stage:
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Sanguine, self)
                yield
        self.caster.kill()

class BloodElemental(API_ChargedSpells.IncantationSpell):
    def on_init(self):
        super(BloodElemental, self).on_init()
        self.name = "Blood Elemental"
        self.level = 4
        self.tags = [Level.Tags.Conjuration, Level.Tags.Sanguine, Level.Tags.Invocation]
        self.max_charges = 6
        self.range = 6
        self.required_charge = 5
        self.health_sacrifice = 40
        self.num_droplets = 4
        self.charging_effect_color = Level.Tags.Sanguine.color
        self.minion_damage = 13
        self.minion_range = 6
        self.minion_health = 35
        self.radius = 3
        self.must_target_walkable = True
        self.must_target_empty = True
        self.stats.append('required_charge')
        self.stats.append('health_sacrifice')
        self.stats.append('num_droplets')

        self.upgrades['num_droplets'] = (4, 3)
        self.upgrades['required_charge'] = (-2, 3)
        self.upgrades['minion_damage'] = (8, 4)
    def make_droplet(self):
        blood_drop = Level.Unit()
        blood_drop.name = "Blood Drop"
        blood_drop.team = self.caster.team
        blood_drop.flying = False
        blood_drop.asset_name = os.path.join("..","..","mods","ATGMChargePack","blood_drop")
        blood_drop.max_hp = 1
        blood_drop.shields = 1
        blood_drop.resists[Level.Tags.Sanguine] = 100
        blood_drop.resists[Level.Tags.Physical] = 50
        bolt = BloodWave()
        bolt.radius = self.get_stat('radius')
        bolt.damage = self.get_stat('minion_damage') // 2
        blood_drop.spells.append(bolt)
        return blood_drop
    def get_description(self):
        self.dropletdmg = self.get_stat('minion_damage') // 2
        self.stats.append('dropletdmg')
        return (
                "Charge this spell for [{required_charge}_turns:required_charge].\n"
                "On recast, sacrifice [{health_sacrifice}_HP:health_sacrifice] and summon a blood elemental.\n"
                "The blood elemental is a [sanguine] creature with a ranged attack dealing [{minion_damage}_damage:sanguine] with [{minion_range}_range:minion_range]. It has [{minion_health}_HP:minion_health], 100 [sanguine] resist, 50 [physical] resist, and 100 [poison] resist.\n"
                "When the elemental dies, it splits into [{num_droplets}_droplets_of_blood:num_targets].\n"
                "Droplets have [1_HP:heal], [1_SH:shields], and a sacrifice attack that deals [{dropletdmg}_damage:sanguine] in a [{radius}_tile:radius] burst of them."
                ).format(**self.fmt_dict())
    def on_cast(self, x, y):
        elem = Level.Unit() 
        elem.name = "Blood Elemental"
        elem.team = self.caster.team
        elem.flying = False
        elem.asset_name = os.path.join("..","..","mods","ATGMChargePack","elemental_blood")
        elem.max_hp = self.get_stat('minion_health')
        elem.resists[Level.Tags.Sanguine] = 100
        elem.resists[Level.Tags.Physical] = 50
        beam = CommonContent.SimpleRangedAttack(name="Bloody Beam", damage=self.get_stat('minion_damage'), damage_type=Level.Tags.Sanguine, range=self.get_stat('minion_range'), beam=True)
        elem.spells.append(beam)
        buff = Monsters.BagOfBugsBuff(self.make_droplet)
        buff.spawns = self.get_stat('num_droplets')
        elem.buffs.append(buff)
        self.summon(elem, Level.Point(x, y))
        self.caster.cur_hp -= self.get_stat('health_sacrifice')
        yield

class BloodLanceBuff(Level.Buff):

    def __init__(self, spell, inflictor):
        self.spell = spell
        self.inflictor = inflictor
        self.buff_type = Level.BUFF_TYPE_CURSE
        self.asset = ['status', 'sealed_fate']
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Blood Draw"
        self.color = Level.Tags.Sanguine.color
        self.show_effect = False
        self.description = "Drains 1 HP per turn from the victim and transfers it to the buff inflictor."

    def on_advance(self):
        self.owner.level.deal_damage(self.owner.x, self.owner.y, 1, Level.Tags.Sanguine, self or self.spell)
        self.owner.level.deal_damage(self.inflictor.x, self.inflictor.y, -1, Level.Tags.Heal, self or self.spell)


class BloodLance(API_ChargedSpells.PowerupSpell):
    def on_init(self):
        super(BloodLance, self).on_init()
        self.name = "Blood Lance"
        self.level = 2
        self.tags = [Level.Tags.Metallic, Level.Tags.Sanguine, Level.Tags.Sorcery, Level.Tags.Fixation]
        self.max_charges = 8
        self.range = 5
        self.max_charge = 5
        self.health_sacrifice = 15
        self.health_transfer = 1
        self.duration = 13
        self.duration_per_turn_charged = 3
        self.charging_effect_color = Level.Tags.Sanguine.color
        self.stats.append('max_charge')
        self.stats.append('health_sacrifice')
        self.stats.append('health_transfer')
        self.stats.append('duration_per_turn_charged')

        self.upgrades['duration_per_turn_charged'] = (2, 3, "Duration Bonus")
        self.upgrades['range'] = (2, 2)
        self.upgrades['max_charges'] = (3, 2)

    def get_description(self):
        return(
                "Charge this spell for up to [{max_charge}_turns:max_charge].\n"
                "On recast, sacrifice [{health_sacrifice}_HP:health_sacrifice] and embed a gruesome lance in the target.\n"
                "It does no damage initially, but applies a debuff for [{duration}_turns:duration] causing the target to lose [{health_transfer}_HP:damage] per turn as [sanguine] damage, healing the caster for that amount.\n"
                "The debuff gains [{duration_per_turn_charged}_duration:sanguine] per turn charged."
                ).format(**self.fmt_dict())
    def on_cast(self, x, y, turns_charged):
        for p in self.caster.level.get_points_in_line(self.caster, Level.Point(x, y))[1:]:
            self.caster.level.projectile_effect(p.x, p.y, proj_name='kobold_arrow', proj_origin=self.caster, proj_dest=Level.Point(x, y))
        self.caster.cur_hp -= self.get_stat('health_sacrifice')
        unit = self.caster.level.get_unit_at(x, y)
        if unit:
            duration = self.get_stat('duration') + turns_charged*self.get_stat('duration_per_turn_charged')
            unit.apply_buff(BloodLanceBuff(self, self.caster), duration)
            yield

class SeededDebuff(Level.Buff):
    def __init__(self, spell):
        Level.Buff.__init__(self)
        self.spell = spell
        self.buff_type = Level.BUFF_TYPE_CURSE
        self.color = Level.Tags.Sanguine.color
        self.name = "Seeded"
    def on_applied(self, owner):
        if owner.resists[Level.Tags.Sanguine] >= 100:
            return Level.ABORT_BUFF_APPLY
        self.owner_triggers[Level.EventOnDeath] = self.on_death
    def on_death(self, evt):
        tree = self.spell.make_tree(self.owner.max_hp)
        if self.spell.get_stat('recombinant'):
            if Level.Tags.Fire in self.owner.tags:
                tag_used = Level.Tags.Fire
            elif Level.Tags.Ice in self.owner.tags:
                tag_used = Level.Tags.Ice
            elif Level.Tags.Lightning in self.owner.tags:
                tag_used = Level.Tags.Lightning
            elif Level.Tags.Dark in self.owner.tags:
                tag_used = Level.Tags.Dark
            else:
                tag_used = None
            if tag_used != None:
                tree.buffs.append(CommonContent.DamageAuraBuff(damage_type=tag_used, damage=1, radius=self.spell.get_stat('minion_range')))
        self.spell.summon(tree)
    def on_advance(self):
        dtypes = [Level.Tags.Sanguine]
        if self.spell.get_stat('pollinate'):
            dtypes.append(Level.Tags.Physical)

        for dtype in dtypes:
            self.owner.deal_damage(3, dtype, self)
            if not self.owner.is_alive():
                break


class SCPTree(API_ChargedSpells.BoundSpell):
    def on_init(self):
        super(SCPTree, self).on_init()
        self.name = "Blood Tree"
        self.level = 5
        self.tags = [Level.Tags.Conjuration, Level.Tags.Sorcery, Level.Tags.Sanguine, Level.Tags.Invocation]
        self.max_charges = 4
        self.range = 6
        self.bound_range = 6
        self.required_charge = 4
        self.health_sacrifice = 35
        self.charging_effect_color = Level.Tags.Sanguine.color

        self.minion_damage = 10
        self.damage = 3
        self.aura_damage = 1
        self.minion_range = 6

        self.stats.append('required_charge')
        self.stats.append('health_sacrifice')
        self.stats.append('aura_damage')

        self.upgrades['bonus_health'] = (1, 2, "Stronger Trees", "Trees gain 20 max HP and 50 [physical] resist.")
        self.upgrades['aura_damage'] = (2, 4)
        self.upgrades['pollinate'] = (1, 5, "Evolved Seeding", "Trees gain a ranged attack which inflicts Seeded.\nSeeded deals [physical] damage in addition to its normal types.", "genetic")
        self.upgrades['recombinant'] = (1, 6, "Recombinant Trees", "If a seeded [fire], [ice], [lightning], or [dark] unit dies, the tree gains an extra aura of that tag that deals 1 damage.", "genetic")

    def get_description(self):
        return (
            "Sacrifice [{health_sacrifice}_HP:health_sacrifice] and charge this spell for [{required_charge}_turns:required_charge]. Can be cast anytime after fully charging.\n"
            "On cast, deal [{damage}:damage] [sanguine] damage and inflict Seeded. Enemies immune to [sanguine] are immune.\n"
            "Seeded enemies take 3 [sanguine] damage each turn.\n"
            "If a seeded enemy dies, a stationary blood tree with 100 [sanguine] resist, 100 [poison] resist, and -50 [fire] resist appears with max HP equal to the target's.\n"
            "Trees have an aura that deals [{aura_damage}_sanguine_damage:sanguine] damage to enemies in [{minion_range}_tiles:radius]."
        ).format(**self.fmt_dict())

    def make_tree(self, HP):
        tree = Level.Unit() 
        tree.name = "Blood Tree"
        tree.team = self.caster.team
        tree.flying = False
        tree.asset_name = os.path.join("..","..","mods","ATGMChargePack","blood_tree")
        tree.max_hp = HP
        if self.get_stat('bonus_health'):
            tree.max_hp += 20
            tree.resists[Level.Tags.Physical] = 50
        tree.stationary = True
        tree.tags = [Level.Tags.Sanguine, Level.Tags.Living]
        tree.resists[Level.Tags.Sanguine] = 100
        tree.resists[Level.Tags.Poison] = 100
        tree.resists[Level.Tags.Fire] = -50
        if self.get_stat('pollinate'):
            launch = CommonContent.SimpleRangedAttack(name="Seed Launch", damage=1, damage_type=Level.Tags.Sanguine, range=(self.get_stat('minion_range')+2), onhit=lambda caster,target: target.apply_buff(SeededDebuff(self)), cool_down=7)
            launch.get_description = lambda: "Inflicts Seeded on the target"
            tree.spells.append(launch)
        tree.buffs.append(CommonContent.DamageAuraBuff(damage_type=Level.Tags.Sanguine, damage=self.get_stat('aura_damage'), radius=self.get_stat('minion_range')))
        return tree

    
    def on_cast(self, x, y):
        self.caster.level.deal_damage(x, y, self.get_stat('damage'), Level.Tags.Sanguine, self)
        u = self.caster.level.get_unit_at(x, y)
        if u and self.caster.level.are_hostile(u, self.caster):
            u.apply_buff(SeededDebuff(self))
        self.caster.cur_hp -= self.get_stat ('health_sacrifice')
        self.range = 6
        yield


#skills

class ChargedConjurer(Upgrades.Upgrade):
    def on_init(self):
        self.name = "Channeled Conjury"
        self.tags = [Level.Tags.Conjuration, Level.Tags.Fixation]
        self.level = 7
        self.owner_triggers[Level.EventOnSpellCast] = self.on_spell_cast
    def get_description(self):
        return "When you cast a [fixation] [conjuration] spell, gain free charge turns equal to the number of non [fixation] [conjuration] spells you own. \n This bonus does not increase the amount of turns you can charge for."
    def on_spell_cast(self, event):
        if Level.Tags.Fixation in event.spell.tags:
            event.spell.turns_charged += len([s for s in self.owner.spells if Level.Tags.Conjuration in s.tags and Level.Tags.Fixation not in s.tags])

class ChargeRepulsorBuff(Level.Buff):

    def __init__(self):
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Dispersion Field"
        self.description = "Teleport nearby enemies away each turn"

    def on_advance(self):
        tped = 0
        units = self.owner.level.get_units_in_ball(self.owner, 4)
        random.shuffle(units)
        for u in units:
            if not Level.are_hostile(self.owner, u):
                continue

            possible_points = []
            for i in range(len(self.owner.level.tiles)):
                for j in range(len(self.owner.level.tiles[i])):
                    if self.owner.level.can_stand(i, j, u):
                        possible_points.append(Level.Point(i, j))

            if not possible_points:
                continue

            target_point = random.choice(possible_points)

            self.owner.level.show_effect(u.x, u.y, Level.Tags.Translocation)
            self.owner.level.act_move(u, target_point.x, target_point.y, teleport=True)
            self.owner.level.show_effect(u.x, u.y, Level.Tags.Translocation)

            tped += 1
            if tped > 999:
                break

class ChargeRepulsor(Upgrades.Upgrade):
    def on_init(self):
        self.name = "Charge Repulsor"
        self.tags = [Level.Tags.Translocation, Level.Tags.Fixation]
        self.level = 5
        self.disperser = ChargeRepulsorBuff()
        self.owner_triggers[Level.EventOnSpellCast] = self.on_spell_cast
        self.radius = 4
    def get_description(self):
        return "If you are charging a [fixation] spell, gain a dispersion field that teleports away units in [{radius}_tiles:radius]".format(**self.fmt_dict())
    def on_spell_cast(self, event):
        if Level.Tags.Fixation in event.spell.tags:
            self.owner.apply_buff(self.disperser, 999)
    def on_pre_advance(self):
        if not self.owner.has_buff(API_ChargedSpells.ChargingBuff):
            self.owner.remove_buff(self.disperser)

class ChargeLord(Upgrades.Upgrade):
    def on_init(self):
        self.name = "Legendary Focuser"
        self.tags = [Level.Tags.Fixation]
        self.level = 7
        self.tag_bonuses[Level.Tags.Fixation]['max_charge'] = 3
        self.tag_bonuses[Level.Tags.Fixation]['max_charges'] = 2
        self.tag_bonuses[Level.Tags.Fixation]['damage'] = 6

class Invoker(Upgrades.Upgrade):
    def on_init(self):
        self.name = "Arch Invoker"
        self.tags = [Level.Tags.Invocation]
        self.level = 7
        self.tag_bonuses[Level.Tags.Invocation]['required_charge'] = -1
        self.tag_bonuses[Level.Tags.Invocation]['max_charges'] = 3
        self.tag_bonuses[Level.Tags.Invocation]['damage'] = 5

#skills for blood magic

class BloodLord(Upgrades.Upgrade):
    def on_init(self):
        self.name = "Blood Lord"
        self.tags = [Level.Tags.Sanguine]
        self.level = 7
        self.tag_bonuses[Level.Tags.Sanguine]['minion_damage'] = 6
        self.tag_bonuses[Level.Tags.Sanguine]['damage'] = 6
        self.tag_bonuses[Level.Tags.Sanguine]['max_charges'] = 2

class SummonSacrifice(Upgrades.Upgrade):
    def on_init(self):
        self.name = "Sacrificial Substitution"
        self.tags = [Level.Tags.Sanguine]
        self.level = 6
        self.owner_triggers[Level.EventOnSpellCast] = self.on_spell_cast
    def get_description(self):
        return "When you cast a [sanguine] spell, drain 3 HP from the nearest enemy and heal for that amount.\nThis damage cannot be modified by skills.".format(**self.fmt_dict())
    def on_spell_cast(self, event):
        if Level.Tags.Sanguine in event.spell.tags:
            enemies = [u for u in self.owner.level.units if Level.are_hostile(self.owner, u)]
            if enemies:
                enemy = random.choice(enemies)
                self.owner.level.deal_damage(enemy.x, enemy.y, 3, Level.Tags.Sanguine, self)
                self.owner.level.deal_damage(self.owner.x, self.owner.y, -3, Level.Tags.Heal, self)

#orb things

class InvokedOrbSpell(API_ChargedSpells.IncantationSpell):

    def __init__(self):
        self.melt_walls = False
        self.orb_walk = False
        super(InvokedOrbSpell, self).__init__()
        # Do not require los, check points on the path instead
        self.requires_los = False

    def can_cast(self, x, y):
        if self.get_stat('orb_walk') and self.get_orb(x, y):
            return True

        path = self.caster.level.get_points_in_line(Level.Point(self.caster.x, self.caster.y), Level.Point(x, y))
        if len(path) < 2:
            return False

        start_point = path[1]
        blocker = self.caster.level.get_unit_at(start_point.x, start_point.y)
        if blocker:
            return False

        if not self.get_stat('melt_walls'):
            for p in path:
                if self.caster.level.tiles[p.x][p.y].is_wall():
                    return False

        return Level.Spell.can_cast(self, x, y)

    # Called before an orb is moved each turn
    def on_orb_move(self, orb, next_point):
        pass

    def on_orb_collide(self, orb, next_point):
        yield

    def on_orb_walk(self, existing):
        yield

    def on_make_orb(self, orb):
        return 

    def get_orb_impact_tiles(self, orb):
        return [Level.Point(orb.x, orb.y)]

    def get_orb(self, x, y):
        existing = self.caster.level.get_unit_at(x, y)
        if existing and existing.name == self.name:
            return existing
        return None

    def on_cast(self, x, y):
        existing = self.get_orb(x, y)
        if self.get_stat('orb_walk') and existing:
            for r in self.on_orb_walk(existing):
                yield r
            return

        path = self.caster.level.get_points_in_line(Level.Point(self.caster.x, self.caster.y), Level.Point(x, y))
        if len(path) < 1:
            return

        start_point = path[1]

        # Clear a wall at the starting point if it exists so the unit can be placed
        if self.get_stat('melt_walls'):
            if self.caster.level.tiles[start_point.x][start_point.y].is_wall():
                self.caster.level.make_floor(start_point.x, start_point.y)

        unit = CommonContent.ProjectileUnit()
        unit.name = self.name
        unit.stationary = True
        unit.team = self.caster.team
        unit.turns_to_death = len(path) + 1

        unit.max_hp = self.get_stat('minion_health')
        
        # path[0] = caster, path[1] = start_point, path[2] = first point to move to
        buff = Spells.OrbBuff(spell=self, dest=Level.Point(x, y))
        unit.buffs.append(buff)
        
        self.on_make_orb(unit)
        blocker = self.caster.level.get_unit_at(start_point.x, start_point.y)

        # Should be taken care of by can_cast- but weird situations could cause this
        if blocker:
            return

        self.summon(unit, start_point)

    def get_collide_tiles(self, x, y):
        return []

    def get_impacted_tiles(self, x, y):
        existing = self.get_orb(x, y)
        if existing and self.get_stat('orb_walk'):
            return self.get_orb_impact_tiles(existing)
        else:
            return self.caster.level.get_points_in_line(self.caster, Level.Point(x, y))[1:] + self.get_collide_tiles(x, y)

class ChargedOrbSpell(API_ChargedSpells.PowerupSpell):

    def __init__(self):
        self.melt_walls = False
        self.orb_walk = False
        super(ChargedOrbSpell, self).__init__()
        # Do not require los, check points on the path instead
        self.requires_los = False
        self.cur_charge_turns = 0

    def can_cast(self, x, y):
        if self.get_stat('orb_walk') and self.get_orb(x, y):
            return True

        path = self.caster.level.get_points_in_line(Level.Point(self.caster.x, self.caster.y), Level.Point(x, y))
        if len(path) < 2:
            return False

        start_point = path[1]
        blocker = self.caster.level.get_unit_at(start_point.x, start_point.y)
        if blocker:
            return False

        if not self.get_stat('melt_walls'):
            for p in path:
                if self.caster.level.tiles[p.x][p.y].is_wall():
                    return False

        return Level.Spell.can_cast(self, x, y)

    # Called before an orb is moved each turn
    def on_orb_move(self, orb, next_point):
        pass

    def on_orb_collide(self, orb, next_point):
        yield

    def on_orb_walk(self, existing):
        yield

    def on_make_orb(self, orb):
        return 

    def get_orb_impact_tiles(self, orb):
        return [Level.Point(orb.x, orb.y)]

    def get_orb(self, x, y):
        existing = self.caster.level.get_unit_at(x, y)
        if existing and existing.name == self.name:
            return existing
        return None

    def on_cast(self, x, y, turns_charged):
        self.cur_charge_turns = turns_charged
        existing = self.get_orb(x, y)
        if self.get_stat('orb_walk') and existing:
            for r in self.on_orb_walk(existing):
                yield r
            return

        path = self.caster.level.get_points_in_line(Level.Point(self.caster.x, self.caster.y), Level.Point(x, y))
        if len(path) < 1:
            return

        start_point = path[1]

        # Clear a wall at the starting point if it exists so the unit can be placed
        if self.get_stat('melt_walls'):
            if self.caster.level.tiles[start_point.x][start_point.y].is_wall():
                self.caster.level.make_floor(start_point.x, start_point.y)

        unit = CommonContent.ProjectileUnit()
        unit.name = self.name
        unit.stationary = True
        unit.team = self.caster.team
        unit.turns_to_death = len(path) + 1

        unit.max_hp = self.get_stat('minion_health')
        
        # path[0] = caster, path[1] = start_point, path[2] = first point to move to
        buff = Spells.OrbBuff(spell=self, dest=Level.Point(x, y))
        unit.buffs.append(buff)
        
        self.on_make_orb(unit)
        blocker = self.caster.level.get_unit_at(start_point.x, start_point.y)

        # Should be taken care of by can_cast- but weird situations could cause this
        if blocker:
            return

        self.summon(unit, start_point)

    def get_collide_tiles(self, x, y):
        return []

    def get_impacted_tiles(self, x, y):
        existing = self.get_orb(x, y)
        if existing and self.get_stat('orb_walk'):
            return self.get_orb_impact_tiles(existing)
        else:
            return self.caster.level.get_points_in_line(self.caster, Level.Point(x, y))[1:] + self.get_collide_tiles(x, y)

class MoonOrb(ChargedOrbSpell):
    def on_init(self):
        super(MoonOrb, self).on_init()
        self.name = "Twilight Moon"
        self.range = 5
        self.max_charges = 2
        self.max_charge = 7

        self.melt_walls = False

        self.minion_health = 20
        self.minion_damage = 5
        self.radius = 8
        
        self.tags = [Level.Tags.Dark, Level.Tags.Holy, Level.Tags.Orb, Level.Tags.Conjuration, Level.Tags.Fixation]
        self.level = 7
        self.stats.append('max_charge')

        self.upgrades['radius'] = (2, 3)
        self.upgrades['range'] = (3, 5)
        self.upgrades['arcanism'] = (1, 7, "Astral Star", "Deal [arcane] damage to all enemies in the moon's radius.", "celestial")
        self.upgrades['orb_walk'] = (1, 9, "Nova Collision", "Targeting a twilight moon with another will destroy both of them and rain 40 fragments down, dealing 5 [dark] or [holy] damage to enemies on those tiles and converting walls into floors.\nThis damage is fixed.", "celestial")
    def get_description(self):
        return ("Summons the twilight moon next to the caster.\n"
                "It has [{minion_health}_HP:minion_health].\n"
                "Each turn, the moon emits a pulse in [{radius}_tiles:radius], dealing [{minion_damage}_dark_damage:dark] to units on its left, and dealing [{minion_damage}_holy_damage:holy] to units on its right.\n"
                "The moon's pulse radius increases by 1 for each turn charged.\n"
                "This spell can be charged for [{max_charge}_turns:max_charge].\n"
                "The moon has no will of its own, each turn it will float one tile towards the target.\n"
                "The moon can be destroyed by [dark] or [holy] damage.").format(**self.fmt_dict())

    def on_make_orb(self, orb):
        orb.resists[Level.Tags.Dark] = 50
        orb.resists[Level.Tags.Holy] = 50
        orb.shields = 2
        orb.asset_name = os.path.join("..","..","mods","ATGMChargePack","twilight_moon")
        orb.name = "Twilight Moon"

    def on_orb_move(self, orb, next_point):
        damage = self.get_stat('minion_damage')
        rad = self.get_stat('radius') + self.cur_charge_turns
        for stage in CommonContent.Burst(self.caster.level, Level.Point(next_point.x, next_point.y), rad):
            for point in stage:
                u = self.caster.level.get_unit_at(point.x, point.y)
                if u and self.caster.level.are_hostile(u, self.caster):
                    dtype = Level.Tags.Dark if point.x <= next_point.x else Level.Tags.Holy
                    self.caster.level.deal_damage(u.x, u.y, damage, dtype, self)
                    if self.get_stat('arcanism'):
                        self.caster.level.deal_damage(u.x, u.y, damage, Level.Tags.Arcane, self)
    
    def on_orb_walk(self, existing):
        existing.kill()
        spots = [t for t in self.caster.level.iter_tiles()]
        zones = random.sample(spots, 40)
        for z in zones:
            if self.caster.level.tiles[z.x][z.y].is_wall():
                self.caster.level.make_floor(z.x, z.y)
            dtype = random.choice([Level.Tags.Dark, Level.Tags.Holy])
            self.caster.level.deal_damage(z.x, z.y, 5, dtype, self)
        yield

class SphereChaos(InvokedOrbSpell):
    def on_init(self):
        super(SphereChaos, self).on_init()
        self.name = "Chaos Sphere"
        self.range = 5
        self.max_charges = 4
        self.required_charge = 3

        self.melt_walls = False

        self.minion_health = 20
        self.minion_damage = 5
        self.radius = 6
        self.num_targets = 6
        
        self.tags = [Level.Tags.Chaos, Level.Tags.Orb, Level.Tags.Conjuration, Level.Tags.Invocation]
        self.level = 7
        self.stats.append('required_charge')

        self.upgrades['radius'] = (2, 3)
        self.upgrades['range'] = (3, 5)
        self.upgrades['minion_damage'] = (5, 2)
        self.upgrades['num_targets'] = (3, 1)
        self.upgrades['annihilator'] = (1, 6, "Decimation Sphere", "The sphere will cast Annihilate on the unit in range with the highest HP each time it moves.\nThis Annihilate gains all of your upgrades and bonuses.")

    def get_description(self):
        return ("Charge this spell for [{required_charge}_turns:required_charge].\n"
                "On cast, summons a chaos sphere next to the caster.\n"
                "It has [{minion_health}_HP:minion_health].\n"
                "Each turn, the sphere sends out [{num_targets}_bolts:num_targets] to enemies in [{radius}_tiles:radius], dealing [{minion_damage}:minion_damage] [fire], [lightning], or [physical] damage.\n"
                "The sphere has no will of its own, each turn it will float one tile towards the target.\n"
                "It can be destroyed by [fire], [lightning], or [physical] damage.").format(**self.fmt_dict())
    
    def get_hostiles_in_los_burst(self, rad, next_point):
        units = []
        for stage in CommonContent.Burst(self.caster.level, Level.Point(next_point.x, next_point.y), rad):
            for point in stage:
                u = self.caster.level.get_unit_at(point.x, point.y)
                if u and self.caster.level.are_hostile(u, self.caster) and u in self.caster.level.get_units_in_los(next_point):
                    units.append(u)
        return units

    def on_make_orb(self, orb):
        orb.resists[Level.Tags.Fire] = 0
        orb.resists[Level.Tags.Lightning] = 0
        orb.resists[Level.Tags.Physical] = 0
        orb.shields = 4
        orb.asset_name = os.path.join("..","..","mods","ATGMChargePack","sphere_chaos")
        orb.name = "Chaos Sphere"

    def on_orb_move(self, orb, next_point):
        damage = self.get_stat('minion_damage')
        rad = self.get_stat('radius')
        units = self.get_hostiles_in_los_burst(rad, next_point)
        if self.get_stat('annihilator') and units:
            units.sort(key=lambda u: u.cur_hp)
            nihil = Spells.AnnihilateSpell()
            nihil.statholder = self.caster
            nihil.max_charges = 0
            nihil.cur_charges = 0
            nihil.caster = orb
            self.owner.level.act_cast(orb, nihil, units[-1].x, units[-1].y)
        units = self.get_hostiles_in_los_burst(rad, next_point)
        if units:
            for i in range(self.get_stat('num_targets')):
                bolt_type = random.choice([Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical])
                bolt = CommonContent.SimpleRangedAttack(damage=damage, damage_type=bolt_type, range=Level.RANGE_GLOBAL)
                bolt.caster = orb
                target = random.choice([u for u in units if u.is_alive()])
                self.owner.level.act_cast(orb, bolt, target.x, target.y)

#constructors

#Spells.all_player_spell_constructors.append(CheatSpell)
Spells.all_player_spell_constructors.append(ChaosRay)
Spells.all_player_spell_constructors.append(GravityWell)
Spells.all_player_spell_constructors.append(ChaosTome)
Spells.all_player_spell_constructors.append(IceMelt)
Spells.all_player_spell_constructors.append(LeyDraw)
Spells.all_player_spell_constructors.append(SoulSuck)
Spells.all_player_spell_constructors.append(DracoPillar)
Spells.all_player_spell_constructors.append(DarkDragon)
Spells.all_player_spell_constructors.append(SummonJormungandr)
Spells.all_player_spell_constructors.append(SpiritBlade)
Spells.all_player_spell_constructors.append(MagicDagger)
Spells.all_player_spell_constructors.append(AmoebaFuse)
Spells.all_player_spell_constructors.append(NetherPact)
Spells.all_player_spell_constructors.append(Bloodball)
Spells.all_player_spell_constructors.append(BattleAltar)
Spells.all_player_spell_constructors.append(WordSacrifice)
Spells.all_player_spell_constructors.append(SoulSever)
Spells.all_player_spell_constructors.append(InvokeStorm)
Spells.all_player_spell_constructors.append(BloodSimulacrum)
Spells.all_player_spell_constructors.append(BloodElemental)
Spells.all_player_spell_constructors.append(BloodLance)
Spells.all_player_spell_constructors.append(CoalSwarm)
Spells.all_player_spell_constructors.append(VoidFlare)
Spells.all_player_spell_constructors.append(SilverStream)
Spells.all_player_spell_constructors.append(MoonOrb)
Spells.all_player_spell_constructors.append(SphereChaos)
Spells.all_player_spell_constructors.append(SummonClay)
Spells.all_player_spell_constructors.append(PyrostaticStorm)
Spells.all_player_spell_constructors.append(SCPTree)
Upgrades.skill_constructors.append(ChargedConjurer)
Upgrades.skill_constructors.append(ChargeRepulsor)
Upgrades.skill_constructors.append(ChargeLord)
Upgrades.skill_constructors.append(Invoker)
Upgrades.skill_constructors.append(BloodLord)
Upgrades.skill_constructors.append(SummonSacrifice)