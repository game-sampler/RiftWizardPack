from re import S
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
import mods.API_TileHazards.API_TileHazards as THAPI

class MiasmaTile(THAPI.TileHazardBasic):
    def __init__(self, name, duration, user, spell):
        super(MiasmaTile, self).__init__(name, duration, user)
        self.asset = ['SampleSpells', 'miasma']
        self.spell = spell
        self.damage_type = [Level.Tags.Dark, Level.Tags.Poison]
    
    def effect(self, unit):
        if self.spell.get_stat('symbiosis') and not self.user.level.are_hostile(unit, self.user):
            return
        unit.apply_buff(CommonContent.Poison(), self.spell.get_stat('poison_duration'))
    
    def advance_effect(self):
        self.aura()

    def aura(self):
        effects_left = 7

        for unit in self.user.level.get_units_in_ball(Level.Point(self.x, self.y), self.spell.get_stat('radius')):

            if (not self.user.level.are_hostile(self.user, unit)) and self.spell.get_stat('symbiosis'):
                continue
            damage_type = random.choice(self.damage_type)
            unit.deal_damage(self.spell.get_stat('damage'), damage_type, self.spell)
            effects_left -= 1

        points = self.user.level.get_points_in_ball(self.x, self.y, self.spell.get_stat('radius'))
        points = [p for p in points if not self.user.level.get_unit_at(p.x, p.y)]
        random.shuffle(points)
        for i in range(effects_left):
            if not points:
                break
            p = points.pop()
            damage_type = random.choice(self.damage_type)
            self.user.level.deal_damage(p.x, p.y, 0, damage_type, source=self.spell)

    def get_description(self):
        return "Deals %d [dark] or [poison] damage to units in %d tiles each turn.\nPoisons units entering for %d turns.\n%d turns remaining" % (self.spell.get_stat('damage'), self.spell.get_stat('radius'), self.spell.get_stat('poison_duration'), self.duration)

class PoisonField(Level.Spell):
    def on_init(self):
        self.level = 5
        self.tags = [Level.Tags.Dark, Level.Tags.Nature, Level.Tags.Sorcery]
        self.name = "Miasma Cover"
        self.max_charges = 3
        self.damage = 11
        self.range = 8
        self.radius = 3
        self.duration = 15
        self.poison_duration = 40
        self.stats.append('poison_duration')

        self.must_target_empty = True
        self.must_target_walkable = True

        self.upgrades['radius'] = (2, 3)
        self.upgrades['requires_los'] = (-1, 3, "Blindcasting", "Miasmatic Coating can be cast without line of sight.")
        self.upgrades['symbiosis'] = (1, 5, "Symbiotic Miasma", "Miasma no longer poisons or damages allies.")

    def get_impacted_tiles(self, x, y):
        return [Level.Point(x, y)]
    
    def get_description(self):
        return (
            "Coat target tile in miasma.\n"
            "The miasma emits noxious gases that deal [{damage}:damage] [poison] or [dark] damage each turn to units in [{radius}_tiles:radius].\n"
            "If an enemy steps directly onto the miasma, they become poisoned for [{poison_duration}_turns:dark].\n"
            "The miasma lasts [{duration}_turns:duration].\n"
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        tile = self.caster.level.tiles[x][y]
        if not tile.prop or tile.prop == None:
            miasma = MiasmaTile("Miasmatic Pool", self.get_stat('duration'), self.caster, self)
            self.caster.level.add_obj(miasma, x, y)

class WarpTile(THAPI.TileHazardDepletable):
    def __init__(self, name, uses, user, spell):
        super(WarpTile, self).__init__(name, uses, user)
        self.asset = ['SampleSpells', 'warp_pad']
        self.spell = spell
        self.destination = False
    
    def effect(self, unit):
        if unit != self.user or self.destination:
            self.uses += 1
            return
        else:
            pads = []
            for tile in self.user.level.iter_tiles():
                if isinstance(tile.prop, WarpTile):
                    pads.append(tile)
            pads.sort(key=lambda tile: Level.distance(self, tile))
            if len(pads) > 1:
                pads[1].prop.destination = True
                self.user.level.show_effect(self.user.x, self.user.y, Level.Tags.Translocation)
                self.user.level.act_move(self.user, pads[1].x, pads[1].y, teleport=True, force_swap=True)
            else:
                self.uses += 1
    
    def advance_effect(self):
        self.destination = False
    
    def get_description(self):
        return "Teleports the Wizard to the nearest other warp pad.\n%d uses remaining" % self.uses
    
class WarpPad(Level.Spell):
    def on_init(self):
        self.level = 3
        self.tags = [Level.Tags.Translocation, Level.Tags.Sorcery]
        self.name = "Warp Pad"
        self.max_charges = 4
        self.range = 8
        self.uses = 2

        self.must_target_empty = True
        self.must_target_walkable = True

        self.upgrades['requires_los'] = (-1, 2, "Blindcasting", "Warp Pad can be cast without line of sight")
        self.upgrades['uses'] = (1, 1)
    
    def get_description(self):
        return(
            "Place a warp pad on target tile.\n"
            "Whenever the Wizard steps on a warp pad, they are teleported to the nearest other warp pad.\n"
            "Warp pads have [{uses}_uses:translocation].\n"
        ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        tile = self.caster.level.tiles[x][y]
        if not tile.prop or tile.prop == None:
            miasma = WarpTile("Warp Pad", self.get_stat('uses'), self.caster, self)
            self.caster.level.add_obj(miasma, x, y)

class LightningField(THAPI.TileHazardSubscriptive):
    def __init__(self, name, user, spell):
        super(LightningField, self).__init__(name, user)
        self.asset = ['SampleSpells', 'light_field']
        self.spell = spell
        self.storedspelllv = 0
        self.acceptable_tags = [Level.Tags.Lightning]
        self.global_triggers[Level.EventOnSpellCast] = self.on_spell_cast
        self.subscribe()
    
    def on_spell_cast(self, evt):
        if evt.x == self.x and evt.y == self.y and any(t in self.acceptable_tags for t in evt.spell.tags) and evt.spell.caster == self.user and Level.Tags.Sorcery in evt.spell.tags:
            self.storedspelllv = evt.spell.level
    
    def on_unit_enter(self, unit):
        numarcs = 0
        if self.storedspelllv:
            for point in self.user.level.get_points_in_ball(self.x, self.y, self.spell.get_stat('radius')):
                u = self.user.level.get_unit_at(point.x, point.y)
                if u and self.user.level.are_hostile(self.user, u) and self.user.level.can_see(self.x, self.y, point.x, point.y):
                    self.arc(u.x, u.y)
                    numarcs += 1
                    if numarcs >= self.storedspelllv:
                        break
            if not self.spell.get_stat('reusable'):
                self.level.remove_prop(self)
            else:
                self.storedspelllv = 0

    def arc(self, x, y):
        target = Level.Point(x, y)
        for point in CommonContent.Bolt(self.user.level, Level.Point(self.x, self.y), target):
            self.user.level.deal_damage(point.x, point.y, self.spell.get_stat('damage_multiplier')*self.storedspelllv, Level.Tags.Lightning, self.spell)

    def get_description(self):
        return (
            "Stores lightning sorceries cast directly on it.\n"
            "Will emit a number of flashes equal to the stored spell's level when stepped on, dealing %d times the spell's level in [lightning] damage in a beam.\n"
            "Currently stored spell level: %d"
        ) % (self.spell.get_stat('damage_multiplier'), self.storedspelllv)

class EnergyField(Level.Spell):
    def on_init(self):
        self.level = 4
        self.tags = [Level.Tags.Lightning, Level.Tags.Sorcery]
        self.name = "Capacitant Field"
        self.max_charges = 4
        self.range = 5
        self.radius = 7
        self.damage_multiplier = 4
        self.stats.append('damage_multiplier')

        self.upgrades['damage_multiplier'] = (2, 3)
        self.upgrades['radius'] = (2, 3)
        self.upgrades['reusable'] = (1, 4, "Residual Capacitance", "Capacitant fields have their stored spell level reduced to 0 rather than being destroyed when stepped on.")
    
    def get_impacted_tiles(self, x, y):
        return [Level.Point(x, y)]

    def get_description(self):
        return (
            "Creates a capacitant field on target tile.\n"
            "Whenever a [lightning] [sorcery] spell is cast on a capacitant field, the field charges.\n"
            "Capacitant fields will dissipate when entered, causing flashes of lightning to arc to enemies in [{radius}_tiles:radius].\n"
            "The field emits a number of flashes equal to the cast spell's level.\n"
            "Flashes deal [{damage_multiplier}:damage] times the spell's level as damage to enemies in a beam.\n"
        ).format(**self.fmt_dict())

    def cast_instant(self, x, y):
        tile = self.caster.level.tiles[x][y]
        if not tile.prop or tile.prop == None:
            miasma = LightningField("Capacitant Field", self.caster, self)
            self.caster.level.add_obj(miasma, x, y)

Spells.all_player_spell_constructors.extend([PoisonField, WarpPad, EnergyField])