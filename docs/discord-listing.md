# Discord Listing

The text on Sabacc Droid's pages in the Discord Developer Portal, kept here so it can be restored or matched by the other bots ([Aurebesh Droid](https://github.com/TheAbubakrAbu/Aurebesh-Droid/blob/main/docs/discord-listing.md) and [501st War Room](https://github.com/TheAbubakrAbu/501st-War-Room/blob/main/docs/discord-listing.md)).

## General Information

**Description** (maximum 400 characters, shown in the bot's About Me):

```
🎴 Play Sabacc, the galaxy's most legendary card game, right in your server!
🃏 Corellian Spike · Coruscant Shift · Kessel · Traditional
👥 Up to 8 players, or go solo against Lando
✨ Start with /sabacc · Learn the rules with /help

Created by Abubakr Elmallah
📧 contact@abubakrelmallah.com
🌐 https://abubakrelmallah.com/star-wars/
```

**Tags** (maximum 5, also the App Directory tags): Sabacc, Multiplayer, Star Wars, Card Games, Strategy

**Terms of Service URL** and **Privacy Policy URL:** https://abubakrelmallah.com/star-wars/

## Installation

- **Installation Contexts:** User Install and Guild Install
- **Install Link:** Discord Provided Link
- **User Install scopes:** applications.commands
- **Guild Install scopes:** applications.commands, bot
- **Guild Install permissions:** Attach Files, Embed Links, Send Messages, Send Messages in Threads, Use Slash Commands, View Channels. Every turn, log line and result is posted to the channel with an embed, and turns and results carry a picture, so a server that blocks embeds or files for everyone still lets the bot's own role post them.

The slash commands are registered without `allowed_installs`, so Discord only offers them in servers with the bot and in the bot's own DM (they don't appear in group DMs), and games post to the channel as the bot. User Install therefore adds nothing a person can use outside those places.

## OAuth2

Nothing set: no redirects, and Public Client is off.

## Bot

- **Icon:** the Sabacc Droid logo
- **Banner:** [`banner.png`](../banner.png) (1360 x 480, Discord's 17:6 at twice the size): two fanned hands of the bot's own cards on top of each other, Corellian Spike behind and Kessel in front, beside the four variants. It replaces the Sabacc table scene, which is kept as [`src/sabacc_droid/images/banner-old.jpg`](../src/sabacc_droid/images/banner-old.jpg).
- **Username:** Sabacc Droid
- **Status:** "Playing 🃏 Sabacc", set in code in `sabacc_droid.py`
- **Public Bot:** on
- **Requires OAuth2 Code Grant:** off
- **Privileged Gateway Intents:** all off (Presence, Server Members, Message Content)
- **Bot Permissions:** left empty; it is only a calculator and saves nothing

## Emojis and Rich Presence

- **Emojis:** none uploaded. Every icon is a Unicode emoji from `theme.py`.
- **Rich Presence:** not used. Rich Presence art is for games that report what a player is doing; a bot's status is set in code.

## Discovery

**Discovery Status:** on (the bot is listed in the App Directory)

**Summary** (maximum 200 characters):

```
Play the galaxy's legendary Star Wars card game on Discord! Challenge up to 8 players or face Lando Calrissian in Corellian Spike, Coruscant Shift, Kessel, and Traditional Sabacc.
```

**Languages:** English, US

**Support Server:** The Skywalker Order

**Media** (1920 x 1080, made from screenshots of the bot in a DM, in this order):

1. [`media/1-variants.png`](media/1-variants.png): Four ways to play Sabacc (`/sabacc`)
2. [`media/2-lobby.png`](media/2-lobby.png): Gather your crew, or face Lando (a Corellian Spike lobby)
3. [`media/3-hand.png`](media/3-hand.png): Your hand stays private (Play Turn)
4. [`media/4-kessel.png`](media/4-kessel.png): Sand, Blood and Impostors (a Kessel hand)
5. [`media/5-reveal.png`](media/5-reveal.png): The big reveal (the results picture)

Each is linked in the portal as `https://raw.githubusercontent.com/TheAbubakrAbu/Sabacc-Droid/main/docs/media/<file>`, so renaming or moving one breaks its slot in the listing.

**Links:**

- Website: https://abubakrelmallah.com/star-wars/
- GitHub: https://github.com/TheAbubakrAbu/Sabacc-Droid
- Try Aurebesh Droid: https://discord.ly/aurebesh-droid

**Expanded Description** (the portal's Markdown has no `#` headings, so the title is bold):

```
**Sabacc Droid | The Ultimate Star Wars Card Game on Discord!**

Bring the galaxy's most legendary card game to your Discord server! Play Sabacc with friends or challenge Lando Calrissian in an immersive, interactive experience inspired by Star Wars.

🎮 **Four Sabacc Variants**

- **Corellian Spike:** As seen in Solo: A Star Wars Story and Galaxy's Edge. Draw, strategize, and aim for a hand totaling zero.
- **Coruscant Shift:** Inspired by Galactic Starcruiser. Roll the dice to determine the target number and suit.
- **Kessel Sabacc:** As seen in Star Wars Outlaws. Master Sand and Blood cards, Impostors, and Sylops.
- **Traditional Sabacc:** As seen in Star Wars Rebels. Aim for positive or negative 23 and call Alderaan to end the game!

🃏 **Features**

• Multiplayer games with up to 8 players

• Solo gameplay against Lando Calrissian

• Interactive buttons, custom card artwork, and private hands

• Automatic dealing, turn management, and scoring

• Customizable rounds, starting hands, and game settings

• Built-in rules for all four variants

• Random game mode for unexpected challenges

🚀 **Getting Started**

Use `/sabacc` to choose your game, `/random` for a surprise, or `/help` to learn the rules. You can also launch each variant directly using its dedicated slash command.

Whether you're a seasoned Sabacc player or just discovering the game, gather your friends, test your luck, and prove you've got what it takes to win!

May the best player win!

Created by Abubakr Elmallah

Website: https://abubakrelmallah.com/star-wars/

Support: contact@abubakrelmallah.com
```
