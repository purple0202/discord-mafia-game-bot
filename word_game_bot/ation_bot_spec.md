# Word Pattern Game — Discord Bot Spec

## Overview

A Discord bot that hosts a multiplayer word game where players take turns saying words matching a pattern (e.g. ends with `-ation`, starts with `un-`). The bot enforces turn order, validates words via dictionary API, tracks used words, and manages game state automatically. No command prefix needed during gameplay — the bot listens to all messages in a dedicated game channel.

Game setup is handled via an **interactive UI panel with buttons, dropdowns, and a modal text input** — no need to memorise command flags.

---

## Project Structure

```
word-pattern-bot/
├── bot.py                  # Entry point, loads cogs, sets up bot
├── cogs/
│   ├── game.py             # Core game logic, message listener, commands
│   └── admin.py            # Host-only controls (skip, stop, setorder)
├── utils/
│   ├── dictionary.py       # Word validation via Free Dictionary API
│   ├── timer.py            # Per-turn countdown timer logic (with live edit)
│   └── patterns.py         # Curated pattern list with metadata + recommender
├── models/
│   └── game_state.py       # GameState dataclass (players, words, scores, mode, pattern)
├── requirements.txt
└── .env                    # BOT_TOKEN only — never commit this
```

---

## Tech Stack

- **Language:** Python 3.11+
- **Library:** `discord.py` (v2.x) — uses Views, Buttons, Select Menus, and Modals
- **Word Validation:** Free Dictionary API — `https://api.dictionaryapi.dev/api/v2/entries/en/{word}` (free, no key required)
- **Environment:** `.env` file for local development

### requirements.txt
```
discord.py>=2.3.0
python-dotenv>=1.0.0
aiohttp>=3.9.0
```

---

## Running Locally (Current Phase)

Running the bot locally on your PC is the recommended approach for development and testing. The bot behaves identically locally vs in production — there is no behavioural difference.

### Setup steps
1. Clone the repo
2. Create a `.env` file with your bot token:
   ```
   BOT_TOKEN=your_discord_bot_token_here
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```
5. The bot is live in your Discord server as long as the script is running in your terminal.

### Why local first
- Instant feedback — edit code, restart, test immediately with no deploy lag
- Logs and errors print directly to your terminal
- Free, no usage limits
- When you're happy with the bot, migrating to Railway is a one-time 10-minute task

### Limitations of local running
- Bot goes offline when your PC is off or the script is stopped
- Fine for testing, not suitable for permanent hosting

---

## Deployment — Railway (Future Implementation)

> ⚠️ **Skip this section during local development. Implement after testing is complete.**

1. Push code to a GitHub repo
2. Sign up at railway.app → New Project → Deploy from GitHub repo
3. Add `BOT_TOKEN` as an environment variable in the Railway dashboard
4. Railway auto-deploys on every `git push` to main
5. Bot runs 24/7 without your PC

No code changes are needed between local and Railway — the `.env` file is replaced by Railway's environment variable system, which `python-dotenv` handles automatically.

---

## Channel Setup

- A server admin creates a single channel, e.g. `#word-game`
- **All game commands and word submissions happen in this channel**
- During an active game, every non-command message in the channel is treated as a word submission from the current player
- Messages from non-current players during a game are silently ignored (do not respond to avoid spam)
- The bot should pin a help/rules message in the channel on first setup (optional: `!setup` command)

---

## Commands

Only a small number of text commands are needed — most interaction happens via UI components.

| Command | Who | Description |
|---|---|---|
| `!start` | Anyone | Opens the interactive game setup panel |
| `!wordlist` | Anyone | DMs the user the full list of used words this game |
| `!scores` | Anyone | Posts current scores/standings in channel |
| `!help` | Anyone | Posts a summary of commands and rules |

Host controls (skip player, stop game, set turn order) are available as **buttons on the active game panel**, not text commands.

The **host** is the user who typed `!start`.

---

## Interactive Setup Panel (UI Components)

When the host types `!start`, the bot posts an **interactive setup panel** in the channel. Only the host can interact with it. The panel looks like:

```
🎮  Game Setup — hosted by Alex

[Last Standing]  [Points Mode]          ← Mode buttons (toggle)

[Strict]  [Generous]  [Voting]          ← Validation buttons (toggle)

Pattern type:  [Ends with ▼]            ← Select menu: "Ends with" / "Starts with"

Pattern:       [ends with: -ation ▼]    ← Select menu: curated list OR custom
               [✨ Recommend a pattern]  ← Button: picks a random well-suited pattern

Timer:         [⏱ Set timer (30s)]      ← Button: opens a modal text input

Rounds (Points mode only):
               [🔢 Set rounds (5)]      ← Button: opens a modal text input

[👥 Join Game]                          ← Visible to all players, not just host
[▶ Begin Game]  [❌ Cancel]             ← Host only
```

### Pattern selection detail

The pattern select menu shows the curated list (see Patterns section). At the bottom of the list is a **"Custom…"** option — selecting it opens a modal where the host types a custom pattern string (e.g. `tion`, `pre`, `ology`).

### Timer modal

Clicking **⏱ Set timer** opens a Discord modal popup with a single text input:
```
┌─────────────────────────────────┐
│  Set Turn Timer                 │
│                                 │
│  Enter seconds (10–120):        │
│  [________________________]     │
│                                 │
│  [Submit]                       │
└─────────────────────────────────┘
```
Validation: must be a number between 10 and 120. If invalid, bot replies ephemerally (only visible to host) with an error. Default is 30s if never changed.

### Join flow

The **👥 Join Game** button is visible to all players. Clicking it adds you to the lobby. The panel updates to show a live player list:
```
Players joined (3): @Clara, @Dan, @Ben
```

### Turn order

- Default: bot randomises join order when host clicks **▶ Begin Game**
- Manual: host can click a **🔀 Set Order** button (appears after 2+ players join) which opens a modal to type the desired order as mentions: `@Clara @Dan @Ben @Alex`

---

## Pattern System

### Pattern types

| Type | Example pattern | Example valid words |
|---|---|---|
| Ends with | `ation` | celebration, nation, elation |
| Starts with | `un` | unable, unfair, universe |

Pattern matching is **case-insensitive**. Leading/trailing hyphens in display (e.g. `-ation`, `un-`) are stripped before matching.

### Curated pattern list (in `patterns.py`)

A hardcoded list of patterns with metadata. Used to populate the pattern select menu and the recommender.

```python
PATTERNS = [
    # Ends with
    {"display": "ends with: -ation", "type": "endswith", "value": "ation", "word_count": 2000, "difficulty": "easy"},
    {"display": "ends with: -ness",  "type": "endswith", "value": "ness",  "word_count": 1500, "difficulty": "easy"},
    {"display": "ends with: -ment",  "type": "endswith", "value": "ment",  "word_count": 1200, "difficulty": "easy"},
    {"display": "ends with: -ful",   "type": "endswith", "value": "ful",   "word_count": 900,  "difficulty": "easy"},
    {"display": "ends with: -less",  "type": "endswith", "value": "less",  "word_count": 900,  "difficulty": "easy"},
    {"display": "ends with: -tion",  "type": "endswith", "value": "tion",  "word_count": 2500, "difficulty": "easy"},
    {"display": "ends with: -ing",   "type": "endswith", "value": "ing",   "word_count": 3000, "difficulty": "easy"},
    {"display": "ends with: -ology", "type": "endswith", "value": "ology", "word_count": 300,  "difficulty": "hard"},
    {"display": "ends with: -ism",   "type": "endswith", "value": "ism",   "word_count": 500,  "difficulty": "medium"},
    {"display": "ends with: -ist",   "type": "endswith", "value": "ist",   "word_count": 600,  "difficulty": "medium"},
    # Starts with
    {"display": "starts with: un-",  "type": "startswith", "value": "un",  "word_count": 800,  "difficulty": "medium"},
    {"display": "starts with: pre-", "type": "startswith", "value": "pre", "word_count": 700,  "difficulty": "medium"},
    {"display": "starts with: over-","type": "startswith", "value": "over","word_count": 500,  "difficulty": "medium"},
    {"display": "starts with: out-", "type": "startswith", "value": "out", "word_count": 400,  "difficulty": "medium"},
    {"display": "starts with: re-",  "type": "startswith", "value": "re",  "word_count": 1000, "difficulty": "easy"},
    {"display": "Custom…",           "type": "custom",     "value": None,  "word_count": None, "difficulty": None},
]
```

### Pattern recommender

Clicking **✨ Recommend a pattern** picks a random pattern from the curated list weighted toward `easy` and `medium` difficulty. It updates the panel's selected pattern and posts an ephemeral message to the host like:

```
✨ Suggested: ends with -ness (~1500 words) — should keep the game going for a while!
```

---

## Word Submission Flow

During an active game, the bot listens to all messages in the game channel. Only the **current player's** message is processed as a word submission.

### Validation Steps (in order)

1. **Matches the pattern?** — `word.lower().endswith(value)` or `word.lower().startswith(value)`
2. **Already used this game?** — check against `game_state.used_words` set
3. **Real word?** — GET request to Free Dictionary API

If all three pass → word accepted, added to used words, turn passes to next player.

### Strict Mode Behaviour

| Mode | On Failure |
|---|---|
| `strict` | Immediate penalty/elimination. No second chance. |
| `generous` | Bot warns the player with reason + time remaining. Player can try again before timer expires. Multiple failed attempts allowed. |
| `voting` | Bot posts ✅/❌ buttons. Non-submitter players vote for 10 seconds. Majority decides. Tie = rejected. |

---

## Timer — Live Visual Countdown

The timer uses **two layers combined**: a native Discord timestamp for a smooth per-second countdown, plus an emoji progress bar edited every 2 seconds for visual flair.

### How Discord native timestamps work

Discord supports a special timestamp format: `<t:UNIX:R>` where `UNIX` is a Unix epoch value (seconds since 1970). Discord's own client renders this as a live relative countdown that updates every second automatically — no bot editing required, no rate limits, no jank.

```python
import time

expiry_unix = int(time.time()) + 30  # 30 seconds from now
await channel.send(f"⏳ Clara's turn!\n<t:{expiry_unix}:R>")
```

Discord renders `<t:UNIX:R>` to every player as:
```
in 30 seconds → in 22 seconds → in 15 seconds → in 8 seconds → in 3 seconds
```

The bot **never edits this value** — Discord handles it entirely client-side.

### Combined timer message format

The bot posts one timer message per turn combining the native timestamp with a progress bar:

**Start of turn (30s):**
```
⏳ Clara's turn!
🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩
Expires in 30 seconds
```

**Mid turn (bot edits bar every 2s, timestamp ticks on its own):**
```
⏳ Clara's turn!
🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜
Expires in 18 seconds
```

**Warning zone — under 10s:**
```
⚠️ Clara — hurry!
🟨🟨⬜⬜⬜⬜⬜⬜⬜⬜
Expires in 8 seconds
```

**Final 3 seconds:**
```
🔴 GO, Clara!
🟥⬜⬜⬜⬜⬜⬜⬜⬜⬜
Expires in 3 seconds
```

### Timer expiry — cleaning up

When a turn ends (valid word submitted OR timer fires), the bot **immediately deletes the timer message**. The player never sees the timestamp tick past zero or show "X seconds ago."

- **Valid word submitted** → asyncio timer task is cancelled → timer message deleted → ✅ result posted
- **Timer expires** → asyncio task fires at exactly the right second → timer message deleted → ⏰ turn-over message posted

The deletion must happen before posting the result message so the channel stays clean.

### Timer implementation notes

- `expiry_unix = int(time.time()) + timer_seconds` calculated once at turn start
- Bot edits the **emoji bar only** every 2 seconds (not the timestamp — it updates itself)
- Bar is always 10 blocks wide. Filled blocks = `ceil(remaining / total * 10)`
- Green (`🟩`) above 10s remaining, yellow (`🟨`) 6–10s, red (`🟥`) under 6s
- Timer runs as an `asyncio.Task`, cancelled immediately on valid word submission
- Store the timer message object so it can be deleted at turn end

## Blocking Messages — Turn Enforcement via Discord Permissions

During an active game, only the current player should be able to send messages in `#word-game`. This is enforced using **Discord channel permission overwrites**, toggled by the bot per turn.

### One-time server setup (required)

A role called `Active Turn` must exist in the server before the bot runs. Create it manually or have the bot create it automatically on first `!start` if it doesn't exist. The role needs no special permissions of its own — it's used purely as a permission target.

The `#word-game` channel must have these baseline permission overwrites:

| Target | Permission | Value |
|---|---|---|
| `@everyone` | Send Messages | ❌ Denied |
| `Active Turn` role | Send Messages | ✅ Allowed |

This means by default, no one can send messages in the channel. Only whoever holds the `Active Turn` role can.

### Per-turn flow

```
Turn starts → bot assigns Active Turn role to current player
Player submits (or timer expires) → bot removes Active Turn role from that player
Next turn starts → bot assigns Active Turn role to next player
```

This is done via `discord.py`'s `member.add_roles()` and `member.remove_roles()`.

### Game start and end

- When a game starts → bot removes `Active Turn` from everyone (clean slate), then assigns to first player
- When a game ends → bot removes `Active Turn` from remaining player, restores `@everyone` Send Messages to ✅ in the channel so normal chat resumes

### What players see when it's not their turn

They simply cannot type in the channel — Discord shows the greyed-out input box with "You do not have permission to send messages in this channel." No bot message needed.

### Hosts and observers

- The **host** should also be blocked when it's not their turn (they're a player too)
- Consider giving server admins/moderators a bypass by giving their existing admin role an explicit `Send Messages: ✅` overwrite on the channel, so they can intervene if needed

### Voting mode exception

During a vote (when players react ✅/❌ to a challenged word), sending is still blocked. Voting is handled entirely via **button clicks**, not messages, so this works fine.

---

Once the game begins, the bot posts a **persistent game status panel** that is edited after each turn:

```
🎮  Word Pattern Game — ends with -ation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: Last Standing | Validation: Generous
Words used: 7

Turn order: ~~Ben~~ → Clara → Dan → **Alex** → ...
           (Ben eliminated)

[⏭ Skip Player]  [🛑 Stop Game]    ← Host only buttons
```

This panel is separate from the timer message and word submission messages.

---

## Game Mode Logic

### Last One Standing

- Elimination triggers:
  - Timer runs out
  - `strict` mode: any invalid submission
  - `voting` mode: majority votes ❌
- In `generous` mode: only timer expiry eliminates
- Game ends when one player remains → winner announced

### Points Mode

- Each valid word = 1 point
- Game runs for N full rounds (every player gets equal turns)
- Player with most points at the end wins
- Timer expiry = 0 points for that turn, no elimination
- Tie: both listed as winners; optionally add sudden-death round

---

## Example Game Flow (Last Standing, Generous, 30s, ends with -ation)

```
[Alex types]: !start
[Bot posts interactive setup panel]

[Alex configures: Last Standing, Generous, ends with -ation, 30s timer]
[Ben, Clara, Dan click 👥 Join Game]
[Alex clicks ▶ Begin Game]

[Bot]: 🔀 Turn order: Clara → Dan → Ben → Alex

[Bot assigns Active Turn role to Clara]
[Bot posts timer message]:
  ⏳ Clara's turn!
  🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩
  Expires in 30 seconds        ← ticks down every second automatically

[Clara types]: elation         ← only Clara can type; others see greyed-out input
[Bot deletes timer message]
[Bot posts]: ✅ elation — nice one, Clara! (1 word)

[Bot removes Active Turn from Clara, assigns to Dan]
[Bot posts new timer]:
  ⏳ Dan's turn!
  🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩
  Expires in 30 seconds

[Dan types]: nation123
[Bot posts]: ⚠️ That doesn't look like a real word, Dan! Try again.
[Timer bar continues updating every 2s — timestamp ticks on its own]

[Dan types]: nation
[Bot deletes timer message]
[Bot posts]: ✅ nation — good save, Dan! (2 words)

--- Ben's turn — timer fires ---
[Bot deletes timer message]    ← player never sees "X seconds ago"
[Bot removes Active Turn from Ben]
[Bot posts]: ⏰ Time's up, Ben! 💀 Eliminated.
             Remaining: Clara, Dan, Alex

--- Game ends ---
[Bot]: 🏆 Clara wins! Last one standing!
       📋 14 words used: elation, nation, ...
       Play again? Type !start!
```

---

## Error / Edge Cases

- `!start` called while a game is active → reject with message
- Begin clicked with fewer than 2 players → reject ephemerally
- Player leaves server mid-game → remove `Active Turn` role if they had it, silently remove from rotation
- Bot lacks `Manage Roles` permission → warn on `!start`, permission enforcement won't work without it
- `Active Turn` role doesn't exist → bot creates it automatically on first `!start`
- Dictionary API down or timeout → treat word as valid with a note, do not penalise
- Custom pattern with 0 known words → warn host during setup but allow it
- Bot restarted mid-game → game state lost, `Active Turn` role may be stuck on a player → bot should strip the role from all members on startup as a cleanup step, players must `!start` again

---

## Bot Personality / Message Style

- Emojis: ✅ valid, ⚠️ warning, ❌ invalid, ⏰ timeout, 🏆 winner, 💀 eliminated, 🎮 game start, 🔀 randomised, ✨ recommendation
- Short and punchy — players are on a timer
- After each valid word, always show whose turn is next
- DM players only for `!wordlist` — never flood the channel

---

## Out of Scope for v1

- Persistent leaderboards across sessions (no database)
- Multiple simultaneous games in different channels
- Web dashboard
- Claude Code / AI integration

These can be added in v2.
