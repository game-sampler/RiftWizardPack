import Mutators, Level, CommonContent

Mutators.all_trials.append(Mutators.Trial("Humblepath", [Mutators.SpPerLevel(2), Mutators.SpellTagRestriction(Level.Tags.Conjuration), Mutators.NumPortals(1), Mutators.EnemyBuff(CommonContent.TrollRegenBuff)]))