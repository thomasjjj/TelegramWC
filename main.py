from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import os
import datetime

print("\nSIMPLE TELEGRAM WORDCLOUD GENERATOR Version 0.1.1\n"
      "Please add the exported csv to the\n"
      "directory and name it 'result.csv\n\n")

filename = "result.csv"
if os.path.exists(filename):
    print(f"{filename} exists in the current working directory.\n")
else:
    print(f"{filename} does not exist in the current working directory.\n")

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
stopwords = ['the', 'a', 'an', 'nan', 'to']
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


