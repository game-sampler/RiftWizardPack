import Level, Mutators
import random

class RogueLikeMode(Mutators.Mutator):
    #most of this remains the same as the original roguelike mod, just some optimizations where necessary
    def __init__(self, numspells=12, num_newspells=1, num_newskills=1):
        Mutators.Mutator.__init__(self)		
        self.numspells = numspells
        self.num_newspells = num_newspells
        self.num_newskills = num_newskills
        self.description = "Start with %d spells. Gain %d new spells and %d new skills each rift. Skills are 2 SP cheaper. " % (numspells, num_newspells, num_newskills)
        self.otherspells = None
        self.availablespells = None
        self.availableskills = None
        self.otherskills = None
        
    def on_generate_spells(self, spells):
        self.availablespells, self.otherspells = spells, list(spells)
        
    def on_generate_skills(self, skills):
        self.availableskills, self.otherskills = skills, list(skills)
        
    def on_game_begin(self, game):
        self.availablespells.clear()
        starters = [s for s in self.otherspells if s.level < 2]
        random.shuffle(starters)
        self.availablespells.insert(0,starters[0])
        self.otherspells.remove(starters[0])
        random.shuffle(self.otherspells)
        #minor iteration change to make sure players start with the correct number of spells
        for s in range(0, self.numspells-1):
            self.availablespells.insert(0,self.otherspells[s])
            self.otherspells.remove(self.otherspells[s])
        self.availableskills.clear()
        #applies the new form of the roguelike buff
        game.p1.apply_buff(RogueLikeModeBuff(self.numspells, self.num_newspells, self.num_newskills, self.availablespells, self.otherspells, self.availableskills, self.otherskills))       

class RogueLikeModeBuff(Level.Buff):
    #keeps track of the new numbers
    def __init__(self, numspells, num_newspells, num_newskills, availablespells, otherspells, availableskills, otherskills):
        Level.Buff.__init__(self)
        #makes the roguelike mode buff passive since fae arcanists can only dispel buffs of bless type
        self.buff_type = Level.BUFF_TYPE_PASSIVE
        self.numspells = numspells
        self.num_newspells = num_newspells
        self.num_newskills = num_newskills
        self.availablespells = availablespells
        self.otherspells = otherspells
        self.availableskills = availableskills
        self.otherskills = otherskills
        self.name = "Roguelike Mode"
        self.description = "Gain %d new spells and %d new skills every rift. Skills cost 2 SP less."
        self.owner_triggers[Level.EventOnUnitAdded] = self.update_spells
    def update_spells(self, owner):
        #just does some stuff multiple times instead of once
        random.shuffle(self.otherspells)
        for _ in range(self.num_newspells):
            self.availablespells.insert(0,self.otherspells[0])
            self.otherspells.remove(self.otherspells[0])
        random.shuffle(self.otherskills)
        for _ in range(self.num_newskills):
            #the real kicker, since price is based on level just change that instead, no need to override cost stuff
            self.otherskills[0].level = max(1, self.otherskills[0].level-2)
            self.availableskills.insert(0,self.otherskills[0])
            self.otherskills.remove(self.otherskills[0]) 
        
Mutators.all_trials.clear()
Mutators.all_trials.append(Mutators.Trial("RogueLikeMode", [RogueLikeMode(9, 2, 2)]))
