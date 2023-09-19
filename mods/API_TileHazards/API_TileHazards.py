import Level

print("API_TileHazards Loaded")

#Implements a structure for creating hazard tiles with various effects.
    
class TileHazardBasic(Level.Prop):
    #The basic form of a tile hazard. 
    #Just does something whenever a unit goes in it and has a turn counter.
    def __init__(self, name, duration, user):
        self.name = name
        self.duration = duration
        self.user = user

    def on_unit_enter(self, unit):
        self.user.level.event_manager.raise_event(Level.EventOnPropEnter(unit, self), unit)
        self.effect(unit) #Implement effect to make the hazard do something when a unit enters.
        
    def advance(self):
        self.advance_effect()
        self.duration -= 1
        if self.duration <= 0:
            self.level.remove_prop(self)
            self.expire_effect()
    
    def advance_effect(self):
        pass #Implement to make the hazards do something each turn they're active.

    def expire_effect(self):
        pass #Implement to do something when a hazard's duration ends.

    def get_description(self):
        return "%d turns remaining" % self.duration #Sample readout of how many turns a prop has left.

class TileHazardDepletable(Level.Prop):
    #A hazard that lasts an infinite number of turns but has a limited amount of uses for its effects.
    def __init__(self, name, uses, user):
        self.name = name
        self.uses = uses
        self.user = user

    def on_unit_enter(self, unit):
        self.user.level.event_manager.raise_event(Level.EventOnPropEnter(unit, self), unit)
        self.effect(unit) #Implement effect to make the hazard do something when a unit enters.
        self.uses -= 1
        if self.uses <= 0:
            self.level.remove_prop(self)
            self.expire_effect()

    def advance(self):
        self.advance_effect()

    def advance_effect(self):
        pass #Implement to make the hazards do something each turn they're active.

    def expire_effect(self):
        pass #Implement to do something when a hazard runs out of uses.

    def get_description(self):
        return "%d uses remaining" % self.uses #sample readout of how many more times a prop can be triggered
    
class TileHazardSubscriptive(Level.Prop):
    #A hazard that lasts an infinite number of turns and is triggered by a specific event.
    def __init__(self, name, user):
        self.name = name
        self.user = user
        self.owner_triggers = {}
        self.global_triggers = {}

    def on_unit_enter(self, unit):
        self.user.level.event_manager.raise_event(Level.EventOnPropEnter(unit, self), unit)
        self.effect(unit) #Implement effect to make the hazard do something when a unit enters.

    def advance(self):
        self.advance_effect()

    def advance_effect(self):
        pass #Implement to make the hazards do something each turn they're active.

    def get_description(self):
        pass #Usually contains what the prop does when triggered and what its triggers are.

    #Blatantly stolen from Level.Buff pretty much. Allows a TileHazard to subscribe and unsubscribe to events in the same style a buff would.
    def subscribe(self):
        event_manager = self.user.level.event_manager

        for event_type, trigger in self.owner_triggers.items():
            event_manager.register_entity_trigger(event_type, self.user, trigger)
        for event_type, trigger in self.global_triggers.items():
            event_manager.register_global_trigger(event_type, trigger)
            
    def unsubscribe(self):
        event_manager = self.user.level.event_manager
        
        for event_type, trigger in self.owner_triggers.items():
            event_manager.unregister_entity_trigger(event_type, self.user, trigger)
        for event_type, trigger in self.global_triggers.items():
            event_manager.unregister_global_trigger(event_type, trigger)
