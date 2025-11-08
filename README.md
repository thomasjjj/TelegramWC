# TelegramWordCloud
TelegramWordCloud is a simple tool that can extract the most common words in a Telegram channel and analyse them into a word cloud. Version 1.1 keeps the lightweight GUI while adding the option to log in with Telethon and pull channel history directly, so you can generate clouds either from existing CSV exports or straight from Telegram.

## Update version 1.1 - Telethon and GUI quality-of-life
- Added a data-source selector so you can switch between CSV exports and direct channel downloads.
- Integrated Telethon authentication (API ID + API hash) with in-GUI prompts for login codes and optional 2FA passwords.
- Added file/directory browse buttons, processing toggles, better status reporting, and clearer guidance inside the Help dialog.
[![](https://user-images.githubusercontent.com/118008765/210123628-3505e8ee-8c67-43f4-b6f2-203b8c1a1e3a.png)](http:/https://user-images.githubusercontent.com/118008765/210123628-3505e8ee-8c67-43f4-b6f2-203b8c1a1e3a.png/)

## Features
- Stopword removal - filter filler words such as "the", "and", and "be" to highlight relevant terms.
- Russian/Ukrainian language support - the bundled stopwords file includes many entries for both languages and can be expanded.
- Two ingestion options - load a CSV/Telegram Desktop JSON export or download any channel you can access via Telethon.
- Processing flexibility - choose whether to save the generated image, download-only mode, and (for Telethon) fetch all posts, a date range, or the last N posts.
- Authentication status indicator - the Telethon panel shows whether your session is already authenticated and offers a one-click status check.
- Telethon progress tracking - while downloading a channel, the progress bar shows processed messages vs. the estimated total (from the latest post ID).
- Optional credential storage - save your API ID/hash/phone to a local `.env` file so the GUI auto-fills them next time (API hash entry is masked).
- Preview convenience - right-click the live wordcloud preview to copy it to the clipboard or save it via "Save image as...".
- Shows and saves the output - the word cloud is displayed and (optionally) written to disk automatically.

[![](https://user-images.githubusercontent.com/118008765/209982287-1b195e17-e84d-43e7-805c-d2172bd6079c.png)](https://user-images.githubusercontent.com/118008765/209982287-1b195e17-e84d-43e7-805c-d2172bd6079c.png)

## Installing
To get started, make sure you have Python downloaded and git installed.

```bash
git clone https://github.com/thomasjjj/TelegramWordCloud.git
pip install wordcloud matplotlib pandas telethon
```

Telethon is only required if you plan to log in through the GUI; CSV processing works without it.

## Using the GUI
1. Launch `python main.py`.
2. If a `.env` file containing `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and `TELEGRAM_PHONE` exists in the project folder, the GUI fills those fields automatically (they remain editable so you can switch accounts).
3. Pick a **Data source**:
   - **Load CSV export** - choose whether you are loading a CSV or a Telegram Desktop `result.json`. JSON mode automatically flattens text arrays (links/hashtags/etc.) into a single string before generating the cloud.
   - **Download via Telethon** - enter your API ID/API hash (from [my.telegram.org](https://my.telegram.org)), the phone number tied to that API, and the channel username/link. Choose whether to fetch all posts, a date range, or only the last N posts. Click **Send login code** to have Telegram deliver an SMS, then provide the code in the popup (or when prompted as you press **Run**). Use **Check authentication** to see whether a session is already cached (the status line turns green when you're signed in). Enter your 2FA password if requested; a reusable session file is stored locally.
4. In **Processing options**, decide whether to:
   - Save the rendered word cloud image (checked by default), or just preview it on screen.
   - Download only the channel messages (Telethon mode) to produce a CSV and skip word cloud generation.
   - For Telethon runs, choose the download scope (all posts, date range, or last N posts).
5. Choose the output directory, press **Run**, and TelegramWordCloud will handle the selected workflow automatically.

## Credential storage (.env)
1. After entering your API ID/API hash/phone, click **Save credentials to .env** to store them locally (beside `main.py`).
2. TelegramWordCloud only reads from `.env` on startup; you can still edit or overwrite the values before authenticating. After saving you can click **Check authentication** to verify whether the stored session is still valid.
3. The `.env` file is meant for local use-avoid committing it to source control if you share the project.

## Debugging Telethon logins
If Telegram keeps rejecting code requests, run the helper script to inspect the flow outside the GUI:

```bash
python debug_telethon_login.py --channel bbcrussian
```

It uses the credentials in `.env`, prompts for the SMS/Telegram-app code (and 2FA password if enabled), and then fetches the latest message from the chosen channel. Once this script succeeds, the GUI can reuse the same session.

## Download-only exports
When **Download channel messages only** is enabled, Telethon mode saves the retrieved messages to `telegram_messages_<channel>_<timestamp>.csv` in the selected output directory. Each CSV row includes the message ID, date, sender ID, and text so it can be re-used in TelegramWordCloud or processed elsewhere.

## Creating a dataset
1. Export a Telegram channel of your choice as JSON or CSV (*Linux only*). Deselect media unless you specifically need it.
2. Convert the output JSON to CSV for processing. The [SaveJSON2CSV](https://gunamoi.com.au/soft/savejson2csv/index.html "SaveJSON2CSV") tool works well with Telegram export data.
3. CSV/JSON mode can read the file from any directory; just browse to it in the GUI.

## Editing the stopwords list
Stopwords are words that you don't want to include in the word cloud. These are normally the "filler" words that are used to construct a sentence but may be useless in themselves. Consider the following phrase:

```text
The revolution is going to be at the palace
```

We don't care about the following words:

```text
"The", "is", "going", "to", "be", "at"
```

What we care about is that this channel keeps mentioning words such as "Revolution".

The list of stopwords is present in the stopwords.txt file. It currently supports English, Russian, and some Ukrainian. More can be added depending on the language and use case.

For example, if there is a channel that regularly links to YouTube but that is irrelevant, you can add "YouTube" to the stopwords file.

### Example
The following image is from a Wagner channel. Taking out all of the stopwords in the primary languages reveals that the most common phrases and terms used are actually usernames, indicating that this channel is possibly a primary hub for sharing and discussing content.

[![](https://user-images.githubusercontent.com/118008765/209985366-d01de100-80dd-45d8-aab8-2b0031dd712f.png)](https://user-images.githubusercontent.com/118008765/209985366-d01de100-80dd-45d8-aab8-2b0031dd712f.png)

## About fonts and languages
The current default font has been set to *Arial.ttf*. If this font does not work for the language you are looking at, you will likely see squares and rectangles in place of characters in the word cloud.

This can be fixed by searching what fonts are compatible with the language you are looking at and you can download and call one of those fonts instead.

Note: I have not tested every language and dialect so some issues are likely to remain.

## Logging
Every run writes progress updates and errors to `telegramwordcloud.log` in the project directory so you can review what happened after the fact.
