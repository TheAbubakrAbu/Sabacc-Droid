# sabacc_console.py

import random
from typing import List

def print_error_message() -> None:
    '''
    Print an error message for invalid input.
    '''

    print('\nIncorrect input. Try again.')
    print('---------------------------')

def get_input(message: str) -> str:
    '''
    Show a message and return the user's input.
    '''

    print('\n' + '-' * len(message))
    prompt = input(f'{message} ').strip()
    return prompt

class Player:
    '''
    Represents a player with a name and a hand of cards.
    '''

    def __init__(self, name: str):
        '''
        Initialize a new player with the given name.
        '''

        self.name: str = name
        self.cards: List[int] = []

    def draw_card(self, deck: List[int]) -> None:
        '''
        Draw a card from the deck and add it to the player's hand.
        '''

        if not deck:
            raise ValueError('The deck is empty. Cannot draw more cards.')
        card: int = deck.pop()
        self.cards.append(card)

    def discard_card(self, card: int) -> bool:
        '''
        Discard a card from the player's hand. Returns True if it was discarded, or False if it wasn't in the hand.
        '''

        if card in self.cards:
            self.cards.remove(card)
            return True
        return False

    def replace_card(self, card: int, deck: List[int]) -> bool:
        '''
        Replace a card in the player's hand with a new one from the deck. Returns True if it was replaced, or False otherwise.
        '''

        if card in self.cards and deck:
            self.cards.remove(card)
            self.draw_card(deck)
            return True
        return False

    def print_cards(self) -> None:
        '''
        Print the player's hand and the total of their cards.
        '''

        print(f'\n{self.name}\'s Hand:')
        for card in self.cards:
            print(f'| {'+' if card > 0 else ''}{card} ', end='')
        print('|')
        print(f'\nTotal: {sum(self.cards)}')

class Game:
    '''
    Manages the deck, the players, and the flow of a two-player game.
    '''

    def __init__(self):
        '''
        Initialize a new game by generating the deck.
        '''

        self.deck: List[int] = self.generate_deck()
        self.players: List[Player] = []

    def generate_deck(self) -> List[int]:
        '''
        Generate and return a shuffled deck of Corellian Spike cards.
        '''

        deck: List[int] = [i for i in range(1, 11) for _ in range(3)]  # Positive cards
        deck += [-i for i in range(1, 11) for _ in range(3)]  # Negative cards
        deck += [0, 0]  # Sylops
        random.shuffle(deck)
        return deck

    def get_card(self) -> int:
        '''
        Draw a card from the deck and return it.
        '''

        if not self.deck:
            raise ValueError('The deck is empty. Cannot draw more cards.')
        return self.deck.pop()

    def play_turn(self, player: Player) -> bool:
        '''
        Run a single turn for a player. Returns True if the game continues, or False if the player junks.
        '''

        while True:
            player.print_cards()

            options: str = '"D" to draw, "T" to discard, "R" to replace, "S" to stand, or "J" to junk'
            if len(player.cards) == 1:
                options = '"D" to draw, "R" to replace, "S" to stand, or "J" to junk'

            decision: str = get_input(f'Enter {options}:').upper()

            if decision == 'D':
                player.draw_card(self.deck)
                print(f'\n{player.name} drew a card.')
                player.print_cards()
                return True
            elif decision == 'T' and len(player.cards) >= 2:
                card_to_discard: int = int(get_input('Enter the value of the card to discard:'))
                if player.discard_card(card_to_discard):
                    print(f'\n{player.name} discarded {card_to_discard}.')
                    player.print_cards()
                    return True
                else:
                    print(f'\n{card_to_discard} is not in your hand.')
            elif decision == 'R':
                card_to_replace: int = int(get_input('Enter the value of the card to replace:'))
                if player.replace_card(card_to_replace, self.deck):
                    print(f'\n{player.name} replaced {card_to_replace} with a new card.')
                    player.print_cards()
                    return True
                else:
                    print(f'\n{card_to_replace} is not in your hand.')
            elif decision == 'S':
                print(f'\n{player.name} stands.')
                return True
            elif decision == 'J':
                print(f'\n{player.name} junks and is out of the game.')
                return False
            else:
                print_error_message()

    def determine_winner(self) -> None:
        '''
        Determine and announce the winner based on the players' hands.
        '''

        player1, player2 = self.players
        player1_sum: int = sum(player1.cards)
        player2_sum: int = sum(player2.cards)

        player1.print_cards()
        player2.print_cards()
        print()

        # Check for Pure Sabacc (two Sylops)
        if player1.cards == [0, 0]:
            print(f'{player1.name} wins with a Pure Sabacc!')
            return
        elif player2.cards == [0, 0]:
            print(f'{player2.name} wins with a Pure Sabacc!')
            return

        # Check for a total of 0
        if player1_sum == 0 and player2_sum != 0:
            print(f'{player1.name} wins with a total of 0!')
            return
        elif player2_sum == 0 and player1_sum != 0:
            print(f'{player2.name} wins with a total of 0!')
            return

        # Compare totals
        if abs(player1_sum) < abs(player2_sum) or (
            abs(player1_sum) == abs(player2_sum) and player1_sum > player2_sum
        ):
            print(f'{player1.name} wins with a total closer to 0!')
        elif abs(player1_sum) > abs(player2_sum) or (
            abs(player1_sum) == abs(player2_sum) and player1_sum < player2_sum
        ):
            print(f'{player2.name} wins with a total closer to 0!')
        else:
            print('It\'s a tie!')

    def play_game(self, rounds: int, num_cards: int) -> None:
        '''
        Deal the starting cards, play every round, and announce the winner.
        '''

        # Initialize players
        self.players = [Player('Han Solo'), Player('Lando Calrissian')]

        # Deal the starting cards
        for player in self.players:
            for _ in range(num_cards):
                player.draw_card(self.deck)

        # Play rounds
        for round_num in range(1, rounds + 1):
            for player in self.players:
                print('\n' * 40)
                print(f'\nRound {round_num}/{rounds}')

                junk: bool = self.play_turn(player)

                if not junk:
                    return

                get_input('Press Enter to end your turn:')

        # Determine the winner
        self.determine_winner()

def run_Sabacc() -> None:
    '''
    Run the Sabacc game, handling user interaction and game setup.
    '''

    print('Welcome to Corellian Spike Sabacc, the game Han Solo played to win the Millennium Falcon from Lando Calrissian!')
    print('This is the version seen in Solo: A Star Wars Story and sold at Galaxy\'s Edge.')

    choice: str = get_input('Enter "H" to learn the rules or "P" to play:').upper()

    if choice == 'H':
        print('\nCorellian Spike Sabacc Rules:')
        print(
            '''
            1. The goal is a hand total as close to 0 as possible.
            2. Each player starts with the same number of cards.
            3. On your turn, you can draw, discard, replace, or stand. You can also junk to give up.
            4. Pure Sabacc (two Sylops, the 0 cards) wins automatically.
            5. Otherwise, a total of 0 wins. If neither player has 0, the total closest to 0 wins,
               and a positive total beats a negative one at the same distance.

            Good luck, and may the Force be with you!
            '''
        )

    try:
        rounds: int = int(get_input('Enter the number of rounds (default: 3):') or 3)
        num_cards: int = int(get_input('Enter the number of starting cards (default: 2):') or 2)

        if 1 <= rounds <= 10 and 1 <= num_cards <= 5:
            game = Game()
            game.play_game(rounds, num_cards)
        else:
            print('\nRounds must be between 1 and 10, and starting cards must be between 1 and 5.')
    except ValueError:
        print_error_message()

if __name__ == '__main__':
    run_Sabacc()