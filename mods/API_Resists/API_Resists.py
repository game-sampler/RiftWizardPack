import Level
from inspect import isfunction
print("API_Resists Loaded")
#Implements a simple structure for mods to set default enemy resists for tags or names.

resists_TBA = [] #the list of resist assignments in tuple form

#Simply appends a tuple representation of a given resist assignment to the list. 
#The criterion argument must either be a string, a tag in Level.Tags, or a function that takes in a unit object and returns a boolean.
def addResist(criterion, tag, value):
    resists_TBA.append((criterion, tag, value))

#Overrides regular resist gen to iterate through the resist list and assign each resist.
set_default_resistances_old = Level.Level.set_default_resitances

def __set_default_resistances_new(self, unit):
    set_default_resistances_old(self, unit)
    for tup in resists_TBA:
        if type(tup[0]) == str:
            if tup[0] in unit.name:
                unit.resists.setdefault(tup[1], tup[2])
        elif type(tup[0]) == Level.Tag:
            if tup[0] in unit.tags:
                unit.resists.setdefault(tup[1], tup[2])
        elif isfunction(tup[0]):
            if tup[0](unit) == True:
                unit.resists.setdefault(tup[1], tup[2])

Level.Level.set_default_resitances = __set_default_resistances_new
