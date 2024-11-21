# sabaac_droid.py

import random
from dotenv import load_dotenv
import os
import logging
from discord import Intents, Embed, ButtonStyle, ui, Interaction, app_commands
from discord.ext import commands

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Step 0: Load Token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN is None:
    raise ValueError('DISCORD_TOKEN environment variable not found in .env file.')

active_games = []

# Step 1: Setup Bot
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Step 2: Sabaac Game Management
class Player:
    '''Initialize a Player with a Discord user.'''
    
    def __init__(self, user):
        '''Initialize the player with a Discord User.'''

        self.user = user
        self.cards: list[int] = []

    def draw_card(self, deck: list[int]) -> None:
        '''Draw a card from the deck and add it to the player's hand.'''

        if not deck:
            raise ValueError('The deck is empty. Cannot draw more cards.')
        card = deck.pop()
        self.cards.append(card)

    def discard_card(self, card: int) -> bool:
        '''Discard a card from the player's hand. Returns True if successful.'''

        if len(self.cards) <= 1:
            return False
        if card in self.cards:
            self.cards.remove(card)
            return True
        return False

    def replace_card(self, card: int, deck: list[int]) -> bool:
        '''Replace a card in hand with a new one from the deck. Returns True if successful.'''

        if card in self.cards and deck:
            self.cards.remove(card)
            self.draw_card(deck)
            return True
        return False

    def get_cards_string(self) -> str:
        '''Get a string representation of the player's hand.'''

        return ' | ' + ' | '.join(f"{'+' if c > 0 else ''}{c}" for c in self.cards) + ' |'

    def get_total(self) -> int:
        '''Calculate the total sum of the player's hand.'''

        return sum(self.cards)

class SabaacGameView(ui.View):
    '''Manage the game's state and UI components.'''

    def __init__(self, rounds: int = 3, num_cards: int = 2):
        '''Initialize the game view with optional rounds and number of initial cards.'''

        super().__init__(timeout=None)
        self.players: list[Player] = []
        self.game_started = False
        self.current_player_index = -1  # Start at -1 to proceed to player 0 on first turn
        self.deck: list[int] = []
        self.rounds = rounds
        self.num_cards = num_cards
        self.message = None
        self.current_message = None
        self.active_views: list[ui.View] = []

        self.view_rules_button = ViewRulesButton()
        self.add_item(self.view_rules_button)

    async def reset_lobby(self, interaction: Interaction) -> None:
        '''Reset the game lobby to its initial state.'''

        self.game_started = False
        self.players.clear()
        self.current_player_index = -1

        self.play_game_button.disabled = False
        self.leave_game_button.disabled = False
        self.start_game_button.disabled = True

        embed = Embed(
            title='Sabaac Game Lobby',
            description=f'Click **Play Game** to join the game.\n\n'
                    f'**Game Settings:**\n{self.rounds} rounds\n{self.num_cards} starting cards\n\n'
                    'Once at least two players have joined, the **Start Game** button will be enabled.',
            color=0x964B00
        )
        embed.set_footer(text='Corellian Spike Sabaac')
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')

        await interaction.response.edit_message(embed=embed, view=self)

    async def update_game_embed(self) -> None:
        '''Update the game embed to reflect the current player's turn.'''

        current_player = self.players[self.current_player_index]
        description = f'**Players:**\n' + '\n'.join(
            player.user.mention for player in self.players) + '\n\n'
        description += f'**Round {self.rounds_completed}/{self.total_rounds}**\n'
        description += f'It\'s now {current_player.user.mention}\'s turn.\n'
        description += 'Click **Play Turn** to take your turn.'

        embed = Embed(
            title='Sabaac Game',
            description=description,
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')

        # Remove previous message's buttons
        if self.current_message:
            try:
                await self.current_message.edit(view=None)
            except Exception as e:
                logger.error(f'Error removing previous message buttons: {e}')

        self.clear_items()
        self.add_item(PlayTurnButton(self))
        self.add_item(self.view_rules_button)
        self.current_message = await self.message.channel.send(
            content=f'{current_player.user.mention}',
            embed=embed,
            view=self
        )

    async def update_lobby_embed(self, interaction=None) -> None:
        '''Update the lobby embed with the current list of players and custom settings.'''

        if len(self.players) == 0:
            if interaction:
                await self.reset_lobby(interaction)
            return

        description = f'**Players Joined ({len(self.players)}/8):**\n' + '\n'.join(
            player.user.mention for player in self.players) + '\n\n'

        if self.game_started:
            description += 'The game has started!'
        elif len(self.players) >= 8:
            description += 'The game lobby is full.'

        description += f'**Game Settings:**\n{self.rounds} rounds\n{self.num_cards} starting cards\n\n'

        if len(self.players) < 2:
            description += 'Waiting for more players to join...\n'
        else:
            description += 'Click **Start Game** to begin!\n'

        embed = Embed(
            title='Sabaac Game Lobby',
            description=description,
            color=0x964B00
        )
        embed.set_footer(text='Corellian Spike Sabaac')
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')

        self.start_game_button.disabled = len(self.players) < 2 or self.game_started
        self.play_game_button.disabled = len(self.players) >= 8 or self.game_started

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await self.message.edit(embed=embed, view=self)

    @ui.button(label='Play Game', style=ButtonStyle.primary)
    async def play_game_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Add the user to the game when they press Play Game.'''

        user = interaction.user
        if self.game_started:
            await interaction.response.send_message('The game has already started.', ephemeral=True)
            return
        if any(player.user.id == user.id for player in self.players):
            await interaction.response.send_message('You are already in the game.', ephemeral=True)
        elif len(self.players) >= 8:
            await interaction.response.send_message('The maximum number of players (8) has been reached.', ephemeral=True)
        else:
            self.players.append(Player(user))
            await self.update_lobby_embed(interaction)

    @ui.button(label='Leave Game', style=ButtonStyle.danger)
    async def leave_game_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Remove the user from the game when they press Leave Game.'''

        user = interaction.user
        if self.game_started:
            await interaction.response.send_message('You can\'t leave the game after it has started.', ephemeral=True)
            return
        player = next((p for p in self.players if p.user.id == user.id), None)
        if player:
            self.players.remove(player)
            await self.update_lobby_embed(interaction)
        else:
            await interaction.response.send_message('You are not in the game.', ephemeral=True)

    @ui.button(label='Start Game', style=ButtonStyle.success, disabled=True)
    async def start_game_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Start the game when the Start Game button is pressed.'''

        user = interaction.user
        if self.game_started:
            await interaction.response.send_message('The game has already started.', ephemeral=True)
            return
        if interaction.user.id not in [player.user.id for player in self.players]:
            await interaction.response.send_message('Only players in the game can start the game.', ephemeral=True)
            return
        if len(self.players) >= 2:
            self.game_started = True

            # Initialize the game
            self.deck = self.generate_deck()
            random.shuffle(self.players)

            # Deal initial cards
            for player in self.players:
                for _ in range(self.num_cards):
                    player.draw_card(self.deck)

            # Initialize round counters
            self.total_rounds = self.rounds
            self.rounds_completed = 1  # Start at round 1
            self.first_turn = True

            await interaction.response.defer()

            # Start the first turn
            await self.proceed_to_next_player()
        else:
            await interaction.response.send_message('Not enough players to start the game.', ephemeral=True)

    def generate_deck(self) -> list[int]:
        '''Generate and shuffle a new deck for the game.'''

        deck = [i for i in range(1, 11) for _ in range(3)]  # Positive cards
        deck += [-i for i in range(1, 11) for _ in range(3)]  # Negative cards
        deck += [0, 0]
        random.shuffle(deck)
        return deck

    async def proceed_to_next_player(self) -> None:
        '''Proceed to the next player's turn or end the round if necessary.'''

        self.current_player_index = (self.current_player_index + 1) % len(self.players)

        if self.current_player_index == 0 and not self.first_turn:
            self.rounds_completed += 1
            if self.rounds_completed > self.total_rounds:
                # Game over
                await self.end_game()
                return

        await self.update_game_embed()

        if self.first_turn:
            self.first_turn = False

    def evaluate_hand(self, player: Player) -> tuple:
        '''Evaluate a player's hand to determine its rank and type.'''

        cards = player.cards
        total = sum(cards)
        hand_type = None
        hand_rank = None
        tie_breakers = []
        counts = {}

        # Count occurrences of each card value
        for card in cards:
            counts[card] = counts.get(card, 0) + 1

        positive_cards = [c for c in cards if c > 0]
        negative_cards = [c for c in cards if c < 0]
        zeros = counts.get(0, 0)

        # Create counts of absolute card values
        abs_counts = {}
        for card in cards:
            abs_card = abs(card)
            abs_counts[abs_card] = abs_counts.get(abs_card, 0) + 1

        # Check for specialty hands (must total zero)
        if total == 0:
            # Pure Sabacc (two zeros)
            if zeros == 2 and len(cards) == 2:
                hand_type = 'Pure Sabacc'
                hand_rank = 1
                tie_breakers = [min(abs(c) for c in cards if c != 0)]  # Lower integer wins tie
            # Full Sabacc (+10, +10, -10, -10, 0)
            elif sorted(cards) == [-10, -10, 0, +10, +10]:
                hand_type = 'Full Sabacc'
                hand_rank = 2
                tie_breakers = []
            # Yee-Haa (one pair and a zero)
            elif zeros == 1 and any(count >= 2 for value, count in abs_counts.items() if value != 0):
                hand_type = 'Yee-Haa'
                hand_rank = 3
                tie_breakers = [min(abs(c) for c in cards if c != 0)]  # Lower integer wins tie
            # Banthas Wild (three of a kind)
            elif any(count >= 3 for count in abs_counts.values()):
                hand_type = 'Banthas Wild'
                hand_rank = 4
                tie_breakers = [min(abs(c) for c in cards)]  # Lower integer wins tie
            # Rule of Two (two pairs)
            elif len([count for count in abs_counts.values() if count >= 2]) >= 2:
                hand_type = 'Rule of Two'
                hand_rank = 5
                tie_breakers = [min(abs(c) for c in cards)]  # Lower integer wins tie
            # Sabacc (one pair)
            elif any(count >= 2 for count in abs_counts.values()):
                hand_type = 'Sabacc'
                hand_rank = 6
                tie_breakers = [min(abs(c) for c in cards)]  # Lower integer wins tie
            else:
                # Non-specialty hand that equals zero
                hand_type = 'Zero Sum Hand'
                hand_rank = 7
                tie_breakers = [
                    min(abs(c) for c in cards),  # Lower integer wins
                    -len(cards),  # More cards wins
                    -sum(positive_cards),  # Higher positive sum wins
                    -max(positive_cards) if positive_cards else float('-inf'),  # Highest single positive value
                ]
        else:
            # Nulrhek hands (not totaling zero)
            hand_type = 'Nulrhek'
            hand_rank = 10
            tie_breakers = [
                abs(total),  # Closest to zero
                0 if total > 0 else 1,  # Positive beats negative
                -len(cards),  # More cards wins
                -sum(positive_cards),  # Higher positive sum wins
                -max(positive_cards) if positive_cards else float('-inf'),  # Highest single positive card
            ]

        return (hand_rank, *tie_breakers), hand_type, total

    async def end_game(self) -> None:
        '''Determine the winner of the game and end it.'''

        # Evaluate all players' hands
        evaluated_hands = []
        for player in self.players:
            hand_value, hand_type, total = self.evaluate_hand(player)
            evaluated_hands.append((hand_value, player, hand_type, total))

        evaluated_hands.sort(key=lambda x: x[0])

        results = '**Game Over!**\n\n**Final Hands:**\n'
        for eh in evaluated_hands:
            _, player, hand_type, total = eh
            results += f'{player.user.mention}: {player.get_cards_string()} (Total: {total}, Hand: {hand_type})\n'

        best_hand_value = evaluated_hands[0][0]
        winners = [eh for eh in evaluated_hands if eh[0] == best_hand_value]

        if len(winners) == 1:
            winner = winners[0][1]
            hand_type = winners[0][2]
            results += f'\n🎉 {winner.user.mention} wins with a **{hand_type}**!'
        else:
            results += '\nIt\'s a tie between:'
            for eh in winners:
                player = eh[1]
                results += f' {player.user.mention}'
            results += '!'

        embed = Embed(
            title='Sabaac Game Over',
            description=results,
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        mentions = ' '.join(player.user.mention for player in self.players)
        await self.message.channel.send(content=f'{mentions}', embed=embed)

        if self.current_message:
            try:
                await self.current_message.delete()
            except Exception as e:
                logger.error(f'Error deleting current message: {e}')

        if self in active_games:
            active_games.remove(self)

class PlayTurnButton(ui.Button):
    '''Initialize the Play Turn button.'''

    def __init__(self, game_view: SabaacGameView):
        '''Initialize the button.'''

        super().__init__(label='Play Turn', style=ButtonStyle.primary)
        self.game_view = game_view

    async def callback(self, interaction: Interaction) -> None:
        '''Handle the Play Turn button press.'''

        current_player = self.game_view.players[self.game_view.current_player_index]
        if interaction.user.id != current_player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return
        # Send an ephemeral message with the player's hand and action buttons
        turn_view = TurnView(self.game_view, current_player)
        self.game_view.active_views.append(turn_view)
        embed = Embed(
            title=f'Your Turn - Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}',
            description=f'**Your Hand:** {current_player.get_cards_string()}\n**Total:** {current_player.get_total()}',
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        await interaction.response.send_message(embed=embed, view=turn_view, ephemeral=True)

class TurnView(ui.View):
    '''Provide action buttons for the player's turn.'''

    def __init__(self, game_view: SabaacGameView, player: Player):
        '''Initialize the turn view.'''

        super().__init__(timeout=30)
        self.game_view = game_view
        self.player = player

    async def interaction_check(self, interaction: Interaction) -> bool:
        '''Ensure that only the current player can interact with the turn view.'''

        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return False
        return True

    @ui.button(label='Draw Card', style=ButtonStyle.primary)
    async def draw_card_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Handle the Draw Card action.'''

        self.player.draw_card(self.game_view.deck)
        embed = Embed(
            title=f'You Drew a Card - Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}',
            description=f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}',
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
        await self.game_view.proceed_to_next_player()

    @ui.button(label='Discard Card', style=ButtonStyle.secondary)
    async def discard_card_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Handle the Discard Card action.'''

        if len(self.player.cards) <= 1:
            await interaction.response.send_message('You cannot discard when you have only one card.', ephemeral=True)
            return
        # Send a message with buttons representing the player's cards
        card_select_view = CardSelectView(self, action='discard')
        self.game_view.active_views.append(card_select_view)
        embed = Embed(
            title=f'Discard a Card - Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}',
            description='Click the button corresponding to the card you want to discard.',
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        await interaction.response.send_message(embed=embed, view=card_select_view, ephemeral=True)
        self.stop()

    @ui.button(label='Replace Card', style=ButtonStyle.secondary)
    async def replace_card_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Handle the Replace Card action.'''

        # Send a message with buttons representing the player's cards
        card_select_view = CardSelectView(self, action='replace')
        self.game_view.active_views.append(card_select_view)
        embed = Embed(
            title=f'Replace a Card - Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}',
            description='Click the button corresponding to the card you want to replace.',
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        await interaction.response.send_message(embed=embed, view=card_select_view, ephemeral=True)
        self.stop()

    @ui.button(label='Stand', style=ButtonStyle.success)
    async def stand_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Handle the Stand action.'''

        embed = Embed(
            title=f'You Chose to Stand - Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}',
            description=f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}',
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
        await self.game_view.proceed_to_next_player()

    @ui.button(label='Junk', style=ButtonStyle.danger)
    async def junk_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Handle the Junk action, removing the player from the game.'''

        embed = Embed(
            title=f'You Chose to Junk - Round {self.game_view.rounds_completed}/{self.game_view.total_rounds}',
            description='You have given up and are out of the game.',
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
        await interaction.response.edit_message(embed=embed, view=None)
        self.game_view.players.remove(self.player)
        self.stop()
        if len(self.game_view.players) < 2:
            await self.game_view.end_game()
        else:
            await self.game_view.proceed_to_next_player()

    async def on_timeout(self) -> None:
        '''Handle the scenario where a player does not make a move within the timeout period.'''

        try:
            channel = self.game_view.current_message.channel
            embed = Embed(
                title='Turn Skipped',
                description=f'{self.player.user.mention} took too long and their turn was skipped.',
                color=0xFF0000
            )
            await channel.send(embed=embed)
            self.stop()
            await self.game_view.proceed_to_next_player()
        except Exception as e:
            logger.error(f'Error during timeout handling: {e}')

    def stop(self) -> None:
        '''Stop the view and remove it from the active views list.'''

        super().stop()
        if self in self.game_view.active_views:
            self.game_view.active_views.remove(self)

class CardSelectView(ui.View):
    '''Initialize the CardSelectView for choosing a card to discard or replace.'''

    def __init__(self, turn_view: TurnView, action: str):
        '''Initialize the card selection view.'''

        super().__init__(timeout=30)
        self.turn_view = turn_view
        self.game_view = turn_view.game_view
        self.player = turn_view.player
        self.action = action
        self.create_buttons()

    def create_buttons(self) -> None:
        '''Create buttons for each card in the player's hand.'''

        for idx, card in enumerate(self.player.cards):
            button = ui.Button(label=f"{'+' if card > 0 else ''}{card}", style=ButtonStyle.primary)
            button.callback = self.make_callback(card, idx)
            self.add_item(button)
            if len(self.children) >= 25:
                break

    def make_callback(self, card_value: int, card_index: int):
        '''Create a callback function for a card button.'''

        async def callback(interaction: Interaction) -> None:
            if self.action == 'discard':
                if len(self.player.cards) <= 1:
                    await interaction.response.send_message('You cannot discard when you have only one card.', ephemeral=True)
                    return
                self.player.cards.pop(card_index)
                embed = Embed(
                    title=f'You Discarded {card_value} - Round {self.turn_view.game_view.rounds_completed}/{self.turn_view.game_view.total_rounds}',
                    description=f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}',
                    color=0x964B00
                )
            elif self.action == 'replace':
                self.player.cards.pop(card_index)
                self.player.draw_card(self.turn_view.game_view.deck)
                embed = Embed(
                    title=f'You Replaced {card_value} - Round {self.turn_view.game_view.rounds_completed}/{self.turn_view.game_view.total_rounds}',
                    description=f'**Your Hand:** {self.player.get_cards_string()}\n**Total:** {self.player.get_total()}',
                    color=0x964B00
                )
            else:
                embed = Embed(title='Unknown Action', description='An error occurred.', color=0xFF0000)
            embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
            await interaction.response.edit_message(embed=embed, view=None)
            self.stop()
            await self.turn_view.game_view.proceed_to_next_player()
        return callback

    async def interaction_check(self, interaction: Interaction) -> bool:
        '''Ensure that only the current player can interact with the card selection view.'''

        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('This is not your card selection.', ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        '''Handle the scenario where a player does not select a card within the timeout period.'''

        try:
            channel = self.game_view.current_message.channel
            embed = Embed(
                title='Turn Skipped',
                description=f'{self.player.user.mention} took too long and their turn was skipped.',
                color=0xFF0000
            )
            await channel.send(embed=embed)
            self.stop()
            await self.turn_view.game_view.proceed_to_next_player()
        except Exception as e:
            logger.error(f'Error during timeout handling: {e}')

    def stop(self) -> None:
        '''Stop the view and remove it from the active views list.'''

        super().stop()
        if self in self.game_view.active_views:
            self.game_view.active_views.remove(self)

class ViewRulesButton(ui.Button):
    '''Initialize the View Rules button.'''

    def __init__(self):
        '''Initialize the button.'''

        super().__init__(label='View Rules', style=ButtonStyle.secondary)

    async def callback(self, interaction: Interaction) -> None:
        '''Display the game rules when the button is pressed.'''

        rules_embed = get_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)

def get_rules_embed() -> Embed:
    '''Create an embed containing the game rules.'''

    rules_embed = Embed(
        title='Sabaac Game Rules',
        description='**Objective:**\nAchieve a hand with a total sum as close to zero as possible.\n\n'
                    '**Gameplay:**\n- Each player starts with two cards.\n'
                    '- On your turn, you can choose to **Draw**, **Discard**, **Replace**, **Stand**, or **Junk**.\n\n'
                    '**Actions:**\n'
                    '- **Draw Card:** Draw one card from the deck.\n'
                    '- **Discard Card:** Remove one card from your hand.\n'
                    '- **Replace Card:** Swap one card in your hand with a new one from the deck.\n'
                    '- **Stand:** Keep your current hand without changes.\n'
                    '- **Junk:** Give up and exit the game.\n\n'
                    '**Winning Conditions:**\n'
                    '1. **Special Hands (Total sum equals zero):**\n'
                    '   - **Pure Sabacc:** Two zeros.\n'
                    '   - **Full Sabacc:** +10, +10, -10, -10, 0.\n'
                    '   - **Yee-Haa:** One pair and a zero.\n'
                    '   - **Banthas Wild:** Three of a kind.\n'
                    '   - **Rule of Two:** Two pairs.\n'
                    '   - **Sabacc:** One pair (e.g., +5 and -5).\n'
                    '   - *Note:* Lower integer values win ties.\n\n'
                    '2. **Zero Sum Hands (Total sum equals zero):**\n'
                    '   - Lower integer values win.\n'
                    '   - Most cards win.\n'
                    '   - Highest positive sum wins.\n'
                    '   - Highest single positive card wins.\n\n'
                    '3. **Nulrhek Hands (Total sum does not equal zero):**\n'
                    '   - Closest to zero wins.\n'
                    '   - Positive totals beat negative totals.\n'
                    '   - Most cards win.\n'
                    '   - Highest positive sum wins.\n'
                    '   - Highest single positive card wins.\n\n'
                    'A default game lasts for 3 rounds. Good luck! May the Force be with you!',
        color=0x964B00
    )
    rules_embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
    return rules_embed

# Slash command to start the game with optional parameters
@bot.tree.command(name='sabaac', description='Start a Sabaac game with optional custom settings')
@app_commands.describe(
    rounds='Number of rounds (default: 3, max: 5)',
    num_cards='Number of initial cards (default: 2, max: 3)'
)
async def sabaac_command(interaction: Interaction, rounds: int = 3, num_cards: int = 2) -> None:
    '''Initiate a new Sabaac game with optional custom settings.'''

    rounds = max(1, min(rounds, 5))
    num_cards = max(1, min(num_cards, 3))

    view = SabaacGameView(rounds=rounds, num_cards=num_cards)
    embed = Embed(
        title='Sabaac Game Lobby',
        description=f'Click **Play Game** to join the game.\n\n'
                    f'**Game Settings:**\n{rounds} rounds\n{num_cards} starting cards\n\n'
                    'Once at least two players have joined, the **Start Game** button will be enabled.',
        color=0x964B00
    )
    embed.set_footer(text='Corellian Spike Sabaac')
    embed.set_thumbnail(url='https://raw.githubusercontent.com/compycore/sabacc/gh-pages/images/logo.png')
    try:
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()
        active_games.append(view)
    except Exception as e:
        await interaction.response.send_message('An error occurred while starting the game.', ephemeral=True)
        logger.error(f'Error in sabaac_command: {e}')

# Slash command to display rules publicly
@bot.tree.command(name='help', description='Display the Sabaac game rules')
async def help_command(interaction: Interaction) -> None:
    '''Display the game rules publicly.'''

    rules_embed = get_rules_embed()
    await interaction.response.send_message(embed=rules_embed)

# Step 4: Handle Startup
@bot.event
async def on_ready() -> None:
    '''Event handler for when the bot is ready.'''

    await bot.tree.sync()  # Sync slash commands with Discord
    print(f'{bot.user} is now running!')

# Step 5: Run Bot
def main() -> None:
    '''Run the Discord bot.'''

    bot.run(TOKEN)

if __name__ == '__main__':
    main()