import pickle
import random
from operator import itemgetter

'''
This file is stolen from additional pylons.
Simplified for learning purposes.

Saves the result to find better strats that work.

#{opp_id: [[match_id, strat_id, result, race],]}
{opp_id: [[strat_id, result],]}
{opponent_id: {strategy_id: [games_total, losses_total]}}

'''


class TrainingData:

    def __init__(self):
        self.results = {}
        # load the pickle data.
        self.loadData()

    def saveVictory(self, opp_id, strategy):
        self.results.update({opp_id: strategy})
        self.saveData()

    def saveData(self):
        try:
            with open("data/res.dat", "wb") as fp:
                pickle.dump(self.results, fp)
        except (OSError, IOError) as e:
            print(str(e))

    def loadData(self):
        try:
            with open("data/res.dat", "rb") as fp:
                self.results = pickle.load(fp)
        except (OSError, IOError) as e:
            print(e)

    def findStrat(self, opp_id):
        # check if this is a new opponent.
        if not self.results.get(opp_id):
            strategy = None
        else:
            strategy = self.results.get(opp_id)
            print("opp_id", opp_id)
            print("Last victory came with strategy", strategy)
        return strategy

    def removeResult(self, opp_id):
        # remove the match from the list and save.

        "nothing to be removed -> return"
        if not self.results.get(opp_id):
            print('ut oh, where is the match?')
            return
        self.results.pop(opp_id)
        self.saveData()
