# TelegramWC
TelegramWC is a simple tool that can extract the most common words in a Telegram channel export and analyse them into a Word Cloud. This can be used to get an initial idea of the topics and content within the channel. It could also be used as part of a larger Telegram analysis tool.
## Features
- Stopword removal - this allows the most common words such as "the", "and", and "be" to be ommited from the output which increases the relevance of topic words and adjectives.
- Russian/Ukrainian language support - this includes a few stopwords but can be increased by editing the code. 
- Shows and saves the output - Allows you to have a saved image from the process.

## Installing
To get started, make sure you have Python downloaded and git installed. 

Run the following to download this project and its dependencies:

```git clone https://github.com/thomasjjj/TelegramWC.git```

```pip install wordcloud matplotlib pandas```

## Creating a dataset
1. Export a Telegram channel of your choice as JSON or CSV (*Linux only*). I recommend deselecting all the media and only keeping the text to avoid downloading extreme or illegal materials.
2. Convert the output result.json to CSV for processing. I recommend using the [SaveJSON2CSV](http://https://gunamoi.com.au/soft/savejson2csv/index.html "SaveJSON2CSV") tool which works very well with Telegram export data.
3. Place the resulting CSV into the project directory. Make sure it is named "result.csv".



