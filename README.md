# ANIVO

ANIVO is a starter project for monitoring anime-news sources, preparing Arabic posts, and delivering them to one Discord user's DMs.

## Current status

This first version includes:
- A Discord DM connectivity test.
- A modular source-processing structure.
- A persistent JSON file for duplicate tracking during local runs.
- A GitHub Actions workflow scheduled every 15 minutes.
- An Arabic post formatter using the ANIVO signature.

**Important:** This starter does not yet scrape X or Instagram. Their public pages do not provide a dependable, officially supported free interface for arbitrary account monitoring. Scraping may break or be blocked. We will add and test each source adapter separately before enabling automatic publishing. Do not assume the five accounts are being monitored yet.

It also does not generate AI translations or independently verify images yet. Those require selecting a workable free model/provider and reliable source retrieval. The current formatter is a safe template, not an AI translator.

## 1. Add GitHub Secrets

In your repository, open **Settings → Secrets and variables → Actions** and add:

- `DISCORD_BOT_TOKEN`: your Discord application bot token
- `DISCORD_USER_ID`: your Discord user ID

Never put the token in a committed file.

## 2. Test Discord DM delivery

1. Push this project to your GitHub repository.
2. In GitHub, open **Actions**.
3. Select **ANIVO - Test Discord DM**.
4. Click **Run workflow**.
5. Check your Discord DMs.

The bot must be in your private server, and you may need to open the bot's profile and start a DM once. Discord privacy settings must allow the DM.

## 3. Scheduled workflow

The scheduled workflow is configured for every 15 minutes. GitHub scheduled jobs can be delayed, especially during busy periods, and are not guaranteed to run at an exact minute. The workflow currently runs a harmless placeholder check; it does not publish scraped news.

## 4. Post format

The intended format is:
1. Poster/image
2. Arabic (Modern Standard Arabic) news text
3. `🌸 أنيفو || ANIVO 🌸`

Anime titles remain in English. For trailers, the original trailer link should be included with the post. This initial project only defines the formatting contract.

## 5. Sources planned

- X: @animetherapy
- X: @ahmedm94m
- X: @ascom0
- X: @animerakuar
- Instagram: @k_uroi

No source is active until its adapter is implemented and tested.

## Local setup (optional)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

Set `DISCORD_BOT_TOKEN` and `DISCORD_USER_ID` as environment variables, then run:

```bash
python -m anivo.test_dm
```
