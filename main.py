import tkinter as tk
import tkinter.messagebox as messagebox
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import os
import datetime

version = "1.0.1"

# Change the CWD to the directory containing main.py
os.chdir(os.path.dirname(__file__))

class GUI:
    '''
    This class is simply the GUI, if you are a beginner, don't worry too much about it.
    It was made by following a load of TKinter tutorials and messing around.

    Essentially it has three stages, a title frame, a user entry grid, then a button frame.
    '''


    def __init__(self):
        self.root = tk.Tk()
        self.root.title('TelegramWC (word cloud generator for Telegram exports)')

        title_font = ('Arial', 18)
        body_font = ('Arial', 10)
        warning_font = ('Arial', 10, 'bold')

    # Frame Creation ---------------------------------------------------------------------------------------------------
    # Create a frame to hold the TITLES
        self.TGWC_title_frame = tk.Frame(self.root)
        self.TGWC_title_frame.pack()

    # Create a separate frame to hold the USER ENTRY GRID
        self.TGWC_grid_frame = tk.Frame(self.root)
        self.TGWC_grid_frame.pack()
        # Grid frame settings
        user_entry_frame = tk.Frame(self.TGWC_grid_frame)
        user_entry_frame.columnconfigure(0, weight=1)
        user_entry_frame.columnconfigure(1, weight=1)
        user_entry_frame.columnconfigure(2, weight=1)
        user_entry_frame.columnconfigure(3, weight=1)

    # Create a frame to hold the BUTTONS
        self.TGWC_button_frame = tk.Frame(self.root)
        self.TGWC_button_frame.pack()

    # Title and Subtitle -----------------------------------------------------------------------------------------------
        # Add the title and subtitle
        self.label = tk.Label(self.TGWC_title_frame, text ='TelegramWC', font = title_font)
        self.label.pack(padx=10, pady=5)

        self.label_info = tk.Label(self.TGWC_title_frame,
                                   text='A tool to generate wordclouds from Telegram chat exports. '
                                   '\n Please ensure the source file is a csv file.'
                                   '\n Version {}.'.format(version), # add version number as defined at the top
                                   font=body_font)
        self.label_info.pack(padx=10)
        self.label_warning = tk.Label(self.TGWC_title_frame,
                                   text='WARNING: Make sure no " (double quotes) are added when copying path',
                                   font=warning_font, fg='red')
        self.label_warning.pack(padx=10, pady=10)

    # User entry boxes -------------------------------------------------------------------------------------------------
    # Source path
        # Entry Box - User enters the file path of the CSV they want to read
        self.source_enter_path = tk.Entry(self.TGWC_grid_frame)
        self.source_enter_path.grid(row=0, column=1)
        # Label
        self.source_enter_path_label = tk.Label(self.TGWC_grid_frame,
                                                text='Enter filepath for source:',
                                                font=body_font)
        self.source_enter_path_label.grid(row=0, column=0)

    # output directory
        # Entry Box - User enters the directory path to save the output to
        self.output_dir_enter_path = tk.Entry(self.TGWC_grid_frame)
        self.output_dir_enter_path.grid(row=1, column=1)
        # Label
        self.output_dir_enter_path_label = tk.Label(self.TGWC_grid_frame,
                                                    text='Enter directory for output:',
                                                    font=body_font)
        self.output_dir_enter_path_label.grid(row=1, column=0)

    # Buttons ----------------------------------------------------------------------------------------------------------
        # Run program button
        self.run_button = tk.Button(self.TGWC_button_frame, text='Run', font=title_font, command=self.run_main_app)
        self.run_button.grid(row=2, column=0, padx=5, pady=5)

        # Help button
        self.help_button = tk.Button(self.TGWC_button_frame, text='Help', font=('Arial', 18), command=self.show_help)
        self.help_button.grid(row=2, column=1, padx=5, pady=5)

    # Make sure this is at the end -------------------------------------------------------------------------------------
        self.root.mainloop()


    def show_help(self):

        '''
        This section add functionality to the Help button and allows it to display
        text from the help.txt file which NEEDS to be included in the project
        '''

        # Create a new Toplevel window
        help_window = tk.Toplevel(self.root)

        # Set the title of the window
        help_window.title('Help')

        # Read the contents of the help.txt file into a string
        with open('help.txt', 'r') as f:
            help_text = f.read()

        # Create a label with the help information
        help_label = tk.Label(help_window, text=help_text, anchor='w', justify='left')
        help_label.pack(padx=10)

        # Add a close button
        close_button = tk.Button(help_window, text='Close', command=help_window.destroy)
        close_button.pack()

    def get_source_path(self):

        self.filename = self.source_enter_path.get().strip()

        print(f'Source Filepath: {self.filename}')

    def get_output_path(self):

        self.output = str(self.output_dir_enter_path.get()).strip()

        print(f'Output Directory: {self.output}')

    def run_main_app(self):

        print("\nSIMPLE TELEGRAM WORDCLOUD GENERATOR Version 0.1.7\n"
              "Please add the exported csv to the\n"
              "directory and name it 'result.csv\n\n")

        '''
        This is the main section of the tool. It was previously a CLI tool, but now it is embedded
        in a GUI class for better accessibility.
        '''

        # Grab the filepath from the user entry and store it as an absolute path to avoid errors
        filepath = os.path.abspath(self.source_enter_path.get())

        # Sometimes copying a file path makes it start and end with " characters. If they exist, strip start and end
        if filepath[0] == '"' and filepath[-1] == '"':
            filepath = filepath[1:-1]
            print(filepath)

        # Grab the output directory from the user entry and store it as an absolute path to avoid errors
        output_dir = self.output_dir_enter_path.get()

        # Simple check to ensure all is working well and to assist debugging
        print('User entered filepath: ' + filepath + '\nand output dir: ' + output_dir)

        # This font generally works well with Latin and Cyrillic characters. It can be adjusted to suit the language you
        # require. Just make sure the font is downloaded to your computer and call the font name.
        font = 'arial.ttf'

        # Define the name of the Stopwords file
        stopwords_filename = os.path.join(os.getcwd(), "stopwords.txt")


        def create_stoplist(stopwords_filename):  # Declares which words to exclude from wordcloud
            with open(stopwords_filename, 'r', encoding='utf-8') as f:
                text = f.read()

            words = text.split()
            stoplist = set()
            for word in words:
                stoplist.add(word)

            print('Stoplist accessed')

            return set(stoplist)

        stopwords = create_stoplist(stopwords_filename)  # create the stoplist by calling the above function


        # Check to ensure the correct file is in the path
        if os.path.exists(filepath):
            print(f"{filepath} exists.\n")
        else:
            print(f"{filepath} does not exist.\n")

        # Create a Pandas dataframe to hold the data
        print("Reading the CSV at " + filepath + "...")
        df = pd.read_csv(filepath, low_memory=False,
                         encoding='utf-8')  # low_memory clause to remove DType error (remove & we all die)
        print("CSV read; Dataframe made...")

        # Replace 'NaN' and 'nan' values with the actual NaN value

        df = df.replace('NaN', float('nan'))
        df = df.replace('nan', float('nan'))

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

        df = df.dropna()

        # Generate a wordcloud from the combined text, specifying the width and height of the image
        print("Generating Wordcloud...")

        wordcloud = WordCloud(font_path=font, width=800, height=800, stopwords=stopwords).generate(
            ' '.join(combined_text))

        # Display the wordcloud
        print("Displaying Wordcloud...")
        plt.figure(figsize=(10, 10))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")

        # Check if the output directory exists
        if not os.path.exists(output_dir):
            # Create the output directory if it does not exist
            os.makedirs(output_dir)

        # Save the figure as a JPEG file with the current date and time appended to the filename
        output_filename = os.path.join(output_dir, 'wordcloud_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.jpg')
        plt.savefig(output_filename)

        plt.show()


GUI()