import numpy as np

class BlackjackSimulator:

    def __init__(self, bse_df, card_distribution, surrender = False):

        #Define Blacjack strategy
        self.split_df = bse_df["split"]
        self.surrender_df = bse_df["surrender"].copy()
        self.hard_hit_df = bse_df["hard_hit"].copy()
        self.soft_hit_df = bse_df["soft_hit"].copy()
        self.hard_double_df = bse_df["hard_doubling"].copy()
        self.soft_double_df = bse_df["soft_doubling"].copy()

        #Play
        self.play = True

        #Set soft hand
        self.soft_hand = False

        #Variable to keep track of double downs
        self.double_down_tracker = {}

        #Define card distribution
        self.card_distribution = card_distribution

        #Blackjack rules
        self.surrender = surrender

    def card_draw(self, n_cards):

        cards = list(self.card_distribution.keys())
        probability_distribution = [p / sum(self.card_distribution.values()) for p in self.card_distribution.values()]

        picked_cards =  np.random.choice(cards, n_cards, p = probability_distribution)

        return picked_cards

    def update_distribution(self, player_cards):
    
        for card_drawn in player_cards:

            self.card_distribution[card_drawn] = self.card_distribution[card_drawn] - 1
        

    def bse_outcome(self, bse_rule, hand_cards, dealer_card):

        outcome = bse_rule.loc[bse_rule["Hand"] == hand_cards, dealer_card].reset_index(drop=True)[0]

        return outcome
    
    def update_player_hands_split(self, player_cards, original_hand_number, new_hand_1, new_hand_2):

        #Create a key for the hands dictionary
        player_last_hand = list(player_cards.keys())[-1]
        player_last_hand_number = int(player_last_hand.split("_")[1]) 
        player_extra_hand = "hand_{new_hand}".format(new_hand = player_last_hand_number + 1)

        #Update original hand and add the new hand cretaed after the split
        player_cards[original_hand_number] = new_hand_1
        player_cards[player_extra_hand] = new_hand_2

        return player_cards
    
    def splits_required(self, player_cards):

        splits_required = False

        for hand in player_cards.values():

            card_1 = hand[0]
            card_2 = hand[1]

            if card_1 == card_2:

                #Aces can only be splitted once, check it
                if (card_1 != 1) | ((card_2 == 1) & (len(player_cards.keys()) < 2)):

                    splits_required = True

        return splits_required
    
    def hand_splitter(self, player_cards, hand_number, dealer_card):

        card_1 = player_cards[hand_number][0]
        card_2 = player_cards[hand_number][1]

        #Check if split

        if card_1 == card_2:
            
            outcome = self.bse_outcome(self.split_df, card_1, dealer_card)
            
            if outcome == "SP":

                #Aces can only be splitted once, check it
                if (card_1 != 1) | ((card_1 == 1) & (len(player_cards.keys()) < 2)):

                    split_cards_1 = self.card_draw(1)
                    self.update_distribution(split_cards_1)
                    hand_1 = [card_1, split_cards_1[0]]

                    split_cards_2 = self.card_draw(1)
                    self.update_distribution(split_cards_2)
                    hand_2 = [card_2, split_cards_2[0]]

                    #Update player hands
                    self.update_player_hands_split(player_cards, hand_number, hand_1, hand_2)

                else:

                    self.split = False

            else:

                self.split = False

        else:
            self.split = False

    def surrender_check(self, player_cards, hand_value, dealer_card):

        #Never surrender when an ace in hand
        if 1 in player_cards:

            self.play = True

        #Check if the count and dealer card meand you have to surrender
        elif (hand_value in self.surrender_df["Hand"]) & (dealer_card in self.surrender_df.columns.to_list()):

            if self.surrender_df.loc[self.surrender_df["Hand"] == hand_value, dealer_card].reset_index(drop = True)[0] == "Surrender":

                self.play = False

            else:

                self.play = True
        #Play
        else:

            self.play = True
    
    def hand_value_calculator(self, player_hand):

        if 1 not in player_hand:

            hand_value = sum([int(card) for card in player_hand])

        #A is tricky because could be valued 1 or 11
        else:
            n_aces = player_hand.count(1)
            non_aces_sum = sum([int(card) if card != 1 else 0 for card in player_hand])

            for ace in range(2):

                #Only a maximum of one 11 value ace
                n_aces_11_value = 1 - ace

                #All aces in hand have a value of 1 excep 1
                n_aces_1_value = n_aces - n_aces_11_value

                hand_value = non_aces_sum + n_aces_1_value * 1 + n_aces_11_value * 11

                #If when running the value count, there are no 11 aces, hard hand
                if n_aces_11_value == 0:

                    soft_hand = False

                #The maximum value of the hand has been calculated
                if hand_value <= 21:

                    break
                
        
        return hand_value
    
    def player_draws(self, hand_cards):

        hit_card = self.card_draw(1)
        hand_cards.append(int(hit_card[0]))
        self.update_distribution(hit_card)

        return hand_cards
    
    def player_draw_rules(self, hand_cards, hand_value, dealer_card):

        #If we have a soft hand, follow soft hit strategy
        if self.soft_hand:

            max_soft_hit = max(self.soft_hit_df["Hand"])
            min_soft_hit = min(self.soft_hit_df["Hand"])

            if hand_value < min_soft_hit:

                hand_cards = self.player_draws(hand_cards)
                hand_value = self.hand_value_calculator(hand_cards)

            elif hand_value > max_soft_hit:

                self.play = False

            else:

                playing_decision = self.soft_hit_df.loc[self.soft_hit_df["Hand"] == hand_value, dealer_card].reset_index(drop = True)[0]

                if playing_decision == "H":

                    hand_cards = self.player_draws(hand_cards)
                    hand_value = self.hand_value_calculator(hand_cards)

                else:

                    self.play = False

        
        #Follow hard hit strategy
        else:

            max_hard_hit = max(self.hard_hit_df["Hand"])
            min_hard_hit = min(self.hard_hit_df["Hand"])

            if hand_value < min_hard_hit:

                hand_cards = self.player_draws(hand_cards)
                hand_value = self.hand_value_calculator(hand_cards)

            elif hand_value > max_hard_hit:

                self.play = False

            else:

                playing_decision = self.hard_hit_df.loc[self.hard_hit_df["Hand"] == hand_value, dealer_card].reset_index(drop = True)[0]

                if playing_decision == "H":

                    hand_cards = self.player_draws(hand_cards)
                    hand_value = self.hand_value_calculator(hand_cards)

                else:

                    self.play = False

        return hand_cards

        
    
    def double_down_check(self, hand_cards, hand_value, dealer_card):

        #Check if hard douling
        max_hard_double = max(self.hard_double_df["Hand"])
        min_hard_double = min(self.hard_double_df["Hand"])

        if (hand_value <= max_hard_double) & (hand_value >= min_hard_double):

            #Check if DD based on dealer card
            playing_decision = self.hard_double_df.loc[self.hard_double_df["Hand"] == hand_value, dealer_card].reset_index(drop = True)[0]
            
            if playing_decision == "D":

                hand_cards = self.player_draws(hand_cards)
                hand_value = self.hand_value_calculator(hand_cards)

                #Cant draw more cards
                self.play = False

        #Check if soft doubling
        elif 1 in hand_cards:
            non_ace_card = [int(card) for card in hand_cards if card != 1][0]

            max_soft_double = int(max(self.soft_double_df["Hand"]))
            min_soft_double = int(min(self.soft_double_df["Hand"]))

            if dealer_card != 1:

                if (non_ace_card <= max_soft_double) & (non_ace_card >= min_soft_double) & (int(dealer_card) < 7):

                    playing_decision = self.soft_double_df.loc[self.soft_double_df["Hand"] == non_ace_card, dealer_card].reset_index(drop = True)[0]

                    if playing_decision == "D":

                        hand_cards = self.player_draws(hand_cards)
                        hand_value = self.hand_value_calculator(hand_cards)

                        #Cant draw more cards
                        self.play = False

        return hand_cards
    
    def ace_split_check(self, player_hands):

        if len(player_hands.keys()) != 2:

            ace_split = False

        else:

            if (player_hands[list(player_hands.keys())[0]][0] == 1) & (player_hands[list(player_hands.keys())[1]][0] == 1):

                ace_split = True

            else:

                ace_split = False

        return ace_split

    def player_decision(self, player_hands, hand_number, dealer_card):

        hand_cards = player_hands[hand_number]
        hand_value = self.hand_value_calculator(hand_cards)

        #Check if the hand is soft or not
        if hand_cards.count(1) > 0:

            self.soft_hand = True

        #Check if surrender
        if self.surrender:

            self.surrender_check(hand_cards, hand_value)

            #Did double down?
            self.double_down_tracker[hand_number] = False

        #If we are allowed to play (no surrender)
        if self.play:

            #Check if I can play (did I split aces?)
            ace_split_check = self.ace_split_check(player_hands)
            if ace_split_check == False:

                #Check if double down
                hand_cards = self.double_down_check(hand_cards, hand_value, dealer_card)

                #Did double down?
                if self.play:
                    self.double_down_tracker[hand_number] = False
                else:
                    self.double_down_tracker[hand_number] = True

                #Stop hitting when BSE says so
                while self.play:

                    hand_cards = self.player_draw_rules(hand_cards, hand_value, dealer_card)
                    #Update hand value
                    hand_value = self.hand_value_calculator(hand_cards)

            else:

                self.double_down_tracker[hand_number] = False
        else:

            hand_cards = "Surrender"

        #Update player hand 
        player_hands[hand_number] = hand_cards
        
    def dealer_draws(self, dealer_hand):

        dealer_hand_value =  self.hand_value_calculator(dealer_hand)

        while dealer_hand_value < 17:

            dealer_hand = self.player_draws(dealer_hand)
            dealer_hand_value = self.hand_value_calculator(dealer_hand)

        return dealer_hand

    def winners_check(self, player_hands, dealer_hand):

        #Calculate dealer hand
        dealer_hand_value = self.hand_value_calculator(dealer_hand)
        dealer_n_cards = len(dealer_hand)

        results = []

        for player_hand in player_hands.keys():


            hand_cards = player_hands[player_hand]

            if hand_cards == "Surrender":
                
                if (dealer_hand_value == 21) & (dealer_n_cards == 2):

                    outcome = "loss"

                elif self.double_down_tracker[player_hand]:

                    outcome = "loss_doubledown"

                else:

                    outcome = "loss_surrender"

            else:
                player_hand_value = self.hand_value_calculator(hand_cards)
                player_n_cards = len(hand_cards)

                #Blackjack win
                if (player_hand_value == 21) & (player_n_cards == 2) & (len(player_hands.keys()) == 1):
                
                    if (player_hand_value == dealer_hand_value) & (dealer_n_cards == 2):

                        outcome = "draw"

                    else:

                        outcome = "win_blackjack" 

                elif player_hand_value > 21:

                    outcome = "loss"

                elif dealer_hand_value > 21:

                    outcome = "win"

                elif player_hand_value > dealer_hand_value:

                    outcome = "win"

                elif player_hand_value < dealer_hand_value:

                    outcome = "loss"

                elif player_hand_value == dealer_hand_value:

                    if (dealer_n_cards == 2) & (dealer_hand_value == 21):

                        outcome = "loss"

                    else:

                        outcome = "draw"

                if self.double_down_tracker[player_hand]:

                    outcome = outcome + "_doubledown"

            results.append(outcome)

            #print(hand_cards)
            #print(dealer_hand)
            #print(outcome)
            #print("---------------------")

        return results
    
    def hand_postprocessing(self, player_hands, dealer_hand):

        for player_hand in player_hands:

            player_hands[player_hand] = [card if card != 1 else "A" for card in player_hands[player_hand]]

        dealer_hand = [card if card != 1 else "A" for card in dealer_hand]

        return player_hands, dealer_hand


    def round_simulator(self):

        #Get player cards
        #print("PLAYER GET INITIAL CARDS - START")
        player_hands = {}
        card_1 = self.card_draw(1)
        self.update_distribution(card_1)
        card_2 = self.card_draw(1)
        self.update_distribution(card_2)
        player_hands["hand_1"] = [int(card_1[0]), int(card_2[0])]
        #print("PLAYER GET INITIAL CARDS - END")

        #Get dealer card
        #print("DEALER GET CARD - START")
        dealer_card = [int(card) for card in self.card_draw(1)]
        self.update_distribution(dealer_card)
        #print("DEALER GET CARD - END")

        #Check how many necessaries split
        #print("PLAYER CHECKS SPLIT - START")
        self.split = self.splits_required(player_hands)
        while self.split:

            n_hands_to_check = len(player_hands.keys())
            for hand_check in range(n_hands_to_check):
                hand = "hand_{number}".format(number = hand_check + 1)
                #Check if split is necessary and perform if so
                self.hand_splitter(player_hands, hand, dealer_card[0])
        #print("PLAYER CHECKS SPLIT - END")

        #Perform player decision
        #print("PLAYER MAKES DECISION - START")
        for hand_number in player_hands.keys():
            #Set to play the hand
            self.play = True
            self.player_decision(player_hands, hand_number, dealer_card[0])
        #print("PLAYER MAKES DECISION - END")

        #Perform dealers draw
        #print("DEALER DRAWS - START")
        dealer_hand = self.dealer_draws(dealer_card)
        #print("DEALER DRAWS - END")

        #Check who won
        #print("ROUND RESULTS - START")
        results = self.winners_check(player_hands, dealer_hand)
        #print("ROUND RESULTS - END")

        #Hands postprocessing - replace 1 with A
        player_hands, dealer_hand = self.hand_postprocessing(player_hands, dealer_hand)

        return player_hands, dealer_hand, results

