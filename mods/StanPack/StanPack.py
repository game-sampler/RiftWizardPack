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
import Consumables

import os

#troubler orb, worm orb
#start with worm

def WormShamblerFriendly(HP=20):
	unit = Monsters.WormBall()
	unit.sprite.char = 'W'
	unit.max_hp = HP

	unit.name = "Giant Worm Ball"
	unit.asset_name = "ball_of_worms_large"

	def summon_worms(caster, target):
		worms = Monsters.WormBall(5)
		p = caster.level.get_summon_point(target.x, target.y, 1.5)
		worms.team = caster.team
		if p:
			caster.level.add_obj(worms, p.x, p.y)

	spitworms = CommonContent.SimpleRangedAttack(damage=1, range=6, damage_type=Level.Tags.Physical, onhit=summon_worms)
	
	spitworms.name = "Spit Worms"
	spitworms.cool_down = 3
	spitworms.description = "Summons a small worm ball adjacent to to the target"

	unit.spells.insert(0, spitworms)

	unit.tags = [Level.Tags.Living]
	return unit

class WormOrbSpell(Spells.OrbSpell):
	def on_init(self):
		self.name = "Worm Amalgam"
		self.range = 9
		self.max_charges = 4

		self.melt_walls = False

		self.minion_health = 20
		self.worm_ball_health = 5
		self.stats.append('worm_ball_health')
		
		self.tags = [Level.Tags.Nature, Level.Tags.Orb, Level.Tags.Conjuration]
		self.level = 5

		self.upgrades['range'] = (2, 2)
		self.upgrades['worm_ball_health'] = (5, 6, "Stronger Balls", "The amalgam will summon large worm balls instead of small ones.")
		self.upgrades['orb_walk'] = (1, 8, "Worm Fusion", "Targeting an existing amalgam melds a new amalgam into the existing one, turning it into a pillar of worms with [100_HP:minion_health]")
	def get_description(self):
		return ("Summons a worm amalgam next to the caster.\n"
				"The amalgam has [{minion_health}_HP:minion_health] and summons worm balls in empty adjacent tiles each turn.\n"
				"Worm balls have [{worm_ball_health}_HP:minion_health] HP and a melee attack dealing [physical] damage equal to half of their maximum health.\n"
				"The amalgam has no will of its own, each turn it will float one tile towards the target.\n"
				"The amalgam can be destroyed by [ice] or [fire] damage.").format(**self.fmt_dict())
	def on_make_orb(self, orb):
		orb.resists[Level.Tags.Ice] = 0
		orb.resists[Level.Tags.Fire] = 0
		orb.shields = 1
		orb.asset_name = os.path.join("..","..","mods","StanPack","worm_orb")
		orb.name = "Worm Amalgam"
	def on_orb_move(self, orb, next_point):
		x = next_point.x
		y = next_point.y
		level = orb.level

		for p in level.get_points_in_ball(x, y, 1, diag=True):
			unit = level.get_unit_at(p.x, p.y)
			if unit or not level.tiles[p.x][p.y].can_walk:
				continue
			else:
				self.summon(Monsters.WormBall(self.get_stat('worm_ball_health')), p)
	def on_orb_walk(self, existing):
		# Burst
		team = existing.team
		x = existing.x
		y = existing.y
		
		existing.kill()
		pillar = RareMonsters.PillarOfWorms()
		pillar.max_hp = 100
		pillar.spells[1].heal //=2
		pillar.spells[1].damage //=2
		pillar.spells[1].description = "Heals one %s ally for %d" % (pillar.spells[1].tag.name, pillar.spells[1].heal)
		pillar.spells.pop(2)
		pillar.spells[0] = CommonContent.SimpleSummon(WormShamblerFriendly, cool_down=15, global_summon=True, max_channel=2, path_effect=Level.Tags.Poison)
		pillar.team = team
		self.caster.level.add_obj(pillar, x, y)
		yield
	def on_orb_collide(self, orb, next_point):
		orb.level.show_effect(next_point.x, next_point.y, Level.Tags.Physical)
		yield

	def get_orb_impact_tiles(self, orb):
		return [p for stage in CommonContent.Burst(self.caster.level, orb, 1, ignore_walls=True) for p in stage]

class TroubleOrbSpell(Spells.OrbSpell):
	def on_init(self):
		self.name = "Troublesome Sphere"
		self.range = 7
		self.max_charges = 3

		self.melt_walls = False

		self.minion_health = 20
		self.minion_damage = 9
		
		self.tags = [Level.Tags.Arcane, Level.Tags.Orb, Level.Tags.Conjuration]
		self.level = 6

		self.upgrades['minion_damage'] = (5, 3)
		self.upgrades['range'] = (4, 3)
		self.upgrades['large_ball'] = (1, 6, "Super Phaser", "The sphere's phaser hits in a burst and teleports targets farther away.")
	def get_description(self):
		return ("Summons a troubling sphere next to the caster.\n"
				"The sphere has [{minion_health}_HP:minion_health].\n"
				"Each turn, targets a random enemy in line of sight with a phase bolt dealing [{minion_damage}_arcane_damage:arcane] and teleporting them away.\n"
				"The sphere has no will of its own, each turn it will float one tile towards the target.\n"
				"The sphere can be destroyed by [arcane] damage.").format(**self.fmt_dict())
	def on_make_orb(self, orb):
		orb.resists[Level.Tags.Arcane] = 0
		orb.shields = 7
		orb.asset_name = os.path.join("..","..","mods","StanPack","trouble_orb")
		orb.name = "Troubling Sphere"
	def on_orb_move(self, orb, next_point):
		damage = self.get_stat('minion_damage')
		los_units = [u for u in orb.level.get_units_in_los(next_point) if self.caster.level.are_hostile(u, self.caster)]
		if len(los_units) > 0:
			choice = random.choice(los_units)
			if self.get_stat('large_ball'):
				phaser = Variants.TroublerBig().spells[0]
				phaser.max_channel = 0
				phaser.cast_after_channel = False
			else:
				phaser = Monsters.Troubler().spells[0]
			phaser.damage = damage
			phaser.caster = orb
			phaser.range = Level.RANGE_GLOBAL
			self.caster.level.act_cast(orb, phaser, choice.x, choice.y)

class MaskSpell(Level.Spell):

	def on_init(self):
		self.range = 0

	def cast(self, x, y):
		points = list(self.caster.level.get_points_in_ball(x, y, 2, diag=True))

		random.shuffle(points)
		for p in points:
			if not self.caster.level.tiles[p.x][p.y].can_fly or self.caster.level.tiles[p.x][p.y].unit:
				continue
			spawner = random.choice([Monsters.Troubler, Variants.TroublerIron, Variants.TroublerGlass, Variants.TroublerBig])
			trouble = spawner()
			trouble.team = self.caster.team
			self.caster.level.add_obj(trouble, p.x, p.y)
			yield

def trouble_bag():
	item = Level.Item()
	item.name = "Troubling Sack"
	item.asset = ["StanPack", "bag_of_trouble"]
	item.description = "Summon friendly troublers in each unoccupied square in 2 tiles."
	item.set_spell(MaskSpell())
	return item

Spells.all_player_spell_constructors.append(WormOrbSpell)
Spells.all_player_spell_constructors.append(TroubleOrbSpell)
Consumables.all_consumables.append((trouble_bag, Consumables.COMMON))