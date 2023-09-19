# Copyright 2022 anotak

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import mods.API_Universal.APIs.API_LevelGenProps.API_LevelGenProps as API_LevelGenProps

import mods.API_Universal.APIs.API_Spells.API_Spells as API_Spells

import sys, math, random, inspect
sys.path.append('../..')

from Shrines import *
import Shrines
import Spells
import Monsters
import RareMonsters
import Variants
import CommonContent
import LevelGen
from Level import *

class WormholeBuff(ShrineBuff):
	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if not self.is_enhanced_spell(evt.spell):
			return
		
		p = self.owner.level.get_summon_point(evt.x, evt.y)
		if p:
			self.owner.level.queue_spell(self.trigger(p))
	
	def trigger(self, target):
		p = self.owner.level.get_summon_point(target.x, target.y)
		if p:
			self.owner.level.show_effect(self.owner.x, self.owner.y, Tags.Translocation)
			
			self.owner.level.act_move(self.owner, p.x, p.y, teleport=True)
			self.owner.level.show_effect(p.x, p.y, Tags.Translocation)
		yield

class WormholeShrine(Shrine):
	def on_init(self):
		self.name = "Wormhole"
		self.tags = []
		self.conj_only = False
		self.description = "Teleports you to the spell's target after cast"
		self.buff_class = WormholeBuff
	
	def can_enhance(self, spell):
		if spell.range < 1:
			return False
		if not spell.can_target_empty:
			return False
		
		return Shrine.can_enhance(self,spell)

# ######################################
# ######################################
# ######################################

class SharpeningShrine(Shrine):
	class LocalShrineBuff(OnKillShrineBuff):
		def on_init(self):
			OnKillShrineBuff.on_init(self)
			
			self.spell = False
		
		def on_kill(self, unit):
			if not self.spell:
				for maybe_spell in self.owner.spells:
					if type(maybe_spell) == self.spell_class:
						self.spell = maybe_spell
						return
			
			if unit and not unit.is_alive() and Tags.Living in unit.tags:
				self.spell.damage += 1
	
	def on_init(self):
		self.name = "Sharpening"
		self.tags = [Tags.Metallic, Tags.Ice]
		self.no_conj = True
		self.description = "This spell permenantly gains 1 damage whenever it slays a living target."
		self.buff_class = self.LocalShrineBuff
	
	def can_enhance(self, spell):
		if not hasattr(spell,'damage'):
			return False
		
		return Shrine.can_enhance(self,spell)


# ######################################
# ######################################
# ######################################

class PrismaticShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
			
			self.spell = False

		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			
			if not self.spell:
				spell = Spells.HolyBlast()
				spell.statholder = self.owner
				spell.caster = self.owner
			
			self.owner.level.queue_spell(spell.cast(evt.x,evt.y))
	
	def on_init(self):
		self.name = "Prismatic"
		self.tags = [Tags.Ice]
		self.description = "Whenever you cast this spell, you also cast Heavenly Blast at the target."
		self.buff_class = self.LocalShrineBuff


# ######################################
# ######################################
# ######################################

class PermafrostShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.spell_conversions[self.spell_class][Tags.Ice][Tags.Poison] = .5
			self.global_triggers[EventOnDamaged] = self.on_damage
			
		def on_damage(self, evt):
			if self.is_enhanced_spell(evt.source):
				evt.unit.apply_buff(Poison(), 30)
				
	def on_init(self):
		self.name = "Permafrost"
		self.description = "Half of all [ice] damage dealt by this shrine is redealt as [poison] damage. Damaged units are poisoned for 30 turns."
		self.buff_class = self.LocalShrineBuff
		self.tags = [Tags.Ice]
		self.no_conj = True

# ######################################
# ######################################
# ######################################
class GazingShrineEyeBuff(Spells.ElementalEyeBuff):

	def __init__(self, damage, freq, spell):
		Spells.ElementalEyeBuff.__init__(self,Tags.Dark, damage, freq, spell)
		self.name = "Eye of Darkness"
		self.element = Tags.Dark
		self.color = Tags.Dark.color

class GazingShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
			self.global_triggers[EventOnUnitAdded] = self.on_unit_add
			self.spell = False

		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			
			buff = GazingShrineEyeBuff(19, 2, evt.spell)
			buff.element = Tags.Dark
			evt.spell.caster.apply_buff(buff, 19)
		
		def on_unit_add(self, evt):
			if not isinstance(evt.unit.source, Spells.SummonFloatingEye):
				return
			if evt.unit.source.owner != self.owner:
				return
			
			if not self.spell:
				for maybe_spell in self.owner.spells:
					if type(maybe_spell) == self.spell_class:
						self.spell = maybe_spell
						break
			
			buff = GazingShrineEyeBuff(19, 2, self.spell)
			buff.element = Tags.Dark
			evt.unit.apply_buff(buff, 19)

	def on_init(self):
		# FIXME - restrict to enchantments?
		self.name = "Gazing"
		self.description = "Applies Eye of Darkness. Every 2 turns Eye of Darkness deals 19 [dark] damage to a random enemy unit in line of sight.\nLasts 19 turns."
		
		self.tags = [Tags.Eye]
		self.no_conj = True
		
		self.buff_class = self.LocalShrineBuff
		
# ######################################
# ######################################
# ######################################
class ConformityShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.global_triggers[EventOnUnitAdded] = self.on_unit_add
		
		def on_unit_add(self, evt):
			if evt.unit == self.owner:
				return
			if evt.unit.team != self.owner.team:
				return
			
			local_spell = self.spell_class()
			local_spell.caster = evt.unit
			local_spell.owner = evt.unit
			local_spell.statholder = self.owner
			if local_spell.range > 0:
				return
			
			# ?? act_cast seems to not do anything with houndlord and other things that spawn on first turn
			local_spell.cast_instant(evt.unit.x,evt.unit.y)

	def on_init(self):
		self.name = "Conformity"
		self.description = "All allies you summon have this [Eye] spell applied to them."
		
		self.tags = [Tags.Eye]
		self.no_conj = True
		
		self.buff_class = self.LocalShrineBuff

# ######################################
# ######################################
# ######################################
class HollowShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			
			hollow_count = 0
			for maybe_spell in self.owner.spells:
				if maybe_spell.cur_charges <= 0 and maybe_spell.max_charges > 0:
					hollow_count += 1
			
			if hollow_count <= 0:
				return
			
			self.owner.level.queue_spell(self.do_razors(evt,hollow_count))
	
		def do_razors(self, evt, hollow_count):
			previous_target = False
			damage = 19
			
			for _ in range(hollow_count):
				other_targets = self.owner.level.get_units_in_los(self.owner)
				
				other_targets = [t for t in other_targets if self.owner.level.are_hostile(t, self.owner)]
				
				other_targets.sort(key = lambda o: distance(o,self.owner))
				
				if other_targets:
					cur_target = other_targets[0]
				else:
					yield
					return

				cur_target.deal_damage(damage, Tags.Physical, self)
				
				if previous_target != cur_target:
					for p in self.owner.level.get_points_in_line(self.owner, cur_target)[1:-1]:
						self.owner.level.show_effect(p.x, p.y, Tags.Physical, minor=True)
					
					yield
				
				previous_target = cur_target

	def on_init(self):
		self.name = "Hollow"
		self.description = "Whenever you cast this spell, deal 19 physical damage to the nearest enemy in your line of sight for each spell you have with 0 charges."
		
		self.tags = [Tags.Metallic, Tags.Chaos, Tags.Orb]
		
		self.buff_class = self.LocalShrineBuff

# ######################################
# ######################################
# ######################################
class CrystallineShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
			self.cur_target = None

		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			
			other_targets = self.owner.level.get_units_in_los(self.owner)
			
			other_targets = [t for t in other_targets if self.owner.level.are_hostile(t, self.owner)]
			
			other_targets.sort(reverse = True, key = lambda o: distance(o,self.owner))
			
			if other_targets:
				for t in other_targets:
					if not any(isinstance(buff, GlassPetrifyBuff) for buff in t.buffs):
						self.cur_target = t
						break
			
			if not self.cur_target:
				return

			self.cur_target.apply_buff(GlassPetrifyBuff(), 6)
			
			for p in self.owner.level.get_points_in_line(self.owner, self.cur_target)[1:-1]:
				self.owner.level.show_effect(p.x, p.y, Tags.Physical, minor=True)
			
			self.cur_target = None

	def on_init(self):
		self.name = "Crystalline"
		self.description = "Whenever you cast this spell, [glassify] the farthest non-glassed enemy in your line of sight for 6 turns. Glassified targets have -100 physical resist."
		
		self.tags = [Tags.Orb, Tags.Enchantment]
		
		self.buff_class = self.LocalShrineBuff
		
# ######################################
# ######################################
# ######################################

class PolarShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.global_triggers[EventOnDamaged] = self.on_damage
			
		def on_damage(self, evt):
			if not self.is_enhanced_spell(evt.source):
				return
			
			if evt.unit.x != self.owner.x:
				return
			
			if evt.unit.y == self.owner.y:
				return
			
			self.owner.level.queue_spell(self.do_damage(evt))
			
		def do_damage(self, evt):
			evt.unit.deal_damage(64, Tags.Ice, self)
			
			for p in self.owner.level.get_points_in_line(self.owner, evt.unit)[1:-1]:
				self.owner.level.show_effect(p.x, p.y, Tags.Ice, minor=True)
			
			yield
	
	def on_init(self):
		self.name = "Polar"
		self.description = "Whenever this spell deals damage to a unit in a straight line to the north or south of you, deal 64 [ice] damage to that unit."
		self.buff_class = self.LocalShrineBuff
		self.tags = [Tags.Ice]
		self.no_conj = True
		
# ######################################
# ######################################
# ######################################

class BloodMagicShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
			self.spell = False

		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			self.owner.deal_damage(evt.spell.level * 3, Tags.Dark, self)
		
		#change by ATGM to make it work with charge consumer upgrades
		def on_pre_advance(self):
			tgt = [s for s in self.owner.spells if self.is_enhanced_spell(s)][0]
			tgt.cur_charges = tgt.get_stat('max_charges')
	
	def on_init(self):
		self.name = "Blood Magic"
		self.description = "Instead of using spell charges, spend three times the spell level in HP."
		self.buff_class = self.LocalShrineBuff
		self.tags = [Tags.Sorcery]
		
# ######################################
# ######################################
# ######################################

class HarmonicShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
			self.can_copy = True

		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			
			# check for even because the odd has already been spent
			if self.can_copy and evt.spell.cur_charges % 2 == 0:
					self.can_copy = False
					
					if evt.spell.can_cast(evt.x, evt.y):
						evt.caster.level.act_cast(evt.caster, evt.spell, evt.x, evt.y, pay_costs=False)
					evt.caster.level.queue_spell(self.reset())
			
			
		def reset(self):
			self.can_copy = True
			yield
	
	def on_init(self):
		self.name = "Harmonic"
		self.description = "Whenever you cast this spell, if this spell had an odd number of spell charges, copy it.\nCan be applied only to non-[conjuration] and non-[enchantment] spells."
		self.buff_class = self.LocalShrineBuff
		self.tags = [Tags.Ice, Tags.Holy]
	
	def can_enhance(self, spell):
		if Tags.Conjuration in spell.tags or Tags.Enchantment in spell.tags:
			return False
		
		return Shrine.can_enhance(self,spell)
		
# ######################################
# ######################################
# ######################################

class ProselytizingShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			
			count = 0
			for maybe_spell in self.owner.spells:
				if Tags.Holy in maybe_spell.tags:
					count += 1
			
			if count >= 4:
				evt.caster.level.queue_spell(self.proselytize())
			
		def proselytize(self):
			other_targets = [t for t in self.owner.level.units if self.owner.level.are_hostile(t, self.owner)]
			
			if other_targets:
				other_targets.sort(key = lambda o: o.cur_hp)
				
				other_targets[0].team = self.owner.team
			
			yield
	
	def on_init(self):
		self.name = "Proselytizing"
		self.description = "Whenever you cast this spell, if you know at least 4 [Holy] spells, the enemy with the lowest current HP becomes your minion."
		self.buff_class = self.LocalShrineBuff
		self.tags = [Tags.Holy, Tags.Word]
		
# ######################################
# ######################################
# ######################################

class CharonShrine(Shrine):
	class LocalMinionBuff(Buff):
		def __init__(self):
			Buff.__init__(self)
			self.description = "On death, teleport wizard to location."
			self.owner_triggers[EventOnDeath] = self.on_death

		def on_death(self, evt):
			self.owner.level.queue_spell(self.trigger(self.owner.x,self.owner.y))
	
		def trigger(self, x, y):
			if not self.owner.source:
				yield
				return
			
			if hasattr(self.owner.source,'caster'):
				wizard = self.owner.source.caster
			elif hasattr(self.owner.source,'owner'):
				wizard = self.owner.source.caster
			else:
				yield
				return
			
			p = self.owner.level.get_summon_point(x, y)
			
			if p and wizard:
				self.owner.level.show_effect(wizard.x, wizard.y, Tags.Translocation)
				
				self.owner.level.act_move(wizard, p.x, p.y, teleport=True)
				self.owner.level.show_effect(p.x, p.y, Tags.Translocation)
			yield
	
	class LocalShrineBuff(ShrineSummonBuff):
		def on_summon(self, unit):
			buff = CharonShrine.LocalMinionBuff()
			buff.apply_bonuses = False
			buff.buff_type = BUFF_TYPE_PASSIVE
			unit.apply_buff(buff)
	
	def on_init(self):
		self.name = "Charon"
		self.description = "When the summoned unit dies, you are teleported to its location."
		self.buff_class = self.LocalShrineBuff
		self.tags = []
		self.conj_only = True

# ######################################
# ######################################
# ######################################

class ThrivingShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		
		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			
			evt.caster.max_hp += 1
	
	def on_init(self):
		self.name = "Thriving"
		self.tags = []
		self.description = "Whenever you cast this spell, you gain 1 maximum HP.\nCan be applied only to spells of level 5 or greater."
		self.buff_class = self.LocalShrineBuff
	
	def can_enhance(self, spell):
		if spell.level < 5:
			return False
		
		return Shrine.can_enhance(self,spell)

# ######################################
# ######################################
# ######################################

class SporeShrine(Shrine):
	class LocalMinionBuff(Buff):
		def on_init(self):
			self.name = "Spores"
			self.healing = 8
			self.radius = 2
			self.owner_triggers[EventOnDamaged] = self.on_damage_taken

		def on_damage_taken(self, event):
			if random.random() < .3:
				self.owner.level.queue_spell(self.heal_burst())

		def heal_burst(self):
			wizard = self.owner.level.player_unit
			
			for stage in Burst(self.owner.level, Point(self.owner.x, self.owner.y), self.radius):
				for p in stage:
					u = self.owner.level.get_unit_at(p.x, p.y)
					if u and are_hostile(self.owner, u):
						continue
					elif not wizard or (p.x != wizard.x or p.y != wizard.y):
						self.owner.level.deal_damage(p.x, p.y, -self.healing, Tags.Heal, self)
				yield

		def get_tooltip(self):
			return "When damaged, has a 30%% chance to heal your allies within %d tiles %d HP" % (self.radius, self.healing)
	
	class LocalShrineBuff(ShrineSummonBuff):
		def on_summon(self, unit):
			buff = SporeShrine.LocalMinionBuff()
			unit.apply_buff(buff)
	
	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Spore"
		self.description = "When the summoned unit is damaged, has a 30%% chance to heal your allies within 2 tiles 8 HP."
		self.tags = [Tags.Nature]
		self.conj_only = True

# ######################################
# ######################################
# ######################################

# TODO (Implemented by ATGM)
class ReverenceShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		
		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			
			valid_allies = [u for u in self.owner.level.units if are_hostile(self.owner, u) and (Tags.Holy in u.tags or Tags.Arcane in u.tags)]
			if not valid_allies:
				return
			
			for u in self.owner.level.get_units_in_los(Point(evt.x, evt.y)):
				buff = CommonContent.GlobalAttrBonus("damage", -7)
				buff.color = Tags.Holy.color
				buff.name = "Reverence"
				buff.buff_type = BUFF_TYPE_CURSE
				u.apply_buff(buff, 3)
	
	def on_init(self):
		self.name = type(self).__name__[:-6]
		self.tags = [Tags.Holy]
		self.description = "Whenever you cast this spell, if you have a [holy] or [arcane] ally, all enemies in line of sight deal 7 less damage for 3 turns."
		self.buff_class = self.LocalShrineBuff
		self.no_conj = True
	

# ######################################
# ######################################
# ######################################
class RepulsionShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		
		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			
			self.owner.level.queue_spell(self.trigger(evt))
		
		def trigger(self, evt):
			x = evt.x
			y = evt.y
			
			units = [u for u in self.owner.level.get_units_in_los(evt) if self.owner.level.are_hostile(u, self.owner)]
			random.shuffle(units)
			units.sort(key=lambda u: distance(u, Point(x, y)))
			for u in units:
				if u.x == x and u.y == y:
					continue
				
				self.owner.level.show_effect(u.x, u.y, Tags.Translocation, minor=True)

				push(u, Point(x, y), 1)
				yield
	
	def on_init(self):
		self.name = type(self).__name__[:-6]
		self.tags = []
		self.description = "Whenever you cast this spell, enemy units in line of sight of the target are pushed away from the target."
		self.buff_class = self.LocalShrineBuff


# ######################################
# ######################################
# ######################################

class AttractionShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		
		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			
			self.owner.level.queue_spell(self.trigger(evt))
		
		def trigger(self, evt):
			x = evt.x
			y = evt.y
			
			units = [u for u in self.owner.level.get_units_in_los(evt) if self.owner.level.are_hostile(u, self.owner)]
			random.shuffle(units)
			units.sort(key=lambda u: distance(u, Point(x, y)))
			for u in units:
				if u.x == x and u.y == y:
					continue
				
				self.owner.level.show_effect(u.x, u.y, Tags.Translocation, minor=True)

				pull(u, Point(x, y), 1)
				yield
	
	def on_init(self):
		self.name = type(self).__name__[:-6]
		self.tags = []
		self.description = "Whenever you cast this spell, enemy units in line of sight of the target are pulled toward the target."
		self.buff_class = self.LocalShrineBuff

# ######################################
# ######################################
# ######################################

class WolvenShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
			
			self.spell = False

		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
				
			count = 0
			for maybe_spell in self.owner.spells:
				if Tags.Nature in maybe_spell.tags:
					count += 1
			
			if count < 4:
				return
			
			if not self.spell:
				# TODO - figure out applying shrines here (fixed by ATGM)
				playerwolf = [s for s in self.owner.spells if type(s) == Spells.SummonWolfSpell]
				spell = playerwolf[0] if playerwolf else Spells.SummonWolfSpell()
			
			self.owner.level.queue_spell(spell.cast(self.owner.x,self.owner.y))
	
	def on_init(self):
		self.name = "Wolven"
		self.tags = [Tags.Nature]
		self.description = "Whenever you cast this spell, if you know at least 4 [Nature] spells, you also cast Wolf adjacent to you."
		self.buff_class = self.LocalShrineBuff

# ######################################
# ######################################
# ######################################

class UnlearningShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_applied(self, owner):
			spells_to_remove = [s for s in owner.spells if self.is_enhanced_spell(s)]
			
			for spell in spells_to_remove:
				for upgrade in spell.spell_upgrades:
					if upgrade.applied:
						owner.xp += upgrade.level
				
				owner.remove_spell(spell)
				owner.xp += spell.level
				
				spells_to_reset = [(i, s) for i, s in enumerate(self.owner.level.gen_params.game.all_player_spells) if s == spell]
				
				setup_unit = Unit()
				for i, s in spells_to_reset:
					new_spell = self.spell_class()
					setup_unit.add_spell(new_spell)
					self.owner.level.gen_params.game.all_player_spells[i] = new_spell
			
			return ABORT_BUFF_APPLY
	
	def on_init(self):
		self.name = type(self).__name__[:-6]
		self.tags = []
		self.description = "Forget the chosen spell and all upgrades, and refund their SP costs."
		self.buff_class = self.LocalShrineBuff	

# ######################################
# ######################################
# ######################################

class AstralShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
			
		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			
			self.owner.level.queue_spell(self.do_damage(evt))
			
		def do_damage(self, evt):
			previous_target = False
			damage = 15
			
			count = 0
			for b in self.owner.buffs:
				if b.buff_type != BUFF_TYPE_PASSIVE:
					count += 1
			
			for _ in range(count):
				other_targets = self.owner.level.get_units_in_los(self.owner)
				
				other_targets = [t for t in other_targets if self.owner.level.are_hostile(t, self.owner)]
				
				other_targets.sort(key = lambda o: distance(o,self.owner))
				
				if other_targets:
					cur_target = other_targets[0]
				else:
					yield
					return

				cur_target.deal_damage(damage, Tags.Holy, self)
				
				if previous_target != cur_target:
					for p in self.owner.level.get_points_in_line(self.owner, cur_target)[1:-1]:
						self.owner.level.show_effect(p.x, p.y, Tags.Holy, minor=True)
					
					yield
				
				previous_target = cur_target
	
	def on_init(self):
		self.name = type(self).__name__[:-6]
		self.description = "Whenever you cast this spell, deal 15 [holy] damage to the nearest enemy in line of sight for each enchantment affecting you."
		self.buff_class = self.LocalShrineBuff
		self.tags = []

# ######################################
# EVERY SHRINE DEFINITION BELOW THIS LINE IS FROM ATGM!
# ######################################

class NecrosisShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.global_triggers[EventOnUnitPreAdded] = self.on_add

		def on_add(self, evt):
			if not evt.unit.source or evt.unit.source != [s for s in self.owner.spells if self.is_enhanced_spell(s)][0]:
				return
			evt.unit.tags.append(Tags.Undead)
			evt.unit.resists[Tags.Dark] = 100
	
	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Necrosis"
		self.description = "Summoned minions gain [undead] and 100 [dark] resist.\nCannot be applied to [dark] spells."
		self.tags = []
		self.conj_only = True

	def can_enhance(self, spell):
		if Tags.Dark in spell.tags:
			return False
		return Shrine.can_enhance(self,spell)

# ######################################
# ######################################
# ######################################

class RoyalShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_applied(self, owner):
			spells_to_affect = [s for s in owner.spells if self.is_enhanced_spell(s)]
			if not spells_to_affect:
				return
			spells_to_affect[0].tags *= 2
		
		def on_unapplied(self):
			spells_to_affect = [s for s in self.owner.spells if self.is_enhanced_spell(s)]
			if not spells_to_affect:
				return
			spells_to_affect[0].tags = list(set(spells_to_affect[0].tags))

	def on_init(self):
		self.name = "Royal"
		self.tags = []
		self.description = "This spell gains double benefits from Lord skills."
		self.buff_class = self.LocalShrineBuff

# ######################################
# ######################################
# ######################################

class TurboShrine(Shrine):
	def on_init(self):
		self.name = "Turbo"
		self.attr_bonuses['max_charges'] = -.5
		self.attr_bonuses['minion_damage'] = 1.0
		self.attr_bonuses['minion_health'] = 20
		self.tags = [Tags.Fire, Tags.Arcane]
		self.conj_only = True

# ######################################
# ######################################
# ######################################

class HasteShrine(Shrine):
	class LocalMinionBuff(Buff):
		def on_init(self):
			self.name = "Haste"
			self.color = Tags.Lightning.color
			self.buff_type = BUFF_TYPE_PASSIVE

		def on_advance(self):
			if self.owner and self.owner.is_alive():
				self.owner.level.leap_effect(self.owner.x, self.owner.y, Tags.Lightning.color, self.owner)
				self.owner.advance()
		
		def get_description(self):
			return "Takes one extra action each turn"
	
	class LocalShrineBuff(ShrineSummonBuff):
		def on_summon(self, unit):
			buff = HasteShrine.LocalMinionBuff()
			unit.apply_buff(buff)
	
	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Haste"
		self.description = "Summoned minions gain one extra action each turn.\nCannot be used on spells that summon multiple minions."
		self.tags = [Tags.Lightning, Tags.Holy]
		self.attr_bonuses['minion_health'] = 7
		self.conj_only = True
	
	def can_enhance(self, spell):
		return not hasattr(spell, "num_summons") and Shrine.can_enhance(self, spell)

# ######################################
# ######################################
# ######################################

class SafetyShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.global_triggers[EventOnDamaged] = self.on_damage
			
		def on_damage(self, evt):
			spell = [s for s in self.owner.spells if self.is_enhanced_spell(s)][0]
			if not spell:
				return
			if evt.source.owner.source != spell or evt.source.owner == evt.unit:
				return
			shield_buff = Shrines.SorceryShieldStack(evt.damage_type)
			self.owner.apply_buff(shield_buff, 3)

	
	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Safety"
		self.description = "Whenever a summoned minion deals damage, you gain 100 resistance to that type of damage for 3 turns."
		self.tags = []
		self.conj_only = True

# ######################################
# ######################################
# ######################################

class BlacklightShrine(Shrine):
	class LocalShrineBuff(ShrineSummonBuff):
		def on_summon(self, unit):
			buff = CommonContent.DamageAuraBuff(damage=(self.spell_level // 2)+1, damage_type=[Tags.Fire, Tags.Dark], radius=3)
			buff.buff_type = BUFF_TYPE_PASSIVE
			buff.color = Tags.Dark.color
			unit.apply_buff(buff)
	
	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Soul Candle"
		self.description = "Summoned minions gain an aura dealing [fire] or [dark] damage equal to half the spell's level plus one, with a radius of 3 tiles.\nCannot be used on [enchantment] or [sorcery] spells, or spells that summon multiple minions."
		self.tags = [Tags.Dark, Tags.Fire]
		self.attr_bonuses['minion_duration'] = -.2
		self.attr_bonuses['minion_health'] = -10
		self.conj_only = True
	
	def can_enhance(self, spell):
		if hasattr(spell, "num_summons") or Tags.Enchantment in spell.tags or Tags.Sorcery in spell.tags:
			return False
		return Shrine.can_enhance(self, spell)

# ######################################
# ######################################
# ######################################

class HypocriteShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_applied(self, owner):
			spell = [s for s in owner.spells if self.is_enhanced_spell(s)][0]
			if not spell:
				return
			spell.level += 2
		
		def on_unapplied(self):
			spell = [s for s in self.owner.spells if self.is_enhanced_spell(s)][0]
			if not spell:
				return
			spell.level -= 2

	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Duplicitous"
		self.description = "Increases spell level by 2.\nCannot be applied to level 6 or higher spells."
		self.tags = [Tags.Dark, Tags.Holy]

	def can_enhance(self,spell):
		return spell.level < 6 and Shrine.can_enhance(self,spell)
	
# ######################################
# ######################################
# ######################################

class SteamyShrine(Shrine):
	class LocalShrineBuff(ShrineSummonBuff):
		def on_summon(self, unit):
			fire_procced = False
			ice_procced = False
			if not self.is_enhanced_spell(unit.source) or are_hostile(unit, self.owner):
				return

			if any(Tags.Fire in u.tags and not are_hostile(u, self.owner) and u != unit for u in self.owner.level.units):
				fire_procced = True
				for s in unit.spells:
					if hasattr(s, 'damage'):
						s.damage += 11

			if any(Tags.Ice in u.tags and not are_hostile(u, self.owner) and u != unit for u in self.owner.level.units):
				ice_procced = True
				for s in unit.spells:
					if hasattr(s, 'range') and not s.melee:
						s.range += 2
			
			if fire_procced and ice_procced:
				for s in unit.spells:
					s.cool_down = max(0, s.cool_down-1)
	
	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Steamtrust"
		self.description = "When this spell is cast, if you control another [fire] unit, summoned minions gain 11 [damage].\nIf you control another [ice] unit, summoned minions gain 2 [range].\nIf you control both another [fire] and another [ice] unit, summoned minions lose 1 cooldown on all abilities."
		self.tags = [Tags.Ice, Tags.Fire]
		self.attr_bonuses['max_charges'] = 1
		self.conj_only = True

# ######################################
# ######################################
# ######################################

class RedemptionShrine(Shrine):
	class LocalShrineBuff(ShrineSummonBuff):
		def on_summon(self, unit):
			demon_procced, undead_procced = (Tags.Demon in unit.tags), (Tags.Undead in unit.tags)
			unit.tags = [t for t in unit.tags if t != Tags.Demon and t != Tags.Undead] + ([Tags.Living] if Tags.Living not in unit.tags else [])
			if demon_procced:
				unit.resists[Tags.Poison] = 100
			if undead_procced:
				unit.resists[Tags.Holy] = 100
	
	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Redemption"
		self.tags = [Tags.Dark]
		self.description = "Summoned minions lose [demon] and [undead] and gain [living].\nIf a summoned minion lost [demon], it gains 100 [poison] resist.\nIf a summoned minion lost [undead], it gains 100 [holy] resist.\nCannot be used on [enchantment] spells."
		self.attr_bonuses['minion_health'] = .5
		self.conj_only = True
	
	def can_enhance(self, spell):
		return Tags.Enchantment not in spell.tags and Shrine.can_enhance(self, spell)

# ######################################
# ######################################
# ######################################

class LifeCleaveShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.global_triggers[EventOnSpellCast] = self.on_cast
			self.cur_target = None
			self.chained_units = []
		
		def on_cast(self, evt):
			self.cur_target = evt.caster.level.get_unit_at(evt.x, evt.y)
			self.owner.level.queue_spell(self.effect(evt))
		
		def on_advance(self):
			self.chained_units.clear()

		def effect(self, evt):
			if self.cur_target and self.cur_target.is_alive():

				def can_cleave(t):
					if not evt.caster.level.are_hostile(t, evt.caster) or distance(t, self.cur_target) > 6 or not evt.spell.can_cast(t.x, t.y) or not self.is_enhanced_spell(evt.spell) or t == self.cur_target or t in self.chained_units:
						return False
					return True

				cleave_targets = [u for u in evt.caster.level.units if can_cleave(u)]

				if cleave_targets:
					target = random.choice(cleave_targets)
					yield

					for p in self.owner.level.get_points_in_line(self.cur_target, target)[:-1]:
						self.owner.level.show_effect(p.x, p.y, Tags.Holy, minor=True)

					self.chained_units.append(target)
					evt.caster.level.act_cast(evt.caster, evt.spell, target.x, target.y, pay_costs=False)

	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Lifechain"
		self.tags = []
		self.description = "Whenever this spell does not kill its primary target, automatically recast it on a random enemy in line of sight up to [6_tiles_away:range].\nEach enemy can only have this spell recast on them once per turn.\nCannot be applied to [enchantment] spells or spells that do not do damage."
		self.no_conj = True
	
	def can_enhance(self, spell):
		return Tags.Enchantment not in spell.tags and hasattr(spell, "damage") and Shrine.can_enhance(self, spell)

# ######################################
# ######################################
# ######################################

class PoisonTapShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.global_triggers[EventOnSpellCast] = self.on_cast
			self.copying = False

		def on_cast(self, evt):
			if self.copying or not self.is_enhanced_spell(evt.spell):
				return False

			unit = self.owner.level.get_unit_at(evt.x, evt.y)
			if not unit:
				return

			b = unit.get_buff(CommonContent.Poison)
			if not b:
				return
			unit.remove_buff(b)

			copy_targets = [u for u in self.owner.level.get_units_in_los(unit) if are_hostile(self.owner, u) and u.has_buff(CommonContent.Poison) and u != unit]

			self.copying = True

			unit.remove_buff(CommonContent.Poison)
			for u in copy_targets:
				if evt.spell.can_copy(u.x, u.y):
					self.owner.level.act_cast(self.owner, evt.spell, u.x, u.y, pay_costs=False)
					b = u.get_buff(CommonContent.Poison)
					if b:
						u.remove_buff(b)
			
			self.copying = False

	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Venom Tap"
		self.tags = [Tags.Sorcery]
		self.description = "When you cast this spell on a [poisoned] unit, make a copy of it targeting each other [poisoned] unit in line of sight.\nRemove [poison] from all affected units."

# ######################################
# ######################################
# ######################################

class SpikeyShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
			
			self.spell = False

		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			elif (evt.spell.cur_charges+1) % 3 == 0:
				spiky = Monsters.SpikeBall()
				spiky.turns_to_death = 19
				self.summon(spiky, Point(evt.x, evt.y), radius=5)
	
	def on_init(self):
		self.name = "Spiky"
		self.tags = [Tags.Metallic]
		self.description = "Whenever you cast this spell, if it had a number of spell charges divisible by 3, summon a rolling spike ball near the target for [19_turns:minion_health]."
		self.buff_class = self.LocalShrineBuff

# ######################################
# ######################################
# ######################################

class SpikeyGhostShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
			
			self.spell = False

		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			elif not evt.spell.cur_charges:
				spiky = Variants.SpikeBallGhost()
				spiky.max_hp += 20
				spiky.cur_hp = spiky.max_hp
				spiky.spells[0].damage += 5
				self.summon(spiky, Point(evt.x, evt.y), radius=5)
	
	def on_init(self):
		self.name = "Ghost Spike"
		self.tags = [Tags.Metallic, Tags.Dark]
		self.description = "Whenever you cast the last charge of this spell, summon a ghostly spike ball near the target."
		self.buff_class = self.LocalShrineBuff

# ######################################
# ######################################
# ######################################

class ScrapHarvestShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):

		def on_init(self):
			self.global_triggers[EventOnDeath] = self.on_death

		def on_death(self, evt):
			if self.prereq.cur_charges >= self.prereq.get_stat('max_charges') or not self.owner.level.are_hostile(evt.unit, self.owner) or Tags.Construct not in evt.unit.tags:
				return

			chance = .25
			if evt.damage_event and evt.damage_event.damage_type == Tags.Physical:
				chance = .5

			if random.random() < chance:
				self.prereq.cur_charges += 1

	def on_init(self):
		self.name = "Scrap"
		self.description = "Whenever an enemy [construct] dies, this spell has a 25% chance of gaining a charge.\nIf the unit died to [physical] damage, this chance is doubled."
		self.tags = [Tags.Metallic]
		self.buff_class = self.LocalShrineBuff
		self.no_conj = True

# ######################################
# ######################################
# ######################################

class MirrorForceBuff(Buff):
	def __init__(self):
		Buff.__init__(self)
		self.color = Tags.Glass.color
		self.buff_type = BUFF_TYPE_PASSIVE
		self.global_triggers[EventOnSpellCast] = self.on_cast

	def on_applied(self, owner):
		if Tags.Glass not in owner.tags:
			owner.tags.append(Tags.Glass) 

	def on_cast(self, evt):
		if evt.x == self.owner.x and evt.y == self.owner.y and self.owner.level.are_hostile(evt.caster, self.owner):
			evt.spell.cast(evt.caster.x, evt.caster.y)

	def get_tooltip(self):
		return "Reflects targeted enemy attacks"

class ReflectiveShrine(Shrine):
	class LocalShrineBuff(ShrineSummonBuff):
		def on_summon(self, unit):
			unit.apply_buff(MirrorForceBuff())

	def on_init(self):
		self.name = "Reflection"
		self.description = "Summoned minions become [glass] and reflect enemy attacks targeting them.\nCannot be used on spells that summon multiple minions."
		self.tags = []
		self.conj_only = True
		self.buff_class = self.LocalShrineBuff
	
	def can_enhance(self, spell):
		return not hasattr(spell, "num_summons") and Shrine.can_enhance(self, spell)

# ######################################
# ######################################
# ######################################

class CoolDownAssistShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
			
			self.spell = False

		def on_spell_cast(self, evt):
			if not self.is_enhanced_spell(evt.spell):
				return
			for unit in [u for u in self.owner.level.units if not self.owner.level.are_hostile(u, self.owner)]:
				for c in unit.cool_downs:
					unit.cool_downs[c] = max(0, unit.cool_downs[c]-1)
	
	def on_init(self):
		self.name = "Repose"
		self.tags = [Tags.Holy]
		self.description = "Whenever you cast this spell, all of your minions lose 1 turn of cooldown on all abilities."
		self.buff_class = self.LocalShrineBuff
		self.no_conj = True

# ######################################
# ######################################
# ######################################

class AllyOfferingShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):

		def on_init(self):
			self.global_triggers[EventOnDeath] = self.on_death

		def on_death(self, evt):
			if not evt.damage_event:
				return
			elif self.owner.level.are_hostile(evt.unit, self.owner) or evt.damage_event.source != [s for s in self.owner.spells if self.is_enhanced_spell(s)][0]:
				return
			candidates = [u for u in self.owner.level.units if not self.owner.level.are_hostile(u, self.owner) and (Tags.Demon in u.tags or Tags.Undead in u.tags or Tags.Holy in u.tags) and u != evt.unit]
			if not candidates:
				return
			candidates.sort(key=lambda x: x.cur_hp)
			for s in evt.unit.spells:
				if s.name in [s.name for s in candidates[-1].spells]:
					continue
				else:
					s.caster = candidates[-1]
					s.statholder = candidates[-1]
					candidates[-1].spells.append(s)
			self.owner.level.show_path_effect(Point(evt.unit.x, evt.unit.y), candidates[-1], Tags.Dark, minor=True)
			candidates[-1].spells.sort(key=lambda x: x.cool_down, reverse=True)

	def on_init(self):
		self.name = "Dusk Incense"
		self.description = "Whenever this spell kills an ally, your [demon], [undead], or [holy] ally with the highest HP gains all of that ally's spells."
		self.tags = [Tags.Holy, Tags.Dark]
		self.buff_class = self.LocalShrineBuff
		self.no_conj = True

# ######################################
# ######################################
# ######################################

class MysticShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.global_triggers[EventOnUnitPreAdded] = self.on_add

		def on_add(self, evt):
			if not evt.unit.source or evt.unit.source != [s for s in self.owner.spells if self.is_enhanced_spell(s)][0]:
				return
			evt.unit.tags.append(Tags.Arcane)
			evt.unit.resists[Tags.Arcane] = 100
	
	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Mystique"
		self.description = "Summoned minions gain [arcane] and 100 [arcane] resist.\nCannot be applied to [arcane] spells."
		self.tags = []
		self.conj_only = True

	def can_enhance(self, spell):
		if Tags.Arcane in spell.tags:
			return False
		return Shrine.can_enhance(self,spell)

# ######################################
# ######################################
# ######################################

class HolyShrine(Shrine):
	class LocalShrineBuff(ShrineBuff):
		def on_init(self):
			self.global_triggers[EventOnUnitPreAdded] = self.on_add

		def on_add(self, evt):
			if not evt.unit.source or evt.unit.source != [s for s in self.owner.spells if self.is_enhanced_spell(s)][0]:
				return
			evt.unit.tags.append(Tags.Holy)
			evt.unit.resists[Tags.Holy] = 100
	
	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Salvation"
		self.description = "Summoned minions gain [holy] and 100 [holy] resist.\nCannot be applied to [arcane] or [dark] spells."
		self.tags = []
		self.conj_only = True

	def can_enhance(self, spell):
		if Tags.Arcane in spell.tags or Tags.Dark in spell.tags:
			return False
		return Shrine.can_enhance(self,spell)

# ######################################
# ######################################
# ######################################

class SoundShrine(Shrine):
	class LocalShrineBuff(ShrineSummonBuff):
		def on_summon(self, unit):
			if hasattr(unit, "reverb_activated"):
				return
			unit.reverb_activated = True
			self.owner.level.event_manager.raise_event(EventOnUnitAdded(unit), unit)
	
	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Reverb"
		self.description = "Summoned minions are treated as if they were summoned twice."
		self.tags = []
		self.conj_only = True

# ######################################
# ######################################
# ######################################

class MeltShrine(Shrine):
	class LocalShrineBuff(ShrineSummonBuff):
		def on_init(self):
			self.global_triggers[EventOnDamaged] = self.on_damage

		def on_damage(self, evt):
			if not (self.owner.level.are_hostile(evt.unit, self.owner) and self.is_enhanced_spell(evt.source)):
				return
			self.owner.level.queue_spell(self.trick_unfreeze(evt.unit))

		def trick_unfreeze(self, unit):
			self.owner.level.event_manager.raise_event(EventOnUnfrozen(unit, Tags.Fire))
			yield
	
	def on_init(self):
		self.buff_class = self.LocalShrineBuff
		self.name = "Thawing"
		self.description = "Hit enemies act as if they were unfrozen via fire damage once."
		self.tags = [Tags.Fire]
		self.no_conj = True

# ######################################
# ######################################
# ######################################

#Shrines.new_shrines.clear()
#anotak's original set
API_LevelGenProps.add_shrine(WormholeShrine, RARE)
API_LevelGenProps.add_shrine(SharpeningShrine, RARE)
API_LevelGenProps.add_shrine(PrismaticShrine, RARE)
API_LevelGenProps.add_shrine(PermafrostShrine, RARE)
API_LevelGenProps.add_shrine(GazingShrine, RARE)
API_LevelGenProps.add_shrine(ConformityShrine, RARE)
API_LevelGenProps.add_shrine(HollowShrine, RARE)
API_LevelGenProps.add_shrine(CrystallineShrine, RARE)
API_LevelGenProps.add_shrine(PolarShrine, RARE)
API_LevelGenProps.add_shrine(BloodMagicShrine, RARE)
API_LevelGenProps.add_shrine(HarmonicShrine, RARE)
API_LevelGenProps.add_shrine(ProselytizingShrine, RARE)
API_LevelGenProps.add_shrine(CharonShrine, RARE)
API_LevelGenProps.add_shrine(ThrivingShrine, RARE)
API_LevelGenProps.add_shrine(SporeShrine, RARE)
API_LevelGenProps.add_shrine(ReverenceShrine, RARE)
API_LevelGenProps.add_shrine(RepulsionShrine, RARE)
API_LevelGenProps.add_shrine(AttractionShrine, RARE)
API_LevelGenProps.add_shrine(WolvenShrine, RARE)
API_LevelGenProps.add_shrine(UnlearningShrine, RARE)
API_LevelGenProps.add_shrine(AstralShrine, RARE)
#ATGM's first set
API_LevelGenProps.add_shrine(NecrosisShrine, RARE)
API_LevelGenProps.add_shrine(RoyalShrine, RARE)
API_LevelGenProps.add_shrine(TurboShrine, RARE)
API_LevelGenProps.add_shrine(SafetyShrine, RARE)
API_LevelGenProps.add_shrine(HasteShrine, RARE)
API_LevelGenProps.add_shrine(BlacklightShrine, RARE)
#ATGM's second set
API_LevelGenProps.add_shrine(HypocriteShrine, RARE)
API_LevelGenProps.add_shrine(SteamyShrine, RARE)
API_LevelGenProps.add_shrine(RedemptionShrine, RARE)
API_LevelGenProps.add_shrine(LifeCleaveShrine, RARE)
API_LevelGenProps.add_shrine(PoisonTapShrine, RARE)
API_LevelGenProps.add_shrine(SpikeyShrine, RARE)
API_LevelGenProps.add_shrine(SpikeyGhostShrine, RARE)
#ATGM's third set
API_LevelGenProps.add_shrine(ScrapHarvestShrine, RARE)
API_LevelGenProps.add_shrine(ReflectiveShrine, RARE)
API_LevelGenProps.add_shrine(CoolDownAssistShrine, RARE)
API_LevelGenProps.add_shrine(AllyOfferingShrine, RARE)
#NUMBAH FOUR BAYBEE
API_LevelGenProps.add_shrine(MysticShrine, RARE)
API_LevelGenProps.add_shrine(HolyShrine, RARE)
API_LevelGenProps.add_shrine(SoundShrine, RARE)
API_LevelGenProps.add_shrine(MeltShrine, RARE)


# ######################################
# ######################################
# ######################################

original_make_shrine = Shrines.make_shrine

def our_make_shrine(shrine, player):
	shrine_prop = original_make_shrine(shrine,player)
	
	backed_up_asset = shrine_prop.asset
	
	if shrine_prop.asset and 'shrine_white' in shrine_prop.asset:
		shrine_prop.asset = False
	
	if shrine_prop.asset:
		return shrine_prop
	
	maybe_asset = ['SecludedShrines', 'tiles', 'shrine', 'animated', shrine.name.lower().replace(' ', '_')]
	if os.path.exists(os.path.join('mods', *maybe_asset) + '.png'):
		shrine_prop.asset = maybe_asset
	
	
	if shrine_prop.asset:
		return shrine_prop
	
	maybe_asset = ['SecludedShrines', 'tiles', 'shrine', shrine.name.lower().replace(' ', '_')]
	if os.path.exists(os.path.join('mods', *maybe_asset) + '.png'):
		shrine_prop.asset = maybe_asset
	else:
		shrine_prop.asset = backed_up_asset

	return shrine_prop

Shrines.make_shrine = our_make_shrine

# ######################################
# ######################################
# ######################################


#for shrine in Shrines.new_shrines:
	#if shrine[0].__module__ == "mods.SecludedShrines.SecludedShrines" :
		#print("\n")
		#print("-----------------------")
		#print(shrine[0]().name + ": ")
		#print(shrine[0]().get_description())



LevelGen.roll_shrine = API_LevelGenProps.roll_shrine
LevelGen.random_spell_tag = API_Spells.random_spell_tag

# make shrines allowed on floor 2
if API_LevelGenProps.primary_props[2][0] == shrine:
	API_LevelGenProps.primary_props[2] = (shrine, API_LevelGenProps.SHRINE_WEIGHT, lambda level: True)
else:
	print("SecludedShrines can't set floor 2 shrines to allowed, maybe another mod is interfering or there's been a new Rift Wizard version");

print("SecludedShrines v1a loaded")
