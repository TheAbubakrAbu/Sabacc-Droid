# sabaac_console.py

import random
from typing import List

def print_error_message() -> None:
    '''Prints an error message for incorrect inputs.'''
    
    print('\nIncorrect input. Try again.')
    print('---------------------------')

def get_input(message: str) -> str:
    '''Displays a message and gets input from the user. Returns user's input'''

    print('\n' + '-' * len(message))
    prompt = input(f'{message} ').strip()
    return prompt

class Player:
    def __init__(self, name: str):
        '''Initializes a new player with a given name.'''

        self.name: str = name
        self.cards: List[int] = []

    def draw_card(self, deck: List[int]) -> None:
        '''Draws a card from the deck and adds it to the player's hand.'''

        if not deck:
            raise ValueError('The deck is empty. Cannot draw more cards.')
        card: int = deck.pop()
        self.cards.append(card)

    def discard_card(self, card: int) -> bool:
        '''Discards a card from the player's hand. Returns True if the card was discarded, False if the card was not in the hand.'''

        if card in self.cards:
            self.cards.remove(card)
            return True
        return False

    def replace_card(self, card: int, deck: List[int]) -> bool:
        '''Replaces a card in the player's hand with a new one from the deck. Returns True if the card was replaced, False otherwise.'''

        if card in self.cards and deck:
            self.cards.remove(card)
            self.draw_card(deck)
            return True
        return False

    def print_cards(self) -> None:
        '''Prints the player's current hand and the total sum of their cards.'''

        print(f'\n{self.name}\'s Turn:')
        for card in self.cards:
            print(f'| {'+' if card > 0 else ''}{card} ', end='')
        print('|')
        print(f'\nTotal = {sum(self.cards)}')


class Game:
    def __init__(self):
        '''Initializes a new game by generating the deck and setting up players.'''

        self.deck: List[int] = self.generate_deck()
        self.players: List[Player] = []

    def generate_deck(self) -> List[int]:
        '''Generates a shuffled deck of cards for the game. Returns the list'''

        deck: List[int] = [i for i in range(1, 11) for _ in range(3)]  # Positive cards
        deck += [-i for i in range(1, 11) for _ in range(3)]  # Negative cards
        deck += [0, 0]
        random.shuffle(deck)
        return deck

    def get_card(self) -> int:
        '''Draws a card from the deck. Returns the card drawn from the deck.'''

        if not self.deck:
            raise ValueError('The deck is empty. Cannot draw more cards.')
        return self.deck.pop()

    def play_turn(self, player: Player) -> bool:
        '''Executes a single turn for a player. Returns True if the turn proceeds, False if the player junks (gives up).'''

        while True:
            player.print_cards()

            options: str = '"D" to draw, "T" to discard, "R" to replace, "S" to stand, or "J" to junk'
            if len(player.cards) == 1:
                options = '"D" to draw, "R" to replace, "S" to stand, or "J" to junk'
                
            decision: str = get_input(f'Enter {options}:').upper()

            if decision == 'D':
                player.draw_card(self.deck)
                print(f'\n{player.name} just drew a card!')
                player.print_cards()
                return True
            elif decision == 'T' and len(player.cards) >= 2:
                card_to_discard: int = int(get_input('Enter the number of the card to discard:'))
                if player.discard_card(card_to_discard):
                    print(f'\n{card_to_discard} has been removed from {player.name}\'s hand!')
                    player.print_cards()
                    return True
                else:
                    print(f'\n{card_to_discard} is not in your hand.')
            elif decision == 'R':
                card_to_replace: int = int(get_input('Enter the number of the card to replace:'))
                if player.replace_card(card_to_replace, self.deck):
                    print(f'\n{player.name} replaced {card_to_replace} with a new card.')
                    player.print_cards()
                    return True
                else:
                    print(f'\n{card_to_replace} is not in your hand.')
            elif decision == 'S':
                print(f'\n{player.name} stands and does nothing.')
                return True
            elif decision == 'J':
                print(f'\n{player.name} junks and gives up.')
                return False
            else:
                print_error_message()

    def determine_winner(self) -> None:
        '''Determines and announces the winner of the game based on the players' hands.'''

        player1, player2 = self.players
        player1_sum: int = sum(player1.cards)
        player2_sum: int = sum(player2.cards)

        player1.print_cards()
        player2.print_cards()
        print()

        # Check for 'Pure Sabaac' (two zeros)
        if player1.cards == [0, 0]:
            print(f'{player1.name} wins with Pure Sabaac!')
            return
        elif player2.cards == [0, 0]:
            print(f'{player2.name} wins with Pure Sabaac!')
            return

        # Check for zero total
        if player1_sum == 0 and player2_sum != 0:
            print(f'{player1.name} wins with a sum of zero!')
            return
        elif player2_sum == 0 and player1_sum != 0:
            print(f'{player2.name} wins with a sum of zero!')
            return

        # Compare sums
        if abs(player1_sum) < abs(player2_sum) or (
            abs(player1_sum) == abs(player2_sum) and player1_sum > player2_sum
        ):
            print(f'{player1.name} wins with a sum closer to zero!')
        elif abs(player1_sum) > abs(player2_sum) or (
            abs(player1_sum) == abs(player2_sum) and player1_sum < player2_sum
        ):
            print(f'{player2.name} wins with a sum closer to zero!')
        else:
            print('It\'s a tie based on total sums.')

    def play_game(self, rounds: int, num_cards: int) -> None:
        '''Starts and manages the game.'''

        # Initialize players
        self.players = [Player('Han Solo'), Player('Lando Calrissian')]

        # Deal initial cards
        for player in self.players:
            for _ in range(num_cards):
                player.draw_card(self.deck)

        # Play rounds
        for round_num in range(1, rounds + 1):
            for player in self.players:
                print('\n' * 40)
                print(f'\nRound {round_num} / {rounds}:')

                junk: bool = self.play_turn(player)

                if not junk:
                    return

                get_input('Type anything to confirm you are ready to end your turn:')

        # Determine the winner
        self.determine_winner()

def run_sabaac() -> None:
    '''Runs the Sabaac game, handling user interaction and game setup.'''

    print('Welcome to Sabaac (Corellian Spike Edition) - The game that led Han Solo to win the Millennium Falcon from Lando Calrissian!')
    print('This version of the game is found in *Solo* and sold in Galaxy\'s Edge.')

    choice: str = get_input('Type "H" if you\'d like to learn the rules or "P" to play:').upper()

    if choice == 'H':
        print('\nWelcome to the rules of Sabaac (Corellian Spike Edition):')
        print(
            '''
            1. The goal is to have the sum of your cards as close to zero as possible.
            2. Each player is dealt a certain number of cards to start with.
            3. During each turn, players can choose to draw a card, discard a card, replace a card, or stand.
            4. Pure Sabaac (two zeros) wins automatically.
            5. Other special rules apply when both players have a sum of zero:
            6. The game is based on the version seen in *Solo* and sold at Galaxy's Edge, where Han Solo famously won the Millennium Falcon from Lando Calrissian.
            
            Good luck, and may the Force be with you!
            '''
        )

    try:
        rounds: int = int(get_input('Enter the number of rounds to play (default 3):') or 3)
        num_cards: int = int(get_input('Enter the number of starting cards (default 2):') or 2)

        if 1 <= rounds <= 10 and 1 <= num_cards <= 5:
            game = Game()
            game.play_game(rounds, num_cards)
        else:
            print('\nRounds must be between 1 and 10, and cards must be between 1 and 5.')
    except ValueError:
        print_error_message()

if __name__ == '__main__':
    run_sabaac()