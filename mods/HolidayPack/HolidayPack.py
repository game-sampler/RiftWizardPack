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
import os

class Festivities(Level.Spell):
    def on_init(self):
        self.level = 6
        self.tags = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Sorcery, Level.Tags.Conjuration]
        self.name = "Magely Festivities"
        self.max_charges = 3
        self.minion_health = 45
        self.shields = 1
        self.minion_damage = 9
        self.minion_range = 8
        self.minion_duration = 22
        self.damage = 17
        self.range = 8
        self.radius = 4
        self.minion_radius = 2
        self.stats.append('minion_radius')
        self.asset = ["HolidayPack", "Festivities"]

        self.upgrades['minion_damage'] = (8, 3)
        self.upgrades['minion_radius'] = (1, 2)
        self.upgrades['radius'] = (1, 3)
    def get_description(self):
        return (
                "Deal [{damage}:damage] [fire] and [{damage}:damage] [ice] damage in a [{radius}_tile_burst:radius].\n"
                "Summons a festive wizard at the center tile.\n"
                "The festive wizard has [{minion_health}_HP:minion_health], [{shields}_SH:shields], 100 [fire] resist, 100 [ice] resist, and 50 [dark] resist.\n"
                "The festive wizard can hurl fresh snow or hot chocolate at enemies in [{minion_range}_tiles:minion_range], dealing [{minion_damage}:minion_damage] [fire] or [ice] damage respectively in a [{minion_radius}_tile_burst:radius].\n"
                "The festive wizard vanishes after [{minion_duration}_turns:minion_duration]\n"
                ).format(**self.fmt_dict())
    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]
    def make_wiz(self):
        wiz = Level.Unit()
        wiz.asset_name = os.path.join("..","..","mods","HolidayPack","festive_wiz")
        wiz.name = "Festive Wizard"
        wiz.shields = self.get_stat('shields')
        wiz.max_hp = self.get_stat('minion_health')
        snow = CommonContent.SimpleRangedAttack(name="Fresh Snow", damage=self.get_stat('minion_damage'), damage_type=Level.Tags.Ice, range=self.get_stat('minion_range'), radius=self.get_stat('minion_radius'))
        cocoa = CommonContent.SimpleRangedAttack(name="Hot Chocolate", damage=self.get_stat('minion_damage'), damage_type=Level.Tags.Fire, range=self.get_stat('minion_range'), radius=self.get_stat('minion_radius'))
        wiz.spells = [snow, cocoa]
        wiz.turns_to_death = self.get_stat('minion_duration')
        wiz.resists[Level.Tags.Ice] = 100
        wiz.resists[Level.Tags.Fire] = 100
        wiz.resists[Level.Tags.Dark] = 50
        wiz.tags = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Living]
        return wiz
    def cast(self, x, y):
        dtypes = [Level.Tags.Fire, Level.Tags.Ice]
        for spread in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
            for point in spread:
                for dtype in dtypes:
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)
                yield
        self.summon(self.make_wiz(), Level.Point(x, y))
        yield

class ChristmasCards(Level.Spell):
    def on_init(self):
        self.name = "Christmas Cards"
        self.level = 5
        self.range = 8
        self.minion_damage = 15
        self.minion_range = 9
        self.minion_radius = 2
        self.minion_health = 1
        self.shields = 2
        self.min_num_summons = 3
        self.max_num_summons = 9
        self.max_charges = 4
        self.tags = [Level.Tags.Ice, Level.Tags.Conjuration]
        self.stats.append('min_num_summons')
        self.stats.append('max_num_summons')
        self.stats.append('minion_radius')

        self.asset = ["HolidayPack", "Christmas_Cards"]

        self.upgrades['min_num_summons'] = (3, 3)
        self.upgrades['max_num_summons'] = (4, 3)
        self.upgrades['max_charges'] = (4, 3)
    def make_card(self):
        card = Level.Unit()
        card.name = "Christmas Card"
        card.max_hp = self.get_stat('minion_health')
        card.shields = self.get_stat('shields')
        card.tags = [Level.Tags.Ice, Level.Tags.Construct]
        card.asset_name = os.path.join("..","..","mods","HolidayPack","christmas_scroll")
        card.flying = True
        card.resists[Level.Tags.Ice] = 100
        bolt = CommonContent.SimpleRangedAttack(name="Season's Greetings", damage=self.get_stat('minion_damage'), damage_type=Level.Tags.Ice, range=self.get_stat('minion_range'), radius=self.get_stat('minion_radius'))
        bolt.suicide = True
        card.spells.append(bolt)
        return card
    def get_description(self):
        return (
                "Randomly summon between [{min_num_summons}:num_summons] and [{max_num_summons}:num_summons] living christmas cards.\n"
                "Each card has [{minion_health}_HP:minion_health] and [{shields}_SH:shields], and 100 [ice] resist.\n"
                "Cards have [ice] ranged attacks which deal [{minion_damage}_damage:minion_damage] in a [{minion_radius}_tile_burst:radius], [freeze] enemies for [4_turns:duration], and kill the user on cast.\n"
                ).format(**self.fmt_dict())
    def cast(self, x, y):
        for i in range(random.randint(self.get_stat('min_num_summons'), self.get_stat('max_num_summons'))):
            self.summon(self.make_card(), Level.Point(x, y))
            for i in range(4):
                yield

class OrnamentGlassify(CommonContent.GlassPetrifyBuff):
    def __init__(self, origspell):
        self.origspell = origspell
        CommonContent.GlassPetrifyBuff.__init__(self)
    def on_applied(self, owner):
        if self.origspell.get_stat('phosphoric'):
            self.resists[Level.Tags.Fire] = 0
            self.resists[Level.Tags.Ice] = 0
            self.resists[Level.Tags.Lightning] = 0
            self.name = "Acid Glassed"
    def on_attempt_advance(self):
        if self.origspell.get_stat('phosphoric'):
            self.owner.level.deal_damage(self.owner.x, self.owner.y, 8, Level.Tags.Arcane, self)
        return False
    
class Ornament(Level.Spell):
    def on_init(self):
        self.level = 2
        self.tags = [Level.Tags.Arcane, Level.Tags.Sorcery]
        self.name = "Ornament Shatter"
        self.damage = 13
        self.range = 8
        self.radius = 3
        self.duration = 4
        self.max_charges = 9

        self.asset = ["HolidayPack", "Ornament"]

        self.upgrades['duration'] = (3, 4)
        self.upgrades['damage'] = (12, 3)
        self.upgrades['radius'] = (2, 4)
        self.upgrades['phosphoric'] = (1, 5, "Glass Melt", "Ornaments inflict a special form of glassification that grants no bonuses to the target's [fire], [ice] or [lightning] resistances and deals 8 [arcane] damage to them every turn.", "boost")
        self.upgrades['metallize'] = (1, 5, "Tungsten Ornaments", "Ornaments deal [physical] damage in their radius, and double at the center tile.", "boost")
        self.upgrades['shardshot'] = (1, 6, "Shardshot", "Ornaments do not directly impact the targeted tile, but instead split into 4 shards that home in on random enemies in a [7_tile_burst:radius], casting this spell on them but with halved damage and radius.\nIf there are 4 or less enemies in range, the shards target all enemies in the burst.", "boost")

    def get_description(self):
        return (
                "Break a magic ornament on target tile, dealing [{damage}_arcane_damage:arcane] in a [{radius}_tile_burst:radius].\n"
                "The ornament inflicts [glassify] on units in its radius for [{duration}_turns:duration].\n"
                + text.glassify_desc
                ).format(**self.fmt_dict())
    def get_impacted_tiles(self, x, y):
        if not self.get_stat('shardshot'):
            return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')) for p in stage]
        else:
            points = []
            units = self.get_shardshot_targets(x, y)
            for u in units:
                plist = [p for stage in CommonContent.Burst(self.caster.level, Level.Point(u.x, u.y), self.get_stat('radius')//2) for p in stage]
                points += plist
            return points

    def get_shardshot_targets(self, xpt, ypt):
        units = []
        for spread in CommonContent.Burst(self.caster.level, Level.Point(xpt, ypt), 7):
            for point in spread:
                u = self.caster.level.get_unit_at(point.x, point.y)
                if u and self.caster.level.are_hostile(self.caster, u):
                    units.append(u) 
                continue
        return units
    def cast(self, x, y):
        if not self.get_stat('shardshot'):
            if self.get_stat('metallize'):
                self.caster.level.deal_damage(x, y, self.get_stat('damage'), Level.Tags.Physical, self)
            for spread in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius')):
                for point in spread:
                    u = self.caster.level.get_unit_at(point.x, point.y)
                    if u and self.caster.level.are_hostile(self.caster, u):
                        glassify = OrnamentGlassify(self)
                        u.apply_buff(glassify, self.get_stat('duration'))
                    self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Arcane, self)
                    if self.get_stat('metallize'):
                        self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Level.Tags.Physical, self)
                yield
        else:
            candidates = self.get_shardshot_targets(x, y)
            realrad = self.get_stat('radius') // 2
            realdmg = self.get_stat('damage') // 2
            targets = candidates if len(candidates) <= 4 else random.sample(candidates, 4)
            for unit in targets:
                for spread in CommonContent.Burst(self.caster.level, Level.Point(unit.x, unit.y), realrad):
                    for point in spread:
                        u = self.caster.level.get_unit_at(point.x, point.y)
                        if u and self.caster.level.are_hostile(self.caster, u):
                            glassify = OrnamentGlassify(self)
                            u.apply_buff(glassify, self.get_stat('duration'))
                        self.caster.level.deal_damage(point.x, point.y, realdmg, Level.Tags.Arcane, self)
                    yield

class SecretSanta(Level.Spell):
    def on_init(self):
        self.level = 6
        self.tags = [Level.Tags.Sorcery, Level.Tags.Enchantment]
        self.name = "Secret Santa"
        self.damage = 22
        self.range = 9
        self.radius = 4
        self.duration = 9
        self.max_charges = 3
        self.requires_los = False
        self.magnitude = 7
        self.stats.append('magnitude')

        self.asset = ["HolidayPack", "Secret"]
    def get_targets(self, x, y):
        units = []
        for spread in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius'), ignore_walls=True):
            for point in spread:
                u = self.caster.level.get_unit_at(point.x, point.y)
                if u:
                    units.append(u)
        return units
    def get_impacted_tiles(self, x, y):
        return [p for stage in CommonContent.Burst(self.caster.level, Level.Point(x, y), self.get_stat('radius'), ignore_walls=True) for p in stage]
    def make_buff(self, keylist):
        resist_tags = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Lightning, Level.Tags.Dark, Level.Tags.Holy, Level.Tags.Arcane]
        possible_attrs = ['damage', 'range', 'radius']
        buff = Level.Buff()
        buff.buff_type = Level.BUFF_TYPE_BLESS
        buff.name = "Secret Santa"
        buff.color = Level.Tags.Fire.color
        if keylist[0] > .6:
            num_bonuses = math.floor(keylist[1]/.27)
            if num_bonuses < 1:
                num_bonuses = 1
            attrs = random.sample(possible_attrs, num_bonuses)
            for attr in attrs:
                mag = self.get_stat('magnitude')
                if attr == 'range':
                    mag = mag // 3 if mag > 1 else 1
                buff.global_bonuses[attr] = mag
        if keylist[1] > .4:
            num_bonuses = math.floor(keylist[2]/.225)
            if num_bonuses < 1:
                num_bonuses = 1
            resists_final = random.sample(resist_tags, num_bonuses)
            for resist in resists_final:
                buff.resists[resist] = 50
        if keylist[2] > .8:
            elem = random.choice(resist_tags)
            bolt = CommonContent.SimpleRangedAttack(name="Secret Strike", damage=6, damage_type=elem, range=7)
            if keylist[2] >.9:
                bolt.damage *= 2
            buff.spells = [bolt]
        return buff
    def get_description(self):
        return (
                "Secretly give each ally in a [{radius}_tile_burst:radius] a buff with random effects.\n"
                "Buffs can give ranged attacks of random elements, increase stats of all existing spells, or give 50 resist to random elements.\n"
                "Most buffs have a magnitude of [{magnitude}:damage], and all buffs last [{duration}_turns:duration].\n"
                "Randomly deal [{damage}:damage] [fire], [ice], [lightning], [dark], [holy], or [arcane] damage to hit enemies.\n"
                ).format(**self.fmt_dict())
    def cast_instant(self, x, y):
        dtypes = [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Lightning, Level.Tags.Dark, Level.Tags.Holy, Level.Tags.Arcane]
        for unit in self.get_targets(x, y):
            if self.caster.level.are_hostile(unit, self.caster):
                dtype = random.choice(dtypes)
                self.caster.level.deal_damage(unit.x, unit.y, self.get_stat('damage'), dtype, self)
            else:
                keys = [random.random() for i in range(3)]
                buff = self.make_buff(keys)
                unit.apply_buff(buff, self.get_stat('duration'))

class BombExplode(Level.Buff):
    def __init__(self, spell):
        self.spell = spell
        Level.Buff.__init__(self)
    
    def on_init(self):
        self.color = Level.Tags.Fire.color
        self.owner_triggers[Level.EventOnDeath] = self.on_death
        self.name = "Present Explosion"

    def get_tooltip(self):
        desc_str = "On death, deals %d fire damage to enemies in a %d tile burst." % (self.owner.max_hp, self.spell.get_stat('radius'))
        if self.spell.get_stat('keeps'):
            desc_str += "\nSummons 2 copies of this unit with 75% of this unit's maximum HP in random locations in 8 tiles."
        return desc_str

    def on_death(self, evt):
        for stage in CommonContent.Burst(self.owner.level, Level.Point(self.owner.x, self.owner.y), self.spell.get_stat('radius')):
            for point in stage:
                unit = self.owner.level.get_unit_at(point.x, point.y)
                if unit and not self.owner.level.are_hostile(unit, self.owner):
                    continue
                else:
                    self.owner.level.deal_damage(point.x, point.y, self.owner.max_hp, Level.Tags.Fire, self)
        if self.spell.get_stat('keeps'):
            clone = self.spell.make_bomb()
            new_hp = math.ceil(self.owner.max_hp*.75)
            potential = [p for stage in CommonContent.Burst(self.owner.level, Level.Point(self.owner.x, self.owner.y), 8, ignore_walls=True) for p in stage]
            potential = [t for t in potential if self.owner.level.tiles[t.x][t.y].can_walk]
            if new_hp >= 5 and len(potential) >= 2:
                spots = random.sample(potential, 2)
                for tile in spots:
                    bomb = self.spell.make_bomb()
                    bomb.max_hp = new_hp
                    if bomb.cur_hp > bomb.max_hp:
                        bomb.cur_hp = bomb.max_hp
                    self.summon(bomb, tile)


class PresentBomb(Level.Spell):
    def on_init(self):
        self.name = "Present Bomb"
        self.level = 4
        self.range = 8
        self.radius = 4
        self.minion_health = 21
        self.max_charges = 4
        self.must_target_empty = True
        self.must_target_walkable = True
        self.tags = [Level.Tags.Fire, Level.Tags.Conjuration]

        self.asset = ["HolidayPack", "Present_Bomb"]

        self.upgrades['minion_health'] = (19, 3)
        self.upgrades['radius'] = (2, 3)
        self.upgrades['fragile'] = (1, 4, "Fragile Present", "The present spawns with only a quarter of its maximum HP.")
        self.upgrades['keeps'] = (1, 7, "Gift That Keeps On Giving", "Presents summon 2 copies of themselves with 75% of their maximum HP when they die.\nThe new presents will be summoned in random locations within 8 tiles of the original present.\nCopies will not be summoned if their maximum HP would be lower than 5 or there are no available locations.")
    def get_impacted_tiles(self, x, y):
        return [Level.Point(x, y)]
    def make_bomb(self):
        bomb = Level.Unit()
        bomb.name = "Exploding Present"
        bomb.stationary = True
        bomb.asset_name = os.path.join("..","..","mods","HolidayPack","bord_present")
        bomb.max_hp = self.get_stat('minion_health')
        bomb.tags = [Level.Tags.Fire, Level.Tags.Construct]
        for dtype in [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Physical]:
            bomb.resists[dtype] = -50
        bomb.resists[Level.Tags.Poison] = 0
        bomb.buffs.append(BombExplode(self))
        if self.get_stat('fragile'):
            bomb.cur_hp = bomb.max_hp // 4
            if bomb.cur_hp < 1:
                bomb.cur_hp = 1
        return bomb
    def get_description(self):
        return (
                "Place down an exploding present on target tile.\n"
                "The present is a stationary [fire] [construct] with [{minion_health}_HP:minion_health] and -50 [physical], [fire], and [ice] resist.\n" 
                "When the present dies, it explodes in a [{radius}_tile_burst:radius], dealing [fire] damage equal to [its_maximum_HP:damage].\n"
                ).format(**self.fmt_dict())
    def cast_instant(self, x, y):
        self.summon(self.make_bomb(), Level.Point(x, y))
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

Spells.all_player_spell_constructors.append(Festivities)
Spells.all_player_spell_constructors.append(ChristmasCards)
Spells.all_player_spell_constructors.append(Ornament)
Spells.all_player_spell_constructors.append(SecretSanta)
Spells.all_player_spell_constructors.append(PresentBomb)
#Spells.all_player_spell_constructors.append(CheatSpell)