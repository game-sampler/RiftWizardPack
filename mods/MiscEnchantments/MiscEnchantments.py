import Spells
import Upgrades
import Level, LevelGen
import CommonContent
import Variants
import RareMonsters
import Monsters
import Upgrades
import text
import Consumables

import os, math, random, copy

import inspect 

frm = inspect.stack()[-1]
RiftWizard = inspect.getmodule(frm[0])

RiftWizard.tooltip_colors['requires_los'] = Level.Tags.Eye.color

assetize = lambda png: os.path.join("..","..","mods","MiscEnchantments","sprites",png)

class LuckBoonBuff(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        self.cleared = False
        Level.Buff.__init__(self)
        self.owner_triggers[Level.EventOnUnitAdded] = self.on_add

    def on_init(self):
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.color = Level.Tags.Holy.color
        self.name = "Fortunate"
    
    def on_advance(self):
        if self.owner.level.turn_no >= self.spell.get_stat('turn_threshold') and not self.cleared:
            self.owner.remove_buff(self)
        else:
            enemies = [u for u in self.owner.level.units if Level.are_hostile(u, self.owner)]
            if not enemies:
                self.cleared = True
    
    def on_add(self, evt):
        self.owner.remove_buff(self)

    def on_unapplied(self):
        if self.cleared:
            pool = [i[0] for i in Consumables.all_consumables if i[0] not in [Consumables.corruption_orb, Consumables.memory_draught]]
            pool.append(Consumables.heal_potion)
            if self.spell.get_stat('unsummon'):
                pool = [i for i in pool if i not in [Consumables.troll_crown, Consumables.bag_of_spikes, Consumables.bag_of_bags, Consumables.storm_troll_crown, Consumables.earth_troll_crown]]
            prop = LevelGen.make_consumable_pickup(random.choice(pool)())
            p = random.choice([u for u in self.owner.level.iter_tiles() if self.owner.level.tiles[u.x][u.y].can_walk])
            self.owner.level.add_prop(prop, p.x, p.y)
    
    def mark(self, point):
        self.owner.level.deal_damage(point.x, point.y, 0, Level.Tags.Holy, self)
        yield

class LuckBoon(Level.Spell):
    def on_init(self):
        self.name = "Boon of Fortune"
        self.level = 7
        self.max_charges = 1
        self.range = 0
        self.turn_threshold = 30
        self.stats.append('turn_threshold')
        self.tags = [Level.Tags.Holy, Level.Tags.Enchantment]

        self.upgrades['max_charges'] = (1, 2)
        self.upgrades['unsummon'] = (1, 6, "Lone Fortune", "Summoning items are removed from the pool, except dragon horns.")
        self.upgrades['turn_threshold'] = (10, 4, "Patient Fortune")
    
    def can_cast(self, x, y):
        return self.caster.level.turn_no == 1 and not self.caster.has_buff(LuckBoonBuff) and Level.Spell.can_cast(self, x, y)
    
    def get_description(self):
        return(
            "Can only be cast during the first turn of a realm.\n"
            "If you clear the current realm within [{turn_threshold}:holy] turns, an extra consumable appears in the next realm.\n"
            "This effect cannot create mana potions, draughts of memories, or orbs of corruption."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        self.caster.apply_buff(LuckBoonBuff(self))

class LifeAura(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Life Aura"
        self.color = Level.Tags.Spider.color
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.owner_triggers[Level.EventOnPreDamaged] = self.on_dmg
    
    def on_dmg(self, evt):
        if evt.damage > 0 and evt.damage < 9:
            self.owner.add_shields(1)

class MegaManReference(Level.Spell):
    def on_init(self):
        self.name = "Life Virus"
        self.tags = [Level.Tags.Nature, Level.Tags.Enchantment]
        self.level = 5
        self.max_charges = 4
        self.range = 9
        self.duration = 10
        self.can_target_empty = False

        self.upgrades['duration'] = (10, 3)
        self.upgrades['requires_los'] = (-1, 3, "Blindcasting", "Life Virus can be cast without line of sight.")
        self.upgrades['range'] = (3, 4)

    def can_cast(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        return u and not Level.are_hostile(self.caster, u) and Level.Spell.can_cast(self, x, y)
    
    def get_description(self):
        return(
            "Grants Life Aura to target ally for [{duration}_turns:duration].\n"
            "If an ally with Life Aura would take less than 9 damage before accounting for resistances, they immediately gain 1 SH before taking damage."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        if not u:
            return
        u.apply_buff(LifeAura(self), self.get_stat('duration'))

class SteelForm(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        self.can_casts = {}
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Steel Form"
        self.color = Level.Tags.Metallic.color
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.stack_type = Level.STACK_TYPE_TRANSFORM
        self.transform_asset_name = assetize("player_steel")
        if self.spell.get_stat('steel_force'):
            self.tag_bonuses[Level.Tags.Metallic]["damage"] = 4*self.spell.get_stat('steel_force')
            self.tag_bonuses[Level.Tags.Metallic]["range"] = self.spell.get_stat('steel_force')
        self.resists[Level.Tags.Physical] = 50
        self.resists[Level.Tags.Fire] = 50
        self.resists[Level.Tags.Ice] = 100
        self.resists[Level.Tags.Lightning] = 100
    
    def on_applied(self, owner):
        owner.max_hp += 50
        self.owner.cur_hp += 50
    
    def on_unapplied(self):
        self.owner.max_hp = max(1, self.owner.max_hp-50)
        if self.owner.cur_hp > self.owner.max_hp:
            self.owner.cur_hp = self.owner.max_hp
    
    def modify_spell(self, spell):
        if Level.Tags.Translocation in spell.tags:
            def cannot_cast(*args, **kwargs):
                return False

            self.can_casts[spell] = spell.can_cast
            spell.can_cast = cannot_cast

    def unmodify_spell(self, spell):
        if spell in self.can_casts:
            spell.can_cast = self.can_casts[spell]

class MetalMan(Level.Spell):
    def on_init(self):
        self.name = "Steel Form"
        self.level = 5
        self.max_charges = 2
        self.duration = 12
        self.range = 0
        self.tags = [Level.Tags.Metallic, Level.Tags.Enchantment]

        self.upgrades['steel_force'] = (2, 4, "Steel Force", "[Metallic] spells and skills gain 8 damage and 2 range while Steel Form is active.")
        self.upgrades['duration'] = (6, 3)
    
    def get_description(self):
        return(
            "Turn into steel for [{duration}_turns:duration].\n"
            "While in steel form, the Wizard gains 50 max HP and resists akin to that of a [metallic] unit.\n"
            "However, [translocation] spells cannot be cast."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        self.caster.apply_buff(SteelForm(self), self.get_stat('duration'))    

class PhantomForm(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        self.cur_pos = None
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Phantom Form"
        self.color = Level.Tags.Arcane.color
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.stack_type = Level.STACK_TYPE_TRANSFORM
        self.transform_asset_name = "player_phantom"
        self.resists[Level.Tags.Physical] = 100
        self.owner_triggers[Level.EventOnMoved] = self.on_move
    
    def on_pre_advance(self):
        self.cur_pos = Level.Point(self.owner.x, self.owner.y)
    
    def on_advance(self):
        affected = [u for u in self.owner.level.units if Level.are_hostile(self.owner, u) and Level.Tags.Undead in u.tags]
        for a in affected:
            if not a.is_coward:
                setattr(a, "phantomed", True)
                a.is_coward = True
    
    def on_unapplied(self):
        affected = [u for u in self.owner.level.units if Level.are_hostile(self.owner, u) and Level.Tags.Undead in u.tags]
        for a in affected:
            if hasattr(a, "phantomed"):
                a.is_coward = False
    
    def on_move(self, evt):
        if not self.owner.level.can_see(self.cur_pos.x, self.cur_pos.y, evt.x, evt.y):
            for u in self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('radius')):
                if self.owner.level.are_hostile(u, self.owner):
                    debuff = CommonContent.GlobalAttrBonus("damage", -4)
                    debuff.color = Level.Tags.Arcane.color
                    debuff.buff_type = Level.BUFF_TYPE_CURSE
                    debuff.name = "Surprised"
                    u.apply_buff(debuff, 2)
                    if self.spell.get_stat('venged'):
                        for s in u.spells:
                            s.cool_down += 2

class PhantomFormSpell(Level.Spell):
    def on_init(self):
        self.name = "Phantom Form"
        self.level = 6
        self.max_charges = 1
        self.duration = 13
        self.range = 0
        self.radius = 3
        self.tags = [Level.Tags.Arcane, Level.Tags.Enchantment]

        self.upgrades['radius'] = (2, 3)
        self.upgrades['duration'] = (6, 2)
        self.upgrades['venged'] = (1, 5, "Phantom Terror", "Surprised units have all of their cooldowns increased by 2.")
    
    def get_description(self):
        return(
            "Enter Phantom Form for [{duration}_turns:duration], gaining 100 [physical] resist.\n"
            "[Undead] enemies become terrified while Phantom Form is active and will flee instead of attacking.\n"
            "Whenever you move to a tile which is not visible from your original position, inflict [surprised:sorcery] on enemies in [{radius}_tiles:radius] of you for 2 turns.\n"
            "[Surprised:sorcery] units' attacks deal 4 less damage."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        self.caster.apply_buff(PhantomForm(self), self.get_stat('duration')) 

class Mirror(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Catoptric Veil"
        self.color = Level.Tags.Glass.color
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.global_triggers[Level.EventOnSpellCast] = self.on_cast
        self.global_bonuses['num_targets'] = self.spell.get_stat('split')
    
    def on_cast(self, evt):
        if evt.x == self.owner.x and evt.y == self.owner.y and Level.are_hostile(self.owner, evt.caster):
            potentials = [u for u in self.owner.level.get_units_in_los(self.owner) if Level.are_hostile(u, self.owner)]
            if len(potentials) > self.spell.get_stat('num_targets'):
                potentials = random.sample(potentials, self.spell.get_stat('num_targets'))
            if potentials:
                for u in potentials:
                    self.owner.level.queue_spell(evt.spell.cast(u.x, u.y))
            elif evt.caster == self.owner and self.spell.get_stat('ench'):
                if Level.Tags.Enchantment in evt.spell.tags and not any(t in [Level.Tags.Dark, Level.Tags.Arcane, Level.Tags.Holy] for t in evt.spell.tags) and not evt.spell.range:
                    refund = (7 - evt.spell.level)*0.05
                    if random.random() < refund and evt.spell.cur_charges < evt.spell.max_charges:
                        evt.spell.cur_charges += 1

class MirrorGoBrrr(Level.Spell):
    def on_init(self):
        self.name = "Catoptric Veil"
        self.level = 5
        self.max_charges = 2
        self.duration = 4
        self.range = 0
        self.num_targets = 2
        self.tags = [Level.Tags.Arcane, Level.Tags.Enchantment]

        self.upgrades['duration'] = (3, 3)
        self.upgrades['ench'] = (1, 5, "Thaumic Mirror", "While Catoptric Veil is active, self-targeting [enchantment] spells that are not [dark], [arcane], or [holy] have a 5% additive chance per spell level below 7 to regain a charge when cast.")
        self.upgrades['split'] = (1, 4, "Ley Splitters", "All spells and skills gain [1_num_targets:num_targets] while Catoptric Veil is active")
    
    def get_description(self):
        return(
            "Emit a reflective field around yourself for [{duration}_turns:duration].\n"
            "Whenever an enemy casts a spell on you, it bounces off the field, targeting up to [{num_targets}:num_targets] random enemies in line of sight."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        self.caster.apply_buff(Mirror(self), self.get_stat('duration'))

class AmmoBuff(Level.Buff):
    def __init__(self, spell, mag):
        self.spell = spell
        self.mag = mag
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Ammo %d" % self.mag
        self.color = Level.Tags.Metallic.color
        self.buff_type = Level.BUFF_TYPE_BLESS

class Succ(Level.Spell):
    def on_init(self):
        self.name = "Suck Cannon"
        self.level = 4
        self.max_charges = 12
        self.duration = 4
        self.range = 9
        self.damage = 22
        self.tags = [Level.Tags.Metallic, Level.Tags.Enchantment, Level.Tags.Sorcery]

        self.upgrades['requires_los'] = (-1, 4, "Blindcasting", "Suck Cannon can be cast without line of sight.")
        self.upgrades['damage'] = (22, 3)
        self.upgrades['max_charges'] = (8, 3)
        self.upgrades['vortex_plus'] = (1, 2, "Vortex Engine", "Targets gain flying while being pulled in if they are not flying already.")
        self.upgrades['zapper'] = (1, 4, "Zap Cannon", "Suck Cannon shots redeal a third of their [physical] damage as [lightning] damage.")

    def get_impacted_tiles(self, x, y):
        if not self.caster.has_buff(AmmoBuff):
            return [Level.Point(x, y)]
        else:
            rad = math.ceil(math.sqrt(self.caster.get_buff(AmmoBuff).mag) // 2)
            return [p for p in self.caster.level.get_points_in_ball(x, y, rad)]
    
    def can_cast(self, x, y):
        if not self.caster.has_buff(AmmoBuff):
            u = self.caster.level.get_unit_at(x, y)
            if not u:
                return False
            return Level.Spell.can_cast(self, x, y) and Level.are_hostile(u, self.caster)
        else:
            return Level.Spell.can_cast(self, x, y) 
    
    def get_description(self):
        return(
            "Use a vortex to pull the target as close as possible to you along a path consisting of tiles that it can move on, dealing [4_physical:physical] damage per square traveled.\n"
            "Afterwards, if the target is adjacent to you and has less than half of its HP remaining, it immediately dies.\n"
            "When the target dies, gain Ammo X, where X is the target's maximum HP.\n"
            "Casting Suck Cannon again while Ammo is active will launch the unit at the selected point dealing [{damage}_physical:physical] damage in a radius based on Ammo's magnitude."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        if not self.caster.has_buff(AmmoBuff):
            u = self.caster.level.get_unit_at(x, y)
            path = self.caster.level.get_points_in_line(u, self.owner, find_clear=True, two_pass=True)[1:-1][:99]
            triggered = False
            if not u.flying and self.get_stat('vortex_plus'):
                u.flying = True
            for p in path:
                if self.caster.level.can_move(u, p.x, p.y, teleport=True):
                    self.caster.level.act_move(u, p.x, p.y, teleport=True)
                    self.caster.level.leap_effect(p.x, p.y, Level.Tags.Physical.color, u)
                else:
                    break
            p = u.max_hp
            u.deal_damage(4*(len(path)), Level.Tags.Physical, self)
            if triggered:
                u.flying = False
            if Level.distance(u, self.caster) <= 1.5 and u.cur_hp < (u.max_hp // 2):
                u.kill()
            if not u.is_alive():
                self.caster.apply_buff(AmmoBuff(self, p))
        else:
            rad = math.ceil(math.sqrt(self.caster.get_buff(AmmoBuff).mag) // 2)
            if rad < 1:
                rad = 1
            for p in self.caster.level.get_points_in_ball(x, y, rad):
                self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Level.Tags.Physical, self)
                if self.get_stat('zapper'):
                    self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage') // 3, Level.Tags.Lightning, self)
                self.caster.remove_buff(self.caster.get_buff(AmmoBuff))

class BrokenTime(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        self.points = None
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Unstable Spacetime"
        self.color = Level.Tags.Chaos.color
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.owner_triggers[Level.EventOnSpellCast] = self.on_cast
    
    def on_applied(self, owner):
        self.points = [p for p in owner.level.get_points_in_ball(owner.x, owner.y, self.spell.get_stat('radius'))]
    
    def on_advance(self):
        self.points = [p for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.spell.get_stat('radius'))]
        targets = [self.owner.level.get_unit_at(p.x, p.y) for p in self.points]
        targets = [t for t in targets if t != None]
        if not targets:
            return
        for u in targets:
            if not Level.are_hostile(self.owner, u) and (Level.Tags.Chaos in u.tags or "chaos" in u.name.lower()) and random.random() < .1:
                for s in u.spells:
                    u.cool_downs[s] = 0
            elif Level.Tags.Chaos not in u.tags and Level.are_hostile(self.owner, u):
                for dtype in [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Physical]:
                    u.deal_damage(3, dtype, self)

    def on_cast(self, evt):
        if evt.spell.range <= 0 or Level.Tags.Conjuration in evt.spell.tags or Level.Tags.Chaos not in evt.spell.tags:
            return
        p = Level.Point(evt.x, evt.y)
        if Level.distance(p, self.owner) <= self.spell.get_stat('radius') and not hasattr(evt.spell, "distorted") and random.random() < .33:
            spell = copy.copy(evt.spell)
            setattr(spell, "distorted", True)
            spots = [p for p in self.points if evt.spell.can_cast(p.x, p.y)]
            if not spots:
                return
            pt = random.choice(spots)
            self.owner.level.act_cast(evt.caster, spell, pt.x, pt.y, pay_costs=False)   

class TimeBreak(Level.Spell): 
    def on_init(self):
        self.name = "Discontinuate"
        self.level = 7
        self.max_charges = 1
        self.duration = 7
        self.range = 0
        self.radius = 5
        self.tags = [Level.Tags.Chaos, Level.Tags.Enchantment]

        self.upgrades['max_charges'] = (2, 4)
        self.upgrades['duration'] = (4, 2)
        self.upgrades['radius'] = (1, 3)
    
    def get_description(self):
        return(
            "Destabilize spacetime in [{radius}_tiles:radius] of yourself, gaining Unstable Spacetime for [{duration}_turns:duration].\n"
            "Enemies inside the region take 3 fixed [physical], [fire], and [lightning] damage. [Chaos] units are immune.\n"
            "[Chaos] spells cast inside the region, excluding self-targeting and [conjuration] spells, have a 33% chance to be cast again for free targeting a random valid tile in the region if possible.\n"
            "Each turn, [chaos] allies and allies with \"chaos\" in their names inside the region have a 10% chance for all of their cooldowns to be reset."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        self.caster.apply_buff(BrokenTime(self), self.get_stat('duration'))

class ElectricBurnBuff(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Thermionic Emission"
        self.color = Level.Tags.Metallic.color
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.owner_triggers[Level.EventOnDamaged] = self.on_damaged

    def on_advance(self):
        if self.owner.resists[Level.Tags.Fire] >= 100 or Level.Tags.Metallic not in self.owner.tags:
            self.owner.remove_buff(self)
        self.owner.deal_damage((self.spell.get_stat('damage') // 2), Level.Tags.Fire, self)
        if random.random() < .33 and self.spell.get_stat('retrigger'):
            self.owner.level.event_manager.raise_event(Level.EventOnDamaged(self.owner, (self.spell.get_stat('damage') // 2), Level.Tags.Fire, self), self.owner)
    
    def on_damaged(self, evt):
        dmg = evt.damage
        if evt.source != self.spell and self.spell.get_stat('accept'):
            dmg *= 2
        if evt.damage_type != Level.Tags.Fire:
            return
        points = [p for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.spell.get_stat('radius')) if not self.owner.level.tiles[p.x][p.y].is_wall()]
        if self.spell.get_stat('smart'):
            for p in points:
                u = self.owner.level.get_unit_at(p.x, p.y)
                if u and not Level.are_hostile(u, self.owner):
                    points.remove(p)
        num_bolts = (dmg // 2)
        if num_bolts < 1 + self.spell.get_stat('conductive'):
            num_bolts = 1 + self.spell.get_stat('conductive')
        finals = random.choices(points, k=num_bolts)
        for f in finals:
            for p in CommonContent.Bolt(self.owner.level, self.owner, f):
                u = self.owner.level.get_unit_at(p.x, p.y)
                if self.spell.get_stat('smart') and u and not Level.are_hostile(u, self.owner):
                    continue
                self.owner.level.deal_damage(p.x, p.y, self.spell.get_stat('damage'), Level.Tags.Lightning, self.spell)

class ElectricBurn(Level.Spell): 
    def on_init(self):
        self.name = "Thermionic Module"
        self.level = 4
        self.max_charges = 2
        self.duration = 13
        self.damage = 7
        self.radius = 4
        self.range = 6
        self.tags = [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Metallic, Level.Tags.Enchantment]

        self.upgrades['damage'] = (5, 3)
        self.upgrades['smart'] = (1, 2, "Onboard Targeting", "Lightning flashes will no longer target allies' spaces.")
        self.upgrades['conductive'] = (2, 3, "Enhanced Conductance", "The minimum number of flashes becomes 3.")
        self.upgrades['retrigger'] = (1, 4, "Insulated Components", "Whenever the module deals damage, there is a 33% chance that the ally will pretend to take that much damage again.")
        self.upgrades['accept'] = (1, 5, "Heat Acceptors", "Damage from sources other than this spell counts double.")

    def can_cast(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        if not u:
            return False
        elif Level.are_hostile(u, self.caster) or Level.Tags.Metallic not in u.tags or u.resists[Level.Tags.Fire] >= 100:
            return False
        else:
            return Level.Spell.can_cast(self, x, y)
    
    def fmt_dict(self):
        d = Level.Spell.fmt_dict(self)
        d['self_damage'] = d['damage'] // 2
        return d
    
    def get_description(self):
        return(
            "Attach a thermionic module to target [metallic] ally for [{duration}_turns:duration].\n"
            "Each turn, that ally takes [{self_damage}_fire:fire] damage.\n"
            "Whenever that ally takes [fire] damage, energy is sent out of the module, creating flashes of lightning.\n"
            "For every 2 fire damage the unit took, a flash strikes a random tile in [{radius}_tiles:radius] of them, dealing [{damage}_lightning:lightning] damage in a beam. There will always be at least one flash.\n"
            "The module will be removed if the unit becomes immune to fire or loses [metallic], and this spell cannot target units immune to fire."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        u.apply_buff(ElectricBurnBuff(self), self.get_stat('duration'))

class AshCloud(Level.Cloud):

    def __init__(self, owner, spell):
        Level.Cloud.__init__(self)
        self.owner = owner
        self.duration = spell.get_stat('duration')
        self.name = "Ash Storm"
        self.source = spell
        self.asset_name = "ash_storm"
        self.spell = spell

    def get_description(self):
        return "Pulls in enemies within %d tiles, deals 3 [fire] damage to units inside, [blinds:blind] units inside for %d turns, [poisons:poison] units inside for %d turns, and throws units inside away." % (self.spell.get_stat('pull_radius'), self.spell.get_stat('blind_duration'), self.spell.get_stat('blind_duration')*8)

    def on_advance(self):
        pull_points = [p for p in self.owner.level.get_points_in_ball(self.x, self.y, self.spell.get_stat('pull_radius'))]
        for p in pull_points:
            u = self.owner.level.get_unit_at(p.x, p.y)
            if u and Level.are_hostile(u, self.owner):
                fly_triggered = False
                if self.spell.get_stat('velocity') and not u.flying:
                    u.flying = fly_triggered = True
                path = self.owner.level.get_points_in_line(u, Level.Point(self.x, self.y), find_clear=True, two_pass=True)[1:-1][:99]
                for p in path:
                    if self.owner.level.can_move(u, p.x, p.y, teleport=True):
                        self.owner.level.act_move(u, p.x, p.y, teleport=True)
                        self.owner.level.leap_effect(p.x, p.y, Level.Tags.Fire.color, u)
                    else:
                        break
                if Level.distance(u, self) <= 1.5 and self.owner.level.can_move(u, self.x, self.y, teleport=True):
                    self.owner.level.act_move(u, self.x, self.y, teleport=True)
                if fly_triggered:
                    u.flying = False
            hit_unit = self.owner.level.get_unit_at(self.x, self.y)
            if hit_unit:
                hit_unit.apply_buff(Level.BlindBuff(), self.spell.get_stat('blind_duration'))
                hit_unit.apply_buff(CommonContent.Poison(), self.spell.get_stat('blind_duration')*8)
                hit_unit.deal_damage(3, Level.Tags.Fire, self.spell)
                throw_points = [p for p in self.owner.level.get_points_in_ball(self.x, self.y, 7) if Level.distance(p, self) > self.spell.get_stat('pull_radius') and self.owner.level.can_move(hit_unit, p.x, p.y, teleport=True)]
                if not throw_points:
                    return
                throw_loc = random.choice(throw_points)
                self.owner.level.act_move(hit_unit, throw_loc.x, throw_loc.y, teleport=True)
                hit_unit.deal_damage(0, Level.Tags.Fire, self)


class AshStorm(Level.Spell): 
    def on_init(self):
        self.name = "Ash Tempest"
        self.level = 5
        self.max_charges = 3
        self.duration = 14
        self.range = 8
        self.pull_radius = 3
        self.blind_duration = 2
        self.stats.extend(['pull_radius', 'blind_duration'])
        self.tags = [Level.Tags.Fire, Level.Tags.Dark, Level.Tags.Nature, Level.Tags.Enchantment]

        self.must_target_empty = True

        self.upgrades['pull_radius'] = (2, 3)
        self.upgrades['blind_duration'] = (1, 2)
        self.upgrades['requires_los'] = (-1, 4, "Blindcasting", "Ash Tempest can be cast without line of sight")
        self.upgrades['velocity'] = (1, 3, "Ashen Violence", "Pulled units temporarily become flying while being pulled into the storm if they are not already.")
        self.upgrades['boom'] = (1, 5, "Ash Combustion", "Targeting an ash storm with this spell explodes it, dealing 7 [fire] and [dark] damage in the cloud's pull radius, [blinding:blind] units inside for 5 turns, and [poisoning:poison] them for 30 turns.")
    
    def can_cast(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        if u and not self.get_stat('boom'):
            return False
        elif self.caster.level.tiles[x][y].cloud != None and self.get_stat('boom'):
            return True if type(self.caster.level.tiles[x][y].cloud) == AshCloud else Level.Spell.can_cast(self, x, y)
        else:
            return Level.Spell.can_cast(self, x, y)
    
    def get_impacted_tiles(self, x, y):
        if self.caster.level.tiles[x][y].cloud != None and self.get_stat('boom'):
            if type(self.caster.level.tiles[x][y].cloud) == AshCloud:
                return [p for p in self.caster.level.get_points_in_ball(x, y, self.get_stat('pull_radius'))]
        return [Level.Point(x, y)]


    def fmt_dict(self):
        d = Level.Spell.fmt_dict(self)
        d['poison_dur'] = d['blind_duration']*8
        return d
    
    def get_description(self):
        return(
            "Summon a violent ash storm on target tile.\n"
            "Ash storms pull in enemy units in [{pull_radius}_tiles:radius], along a path consisting of tiles that those units can move on.\n"
            "If a unit is pulled into the cloud, they take 3 [fire] damage, are blinded for [{blind_duration}_turns:blind], are poisoned for [{poison_dur}_turns:poison], and are thrown away from the cloud to a random tile that is not in the cloud's pull radius up to 7 tiles away.\n"
            "The storm's fire damage is fixed.\n"
            "Ash storms last [{duration}_turns:duration]"
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        if self.get_stat('boom') and self.caster.level.tiles[x][y].cloud != None:
            if type(self.caster.level.tiles[x][y].cloud) == AshCloud:
                for p in [p for p in self.caster.level.get_points_in_ball(x, y, self.get_stat('pull_radius'))]:
                    for d in [Level.Tags.Fire, Level.Tags.Dark]:
                        self.caster.level.deal_damage(p.x, p.y, 7, d, self)
                    u = self.caster.level.get_unit_at(p.x, p.y)
                    if u:
                        u.apply_buff(Level.BlindBuff(), 5)
                        u.apply_buff(CommonContent.Poison(), 30)
                self.caster.level.remove_obj(self.caster.level.tiles[x][y].cloud)
        else:
            self.caster.level.add_obj(AshCloud(self.caster, self), x, y)

class Imperm(Level.Spell):
    def on_init(self):
        self.name = "Impermanence"
        self.level = 4
        self.max_charges = 4
        self.range = 7
        self.tags = [Level.Tags.Enchantment]

        self.can_target_empty = False

        self.upgrades['range'] = (3, 4)
        self.upgrades['requires_los'] = (-1, 3, "Blindcasting", "Impermanence can be cast without line of sight.")
        self.upgrades['help'] = (1, 3, "Impermanent Aid", "Allies targeted by Impermanence do not lose buffs or die.\nInstead, affected temporary allies gain 7 duration. Allies with temporary buffs gain 7 duration to those buffs.")
        self.upgrades['mass'] = (1, 3, "Fleeting Masses", "Impermanence affects units in a square extending 2 tiles from the target.")

    def get_impacted_tiles(self, x, y):
        points = [Level.Point(x, y)]
        if self.get_stat('mass'):
            points = [p for p in self.owner.level.get_points_in_ball(x, y, 2, diag=True)]   
        return points

    def get_description(self):
        return(
            "Target unit loses all buffs. If it is a temporary unit, it immediately dies."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        points = self.get_impacted_tiles(x, y)
        for p in points:
            u = self.caster.level.get_unit_at(p.x, p.y)
            if not u or u == self.caster:
                continue
            elif u and not Level.are_hostile(u, self.caster) and self.get_stat('help'):
                if u.turns_to_death:
                    u.turns_to_death += 7
                for b in u.buffs:
                    if b.turns_left:
                        b.turns_left += 7
            else:
                for b in u.buffs:
                    if b.buff_type == Level.BUFF_TYPE_BLESS:
                        u.remove_buff(b)
                if u.turns_to_death:
                    u.kill()

class ThermoUnstable(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Thermal Instability"
        self.color = Level.Tags.Fire.color
        self.buff_type = Level.BUFF_TYPE_CURSE
        self.owner_triggers[Level.EventOnPreDamaged] = self.on_damaged
        self.owner_triggers[CommonContent.EventOnBuffRemove] = self.on_unfreeze
    
    def on_damaged(self, evt):
        if evt.damage_type != Level.Tags.Ice and (evt.damage // 3) <= 0:
            return
        self.owner.deal_damage((evt.damage // 3), Level.Tags.Fire, self)
    
    def on_unfreeze(self, evt):
        if not isinstance(evt.buff, CommonContent.FrozenBuff) or evt.buff.break_dtype != Level.Tags.Fire:
            return
        if evt.buff.turns_left:
            if (evt.buff.turns_left // 2) > 0:
                turns = ((evt.buff.turns_left*3) // 4) if self.spell.get_stat('refreezer') else (evt.buff.turns_left // 2)
                evt.unit.apply_buff(CommonContent.FrozenBuff(), turns)
            dmg = self.spell.get_stat('damage') + self.spell.get_stat('frozen_bonus')*evt.buff.turns_left
            ring = [p for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, evt.buff.turns_left) if Level.distance(p, self.owner) > (evt.buff.turns_left // 2)]
            if not ring:
                return
            for point in ring:
                if point.x == self.owner.x and point.y == self.owner.y:
                    continue
                u = self.owner.level.get_unit_at(point.x, point.y)
                if u and not Level.are_hostile(u, self.spell.caster) and self.spell.get_stat('controlled'):
                    continue
                self.owner.level.deal_damage(point.x, point.y, dmg, Level.Tags.Fire, self)

class ThermoSynergy(Level.Spell):
    def on_init(self):
        self.name = "Heat Shift"
        self.level = 6
        self.max_charges = 4
        self.duration = 9
        self.range = 8
        self.damage = 5
        self.frozen_bonus = 1
        self.stats.extend(['frozen_bonus'])
        self.tags = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Enchantment]

        self.can_target_empty = False

        self.upgrades['duration'] = (3, 2)
        self.upgrades['frozen_bonus'] = (1, 3, "Frozen Bonus", "Thermal Instability's fire ring deals an extra 1 damage per turn of [frozen].")
        self.upgrades['controlled'] = (1, 2, "Controlled Energy", "Thermal Instability's fire ring will not harm allies.")
        self.upgrades['refreezer'] = (1, 5, "Enhanced Displacement", "Unfrozen units with Thermal Instability are refrozen at three-quarters of their original duration instead of half.")

    def get_description(self):
        return(
            "Curse a unit with Thermal Instability for [{duration}_turns:duration].\n"
            "Whenever a unit with Thermal Instability is unfrozen by [fire] damage, heat is moved away from them, refreezing them at half the original duration. The displaced heat deals [{damage}_fire:fire] damage, plus [{frozen_bonus}_extra_fire_damage:fire] per turn of [frozen] that was on the target, in a ring based on the number of turns of [frozen] on the unit.\n"
            "Whenever a unit with Thermal Instability takes [ice] damage, heat is moved towards them, redealing a third of that damage as [fire] damage."
        ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        u = self.owner.level.get_unit_at(x, y)
        u.apply_buff(ThermoUnstable(self), self.get_stat('duration'))

class PlasmaBuff(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Plasma Storm"
        self.color = Level.Tags.Lightning.color
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.tag_bonuses[Level.Tags.Lightning]['requires_los'] = -1
        self.global_triggers[Level.EventOnDamaged] = self.on_damage
        if self.spell.get_stat('recover'):
            self.owner_triggers[Level.EventOnSpellCast] = self.recover_proc
    
    def on_advance(self):
        for unit in (list(self.owner.level.units)):
            unit.deal_damage(1, random.choice([Level.Tags.Lightning, Level.Tags.Fire]), self.spell)
        if not self.spell.get_stat('barrier'):
            self.owner.deal_damage(1, random.choice([Level.Tags.Lightning, Level.Tags.Fire]), self.spell)

    def on_damage(self, evt):
        if evt.source == self.spell or evt.damage_type != Level.Tags.Lightning:
            return
        for s in CommonContent.Burst(self.owner.level, Level.Point(evt.unit.x, evt.unit.y), 1, ignore_walls=True):
            for p in s:
                self.owner.level.deal_damage(p.x, p.y, 1, Level.Tags.Fire, self)
    
    def recover_proc(self, evt):
        if Level.Tags.Lightning not in evt.spell.tags or evt.spell.cur_charges >= evt.spell.max_charges:
            return
        odds = (7 - evt.spell.level) * .03
        if random.random() < odds:
            evt.spell.cur_charges += 1

class HeatAir(Level.Spell): 
    def on_init(self):
        self.name = "Plasma Storm"
        self.level = 7
        self.max_charges = 1
        self.duration = 10
        self.range = 0
        self.tags = [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Enchantment]

        self.upgrades['duration'] = (5, 4)
        self.upgrades['max_charges'] = (1, 2)
        self.upgrades['recover'] = (1, 6, "Ionic Assimilation", "[Lightning] spells cast while Plasma Storm is active have a 3% chance per spell level below 7 to regain a charge.")
        self.upgrades['barrier'] = (1, 3, "Plasma Shield", "The caster is only hit once.")
    
    def get_description(self):
        return(
            "Heat the environment into plasma for [{duration}_turns:duration].\n"
            "Each turn, all units take 1 fixed [fire] or [lightning] damage randomly. The caster takes damage twice.\n"
            "While Plasma Storm is active, [lightning] spells can be cast without line of sight.\n"
            "Whenever a unit takes [lightning] damage from a source other than Plasma Storm, deal 1 fixed [fire] damage in a [1-tile_burst:radius]."
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        self.caster.apply_buff(PlasmaBuff(self), self.get_stat('duration'))

class MetalIceBuff(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        self.affected = []
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Active Cooling"
        self.color = Level.Tags.Ice.color
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.resists[Level.Tags.Ice] = -50

    def on_advance(self):
        self.owner.deal_damage(1, Level.Tags.Ice, self.spell)
    
    def on_applied(self, owner):
        if Level.are_hostile(self.owner, self.spell.caster) and self.spell.get_stat('tested'):
            return
        elif not Level.are_hostile(self.owner, self.spell.caster):
            self.resists[Level.Tags.Ice] += self.spell.get_stat('tested')
        for s in owner.spells:
            if s.cool_down > 2:
                s.cool_down -= 2
                self.affected.append(s)

    def on_unapplied(self):
        for s in self.owner.spells:
            if s in self.affected:
                s.cool_down += 2
        self.affected.clear()
        if self.spell.get_stat('cold_eject'):
            dmg = 2*(self.spell.get_stat('duration')-self.turns_left)
            for p in [p for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, 2)]:
                self.owner.level.deal_damage(p.x, p.y, dmg, Level.Tags.Ice, self)
                
class MetalIce(Level.Spell):
    def on_init(self):
        self.name = "Coolant Injection"
        self.level = 3  
        self.max_charges = 3
        self.duration = 5
        self.range = 6  
        self.tags = [Level.Tags.Ice, Level.Tags.Enchantment, Level.Tags.Metallic]

        self.upgrades['duration'] = (4, 2)
        self.upgrades['max_charges'] = (2, 3)
        self.upgrades['tested'] = (50, 3, "Calibrated Cooling", "Ally targets no longer lose [ice] resistance, and enemy targets no longer gain cooldown reduction.")
        self.upgrades['cold_eject'] = (1, 4, "Dispersive Coolant", "When Active Cooling expires, it deals 2 [ice] damage per turn it was on the target in a 2-tile burst.")

    def can_cast(self, x, y):
        u = self.owner.level.get_unit_at(x, y)
        if not u:
            return False
        elif u.has_buff(Spells.IronSkinBuff):
            return not u.get_buff(Spells.IronSkinBuff).nonmetal
        return False if Level.Tags.Metallic not in u.tags else Level.Spell.can_cast(self, x, y)

    def get_description(self):
        return(
            "Target [metallic] unit gains Active Cooling for [{duration}_turns:duration].\n"
            "The unit loses 50 [ice] resistance and takes 1 fixed [ice] damage every turn, but each of its spells that has a cooldown greater than 2 loses 2 cooldown.\n"
            "Cannot target units that are not [metallic] or non-[metallic] units affected by Ironize."
        ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        u = self.owner.level.get_unit_at(x, y)
        if not u:
            return
        u.apply_buff(MetalIceBuff(self), self.get_stat('duration'))

class ShardPlayerBuff(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        self.affected = []
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Hail Barrier"
        self.color = Level.Tags.Ice.color
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.owner_triggers[Level.EventOnDamaged] = self.on_damage

    def on_damage(self, evt):
        if evt.damage_type == Level.Tags.Fire and not self.spell.get_stat('resist'):
            self.owner.remove_buff(self)
            return
        else:
            units = [u for u in self.owner.level.get_units_in_los(self.owner) if Level.are_hostile(u, self.owner) and Level.distance(u, self.owner) <= self.spell.get_stat('radius')]
            if not units:
                return
            unit = random.choice(units)
            unit.deal_damage(5, Level.Tags.Ice, self.spell)

class IcicleLoom(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Looming Hail"
        self.color = Level.Tags.Ice.color
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.owner_triggers[Level.EventOnDamaged] = self.on_damage

    def on_damage(self, evt):
        if evt.damage_type == Level.Tags.Fire and not self.spell.get_stat('resist'):
            self.owner.remove_buff(self)
            return
    
    def on_advance(self):
        self.owner.deal_damage(5, Level.Tags.Ice, self.spell)

class IcicleTypeShit(Level.Spell):
    def on_init(self):
        self.name = "Snow Cloak"
        self.level = 4 
        self.max_charges = 3
        self.duration = 9
        self.range = 6  
        self.radius = 3
        self.tags = [Level.Tags.Ice, Level.Tags.Enchantment]

        self.upgrades['radius'] = (2, 4)
        self.upgrades['duration'] = (6, 3)
        self.upgrades['homing'] = (1, 3, "Hail Command", "Casting this spell on a unit with Looming Hail will consume the remaining duration of it and deal 5 [ice] damage to them per turn of duration.\nThis damage is dealt in one hit per turn of duration.")
        self.upgrades['resist'] = (1, 3, "Zero Hail", "Hail Barrier and Looming Hail can no longer be removed by [fire] damage.\nAdditionally, Hail Barrier will now activate when taking [fire] damage.")

        self.can_target_self = True
        self.can_target_empty = False

    def get_impacted_tiles(self, x, y):
        return [Level.Point(x, y)] if (x != self.caster.x or y != self.caster.y) else Level.Spell.get_impacted_tiles(self, x, y)

    def get_description(self):
        return(
            "If targeting yourself, gain Hail Barrier for [{duration}_turns:duration].\n"
            "While you have Hail Barrier, whenever you take damage from a spell except [fire] damage, deal 5 [ice] damage to a random enemy unit in line of sight within [{radius}_tiles:radius] of you. Fire damage will remove Hail Barrier.\n"
            "If targeting another unit, inflict Looming Hail for [{duration}_turns:duration].\n"
            "Units with Looming Hail take 5 [ice] damage every turn. Looming Hail will be removed by [fire] damage.\n"
            "This spell's damage is fixed."
        ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        u = self.owner.level.get_unit_at(x, y)
        if not u:
            return
        elif u == self.caster:
            self.caster.apply_buff(ShardPlayerBuff(self), self.get_stat('duration'))   
        elif u.has_buff(IcicleLoom) and self.get_stat('homing'):
            def hit(unit, dtype):
                unit.deal_damage(5, dtype, self)
                yield
            buff = u.get_buff(IcicleLoom)
            for i in range(buff.turns_left):
                self.caster.level.queue_spell(hit(u, Level.Tags.Ice))
            u.remove_buff(buff)
        else:
            u.apply_buff(IcicleLoom(self), self.get_stat('duration'))

class TimeManip(Level.Spell):
    def on_init(self):
        self.name = "Chronoacceleration"
        self.level = 4 
        self.max_charges = 5
        self.range = 7  
        self.hits = 3
        self.stats.extend(["hits"])
        self.tags = [Level.Tags.Enchantment]

        self.upgrades['hits'] = (2, 4, "Warpspeed", "Turn-based effects activate 2 extra times.")
        self.upgrades['range'] = (2, 2)
        self.upgrades['requires_los'] = (-1, 4, "Blindcasting", "Chronoacceleration can be cast without line of sight.")
        self.upgrades['adaptable'] = (1, 3, "Adaptability", "Enemies will only have debuffs affected by this spell, and allies will only have passive effects and buffs affected by this spell.")

        self.can_target_empty = False

    def get_description(self):
        return(
            "Each of the target's buffs, debuffs, and passive effects activates its turn-based effect [{hits}_times:num_targets]."
        ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        u = self.caster.level.get_unit_at(x, y)
        if not u:
            return
        for b in u.buffs:
            if self.get_stat('adaptable') and not Level.are_hostile(u, self.caster) and b.buff_type == Level.BUFF_TYPE_CURSE:
                continue
            elif self.get_stat('adaptable') and Level.are_hostile(u, self.caster) and b.buff_type in [Level.BUFF_TYPE_PASSIVE, Level.BUFF_TYPE_BLESS]:
                continue
            for _ in range(self.get_stat('hits')):
                b.on_advance()

class Karma(Level.Spell):
    def on_init(self):
        self.name = "Karmic Inversion"
        self.level = 3
        self.max_charges = 6
        self.range = 7  
        self.tags = [Level.Tags.Enchantment, Level.Tags.Dark, Level.Tags.Holy]

        self.can_target_empty = False

        self.upgrades['range'] = (3, 2)
        self.upgrades['requires_los'] = (-1, 3, "Blindcasting", "Karmic Inversion can be cast without line of sight")
        self.upgrades['arcane'] = (1, 3, "Invert Arcana", "[Arcane] units lose 100 [arcane] resist and [arcane], and gain [nature] if they do not already have it and 100 [poison] resistance.")
        self.upgrades['judge'] = (1, 4, "Reverse Judgment", "Affected [dark], [demon] and [undead] units take one-third of their current HP as [dark] damage.\nAffected [holy] units take one-third of their current HP as [holy] damage.")

    def get_impacted_tiles(self, x, y):
        return Spells.EssenceFlux.get_impacted_tiles(self, x, y)

    def get_description(self):
        return(
            "Karmically realign a group of units.\n"
            "[Dark], [demon] and [undead] units lose those tags and 100 [dark] resist, then gain [holy] if they do not already have it and 100 [holy] resist.\n"
            "[Holy] units lose 100 [holy] resist and [holy], then randomly gain one of [dark], [demon], or [undead] that they do not already have.\n"
            "Units that are both [dark] and [holy] will be subjected to the first effect only.\n"
            "These effects are permanent."
        ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        points = self.get_impacted_tiles(x, y)
        for p in points:
            unit = self.caster.level.get_unit_at(p.x, p.y)
            if unit:
                if any(t in [Level.Tags.Demon, Level.Tags.Dark, Level.Tags.Undead] for t in unit.tags):
                    for t in set(unit.tags).intersection(set([Level.Tags.Demon, Level.Tags.Undead, Level.Tags.Dark])):
                        unit.tags.remove(t)
                    unit.resists[Level.Tags.Dark] -= 100
                    if Level.Tags.Holy not in unit.tags:
                        unit.tags.append(Level.Tags.Holy)
                    unit.resists[Level.Tags.Holy] += 100
                    if self.get_stat('judge'):
                        unit.deal_damage((unit.cur_hp // 3), Level.Tags.Dark, self)
                elif Level.Tags.Holy in unit.tags:
                    unit.tags.remove(Level.Tags.Holy)
                    unit.resists[Level.Tags.Dark] += 100
                    unit.resists[Level.Tags.Holy] -= 100
                    valids = [t for t in [Level.Tags.Demon, Level.Tags.Dark, Level.Tags.Undead] if t not in unit.tags]
                    if valids:
                        unit.tags.append(random.choice(valids))
                    if self.get_stat('judge'):
                        unit.deal_damage((unit.cur_hp // 3), Level.Tags.Holy, self)
                elif Level.Tags.Arcane in unit.tags and self.get_stat('arcane'):
                    unit.tags.remove(Level.Tags.Arcane)
                    if Level.Tags.Nature not in unit.tags:
                        unit.tags.append(Level.Tags.Nature)
                    unit.resists[Level.Tags.Poison] += 100


class DeathBoom(Level.Spell):
    def on_init(self):
        self.name = "Dead Ringer"
        self.level = 5
        self.max_charges = 4
        self.range = 0
        self.damage = 22
        self.radius = 7  
        self.shields = 2
        self.tags = [Level.Tags.Enchantment, Level.Tags.Arcane, Level.Tags.Sorcery]

        self.upgrades['damage'] = (22, 3)
        self.upgrades['shields'] = (1, 2)
        self.upgrades['wallbust'] = (1, 3, "Crushing Wave", "Dead Ringer destroys walls in its impacted area.")
        self.upgrades['killer'] = (1, 5, "Killer Noise", "Each tile has a 30% chance to be damaged three times instead of one.", "sound")
        self.upgrades['mind'] = (1, 5, "Pink Boom", "Dead Ringer also deals [arcane] damage.", "sound")

    def get_description(self):
        return(
            "You gain 1 reincarnation, then instantly die.\n"
            "The sound of your death emits a shockwave dealing [{damage}_physical_damage:physical] in a [{radius}-tile_radius:radius]. The shockwave ignores walls.\n"
            "After dying, you are teleported to a random tile, and you gain [{shields}_SH:shield] if you do not have any."
        ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        self.caster.apply_buff(CommonContent.ReincarnationBuff(1))
        for p in self.caster.level.get_points_in_ball(x, y, self.get_stat('radius')):
            for _ in range(1 + (2 if random.random() < .3 and self.get_stat('killer') else 0)):
                self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Level.Tags.Physical, self)
                if self.get_stat('mind'):
                    self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Level.Tags.Arcane, self)
                if self.get_stat('wallbust') and self.caster.level.tiles[p.x][p.y].is_wall():
                    self.caster.level.make_floor(p.x, p.y)
        self.caster.kill()
        def shield(self):
            if not self.caster.shields:
                yield self.caster.add_shields(2) 
            yield
        self.owner.level.queue_spell(shield(self))

class PyreBuff(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)

    def on_init(self):
        self.name = "Living Flame"
        self.color = Level.Tags.Fire.color
        self.buff_type = Level.BUFF_TYPE_BLESS
        self.global_triggers[Level.EventOnUnitAdded] = self.on_add

    def get_modifier(self):
        accepted = [Level.Tags.Fire, Level.Tags.Nature]
        if self.spell.get_stat('ice'):
            accepted.append(Level.Tags.Ice)
        modifier = sum([self.spell.get_stat('bonus_per_spell') for s in self.owner.spells if any(t in accepted for t in s.tags)])
        return modifier

    def on_applied(self, owner):
        self.tag_bonuses[Level.Tags.Fire]['minion_health'] = self.spell.get_stat('bonus') + self.get_modifier()
        self.tag_bonuses[Level.Tags.Nature]['minion_health'] = self.spell.get_stat('bonus') + self.get_modifier()
        if self.spell.get_stat('ice'):
            self.tag_bonuses[Level.Tags.Ice]['minion_health'] = self.spell.get_stat('bonus') + self.get_modifier()

    def on_add(self, evt):
        if Level.are_hostile(evt.unit, self.owner) or not self.spell.get_stat('soul'):
            return
        elif (Level.Tags.Ice in evt.unit.tags and self.spell.get_stat('ice'))  or Level.Tags.Fire in evt.unit.tags:
            evt.unit.apply_buff(CommonContent.BloodrageBuff((self.spell.get_stat('bonus') + self.get_modifier()) // 2), 10)

class LifeBooster(Level.Spell):
    def on_init(self):
        self.name = "Life Pyre"
        self.level = 4
        self.max_charges = 2
        self.duration = 15
        self.range = 0
        self.bonus = 12
        self.bonus_per_spell = 2
        self.stats.extend(['bonus', 'bonus_per_spell'])
        self.tags = [Level.Tags.Enchantment, Level.Tags.Fire, Level.Tags.Nature]

        self.upgrades['bonus_per_spell'] = (1, 3)
        self.upgrades['bonus'] = (8, 2)
        self.upgrades['ice'] = (1, 4, "Frostfire Hearth", "Life Pyre's bonus also increases based on [ice] spells, and affects [ice] spells with its full bonus.")
        self.upgrades['soul'] = (1, 5, "Soul of The Pyre", "[Fire] allies summoned while you have Living Flame additionally gain bloodlust equal to half of this spell's health bonus for 10 turns.\nIf you have Frostfire Hearth purchased, [ice] allies are affeted as well.")

    def get_description(self):
        return (
            "Gain Living Flame for [{duration}_turns:duration], during which all [fire] and [nature] spells and skills gain [{bonus}:heal] [minion_health:minion_health].\n"
            "This bonus increases by [{bonus_per_spell}:heal] for each [fire] or [nature] spell you know."
        ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        self.caster.apply_buff(PyreBuff(self), self.get_stat('duration'))
        
Spells.all_player_spell_constructors.extend([LuckBoon, MegaManReference, MetalMan, PhantomFormSpell, MirrorGoBrrr, Succ, TimeBreak, ElectricBurn, AshStorm, Imperm, ThermoSynergy, HeatAir, MetalIce, IcicleTypeShit, TimeManip, Karma, DeathBoom, LifeBooster])
