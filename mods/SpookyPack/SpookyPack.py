from calendar import Calendar
import re
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

class HorseheadBuff(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)
        self.name = "Headless Pursuit"
        self.color = Level.Tags.Dark.color

    def on_pre_advance(self):
        lowest = list(sorted([u for u in self.owner.level.units if Level.are_hostile(self.owner, u)], key=lambda x: x.cur_hp))
        potentials = [t for t in self.owner.level.iter_tiles() if self.owner.level.can_stand(t.x, t.y, self.owner)]
        if lowest and potentials:
            lowest = lowest[0]
            potentials.sort(key=lambda x: Level.distance(x, lowest))
            self.owner.level.show_effect(self.owner.x, self.owner.y, Level.Tags.Translocation)
            self.owner.level.act_move(self.owner, potentials[0].x, potentials[0].y, teleport=True)

    def get_tooltip(self):
        return "Before acting each turn, teleports near the enemy with the lowest HP"

class Horsefear(Level.Buff):
    def on_init(self):
        self.name = "Fear"
        self.color = Level.Tags.Sorcery.color
        self.buff_type = Level.BUFF_TYPE_CURSE
        self.global_bonuses['damage'] = -10
            
class Horsehead(Level.Spell):

    def on_init(self):

        self.name = "Ichabod's Bane"
        
        self.level = 5
        self.tags = [Level.Tags.Dark, Level.Tags.Conjuration]
        self.max_charges = 4

        self.minion_health = 77
        self.minion_damage = 17
        self.minion_range = 6

        self.must_target_walkable = True
        self.must_target_empty = True

        self.upgrades['minion_damage'] = (10, 3)
        self.upgrades['frightening'] = (1, 5, "Terrorblade", "The Headless Horseman's sword inflicts [fear:sorcery] on enemies for 5 turns on hit, reducing the damage of all spells by 10.", "sword")
        self.upgrades['drain'] = (1, 4, "Wight Curse", "The Headless Horseman's sword drains 3 max HP from hit enemies.", "sword")
        self.upgrades['taxation'] = (1, 7, "Price of Death", "The Headless Horseman can cast your Soul Tax spell on a 9 turn cooldown.", "specialty")
        self.upgrades['doom'] = (1, 5, "Pumpkin Strike", "The Headless Horseman can throw jack-o-lanterns dealing [dark] or [fire] damage.", "specialty")
    def get_description(self):
        return ("Summon the legendary Headless Horseman on target tile.\n"
                "The Headless Horseman is a [dark] [undead] with [{minion_health}_HP:minion_health] and a cursed sword attack dealing [{minion_damage}_dark_damage:dark].\n"
                "The Headless Horseman will relentlessly pursue the enemy unit with the lowest HP, and is guaranteed to teleport near it each turn."
                ).format(**self.fmt_dict())

    def make_idol(self):
        idol = Level.Unit()
        idol.asset_name = os.path.join("..","..","mods","SpookyPack","horseman_headless")
        idol.name = "Headless Horseman"
        idol.max_hp = self.get_stat('minion_health')
        idol.tags = [Level.Tags.Dark, Level.Tags.Undead]
        sword = CommonContent.SimpleMeleeAttack(damage=self.get_stat('minion_damage'), damage_type=Level.Tags.Dark, buff=(Horsefear if self.get_stat('frightening') else None), buff_duration=self.get_stat('frightening'))
        sword.name = "Cursed Sword"
        if self.get_stat('frightening'):
            sword.buff = Horsefear
            sword.buff_duration = 5
            sword.description
        if self.get_stat('drain'):
            def drain(c, t):
                t.max_hp -= 3
            sword.onhit = drain
        idol.spells.append(sword)
        idol.buffs.append(HorseheadBuff(self))
        if self.get_stat('taxation'):
            tax = Spells.SoulTax()
            tax.statholder = self.caster
            tax.max_charges = tax.cur_charges = 0
            tax.cool_down = 9
            idol.spells.insert(0, tax)
        if self.get_stat('doom'):
            idol.spells.insert(0, CommonContent.SimpleRangedAttack(name='Lantern Toss', damage=self.get_stat('minion_damage'), damage_type=[Level.Tags.Dark, Level.Tags.Fire], range=self.get_stat('minion_range'), radius=3, cool_down=7))
        return idol
    
    def cast_instant(self, x, y):
        self.summon(self.make_idol(), Level.Point(x, y))

class JackolanternBuffModular(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)
        self.stack_type = Level.STACK_INTENSITY
        self.name = "Halloween"
        self.asset = ['status', 'orange_bloodlust']
        self.global_bonuses['damage'] = self.spell.get_stat('bonus')
        self.color = Level.Color(249, 168, 37)

class JackolanternModular(Level.Spell):
    def __init__(self, spell):
        self.spell = spell
        self.accepted = [Level.Tags.Dark, Level.Tags.Demon, Level.Tags.Undead]
        Level.Spell.__init__(self)
        self.name = "Dark Winter Night"
        self.description = "Up to 4 random allied %s units gain +%d damage for 25 turns" % (' or '.join(("[" + t.name.lower() + "]") for t in self.accepted), self.spell.get_stat('bonus'))
        self.range = 0
        self.color = Level.Color(249, 168, 37)
        
    def can_cast(self, x, y):
        return any(u for u in self.caster.level.units if u != self.caster and not Level.are_hostile(self.caster, u) and any(t in u.tags for t in self.accepted))		

    def cast_instant(self, x, y):
        targets = [u for u in self.caster.level.units if u != self.caster and not Level.are_hostile(self.caster, u) and any(t in u.tags for t in self.accepted)]
        random.shuffle(targets)
        for i in range(4):
            if not targets:
                break
            targets.pop().apply_buff(JackolanternBuffModular(self.spell), 25)

class NotThePose(Level.Spell):

    def on_init(self):

        self.name = "Pumpkin Ritual"
        
        self.level = 4
        self.tags = [Level.Tags.Dark, Level.Tags.Conjuration]
        self.max_charges = 3

        ex = RareMonsters.Jackolantern()
        self.minion_health = ex.max_hp*2
        self.bonus = 1
        self.stats.extend(['bonus'])

        self.must_target_walkable = True
        self.must_target_empty = True

        self.upgrades['minion_health'] = (19, 2)
        self.upgrades['lantern'] = (1, 3, "Toughened Layers", "Jack o' lanterns gain 50 [physical] and [fire] resist.")
        self.upgrades['bonus'] = (1, 5, "Bonus", "The jack o' lantern can grant 2 bonus damage instead of 1.")

    def get_description(self):
        return ("Summon an immobile Jack O' Lantern with [{minion_health}_HP:minion_health] on target tile.\n"
                "The lantern can grant 4 random [dark], [demon], or [undead] units [{bonus}_bonus_damage:demon] for 25 turns."
                ).format(**self.fmt_dict())

    def make_idol(self):
        unit = RareMonsters.Jackolantern()
        unit.spells[0] = JackolanternModular(self)
        CommonContent.apply_minion_bonuses(self, unit)
        if self.get_stat('lantern'):
            unit.resists[Level.Tags.Physical] = 50
            unit.resists[Level.Tags.Fire] = 50
        return unit
    
    def cast_instant(self, x, y):
        self.summon(self.make_idol(), Level.Point(x, y))

class LootedBuff(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)
        self.name = "Looted"
        self.color = Level.Tags.Dark.color
        self.stack_type = Level.STACK_INTENSITY
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.owner_triggers[Level.EventOnSpellCast] = self.cooldown_reduce

    def on_applied(self, owner):
        if not any(t in [Level.Tags.Demon, Level.Tags.Undead, Level.Tags.Living, Level.Tags.Nature] for t in owner.tags):
            self.global_bonuses['damage'] = 1
    
    def cooldown_reduce(self, evt):
        if (Level.Tags.Demon in self.owner.tags or Level.Tags.Undead in self.owner.tags) and self.owner.cool_downs[evt.spell] > 0:
            self.owner.cool_downs[evt.spell] -= 1
            self.owner.remove_buff(self)
    
    def on_pre_advance(self):
        other_stacks = [b for b in self.owner.buffs if b != self and type(b) == type(self)]
        if (Level.Tags.Living in self.owner.tags or Level.Tags.Nature in self.owner.tags) and self.owner.is_alive() and self.owner != self.owner.level.player_unit:
            if other_stacks:
                self.owner.remove_buff(other_stacks[0])
                self.owner.remove_buff(self)
                self.owner.advance()
        elif self.spell.get_stat('greedy') and self.owner == self.owner.level.player_unit and len(other_stacks) >= 2:
            buffs = [b for b in self.owner.buffs if b.buff_type == Level.BUFF_TYPE_BLESS and b.turns_left]
            if buffs:
                buffs.sort(key=lambda x: x.turns_left)
                buffs[0].turns_left += 1
                self.owner.remove_buff(other_stacks[0])
                self.owner.remove_buff(other_stacks[1])
                self.owner.remove_buff(self)

class ThePhrase(Level.Spell):

    def on_init(self):

        self.name = "Trick or Treat"
        
        self.level = 4
        self.tags = [Level.Tags.Dark, Level.Tags.Enchantment]
        self.max_charges = 3
        self.radius = 2
        self.damage = 8
        self.range = 7

        self.upgrades['damage'] = (11, 4)
        self.upgrades['radius'] = (1, 2)
        self.upgrades['powerhaunt'] = (2, 3, "Extra Scariness", "The additional max HP loss per [demon] and [undead] ally increases by 2")
        self.upgrades['greedy'] = (1, 5, "Greed", "Instead of [looted:dark] being split among allies in the square, you gain stacks of [looted:dark] equal to half the lost max HP.\nEach turn, before acting, consume 3 stacks of [looted:dark] to extend the duration of your active buff with the lowest duration by 1 turn.")

    def get_impacted_tiles(self, x, y):
        return list(self.caster.level.get_points_in_ball(x, y, self.get_stat('radius'), diag=True))

    def get_description(self):
        return ("Each enemy in a square extending [{radius}_tiles:radius] away from the target point that is not immune to [dark] loses [{damage}:damage] max HP, plus 3 extra for each [undead] or [demon] ally in the square. Enemies with 0 max HP instantly die.\n"
                "Allies in the square gain stacks of [looted:dark] for duration equal to one-half of the total HP lost, split evenly.\n"
                "[Undead] and [demon] allies consume stacks of [looted:dark] when casting, reducing the used spell's cooldown by 1; [Living] and [nature] allies consume stacks of [looted:dark] before their turn starts to act twice.\n"
                "Other allies do not consume [looted:dark] and instead gain +1 damage per stack."
                ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        haunt_allies = hp_counter = 0
        all_allies = []
        sq = self.get_impacted_tiles(x, y)
        for tile in sq:
            u = self.owner.level.get_unit_at(tile.x, tile.y)
            if u and not Level.are_hostile(u, self.caster):
                if (Level.Tags.Demon in u.tags or Level.Tags.Undead in u.tags):
                    haunt_allies += 1
                if u != self.caster:
                    all_allies.append(u)
        for tile in sq:
            u = self.owner.level.get_unit_at(tile.x, tile.y)
            if u and Level.are_hostile(self.caster, u) and u.resists[Level.Tags.Dark] < 100:
                hp_counter += (min(u.max_hp, self.get_stat('damage')+(3+self.get_stat('powerhaunt'))*haunt_allies))
                u.max_hp -= (min(u.max_hp, self.get_stat('damage')+(3+self.get_stat('powerhaunt'))*haunt_allies))
                if u.cur_hp > u.max_hp:
                    u.cur_hp = u.max_hp
                if u.max_hp <= 0:
                    u.kill()
        hp_counter = math.floor(hp_counter)
        if self.get_stat('greedy'):
            all_allies = [self.caster]
        if all_allies:
            stacks = hp_counter // (2*len(all_allies))
            for u in all_allies:
                for _ in range(stacks):
                    u.apply_buff(LootedBuff(self))

class HauntConvertBuff(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)
        self.name = "Dread Haunt"
        self.color = Level.Tags.Arcane.color
        self.buff_type = Level.BUFF_TYPE_CURSE
        self.owner_triggers[Level.EventOnDamaged] = self.redeal

    def redeal(self, evt):
        if evt.source != self:
            self.owner.deal_damage(evt.damage // 4, evt.damage_type, self)
            if evt.source.owner == self.owner.level.player_unit and Level.Spell in type(evt.source).__bases__:
                self.owner.level.event_manager.raise_event(Level.EventOnDamaged(self.owner, evt.damage // 2, evt.damage_type, evt.source), self.owner)

class HauntCurse(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)
        self.name = "Haunting End"
        self.color = Level.Tags.Dark.color
        self.owner_triggers[Level.EventOnDeath] = self.curse
        self.buff_type = Level.BUFF_TYPE_PASSIVE

    def curse(self, evt):
        targets = self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('radius')//2)
        for t in targets:
            t.apply_buff(HauntConvertBuff(self.spell), 5)

    def get_tooltip(self):
        return "On death, applies Dread Haunt to units in %d tiles, causing them to take 25 percent more damage from all sources" % self.spell.get_stat('radius')

class HauntUp(Level.Spell):

    def on_init(self):

        self.name = "Shadow Haunt"
        
        self.level = 4
        self.tags = [Level.Tags.Dark, Level.Tags.Arcane, Level.Tags.Conjuration]
        self.max_charges = 3
        self.radius = 8
        self.range = 7
        self.requires_los = False

        ex = Variants.Haunter()
        self.minion_health = ex.max_hp // 2
        self.minion_damage = 1
        self.lives = 1

        self.stats.extend(['lives'])

        self.upgrades['lives'] = (1, 2)
        self.upgrades['range'] = (3, 2)
        self.upgrades['holy'] = (1, 4, "Spirit Shadow", "Haunters' auras can also deal [holy] damage, and haunters have their [holy] resist set to 100.")
        self.upgrades['misery'] = (1, 6, "Unyielding Hatred", "Whenever a Haunter dies, it curses all units in half its aura radius for 5 turns, causing them to take an additional 25% damage from all sources.\nIf that damage comes from one of the Wizard's spells, additionally pretend to have that spell redeal another 50% of that damage.")

        self.can_target_empty = False

    def get_description(self):
        return ("Summon a Haunter with [{minion_health}_HP:minion_health] near target unit.\n"
                "Haunters are [dark] [undead] with a melee attack dealing [{minion_damage}_dark_damage:dark] and an aura dealing 2 [dark] or [arcane] damage to enemies in [{radius}_tiles:radius] each turn.\n"
                "Haunters bear intense grudges and can reincarnate [{lives}_times:heal] to exact their revenge."
                ).format(**self.fmt_dict())

    def make_unit(self):
        haunt = Variants.Haunter()
        CommonContent.apply_minion_bonuses(self, haunt)
        haunt.max_hp = self.get_stat('minion_health')
        aura = haunt.get_buff(CommonContent.DamageAuraBuff)
        aura.radius = self.get_stat('radius')
        if self.get_stat('holy'):
            aura.damage_type.append(Level.Tags.Holy)
            haunt.resists[Level.Tags.Holy] = 100
        haunt.get_buff(CommonContent.ReincarnationBuff).lives = self.get_stat('lives')
        if self.get_stat('misery'):
            haunt.buffs.append(HauntCurse(self))
        return haunt

    def cast_instant(self, x, y):
        self.summon(self.make_unit(), Level.Point(x, y))

class Dummy(Level.Spell):
    def __init__(self, tags, level):
        Level.Spell.__init__(self)
        self.tags = tags
        self.name = "Dummy Spell"
        self.range = Level.RANGE_GLOBAL
        self.requires_los = False
        self.can_target_self = True
        self.level = level
    def cast_instant(self, x, y):
        return

class PumpkinBuff(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)
        self.name = "Soul Burn"
        self.color = Level.Tags.Dark.color
        self.buff_tyope = Level.BUFF_TYPE_BLESS

    def on_advance(self):
        self.owner.deal_damage(self.spell.get_stat('burn_damage'), Level.Tags.Fire, self.spell)
        if Level.Tags.Living in self.owner.tags:
            self.owner.deal_damage(self.spell.get_stat('burn_damage'), Level.Tags.Dark, self.spell)

class PumpkinThrow(Level.Spell):

    def on_init(self):

        self.name = "Pumpkin Bomb"
        
        self.level = 3
        self.tags = [Level.Tags.Dark, Level.Tags.Fire, Level.Tags.Sorcery]
        self.max_charges = 3
        self.radius = 2
        self.damage = 13
        self.range = 8
        self.burn_damage = 5
        self.stats.append('burn_damage')

        self.upgrades['radius'] = (1, 2)
        self.upgrades['damage'] = (10, 3)
        self.upgrades['chomp'] = (1, 5, "Soul Blazer", "Each enemy that took damage from this spell experiences its death via taking 10 [fire] damage due to this spell once.", "bombing")
        self.upgrades['nitro'] = (1, 4, "Nitro Blast", "Pumpkin bombs destroy walls and redeal half of their initial explosion damage as [fire] damage.", "bombing")
        self.upgrades['zero'] = (1, 6, "Zero-Space Burst", "Whenever you cast this spell, if it had an odd number of charges, pretend to cast a copy of it with 0 charges left.\nDeal damage twice to the center tile.", "bombing")

    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]

    def get_description(self):
        return ("Throw an explosive pumpkin, dealing [{damage}_dark_damage:dark] in a [{radius}-tile_burst:radius] and inflicting Soul Burn on hit enemies for 4 turns. This duration is fixed.\n"
                "Units with Soul Burn take [{burn_damage}_fire_damage:fire] each turn, plus equal [dark] damage if they are [living]."
                ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for point in stage:
                if point.x == x and point.y == y and self.get_stat('zero'):
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Dark, self)
                u = self.caster.level.get_unit_at(point.x, point.y)
                if u and Level.are_hostile(u, self.caster):
                    u.apply_buff(PumpkinBuff(self), 4)
                if self.get_stat('nitro'):
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Fire, self)
                dmg = self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Dark, self)
                if dmg and self.get_stat('chomp'):
                        self.caster.level.event_manager.raise_event(Level.EventOnDeath(u, Level.EventOnDamaged(u, 10, Level.Tags.Fire, self)), u)
                if self.caster.level.tiles[point.x][point.y].is_wall() and self.get_stat('nitro'):
                    self.caster.level.make_floor(point.x, point.y)
        if self.get_stat('zero') and ((self.cur_charges+1) % 2) == 1:
            zero_spell = copy(self)
            zero_spell.cur_charges = 0
            self.caster.level.event_manager.raise_event(Level.EventOnSpellCast(zero_spell, self.caster, x, y), self.caster)

Spells.all_player_spell_constructors.extend([Horsehead, NotThePose, ThePhrase, HauntUp, PumpkinThrow])