from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import os
import datetime

filename = "result.csv"

print("\nSIMPLE TELEGRAM WORDCLOUD GENERATOR Version 0.1.6\n"
      "Please add the exported csv to the\n"
      "directory and name it 'result.csv\n\n")

# Check to ensure the correct file is in the path
if os.path.exists(filename):
    print(f"{filename} exists in the current working directory.\n")
else:
    print(f"{filename} does not exist in the current working directory.\n")


# Create a Pandas dataframe to hold the data
print("Reading the CSV...")
df = pd.read_csv('result.csv', low_memory=False,
                 encoding='utf-8')  # low_memory clause to remove DType error (remove & we all die)
print("CSV read; Dataframe made...")


# Replace 'NaN' and 'nan' values with the actual NaN value
print("Replacing NaN values#...")
df = df.replace('NaN', float('nan'))
df = df.replace('nan', float('nan'))
print("Replaced NaN values (some may remain)...")


# Create an empty list to store the combined text from all columns
combined_text = []


# Iterate over the columns of the dataframe
print("Iterating over columns in dataset...")
for col in ['text', 'text_1', 'text_2', 'text_3']:
    # Convert the values in the column to strings
    df[col] = df[col].astype(str)
    # Add the text from the column to the combined_text list
    combined_text += df[col].tolist()


# Remove rows with NaN values from the dataframe
print("Replacing NaN values#...")
df = df.dropna()
print("Replaced NaN values (some may remain)...")


# Generate a wordcloud from the combined text, specifying the width and height of the image
print("Generating Wordcloud...")

stopwords = ['nan', 'NaN', 'a', 'about', 'above', 'across', 'after', 'afterwards', 'again', 'against', 'all',
                 'almost', 'alone', 'along', 'already', 'also', 'although', 'always', 'am', 'among', 'amongst',
                 'amoungst', 'amount', 'an', 'and', 'another', 'any', 'anyhow', 'anyone', 'anything', 'anyway',
                 'anywhere', 'are', 'around', 'as', 'at', 'back', 'be', 'became', 'because', 'become', 'becomes',
                 'becoming', 'been', 'before', 'beforehand', 'behind', 'being', 'below', 'beside', 'besides', 'between',
                 'beyond', 'bill', 'both', 'bottom', 'but', 'by', 'call', 'can', 'cannot', 'cant', 'co', 'con', 'could',
                 'couldnt', 'cry', 'de', 'describe', 'detail', 'do', 'done', 'down', 'due', 'during', 'each', 'eg',
                 'eight', 'either', 'eleven', 'else', 'elsewhere', 'empty', 'enough', 'etc', 'even', 'ever', 'every',
                 'everyone', 'everything', 'everywhere', 'except', 'few', 'fifteen', 'fify', 'fill', 'find', 'fire',
                 'first', 'five', 'for', 'former', 'formerly', 'forty', 'found', 'four', 'from', 'front', 'full',
                 'further', 'get', 'give', 'go', 'had', 'has', 'hasnt', 'have', 'he', 'hence', 'her', 'here',
                 'hereafter', 'hereby', 'herein', 'hereupon', 'hers', 'herself', 'him', 'himself', 'his', 'how',
                 'however', 'hundred', 'i', 'ie', 'if', 'in', 'inc', 'indeed', 'interest', 'into', 'is', 'it', 'its',
                 'itself', 'keep', 'last', 'latter', 'latterly', 'least', 'less', 'ltd', 'made', 'many', 'may', 'me',
                 'meanwhile', 'might', 'mill', 'mine', 'more', 'moreover', 'most', 'mostly', 'move', 'much', 'must',
                 'my', 'myself', 'name', 'namely', 'neither', 'never', 'nevertheless', 'next', 'nine', 'no', 'nobody',
                 'none', 'noone', 'nor', 'not', 'nothing', 'now', 'nowhere', 'of', 'off', 'often', 'on', 'once', 'one',
                 'only', 'onto', 'or', 'other', 'others', 'otherwise', 'our', 'ours', 'ourselves', 'out', 'over', 'own',
                 'part', 'per', 'perhaps', 'please', 'put', 'rather', 're', 'same', 'see', 'seem', 'seemed', 'seeming',
                 'seems', 'serious', 'several', 'she', 'should', 'show', 'side', 'since', 'sincere', 'six', 'sixty',
                 'so', 'some', 'somehow', 'someone', 'something', 'sometime', 'sometimes', 'somewhere', 'still', 'such',
                 'system', 'take', 'ten', 'than', 'that', 'the', 'their', 'them', 'themselves', 'then', 'thence',
                 'there', 'thereafter', 'thereby', 'therefore', 'therein', 'thereupon', 'these', 'they', 'thick',
                 'thin', 'third', 'this', 'those', 'though', 'three', 'through', 'throughout', 'thru', 'thus', 'to',
                 'together', 'too', 'top', 'toward', 'towards', 'twelve', 'twenty', 'two', 'un', 'under', 'until', 'up',
                 'upon', 'us', 'very', 'via', 'was', 'we', 'well', 'were', 'what', 'whatever', 'when', 'whence',
                 'whenever', 'where', 'whereafter', 'whereas', 'whereby', 'wherein', 'whereupon', 'wherever', 'whether',
                 'which', 'while', 'whither', 'who', 'whoever', 'whole', 'whom', 'whose', 'why', 'will', 'with',
                 'within', 'without', 'would', 'yet', 'you', 'your', 'yours', 'yourself', 'yourselves', 'https', 'www']

wordcloud = WordCloud(width=800, height=800, stopwords=stopwords).generate(' '.join(combined_text))


# Display the wordcloud
print("Displaying Wordcloud...")
plt.figure(figsize=(10, 10))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")


# Save the figure as a JPEG file with the current date and time appended to the filename
filename = 'wordcloud_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.jpg'
plt.savefig(filename)


plt.show()


