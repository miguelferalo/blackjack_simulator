from src.components.blackjackroundsimulator import BlackjackSimulator
import math
import os
import pickle 

class BlacjackCareerSim:

    def __init__(self, bse_df, config):

        self.card_distribution = config["CARD_DISTRIBUTION"]
        self.surrender = config["SESSION_PARAMETERS"]["RULES"]["SURRENDER"]

        self.config = config
        self.bse_df = bse_df

        #Define session parameters
        self.n_sessions = config["SESSION_PARAMETERS"]["N_SESSIONS"]
        self.rounds_per_hour = config["SESSION_PARAMETERS"]["ROUNDS_PER_HOUR"]
        self.session_length = config["SESSION_PARAMETERS"]["HOURS"]
        self.min_bet = config["SESSION_PARAMETERS"]["MIN_BET"]

        #Define table parameters
        self.n_decks = config["SESSION_PARAMETERS"]["N_DECKS"]
        self.penetration = config["SESSION_PARAMETERS"]["DECK_PEN"]

        #Define startegy
        self.betting_strategy = config["STRATEGY"]["BETTING_STRATEGY"]
        self.count_strategy = config["STRATEGY"]["HIGH_OPT_1"]
        self.deck_resolution = config["STRATEGY"]["DECK_RESOLUTION"]

        #Define Global dictionary for results
        self.career_results = {}

        #super().__init__(bse_df, card_distribution, surrender = surrender)

    def deck_n_cards_resetter(self):

        deck_distribution = {}
        for key in self.config["CARD_DISTRIBUTION"].keys():
            deck_distribution[key] = self.config["CARD_DISTRIBUTION"][key] * self.n_decks

        return deck_distribution
    
    def calculate_round_count(self):

        running_count = sum(self.card_distribution[card] * self.count_strategy[card] for card in self.card_distribution.keys())

        remaining_cards = sum(self.card_distribution[card] for card in self.card_distribution.keys())
        total_cards_deck = sum(self.config["CARD_DISTRIBUTION"].values())

        #Round remaining decks based on deck resolution
        if self.deck_resolution == 0.5:
            remaining_decks = max(round(remaining_cards * 2/ total_cards_deck) / 2, self.deck_resolution)

        else:

            remaining_decks = round(remaining_cards / total_cards_deck)

        #Round remaining decks based on deck resolution
        true_count = math.floor(running_count / remaining_decks)        

        return true_count
    
    def round_bet(self, true_count):

        #Find min and max counts in config
        min_true_count_bet = min(self.config["STRATEGY"]["BETTING_STRATEGY"].keys()) 
        max_true_count_bet = max(self.config["STRATEGY"]["BETTING_STRATEGY"].keys()) 

        if true_count < min_true_count_bet:

            bet_size = self.min_bet

        elif true_count > max_true_count_bet:

            bet_size = self.min_bet * self.config["STRATEGY"]["BETTING_STRATEGY"][max_true_count_bet]

        else:
            
            bet_size = self.min_bet * self.config["STRATEGY"]["BETTING_STRATEGY"][true_count]

        return bet_size
    
    def bet_results(self, bet_size, results):

        #Calculate the win or loss per hand
        money_result_list = []
        for result in results:

            if result == "win_blackjack":

                money_result = bet_size * self.config["SESSION_PARAMETERS"]["BLACKJACK_PAYOUT"]

            elif result == "win_doubledown":

                money_result = bet_size * 2

            elif result == "win":

                money_result = bet_size

            elif result == "loss_surrender":

                money_result = - bet_size * 0.5

            elif result == "draw":

                money_result = 0

            elif result == "draw_doubledown":

                money_result = 0

            elif result == "loss_doubledown":

                money_result = - bet_size * 2

            elif result == "loss":
                
                money_result = - bet_size

            else:

                money_result = - bet_size

            money_result_list.append(money_result)

        return money_result_list
    
    def shoe_result_organizer(self, true_count, player_hands, dealer_hand, outcome_results, money_results):

        round_results = {}
        round_results["TRUE_COUNT"] = true_count
        round_results["PLAYER_HANDS"] = {}
        for player_hand in player_hands:
            round_results["PLAYER_HANDS"][player_hand] = player_hands[player_hand]
        round_results["DEALER_HAND"] = dealer_hand
        round_results["HAND_RESULTS"] = outcome_results
        round_results["MONEY_RESULTS"] = money_results

        return round_results


    def shoe_simulator(self, round_count):

        #Keep playing rounds until cut card
        total_cards = sum(self.card_distribution.values())

        shoe_results = {}

        while sum(self.card_distribution.values()) / total_cards > (1 - self.penetration):

            round_count = round_count + 1

            #Calculate count of current round
            true_count = self.calculate_round_count()

            #Calculate the bet size for the round 
            bet_size = self.round_bet(true_count)

            #Play the round of blackjack
            round_simulator = BlackjackSimulator(self.bse_df, self.card_distribution, surrender = self.surrender)
            player_hands, dealer_hand, results = round_simulator.round_simulator()

            #Calculate bet results
            money_results = self.bet_results(bet_size, results)

            #Append round results to shoe results
            round_results = self.shoe_result_organizer(true_count, player_hands, dealer_hand, results, money_results)

            #Append results to shoe
            round_number = "ROUND_{number}".format(number = round_count)
            shoe_results[round_number] = round_results

        return shoe_results, round_count

    def play_session(self):

        #Session_results
        session_results = []

        #Number of shoes to play
        rounds_to_play = self.rounds_per_hour * self.session_length

        round_count = 0
        while round_count < rounds_to_play:

            #restart deck stats
            self.card_distribution = self.deck_n_cards_resetter()
            print(f"{round_count} ROUNDS PLAYED IN THE SESSION")
            shoe_results, round_count = self.shoe_simulator(round_count)

            #Add shoe results to session results
            session_results.append(shoe_results)

        return session_results
    
    def sim_results_saver(self):
        
        #Define paths to save
        global_path = os.getcwd()
        results_folder = self.config["RESULTS"]["RESULTS_FOLDER"]
        sim_folder = self.config["RESULTS"]["SIMLULATIONS_FOLDER"]
        file_name = self.config["RESULTS"]["SIM_NAME"].format(sessions = self.n_sessions, hours = self.session_length, n_decks = self.n_decks,
                                                              strategy = self.config["STRATEGY"]["STRATEGY_EMPLOYED"], min_bet = self.min_bet, 
                                                              spread = self.config["STRATEGY"]["SPREAD"])
        
        path_to_save_results = os.path.join(global_path, results_folder, sim_folder, file_name)
        #Save as pickle
        with open(path_to_save_results, 'wb') as f:
            pickle.dump(self.career_results, f)
        
    def blackjack_sim(self):

        for session in range(self.n_sessions):

            print(f"------------------------- SESSION {session} START -----------------------------")

            session_number = "SESSION_{session}".format(session = session + 1)

            session_results = self.play_session()

            session_dictionary = {}
            for index, shoe in enumerate(session_results):

                
                shoe_number = "SHOE_{number}".format(number = index)
                session_dictionary[shoe_number] = shoe

            self.career_results[session_number] = session_dictionary

        #Save the results
        self.sim_results_saver()

