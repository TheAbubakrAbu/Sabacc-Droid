# kessel.py

import random
import asyncio
import logging
from discord import Embed, ButtonStyle, ui, Interaction
from rules import get_kessel_rules_embed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Player:
    '''Initialize a Player with a Discord user.'''

    def __init__(self, user):
        '''Initialize the player with a Discord User.'''
        self.user = user
        self.positive_card: int = None  # Positive card
        self.negative_card: int = None  # Negative card
        self.drawn_card: int = None     # Temporarily store the drawn card
        self.drawn_card_type: str = None  # 'positive' or 'negative'
        self.impostor_values = {}  # Store the values chosen for Impostor cards
        self.sylop_values = {}     # Store the values of Sylop cards

    def draw_card(self, deck: list[int], deck_type: str) -> None:
        '''Draw a card from the specified deck and store it temporarily.'''
        if not deck:
            raise ValueError('The deck is empty. Cannot draw more cards.')
        card = deck.pop()
        self.drawn_card = card
        self.drawn_card_type = deck_type

    def discard_drawn_card(self) -> None:
        '''Discard the temporarily stored drawn card.'''
        self.drawn_card = None
        self.drawn_card_type = None

    def get_cards_string(self) -> str:
        '''Get a string representation of the player's hand.'''
        def card_to_str(card):
            if card == 'Impostor':
                return 'Ψ'
            elif card == 'Sylop':
                return 'Ø'
            elif isinstance(card, int) and card >= 0:
                return f"+{card}"
            else:
                return str(card)
        cards = []
        if self.positive_card is not None:
            cards.append(card_to_str(self.positive_card))
        if self.negative_card is not None:
            cards.append(card_to_str(self.negative_card))
        return ' | ' + ' | '.join(cards) + ' |'

    def get_total(self) -> int:
        '''Calculate the total sum of the player's hand, considering Impostor and Sylop cards.'''
        positive_value = self.positive_card_value()
        negative_value = self.negative_card_value()

        if positive_value is None or negative_value is None:
            return None  # Hand is incomplete

        return positive_value + negative_value

    def positive_card_value(self) -> int:
        '''Get the value of the positive card, considering Sylop and Impostor behavior.'''
        if self.positive_card == 'Impostor':
            return self.impostor_values.get('positive', 0)  # Will be set after choice
        elif self.positive_card == 'Sylop':
            return self.sylop_values.get('positive', 0)     # Will be set at game end
        else:
            return self.positive_card

    def negative_card_value(self) -> int:
        '''Get the value of the negative card, considering Sylop and Impostor behavior.'''
        if self.negative_card == 'Impostor':
            return self.impostor_values.get('negative', 0)  # Will be set after choice
        elif self.negative_card == 'Sylop':
            return self.sylop_values.get('negative', 0)     # Will be set at game end
        else:
            return self.negative_card

class KesselGameView(ui.View):
    '''Manage the game's state and UI components for Kessel Sabacc.'''

    def __init__(self, rounds: int = 3, active_games: list = None, channel=None):
        '''Initialize the game view with optional rounds.'''
        super().__init__(timeout=None)
        self.players: list[Player] = []
        self.game_started = False
        self.current_player_index = -1  # Start at -1 to proceed to player 0 on first turn
        self.positive_deck: list = []
        self.negative_deck: list = []
        self.rounds = rounds
        self.message = None
        self.current_message = None
        self.active_views: list[ui.View] = []
        self.active_games = active_games
        self.channel = channel  # Set the channel

        self.view_rules_button = ViewRulesButton()
        self.add_item(self.view_rules_button)
        self.impostor_choices_pending = 0  # Counter for pending Impostor choices

    async def reset_lobby(self, interaction: Interaction) -> None:
        '''Reset the game lobby to its initial state.'''
        self.game_started = False
        self.players.clear()
        self.current_player_index = -1

        self.play_game_button.disabled = False
        self.leave_game_button.disabled = False
        self.start_game_button.disabled = True

        embed = Embed(
            title='Kessel Sabacc Game Lobby',
            description=f'Click **Play Game** to join the game.\n\n'
                        f'**Game Settings:**\n{self.rounds} rounds\n\n'
                        'Once at least two players have joined, the **Start Game** button will be enabled.',
            color=0x964B00
        )
        embed.set_footer(text='Kessel Sabacc')
        embed.set_thumbnail(url='https://static.wikia.nocookie.net/starwars/images/9/90/Sylop.png/revision/latest?cb=20180530101050')

        await interaction.response.edit_message(embed=embed, view=self)

    async def update_game_embed(self) -> None:
        '''Update the game embed to reflect the current player's turn.'''
        current_player = self.players[self.current_player_index]
        description = f'**Players:**\n' + '\n'.join(
            player.user.mention for player in self.players) + '\n\n'
        description += f'**Round {self.rounds_completed + 1}/{self.total_rounds}**\n'
        description += f'It\'s now {current_player.user.mention}\'s turn.\n'
        description += 'Click **Play Turn** to take your turn.'

        embed = Embed(
            title='Kessel Sabacc Game',
            description=description,
            color=0x964B00
        )
        embed.set_thumbnail(url='https://static.wikia.nocookie.net/starwars/images/9/90/Sylop.png/revision/latest?cb=20180530101050')

        # Remove previous message's buttons
        if self.current_message:
            try:
                await self.current_message.edit(view=None)
            except Exception as e:
                logger.error(f'Error removing previous message buttons: {e}')

        self.clear_items()
        self.add_item(PlayTurnButton(self))
        self.add_item(self.view_rules_button)
        self.current_message = await self.channel.send(
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

        description += f'**Game Settings:**\n{self.rounds} rounds\n\n'

        if len(self.players) < 2:
            description += 'Waiting for more players to join...\n'
        else:
            description += 'Click **Start Game** to begin!\n'

        embed = Embed(
            title='Kessel Sabacc Game Lobby',
            description=description,
            color=0x964B00
        )
        embed.set_footer(text='Kessel Sabacc')
        embed.set_thumbnail(url='https://static.wikia.nocookie.net/starwars/images/9/90/Sylop.png/revision/latest?cb=20180530101050')

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
            self.positive_deck, self.negative_deck = self.generate_decks()
            random.shuffle(self.players)

            # Deal initial cards
            for player in self.players:
                player.positive_card = self.positive_deck.pop()
                player.negative_card = self.negative_deck.pop()

            # Initialize round counters
            self.total_rounds = self.rounds
            self.rounds_completed = 0  # Start at round 0
            self.first_turn = True

            await interaction.response.defer()

            # Start the first turn
            await self.proceed_to_next_player()
        else:
            await interaction.response.send_message('Not enough players to start the game.', ephemeral=True)

    def generate_decks(self) -> tuple[list, list]:
        '''Generate and shuffle new decks for the game.'''
        # Positive Deck
        positive_deck = [i for i in range(1, 7) for _ in range(3)]  # Positive cards 1 to 6
        positive_deck += ['Impostor'] * 3  # Three Impostor cards
        positive_deck += ['Sylop']  # One Sylop card
        random.shuffle(positive_deck)

        # Negative Deck
        negative_deck = [-i for i in range(1, 7) for _ in range(3)]  # Negative cards -1 to -6
        negative_deck += ['Impostor'] * 3  # Three Impostor cards
        negative_deck += ['Sylop']  # One Sylop card
        random.shuffle(negative_deck)

        return positive_deck, negative_deck

    async def proceed_to_next_player(self) -> None:
        '''Proceed to the next player's turn or end the round if necessary.'''
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

        if self.current_player_index == 0 and not self.first_turn:
            self.rounds_completed += 1
            if self.rounds_completed >= self.total_rounds:
                # Game over
                await self.end_game()
                return

        await self.update_game_embed()

        if self.first_turn:
            self.first_turn = False

    def evaluate_hand(self, player: Player) -> tuple:
        '''Evaluate a player's hand to determine its rank and type.'''
        positive_value = player.positive_card_value()
        negative_value = player.negative_card_value()

        if positive_value is None or negative_value is None:
            return (float('inf'),), 'Incomplete Hand', None

        total = positive_value + negative_value
        abs_values = [abs(positive_value), abs(negative_value)]

        # Check for Sylop pair
        if player.positive_card == 'Sylop' and player.negative_card == 'Sylop':
            hand_type = 'Pure Sabacc'
            hand_rank = 1
            tie_breakers = []
        # Check for Sabacc hands
        elif total == 0:
            # Prime Sabacc (+1, -1)
            if sorted(abs_values) == [1, 1]:
                hand_type = 'Prime Sabacc'
                hand_rank = 2
            # Standard Sabacc
            else:
                hand_type = 'Standard Sabacc'
                hand_rank = 3
            tie_breakers = [min(abs_values)]  # Lower absolute value wins
        # Cheap Sabacc (+6, -6)
        elif sorted(abs_values) == [6, 6] and total == 0:
            hand_type = 'Cheap Sabacc'
            hand_rank = 4
            tie_breakers = [6]
        else:
            # Nulrhek hands
            hand_type = 'Nulrhek'
            hand_rank = 10
            tie_breakers = [
                abs(total),                # Closest to zero
                0 if total > 0 else 1,     # Positive totals beat negative totals
                -max(positive_value, negative_value)  # Highest positive card wins
            ]

        return (hand_rank, *tie_breakers), hand_type, total

    async def end_game(self) -> None:
        '''Determine the winner of the game and end it.'''

        # Assign values to Sylop cards
        for player in self.players:
            # Sylop cards
            if player.positive_card == 'Sylop' and player.negative_card == 'Sylop':
                # Both Sylops are zero
                player.sylop_values['positive'] = 0
                player.sylop_values['negative'] = 0
            elif player.positive_card == 'Sylop':
                # Sylop takes the value of the other card
                other_value = abs(player.negative_card_value())
                player.sylop_values['positive'] = other_value
            elif player.negative_card == 'Sylop':
                # Sylop takes the negative value of the other card
                other_value = -abs(player.positive_card_value())
                player.sylop_values['negative'] = other_value

        # Collect players with Impostor cards
        players_with_impostors = [player for player in self.players if 'Impostor' in (player.positive_card, player.negative_card)]

        if players_with_impostors:
            # Initialize counter
            self.impostor_choices_pending = sum(
                (1 if player.positive_card == 'Impostor' else 0) +
                (1 if player.negative_card == 'Impostor' else 0)
                for player in players_with_impostors
            )

            # For each player with Impostor cards, prompt them to choose
            for player in players_with_impostors:
                choose_view = ChooseImpostorValueView(self, player)
                self.active_views.append(choose_view)
                try:
                    embed = Embed(
                        title='Choose Your Impostor Card Value',
                        description='You have Impostor card(s). Two dice have been rolled for each Impostor card. Choose your preferred value.',
                        color=0x964B00
                    )
                    await player.user.send(embed=embed, view=choose_view)
                except Exception as e:
                    logger.error(f'Error sending Impostor choice to {player.user}: {e}')
                    # If unable to send message, assign random values
                    if player.positive_card == 'Impostor':
                        player.impostor_values['positive'] = random.randint(1, 6)
                        self.impostor_choices_pending -= 1
                    if player.negative_card == 'Impostor':
                        player.impostor_values['negative'] = -random.randint(1, 6)
                        self.impostor_choices_pending -= 1
                    self.check_impostor_choices_complete()
        else:
            # No Impostor cards, proceed to evaluate hands
            await self.evaluate_and_display_results()

    def check_impostor_choices_complete(self):
        '''Check if all Impostor choices are complete and proceed if so.'''
        if self.impostor_choices_pending <= 0:
            asyncio.create_task(self.evaluate_and_display_results())

    async def evaluate_and_display_results(self):
        '''Evaluate hands and display the game over screen.'''

        # Evaluate all players' hands
        evaluated_hands = []
        for player in self.players:
            hand_value, hand_type, total = self.evaluate_hand(player)
            evaluated_hands.append((hand_value, player, hand_type, total))

        evaluated_hands.sort(key=lambda x: x[0])

        results = '**Final Hands:**\n'
        for eh in evaluated_hands:
            _, player, hand_type, total = eh
            # Show Impostor and Sylop card values
            card_info = ''
            if player.positive_card == 'Impostor':
                impostor_value = player.impostor_values['positive']
                card_info += f' (Ψ value: +{impostor_value})'
            if player.negative_card == 'Impostor':
                impostor_value = player.impostor_values['negative']
                card_info += f' (Ψ value: {impostor_value})'
            if player.positive_card == 'Sylop':
                sylop_value = player.sylop_values['positive']
                card_info += f' (Ø value: +{sylop_value})'
            if player.negative_card == 'Sylop':
                sylop_value = player.sylop_values['negative']
                card_info += f' (Ø value: {sylop_value})'

            results += f'{player.user.mention}: {player.get_cards_string()}{card_info} (Total: {total}, Hand: {hand_type})\n'

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

        # Append explanations for symbols
        results += '\n\n**Legend:**\nΨ Impostor card (you choose its value)\nØ Sylop card (special behavior)'

        embed = Embed(
            title='Game Over',
            description=results,
            color=0x964B00
        )
        embed.set_thumbnail(url='https://static.wikia.nocookie.net/starwars/images/9/90/Sylop.png/revision/latest?cb=20180530101050')
        mentions = ' '.join(player.user.mention for player in self.players)
        await self.channel.send(content=f'{mentions}', embed=embed)

        if self.current_message:
            try:
                await self.current_message.delete()
            except Exception as e:
                logger.error(f'Error deleting current message: {e}')

        if self in self.active_games:
            self.active_games.remove(self)

class ChooseImpostorValueView(ui.View):
    '''View for players to choose their Impostor card values.'''

    def __init__(self, game_view: KesselGameView, player: Player):
        '''Initialize the view.'''
        super().__init__(timeout=60)
        self.game_view = game_view
        self.player = player
        self.state = None  # 'positive' or 'negative' or 'done'
        self.dice_values = []
        self.message = None  # Store the message to edit

        if player.positive_card == 'Impostor':
            self.state = 'positive'
            self.roll_dice()
        elif player.negative_card == 'Impostor':
            self.state = 'negative'
            self.roll_dice()
        else:
            self.state = 'done'

    def roll_dice(self):
        '''Roll two dice for the Impostor card.'''
        if self.state == 'positive':
            self.dice_values = [random.randint(1, 6), random.randint(1, 6)]
        elif self.state == 'negative':
            self.dice_values = [-random.randint(1, 6), -random.randint(1, 6)]

        # Create buttons for the two dice values
        self.clear_items()
        button1 = ui.Button(label=str(abs(self.dice_values[0])), style=ButtonStyle.primary)
        button1.callback = self.make_callback(self.dice_values[0])
        self.add_item(button1)

        button2 = ui.Button(label=str(abs(self.dice_values[1])), style=ButtonStyle.primary)
        button2.callback = self.make_callback(self.dice_values[1])
        self.add_item(button2)

    def make_callback(self, chosen_value: int):
        '''Create a callback function for choosing a dice value.'''

        async def callback(interaction: Interaction) -> None:
            if self.state == 'positive':
                self.player.impostor_values['positive'] = chosen_value
                self.game_view.impostor_choices_pending -= 1
                # Check if there's a negative Impostor to choose next
                if self.player.negative_card == 'Impostor':
                    self.state = 'negative'
                    self.roll_dice()
                    # Update the embed message
                    embed = Embed(
                        title='Choose Your Negative Impostor Card Value',
                        description='Two dice have been rolled for your negative Impostor card. Choose your preferred value.',
                        color=0x964B00
                    )
                    await interaction.response.edit_message(embed=embed, view=self)
                else:
                    self.state = 'done'
                    self.stop()
                    await interaction.response.edit_message(content='You have chosen your Impostor card value(s).', embed=None, view=None)
                    self.game_view.check_impostor_choices_complete()
            elif self.state == 'negative':
                self.player.impostor_values['negative'] = chosen_value
                self.game_view.impostor_choices_pending -= 1
                self.state = 'done'
                self.stop()
                await interaction.response.edit_message(content='You have chosen your Impostor card value(s).', embed=None, view=None)
                self.game_view.check_impostor_choices_complete()
            else:
                await interaction.response.send_message('You have already made your choices.', ephemeral=True)
        return callback

    async def interaction_check(self, interaction: Interaction) -> bool:
        '''Ensure that only the current player can interact with this view.'''
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        '''Handle timeout by assigning random values to any remaining Impostor cards.'''
        if self.state == 'positive':
            # Assign random value
            self.player.impostor_values['positive'] = random.choice(self.dice_values)
            self.game_view.impostor_choices_pending -= 1
            if self.player.negative_card == 'Impostor':
                self.state = 'negative'
                self.roll_dice()
                # Try to send another message
                try:
                    embed = Embed(
                        title='Choose Your Negative Impostor Card Value',
                        description='Two dice have been rolled for your negative Impostor card. Choose your preferred value.',
                        color=0x964B00
                    )
                    await self.player.user.send(embed=embed, view=self)
                    return  # Return here to wait for interaction
                except Exception as e:
                    logger.error(f'Error sending message to {self.player.user}: {e}')
                    self.player.impostor_values['negative'] = random.choice(self.dice_values)
                    self.game_view.impostor_choices_pending -= 1
        elif self.state == 'negative':
            self.player.impostor_values['negative'] = random.choice(self.dice_values)
            self.game_view.impostor_choices_pending -= 1

        self.game_view.check_impostor_choices_complete()
        self.stop()

class PlayTurnButton(ui.Button):
    '''Initialize the Play Turn button.'''

    def __init__(self, game_view: KesselGameView):
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
            title=f'Your Turn - Round {self.game_view.rounds_completed + 1}/{self.game_view.total_rounds}',
            description=f'**Your Hand:** {current_player.get_cards_string()}',
            color=0x964B00
        )
        # Add explanations if the player has Impostor or Sylop cards
        explanations = ''
        if 'Ψ' in current_player.get_cards_string():
            explanations += '\nΨ You have an **Impostor** card. Its value will be determined at the end of the game.'
        if 'Ø' in current_player.get_cards_string():
            explanations += '\nØ You have a **Sylop** card. See rules for its special behavior.'
        if explanations:
            embed.add_field(name='Note:', value=explanations.strip(), inline=False)

        embed.set_thumbnail(url='https://static.wikia.nocookie.net/starwars/images/9/90/Sylop.png/revision/latest?cb=20180530101050')
        await interaction.response.send_message(embed=embed, view=turn_view, ephemeral=True)

class TurnView(ui.View):
    '''Provide action buttons for the player's turn.'''

    def __init__(self, game_view: KesselGameView, player: Player):
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

    @ui.button(label='Draw Positive', style=ButtonStyle.primary)
    async def draw_positive_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Handle drawing a positive card.'''
        if not self.game_view.positive_deck:
            await interaction.response.send_message('The positive deck is empty.', ephemeral=True)
            return

        self.player.draw_card(self.game_view.positive_deck, 'positive')

        # Inform about Impostor or Sylop card
        special_info = ''
        if self.player.drawn_card == 'Impostor':
            special_info = '\n\nYou drew an **Impostor** card (Ψ)! You will choose its value at the end of the game.'
        elif self.player.drawn_card == 'Sylop':
            special_info = '\n\nYou drew a **Sylop** card (Ø)! See rules for its special behavior.'

        discard_view = DiscardCardView(self.game_view, self.player)
        self.game_view.active_views.append(discard_view)

        embed = Embed(
            title='You Drew a Positive Card',
            description=f'You drew: **{self.get_card_display(self.player.drawn_card)}**{special_info}\n\n'
                        f'**Your Hand:** {self.player.get_cards_string()}\n\n'
                        'Choose which card to keep.',
            color=0x964B00
        )
        await interaction.response.edit_message(embed=embed, view=discard_view)
        self.stop()

    @ui.button(label='Draw Negative', style=ButtonStyle.primary)
    async def draw_negative_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Handle drawing a negative card.'''
        if not self.game_view.negative_deck:
            await interaction.response.send_message('The negative deck is empty.', ephemeral=True)
            return

        self.player.draw_card(self.game_view.negative_deck, 'negative')

        # Inform about Impostor or Sylop card
        special_info = ''
        if self.player.drawn_card == 'Impostor':
            special_info = '\n\nYou drew an **Impostor** card (Ψ)! You will choose its value at the end of the game.'
        elif self.player.drawn_card == 'Sylop':
            special_info = '\n\nYou drew a **Sylop** card (Ø)! See rules for its special behavior.'

        discard_view = DiscardCardView(self.game_view, self.player)
        self.game_view.active_views.append(discard_view)

        embed = Embed(
            title='You Drew a Negative Card',
            description=f'You drew: **{self.get_card_display(self.player.drawn_card)}**{special_info}\n\n'
                        f'**Your Hand:** {self.player.get_cards_string()}\n\n'
                        'Choose which card to keep.',
            color=0x964B00
        )
        await interaction.response.edit_message(embed=embed, view=discard_view)
        self.stop()

    @ui.button(label='Stand', style=ButtonStyle.success)
    async def stand_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Handle the Stand action.'''
        embed = Embed(
            title=f'You Chose to Stand - Round {self.game_view.rounds_completed + 1}/{self.game_view.total_rounds}',
            description=f'**Your Hand:** {self.player.get_cards_string()}',
            color=0x964B00
        )
        # Add explanations if the player has Impostor or Sylop cards
        explanations = ''
        if 'Ψ' in self.player.get_cards_string():
            explanations += '\nΨ You have an **Impostor** card. You will choose its value at the end of the game.'
        if 'Ø' in self.player.get_cards_string():
            explanations += '\nØ You have a **Sylop** card. See rules for its special behavior.'
        if explanations:
            embed.add_field(name='Note:', value=explanations.strip(), inline=False)

        embed.set_thumbnail(url='https://static.wikia.nocookie.net/starwars/images/9/90/Sylop.png/revision/latest?cb=20180530101050')
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
        await self.game_view.proceed_to_next_player()

    @ui.button(label='Junk', style=ButtonStyle.danger)
    async def junk_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''Handle the Junk action, removing the player from the game.'''
        embed = Embed(
            title=f'You Chose to Junk - Round {self.game_view.rounds_completed + 1}/{self.game_view.total_rounds}',
            description='You have given up and are out of the game.',
            color=0x964B00
        )
        embed.set_thumbnail(url='https://static.wikia.nocookie.net/starwars/images/9/90/Sylop.png/revision/latest?cb=20180530101050')
        await interaction.response.edit_message(embed=embed, view=None)
        self.game_view.players.remove(self.player)
        self.stop()
        if len(self.game_view.players) < 2:
            await self.game_view.end_game()
        else:
            await self.game_view.proceed_to_next_player()

    def get_card_display(self, card):
        '''Return the display string for a card, using symbols if necessary.'''
        if card == 'Impostor':
            return 'Ψ'
        elif card == 'Sylop':
            return 'Ø'
        else:
            return str(card)

    async def on_timeout(self) -> None:
        '''Handle the scenario where a player does not make a move within the timeout period.'''
        try:
            channel = self.game_view.channel
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

class DiscardCardView(ui.View):
    '''Provide buttons to choose which card to keep after drawing.'''

    def __init__(self, game_view: KesselGameView, player: Player):
        '''Initialize the discard card view.'''
        super().__init__(timeout=30)
        self.game_view = game_view
        self.player = player

        card_type = self.player.drawn_card_type

        existing_card = getattr(self.player, f'{card_type}_card')
        drawn_card = self.player.drawn_card

        if existing_card is not None:
            button = ui.Button(
                label=f"Keep Existing {card_type.capitalize()} ({self.get_card_display(existing_card)})",
                style=ButtonStyle.primary if card_type == 'positive' else ButtonStyle.danger
            )
            button.callback = self.make_callback('keep_existing')
            self.add_item(button)

        button = ui.Button(
            label=f"Keep Drawn {card_type.capitalize()} ({self.get_card_display(drawn_card)})",
            style=ButtonStyle.primary if card_type == 'positive' else ButtonStyle.danger
        )
        button.callback = self.make_callback('keep_drawn')
        self.add_item(button)

    def get_card_display(self, card):
        '''Return the display string for a card, using symbols if necessary.'''
        if card == 'Impostor':
            return 'Ψ'
        elif card == 'Sylop':
            return 'Ø'
        else:
            return str(card)

    def make_callback(self, choice: str):
        '''Create a callback function for choosing which card to keep.'''

        async def callback(interaction: Interaction) -> None:
            card_type = self.player.drawn_card_type
            drawn_card = self.player.drawn_card

            if choice == 'keep_existing':
                # Return the drawn card to the deck
                if card_type == 'positive':
                    self.game_view.positive_deck.append(drawn_card)
                else:
                    self.game_view.negative_deck.append(drawn_card)
                # No changes to player's existing card
            elif choice == 'keep_drawn':
                # Return the existing card to the deck
                existing_card = getattr(self.player, f'{card_type}_card')
                if card_type == 'positive':
                    if existing_card is not None:
                        self.game_view.positive_deck.append(existing_card)
                    self.player.positive_card = drawn_card
                else:
                    if existing_card is not None:
                        self.game_view.negative_deck.append(existing_card)
                    self.player.negative_card = drawn_card

            # Clear temporary drawn card
            self.player.discard_drawn_card()

            # Proceed to next player
            embed = Embed(
                title='Card Selected',
                description=f'**Your Hand:** {self.player.get_cards_string()}',
                color=0x964B00
            )
            # Add explanations if the player has Impostor or Sylop cards
            explanations = ''
            if 'Ψ' in self.player.get_cards_string():
                explanations += '\nΨ You have an **Impostor** card. You will choose its value at the end of the game.'
            if 'Ø' in self.player.get_cards_string():
                explanations += '\nØ You have a **Sylop** card. See rules for its special behavior.'
            if explanations:
                embed.add_field(name='Note:', value=explanations.strip(), inline=False)

            await interaction.response.edit_message(embed=embed, view=None)
            self.stop()
            await self.game_view.proceed_to_next_player()
        return callback

    async def interaction_check(self, interaction: Interaction) -> bool:
        '''Ensure that only the current player can interact with this view.'''
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        '''Handle timeout.'''
        try:
            channel = self.game_view.channel
            await channel.send(f'{self.player.user.mention}, you took too long to choose a card. Your turn has been skipped.')
            self.stop()
            await self.game_view.proceed_to_next_player()
        except Exception as e:
            logger.error(f'Error during DiscardCardView timeout: {e}')

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
        '''Display the Kessel Sabacc game rules when the button is pressed.'''
        rules_embed = get_kessel_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)