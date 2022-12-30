# TelegramWC
TelegramWC is a simple tool that can extract the most common words in a Telegram channel export and analyse them into a Word Cloud. This can be used to get an initial idea of the topics and content within the channel. It could also be used as part of a larger Telegram analysis tool.
## Features
- Stopword removal - this allows the most common words such as "the", "and", and "be" to be ommited from the output which increases the relevance of topic words and adjectives.
- Russian/Ukrainian language support - this includes a many stopwords for Russian and a few for Ukrainian but can be increased by editing the ```stopwords.txt``` file.
- Shows and saves the output - Allows you to have a saved image from the process.

[![](https://user-images.githubusercontent.com/118008765/209982287-1b195e17-e84d-43e7-805c-d2172bd6079c.png)](https://user-images.githubusercontent.com/118008765/209982287-1b195e17-e84d-43e7-805c-d2172bd6079c.png)

## Installing
To get started, make sure you have Python downloaded and git installed. 

Run the following to download this project and its dependencies:

```git clone https://github.com/thomasjjj/TelegramWC.git```

```pip install wordcloud matplotlib pandas```

## Creating a dataset
1. Export a Telegram channel of your choice as JSON or CSV (*Linux only*). I recommend deselecting all the media and only keeping the text to avoid downloading extreme or illegal materials.
2. Convert the output result.json to CSV for processing. I recommend using the [SaveJSON2CSV](http://https://gunamoi.com.au/soft/savejson2csv/index.html "SaveJSON2CSV") tool which works very well with Telegram export data.
3. Place the resulting CSV into the project directory. Make sure it is named "result.csv".

## Editing the stopwords list
Stopwords are words that you don't want to include in the word cloud. These are normally the "filler" words that are used to construct a sentence but may be useless in themselves. Consider the following phrase:

```The revolution is going to be at the palace```

We don't care about the following words:

```"The", "is", "going", "to", be", "at"```

What we care about is that this channel keeps mentioning words such as "Revolution".

The list of stopwords is present in the stopwords.txt file. It currently supports English, Russian, and some Ukrainian. More can be added depending on the language and use case. 

For example, if there is a channel that regularly links to YouTube but that is irrelevant, you can add "YouTube" to the stopwords file.

### Example
The following image is from a Wagner channel. Taking out all of the stopwords in the primary languages reveals that the most common phrases and terms used are actually usernames, indicating that this channel is possibly a primary hub for sharing and discussing content.

[![](https://user-images.githubusercontent.com/118008765/209985366-d01de100-80dd-45d8-aab8-2b0031dd712f.png)](https://user-images.githubusercontent.com/118008765/209985366-d01de100-80dd-45d8-aab8-2b0031dd712f.png)


## About fonts and languages
The current default font has been set to *Arial.ttf*. If this font does not work for the language you are looking at, you will likely see squares and rectangles in place of characters in the wordcloud.

This can be fixed by searching what fonts are compatible with the language you are looking at and you can download and call one of those fonts instead. 

Note: I have not tested every language and dialect so some issues are likely to remain.

