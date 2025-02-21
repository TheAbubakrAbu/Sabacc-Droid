# kessel.py

import random
import logging
from urllib.parse import quote
import discord
from discord import Embed, ui, Interaction
from rules import get_kessel_rules_embed
import requests
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_and_process_image(url: str, resize_width: int = 80, resize_height: int = 120) -> Image.Image:
    '''Download an image and resize it.'''
    try:
        response = requests.get(url, stream=True, timeout=5)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert('RGBA')
        img = img.resize((resize_width, resize_height), Image.LANCZOS)
        return img
    except Exception as e:
        logger.error(f'Error processing image from {url}: {e}')
        return None

def combine_card_images(card_image_urls: list[str], resize_width: int = 80, resize_height: int = 120, padding: int = 10) -> BytesIO|None:
    '''Combine multiple card images horizontally into a single image while preserving order.'''
    if not card_image_urls:
        return None

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [(i, executor.submit(download_and_process_image, url, resize_width, resize_height)) for i, url in enumerate(card_image_urls)]
        results = []
        for idx, future in futures:
            img = future.result()
            results.append((idx, img))
    results.sort()
    card_images = [img for idx, img in results if img is not None]
    if not card_images:
        return None

    total_width = sum(img.width for img in card_images) + padding * (len(card_images) - 1)
    max_height = max(img.height for img in card_images)

    combined_image = Image.new('RGBA', (total_width, max_height), (255, 255, 255, 0))

    x_offset = 0
    for img in card_images:
        combined_image.paste(img, (x_offset, 0))
        x_offset += img.width + padding

    image_bytes = BytesIO()
    combined_image.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    return image_bytes

class Player:
    '''Represents a player in the Kessel Sabacc game.'''

    def __init__(self, user: discord.User) -> None:
        '''
        Initialize the player with a Discord User.
        '''
        self.user = user
        self.positive_card = None
        self.negative_card = None
        self.drawn_card = None
        self.drawn_card_type = None
        self.impostor_values = {}
        self.sylop_values = {}

    def draw_card(self, deck: list[int|str], deck_type: str) -> None:
        '''
        Draw a card from the specified deck and store it temporarily.
        '''
        if not deck:
            raise ValueError('The deck is empty. Cannot draw more cards.')
        card = deck.pop()
        self.drawn_card = card
        self.drawn_card_type = deck_type

    def discard_drawn_card(self) -> None:
        '''
        Discard the temporarily stored drawn card.
        '''
        self.drawn_card = None
        self.drawn_card_type = None

    def get_cards_string(self, include_special_values: bool=False) -> str:
        '''
        Get a string representation of the player's hand.
        '''
        def card_to_str(card: int|str, sign: str) -> str:
            if card == 'Impostor':
                value = self.impostor_values.get(sign)
                if include_special_values and value is not None:
                    value_sign = '+' if value >= 0 else ''
                    return f'{sign}Ψ/{value_sign}{value}'
                else:
                    return f'{sign}Ψ'
            elif card == 'Sylop':
                value = self.sylop_values.get(sign)
                if include_special_values and value is not None:
                    value_sign = '+' if value >= 0 else ''
                    return f'{sign}Ø/{value_sign}{value}'
                else:
                    return f'{sign}Ø'
            elif isinstance(card, int):
                return f'''{'+' if card >= 0 else ''}{card}'''
            else:
                return str(card)

        cards = []
        if self.positive_card is not None:
            cards.append(card_to_str(self.positive_card, '+'))
        if self.negative_card is not None:
            cards.append(card_to_str(self.negative_card, '-'))
        return ' | ' + ' | '.join(cards) + ' |'

    def get_total(self) -> int|None:
        '''
        Calculate the total sum of the player's hand.
        '''
        positive_value = self.positive_card_value()
        negative_value = self.negative_card_value()

        if positive_value is None or negative_value is None:
            return None
        return positive_value + negative_value

    def positive_card_value(self) -> int|None:
        '''
        Get the value of the positive card.
        '''
        if self.positive_card == 'Impostor':
            return self.impostor_values.get('+', 0)
        elif self.positive_card == 'Sylop':
            return self.sylop_values.get('+', 0)
        else:
            return self.positive_card

    def negative_card_value(self) -> int|None:
        '''
        Get the value of the negative card.
        '''
        if self.negative_card == 'Impostor':
            return self.impostor_values.get('-', 0)
        elif self.negative_card == 'Sylop':
            return self.sylop_values.get('-', 0)
        else:
            return self.negative_card

    def get_card_image_urls(self, include_drawn_card: bool=False, include_both_positive_cards: bool=False) -> list[str]:
        '''
        Get the URLs for the player's cards images.
        '''
        base_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/kessel/'
        card_image_urls = []

        if include_both_positive_cards and self.drawn_card_type == 'positive' and self.drawn_card is not None:
            positive_card = self.positive_card
            if positive_card is not None:
                if isinstance(positive_card, int):
                    card_image_urls.append(f'''{base_url}{quote('+' + str(positive_card))}.png''')
                elif isinstance(positive_card, str):
                    card_image_urls.append(f'''{base_url}{quote('+' + positive_card.lower())}.png''')
            drawn_card = self.drawn_card
            if isinstance(drawn_card, int):
                card_image_urls.append(f'''{base_url}{quote('+' + str(drawn_card))}.png''')
            elif isinstance(drawn_card, str):
                card_image_urls.append(f'''{base_url}{quote('+' + drawn_card.lower())}.png''')
            negative_card = self.negative_card
            if negative_card is not None:
                if isinstance(negative_card, int):
                    card_image_urls.append(f'''{base_url}{quote(str(negative_card))}.png''')
                elif isinstance(negative_card, str):
                    card_image_urls.append(f'''{base_url}{quote('-' + negative_card.lower())}.png''')
        else:
            for card_attr, sign in [('positive_card', '+'), ('negative_card', '')]:
                card = getattr(self, card_attr)
                if card is not None:
                    if isinstance(card, int):
                        card_image_urls.append(f'''{base_url}{quote(sign + str(card))}.png''')
                    elif isinstance(card, str):
                        if sign == '+':
                            card_image_urls.append(f'''{base_url}{quote(sign + card.lower())}.png''')
                        else:
                            card_image_urls.append(f'''{base_url}{quote('-' + card.lower())}.png''')

            if include_drawn_card and self.drawn_card is not None:
                drawn_card = self.drawn_card
                sign = '+' if self.drawn_card_type == 'positive' else ''
                if isinstance(drawn_card, int):
                    card_image_urls.append(f'''{base_url}{quote(sign + str(drawn_card))}.png''')
                elif isinstance(drawn_card, str):
                    if sign == '+':
                        card_image_urls.append(f'''{base_url}{quote(sign + drawn_card.lower())}.png''')
                    else:
                        card_image_urls.append(f'''{base_url}{quote('-' + drawn_card.lower())}.png''')

        return card_image_urls

    @staticmethod
    def get_card_display(card: int|str) -> str:
        '''
        Return the display string for a card, using symbols if necessary.
        '''
        if card == 'Impostor':
            return 'Ψ'
        elif card == 'Sylop':
            return 'Ø'
        elif isinstance(card, int):
            return f'''{'+' if card >= 0 else ''}{card}'''
        else:
            return str(card)

class KesselGameView(ui.View):
    '''Manages the game state and user interactions for Kessel Sabacc.'''

    def __init__(self, rounds: int=3, active_games: list=None, channel=None) -> None:
        '''
        Initialize the game view with game settings.
        '''
        super().__init__(timeout=None)
        self.players: list[Player] = []
        self.game_started = False
        self.current_player_index = -1
        self.positive_deck: list[int|str] = []
        self.negative_deck: list[int|str] = []
        self.rounds = rounds
        self.message = None
        self.current_message = None
        self.active_games = active_games
        self.channel = channel
        self.solo_game = False
        self.view_rules_button = ViewRulesButton()
        self.add_item(self.view_rules_button)

    async def reset_lobby(self, interaction: Interaction) -> None:
        '''
        Reset the game lobby to its initial state.
        '''
        self.game_started = False
        self.players.clear()
        self.current_player_index = -1

        self.play_game_button.disabled = False
        self.leave_game_button.disabled = False
        self.start_game_button.disabled = True

        embed = Embed(
            title='Kessel Sabacc Lobby',
            description='Click **Play Game** to join the game!\n\n'
                        f'**Game Settings:**\n{self.rounds} rounds\n2 starting cards\n\n'
                        'Once someone has joined, **Start Game** will be enabled.',
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/kessel/logo.png')

        await interaction.response.edit_message(embed=embed, view=self)

    async def update_game_embed(self) -> None:
        '''
        Update the game embed to reflect the current player's turn.
        '''
        current_player = self.players[self.current_player_index]

        description = f'**Players:**\n' + '\n'.join(
            player.user.mention for player in self.players) + '\n\n'
        description += f'**Round {self.rounds_completed + 1}/{self.rounds}**\n'
        description += f'It\'s now {current_player.user.mention}\'s turn.\n'
        description += 'Click **Play Turn** to proceed.'

        positive_back_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/kessel/%2Bcard.png'
        negative_back_url = 'https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/kessel/-card.png'
        card_image_urls = [positive_back_url, negative_back_url]
        image_bytes = combine_card_images(card_image_urls)

        embed = Embed(
            title='Kessel Sabacc',
            description=description,
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/kessel/logo.png')

        play_turn_view = PlayTurnView(self)

        if image_bytes:
            file = discord.File(fp=image_bytes, filename='combined_cards.png')
            embed.set_image(url='attachment://combined_cards.png')
            self.current_message = await self.channel.send(
                content=current_player.user.mention,
                embed=embed,
                file=file,
                view=play_turn_view
            )
        else:
            self.current_message = await self.channel.send(
                content=current_player.user.mention,
                embed=embed,
                view=play_turn_view
            )

    async def update_lobby_embed(self, interaction: Interaction=None) -> None:
        '''
        Update the lobby embed with the current list of players and custom settings.
        '''
        if len(self.players) == 0:
            if interaction:
                await self.reset_lobby(interaction)
            return

        description = f'**Players Joined ({len(self.players)}/8):**\n' + '\n'.join(
            player.user.mention for player in self.players) + '\n\n'

        if self.game_started:
            description += 'The game has started!\n\n'
        elif len(self.players) >= 8:
            description += 'The game lobby is full.\n\n'

        description += f'**Game Settings:**\n{self.rounds} rounds\n2 starting cards\n\n'

        if len(self.players) < 2:
            description += 'Waiting for more players to join...\n'
            description += 'Click **Start Game** if you want to play with an AI.\n'
        else:
            description += 'Click **Start Game** to begin!\n'

        embed = Embed(
            title='Kessel Sabacc Lobby',
            description=description,
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/kessel/logo.png')

        if self.game_started:
            self.play_game_button.disabled = True
            self.leave_game_button.disabled = True
            self.start_game_button.disabled = True
        else:
            self.start_game_button.disabled = len(self.players) < 1 or self.game_started
            self.play_game_button.disabled = len(self.players) >= 8 or self.game_started

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await self.message.edit(embed=embed, view=self)

    @ui.button(label='Play Game', style=discord.ButtonStyle.primary)
    async def play_game_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''
        Add the user to the game when they press Play Game.
        '''
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

    @ui.button(label='Leave Game', style=discord.ButtonStyle.danger)
    async def leave_game_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''
        Remove the user from the game when they press Leave Game.
        '''
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

    @ui.button(label='Start Game', style=discord.ButtonStyle.success, disabled=True)
    async def start_game_button(self, interaction: Interaction, button: ui.Button) -> None:
        '''
        Start the game when the Start Game button is pressed.
        '''
        if self.game_started:
            await interaction.response.send_message('The game has already started.', ephemeral=True)
            return
        if interaction.user.id not in [player.user.id for player in self.players]:
            await interaction.response.send_message('Only players in the game can start the game.', ephemeral=True)
            return
        if len(self.players) >= 1:
            self.game_started = True

            self.positive_deck, self.negative_deck = self.generate_decks()
            random.shuffle(self.players)

            for player in self.players:
                player.positive_card = self.positive_deck.pop()
                player.negative_card = self.negative_deck.pop()

            self.rounds_completed = 0
            self.first_turn = True

            self.play_game_button.disabled = True
            self.leave_game_button.disabled = True
            self.start_game_button.disabled = True

            await interaction.response.defer()
            await self.update_lobby_embed()
            await self.proceed_to_next_player()

            if len(self.players) == 1:
                self.solo_game = True
        else:
            await interaction.response.send_message('Not enough players to start the game.', ephemeral=True)

    def generate_decks(self) -> tuple[list[int|str], list[int|str]]:
        '''
        Generate and shuffle new decks for the game.
        '''
        positive_deck = [i for i in range(1, 7) for _ in range(3)]
        positive_deck += ['Impostor'] * 3
        positive_deck += ['Sylop']
        second_p_deck = positive_deck.copy()
        random.shuffle(positive_deck)
        random.shuffle(second_p_deck)

        negative_deck = [-i for i in range(1, 7) for _ in range(3)]
        negative_deck += ['Impostor'] * 3
        negative_deck += ['Sylop']
        second_n_deck = negative_deck.copy()
        random.shuffle(negative_deck)
        random.shuffle(second_n_deck)

        return (['Sylop'] + positive_deck + second_p_deck), (['Sylop'] + negative_deck + second_n_deck)

    async def proceed_to_next_player(self) -> None:
        '''
        Proceed to the next player's turn or end the round if necessary.
        '''
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

        if self.current_player_index == 0 and not self.first_turn:
            self.rounds_completed += 1
            if self.rounds_completed >= self.rounds:
                await self.end_game()
                return

        await self.update_game_embed()

        if self.first_turn:
            self.first_turn = False

    def evaluate_hand(self, player: Player) -> tuple[tuple[float|int,...], str, int|None]:
        '''
        Evaluate a player's hand to determine its rank and type.
        '''
        positive_value = player.positive_card_value()
        negative_value = player.negative_card_value()

        if positive_value is None or negative_value is None:
            return (float('inf'),), 'Incomplete Hand', None

        total = positive_value + negative_value
        abs_values = [abs(positive_value), abs(negative_value)]

        if player.positive_card == 'Sylop' and player.negative_card == 'Sylop':
            hand_type = 'Pure Sabacc'
            hand_rank = 1
            tie_breakers = []
        elif total == 0 and sorted(abs_values) == [1, 1]:
            hand_type = 'Prime Sabacc'
            hand_rank = 2
            tie_breakers = [min(abs_values)]
        elif total == 0 and sorted(abs_values) == [6, 6]:
            hand_type = 'Cheap Sabacc'
            hand_rank = 3
            tie_breakers = [6]
        elif total == 0:
            hand_type = 'Standard Sabacc'
            hand_rank = 4
            tie_breakers = [min(abs_values)]
        else:
            hand_type = 'Nulrhek'
            hand_rank = 10
            tie_breakers = [
                abs(total),
                0 if total > 0 else 1,
                -max(positive_value, negative_value)
            ]

        return (hand_rank, *tie_breakers), hand_type, total

    async def end_game(self) -> None:
        '''
        Determine the winner of the game and end it.
        '''
        players_with_impostors = [player for player in self.players if 'Impostor' in (player.positive_card, player.negative_card)]

        if players_with_impostors:
            for player in players_with_impostors:
                if 'Impostor' in (player.positive_card, player.negative_card):
                    choose_view = ChooseImpostorValueView(self, player)
                    await choose_view.send_initial_message()
                    await choose_view.wait()

        self.assign_sylop_values()
        await self.evaluate_and_display_results()

    def assign_sylop_values(self) -> None:
        '''
        Assign values to Sylop cards after Impostor values have been assigned.
        '''
        for player in self.players:
            if player.positive_card == 'Sylop' and player.negative_card == 'Sylop':
                player.sylop_values['+'] = 0
                player.sylop_values['-'] = 0
            elif player.positive_card == 'Sylop':
                other_value = abs(player.negative_card_value())
                player.sylop_values['+'] = other_value
            elif player.negative_card == 'Sylop':
                other_value = -abs(player.positive_card_value())
                player.sylop_values['-'] = other_value

    async def evaluate_and_display_results(self) -> None:
        '''
        Evaluate hands and display the game over screen.
        '''
        if self.solo_game and not hasattr(self, 'ai_player_added'):
            lando_user = type('AIUser', (object,), {'mention': 'Lando Calrissian AI', 'name': 'Lando Calrissian AI'})
            lando = Player(user=lando_user())

            non_impostor_positive_cards = [card for card in self.positive_deck if card != 'Impostor']
            if not non_impostor_positive_cards:
                lando.positive_card = random.randint(1, 6)
            else:
                lando_positive_card = random.choice(non_impostor_positive_cards)
                self.positive_deck.remove(lando_positive_card)
                lando.positive_card = lando_positive_card

            non_impostor_negative_cards = [card for card in self.negative_deck if card != 'Impostor']
            if not non_impostor_negative_cards:
                lando.negative_card = -random.randint(1, 6)
            else:
                lando_negative_card = random.choice(non_impostor_negative_cards)
                self.negative_deck.remove(lando_negative_card)
                lando.negative_card = lando_negative_card

            self.players.append(lando)
            self.ai_player_added = True

        if not self.players:
            embed = Embed(
                title='Game Over',
                description='Nobody won because everyone junked!',
                color=0x964B00
            )
            embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/kessel/logo.png')
            await self.channel.send(embed=embed, view=EndGameView(rounds=self.rounds, active_games=self.active_games, channel=self.channel))
            if self in self.active_games:
                self.active_games.remove(self)
            return

        evaluated_hands = []
        for player in self.players:
            hand_value, hand_type, total = self.evaluate_hand(player)
            evaluated_hands.append((hand_value, player, hand_type, total))

        evaluated_hands.sort(key=lambda x: x[0])

        results = '**Final Hands:**\n'
        for eh in evaluated_hands:
            _, player, hand_type, total = eh
            line1 = f'- {player.user.mention}: {player.get_cards_string(include_special_values=True)}'
            line2 = f'   - Total: {total} | Hand: {hand_type}'
            results += f'{line1}\n{line2}\n'

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

        results += '\n\n**Legend** (View rules for more information):\n'
        results += 'Ψ: Impostor card (value chosen by 2 dice at the end)\n'
        results += 'Ø: Sylop card (value is the same as other card in hand)\n'

        embed = Embed(
            title='Game Over',
            description=results,
            color=0x964B00
        )
        embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/kessel/logo.png')
        mentions = ' '.join(player.user.mention for player in self.players if 'AIUser' not in type(player.user).__name__)
        await self.channel.send(content=mentions, embed=embed, view=EndGameView(rounds=self.rounds, active_games=self.active_games, channel=self.channel))

        if self in self.active_games:
            self.active_games.remove(self)

class EndGameView(ui.View):
    '''Provide buttons for actions after the game ends.'''

    def __init__(self, rounds: int, active_games: list, channel) -> None:
        '''
        Initialize the view with a Play Again button and a View Rules button.
        '''
        super().__init__(timeout=None)
        self.rounds = rounds
        self.active_games = active_games
        self.channel = channel
        self.play_again_clicked = False

        self.play_again_button = ui.Button(label='Play Again', style=discord.ButtonStyle.success)
        self.play_again_button.callback = self.play_again_callback
        self.add_item(self.play_again_button)
        self.add_item(ViewRulesButton())

    async def play_again_callback(self, interaction: Interaction) -> None:
        '''
        Handle the Play Again button press.
        '''
        if self.play_again_clicked:
            await interaction.response.send_message('Play Again has already been initiated.', ephemeral=True)
            return

        self.play_again_clicked = True
        self.play_again_button.disabled = True
        await interaction.response.edit_message(view=self)

        new_game_view = KesselGameView(rounds=self.rounds, active_games=self.active_games, channel=self.channel)
        new_game_view.message = await self.channel.send('New game lobby created!', view=new_game_view)
        new_player = Player(interaction.user)
        new_game_view.players.append(new_player)
        await new_game_view.update_lobby_embed()
        self.active_games.append(new_game_view)

class PlayTurnView(ui.View):
    '''View for the player to start their turn.'''

    def __init__(self, game_view: KesselGameView) -> None:
        '''
        Initialize the play turn view.
        '''
        super().__init__(timeout=None)
        self.game_view = game_view
        self.play_turn_button = PlayTurnButton(game_view)
        self.add_item(self.play_turn_button)
        self.add_item(ViewRulesButton())

class PlayTurnButton(ui.Button):
    '''Button for the player to begin their turn.'''

    def __init__(self, game_view: KesselGameView) -> None:
        '''
        Initialize the play turn button.
        '''
        super().__init__(label='Play Turn', style=discord.ButtonStyle.primary)
        self.game_view = game_view

    async def callback(self, interaction: Interaction) -> None:
        '''
        Handle the Play Turn button press.
        '''
        current_player = self.game_view.players[self.game_view.current_player_index]
        if interaction.user.id != current_player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return

        await interaction.response.edit_message(view=self.view)

        title = f'Your Turn | Round {self.game_view.rounds_completed + 1}/{self.game_view.rounds}'
        description = f'**Your Hand:** {current_player.get_cards_string()}'

        turn_view = TurnView(self.game_view, current_player)
        embed, files = await send_embed_with_hand(
            current_player,
            title,
            description
        )

        if files:
            await interaction.followup.send(embed=embed, view=turn_view, file=files[0], ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, view=turn_view, ephemeral=True)

async def send_embed_with_hand(player: Player, title: str, description: str, include_drawn_card: bool=False, include_both_positive_cards: bool=False) -> tuple[Embed, list[discord.File]]:
    '''
    Prepare the embed (and image file if any) for the player's hand, but do not send it yet.
    '''
    card_image_urls = player.get_card_image_urls(include_drawn_card=include_drawn_card, include_both_positive_cards=include_both_positive_cards)
    files = []

    embed = Embed(
        title=title,
        description=description,
        color=0x964B00
    )

    explanations = ''
    if 'Ψ' in player.get_cards_string():
        explanations += 'Ψ: Impostor card (value chosen by 2 dice at the end)\n'
    if 'Ø' in player.get_cards_string():
        explanations += 'Ø: Sylop card (value is the same as other card in hand)\n'
    if explanations:
        embed.add_field(name='**Legend**:', value=explanations.strip(), inline=False)

    embed.set_thumbnail(url='https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/src/sabacc_droid/images/kessel/logo.png')

    if card_image_urls:
        try:
            image_bytes = combine_card_images(card_image_urls)
            if image_bytes:
                file = discord.File(fp=image_bytes, filename='combined_cards.png')
                embed.set_image(url='attachment://combined_cards.png')
                files.append(file)
        except Exception as e:
            logger.error(f'Failed to combine card images: {e}')

    return embed, files

class TurnView(ui.View):
    '''Provide action buttons for the player's turn.'''

    def __init__(self, game_view: KesselGameView, player: Player) -> None:
        '''
        Initialize the turn view.
        '''
        super().__init__(timeout=None)
        self.game_view = game_view
        self.player = player

        self.draw_positive_button = ui.Button(label='Draw Positive', style=discord.ButtonStyle.primary)
        self.draw_positive_button.callback = self.draw_positive_button_callback
        self.add_item(self.draw_positive_button)

        self.draw_negative_button = ui.Button(label='Draw Negative', style=discord.ButtonStyle.primary)
        self.draw_negative_button.callback = self.draw_negative_button_callback
        self.add_item(self.draw_negative_button)

        self.stand_button = ui.Button(label='Stand', style=discord.ButtonStyle.success)
        self.stand_button.callback = self.stand_button_callback
        self.add_item(self.stand_button)

        self.junk_button = ui.Button(label='Junk', style=discord.ButtonStyle.danger)
        self.junk_button.callback = self.junk_button_callback
        self.add_item(self.junk_button)

    async def interaction_check(self, interaction: Interaction) -> bool:
        '''
        Ensure that only the current player can interact with this view.
        '''
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return False
        return True

    async def draw_positive_button_callback(self, interaction: Interaction) -> None:
        if not self.game_view.positive_deck:
            await interaction.response.send_message('The positive deck is empty.', ephemeral=True)
            return

        self.player.draw_card(self.game_view.positive_deck, 'positive')

        special_info = ''
        if self.player.drawn_card == 'Impostor':
            special_info = '\n\nYou drew an **Impostor** card (Ψ)! You will choose its value at the end of the game.'
        elif self.player.drawn_card == 'Sylop':
            special_info = '\n\nYou drew a **Sylop** card (Ø)! See rules for its special behavior.'

        discard_view = DiscardCardView(self.game_view, self.player)
        title = 'You Drew a Positive Card'
        description = f'You drew: **{Player.get_card_display(self.player.drawn_card)}**{special_info}\n\n' \
                      f'**Your Hand:** {self.player.get_cards_string()}\n\n' \
                      'Choose which card to keep.'

        embed, files = await send_embed_with_hand(
            self.player,
            title,
            description,
            include_drawn_card=True,
            include_both_positive_cards=True
        )

        if files:
            await interaction.response.edit_message(embed=embed, view=discard_view, attachments=[files[0]])
        else:
            await interaction.response.edit_message(embed=embed, view=discard_view)

        self.stop()

    async def draw_negative_button_callback(self, interaction: Interaction) -> None:
        if not self.game_view.negative_deck:
            await interaction.response.send_message('The negative deck is empty.', ephemeral=True)
            return

        self.player.draw_card(self.game_view.negative_deck, 'negative')

        special_info = ''
        if self.player.drawn_card == 'Impostor':
            special_info = '\n\nYou drew an **Impostor** card (Ψ)! You will choose its value at the end of the game.'
        elif self.player.drawn_card == 'Sylop':
            special_info = '\n\nYou drew a **Sylop** card (Ø)! See rules for its special behavior.'

        discard_view = DiscardCardView(self.game_view, self.player)
        title = 'You Drew a Negative Card'
        description = f'You drew: **{Player.get_card_display(self.player.drawn_card)}**{special_info}\n\n' \
                      f'**Your Hand:** {self.player.get_cards_string()}\n\n' \
                      'Choose which card to keep.'

        embed, files = await send_embed_with_hand(
            self.player,
            title,
            description,
            include_drawn_card=True
        )

        if files:
            await interaction.response.edit_message(embed=embed, view=discard_view, attachments=[files[0]])
        else:
            await interaction.response.edit_message(embed=embed, view=discard_view)

        self.stop()

    async def stand_button_callback(self, interaction: Interaction) -> None:
        title = f'You Chose to Stand | Round {self.game_view.rounds_completed + 1}/{self.game_view.rounds}'
        description = f'**Your Hand:** {self.player.get_cards_string()}'

        embed, files = await send_embed_with_hand(
            self.player,
            title,
            description
        )

        if files:
            await interaction.response.edit_message(embed=embed, attachments=[files[0]], view=None)
        else:
            await interaction.response.edit_message(embed=embed, view=None)

        self.stop()
        await self.game_view.proceed_to_next_player()

    async def junk_button_callback(self, interaction: Interaction) -> None:
        title = f'You Chose to Junk | Round {self.game_view.rounds_completed + 1}/{self.game_view.rounds}'
        description = 'You have given up and are out of the game.'

        embed, files = await send_embed_with_hand(
            self.player,
            title,
            description
        )

        if files:
            await interaction.response.edit_message(embed=embed, attachments=[files[0]], view=None)
        else:
            await interaction.response.edit_message(embed=embed, view=None)

        self.game_view.players.remove(self.player)
        self.stop()
        if len(self.game_view.players) < 2:
            await self.game_view.end_game()
        else:
            await self.game_view.proceed_to_next_player()

    def stop(self) -> None:
        super().stop()

class DiscardCardView(ui.View):
    '''Provide buttons to choose which card to keep after drawing.'''

    def __init__(self, game_view: KesselGameView, player: Player) -> None:
        '''
        Initialize the discard card view.
        '''
        super().__init__(timeout=None)
        self.game_view = game_view
        self.player = player

        card_type = self.player.drawn_card_type

        existing_card = getattr(self.player, f'{card_type}_card')
        drawn_card = self.player.drawn_card

        if existing_card is not None:
            button = ui.Button(
                label=f'Keep Existing {card_type.capitalize()} ({Player.get_card_display(existing_card)})',
                style=discord.ButtonStyle.primary if card_type == 'positive' else discord.ButtonStyle.danger
            )
            button.callback = self.make_callback('keep_existing')
            self.add_item(button)

        button = ui.Button(
            label=f'Keep Drawn {card_type.capitalize()} ({Player.get_card_display(drawn_card)})',
            style=discord.ButtonStyle.primary if card_type == 'positive' else discord.ButtonStyle.danger
        )
        button.callback = self.make_callback('keep_drawn')
        self.add_item(button)

    def make_callback(self, choice: str):
        async def callback(interaction: Interaction) -> None:
            card_type = self.player.drawn_card_type
            drawn_card = self.player.drawn_card
            existing_card = getattr(self.player, f'{card_type}_card')

            if choice == 'keep_existing':
                if card_type == 'positive':
                    self.game_view.positive_deck.insert(0, drawn_card)
                else:
                    self.game_view.negative_deck.insert(0, drawn_card)
                action = f'You kept your existing card **{Player.get_card_display(existing_card)}** and discarded the drawn card **{Player.get_card_display(drawn_card)}**.'
            elif choice == 'keep_drawn':
                if card_type == 'positive':
                    if existing_card is not None:
                        self.game_view.positive_deck.insert(0, existing_card)
                    self.player.positive_card = drawn_card
                else:
                    if existing_card is not None:
                        self.game_view.negative_deck.insert(0, existing_card)
                    self.player.negative_card = drawn_card
                action = f'You replaced your {card_type} card **{Player.get_card_display(existing_card)}** with the drawn card **{Player.get_card_display(drawn_card)}**.'

            self.player.discard_drawn_card()

            title = 'Card Selection Completed'
            description = f'{action}\n\n**Your Hand:** {self.player.get_cards_string()}'
            embed, files = await send_embed_with_hand(
                self.player,
                title,
                description
            )

            if files:
                await interaction.response.edit_message(embed=embed, attachments=[files[0]], view=None)
            else:
                await interaction.response.edit_message(embed=embed, view=None)

            self.stop()
            await self.game_view.proceed_to_next_player()
        return callback

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('It\'s not your turn.', ephemeral=True)
            return False
        return True

    def stop(self) -> None:
        super().stop()

class ChooseImpostorValueView(ui.View):
    '''View for players to choose their Impostor card values.'''

    def __init__(self, game_view: KesselGameView, player: Player) -> None:
        '''
        Initialize the view.
        '''
        super().__init__(timeout=None)
        self.game_view = game_view
        self.player = player
        self.state = None
        self.dice_values = []
        self.message = None

        if player.positive_card == 'Impostor':
            self.state = '+'
            self.roll_dice()
        elif player.negative_card == 'Impostor':
            self.state = '-'
            self.roll_dice()
        else:
            self.state = 'done'

    async def send_initial_message(self) -> None:
        if self.state in ('+', '-'):
            card_type = 'positive' if self.state == '+' else 'negative'
            embed = Embed(
                title=f'Choose your {card_type} Impostor card value.',
                description=f'Two dice have been rolled for {self.player.user.mention} Impostor card. Choose your preferred value.',
                color=0x964B00
            )
            self.message = await self.game_view.channel.send(content=self.player.user.mention, embed=embed, view=self)

    def roll_dice(self) -> None:
        if self.state == '+':
            self.dice_values = [random.randint(1, 6), random.randint(1, 6)]
        elif self.state == '-':
            self.dice_values = [-random.randint(1, 6), -random.randint(1, 6)]

        self.clear_items()
        for value in self.dice_values:
            sign = '+' if value >= 0 else ''
            button = ui.Button(label=f'{sign}{value}', style=discord.ButtonStyle.primary)
            button.callback = self.make_callback(value)
            self.add_item(button)

    def make_callback(self, chosen_value: int):
        async def callback(interaction: Interaction) -> None:
            card_type = 'positive' if self.state == '+' else 'negative'
            await interaction.response.defer()

            self.player.impostor_values[self.state] = chosen_value
            await self.announce_choice(chosen_value, card_type)

            if self.state == '+' and self.player.negative_card == 'Impostor':
                self.state = '-'
                self.roll_dice()
                await self.send_initial_message()
            else:
                self.state = 'done'
                self.stop()
        return callback

    async def announce_choice(self, chosen_value: int, card_type: str, timed_out: bool=False) -> None:
        embed = Embed(
            title='Impostor Card Value Chosen',
            description=f'**{chosen_value}** has been selected as the {card_type} Impostor card by {self.player.user.mention}.',
            color=0x964B00
        )
        await self.message.edit(embed=embed, view=None)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message('This is not for you.', ephemeral=True)
            return False
        return True

    def stop(self) -> None:
        super().stop()

class ViewRulesButton(ui.Button):
    '''Button to view the game rules.'''

    def __init__(self) -> None:
        super().__init__(label='View Rules', style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: Interaction) -> None:
        rules_embed = get_kessel_rules_embed()
        await interaction.response.send_message(embed=rules_embed, ephemeral=True)