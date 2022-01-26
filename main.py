import streamlit as st  #front-end
import pymongo          #Databaseconnection
from pymongo import MongoClient   #database-access
import pandas as pd      #dataframe operations
import pdfplumber        #extracting data, including table formatted data from PDF files
import PyPDF2            #reading pdf data
import string
import io
import re
import nltk
from rake_nltk import Rake  #keyword extraction
nltk.download('stopwords')
nltk.download('punkt')
import lxml

country = st.sidebar.text_input('Country')       #input country
uploaded_file = st.file_uploader('Upload your resume')   #upload resume
file_text = ''
phrases = [] #select the acquired key phrases

def keyphrases(file, min_word, max_word, num_phrases):
    text = file
    text = text.lower()
    text = ''.join(s for s in text if ord(s) > 31 and ord(s) < 126) #keeping required characters by ASCII values
    text = text
    text = re.sub(' +', ' ', text)   #Delete multiple spaces
    text = text.translate(str.maketrans('', '', string.punctuation))  #maketrans-specify the list of characters that need to be replaced in the whole string
    text = ''.join([i for i in text if not i.isdigit()])      #translate() method in Python for making many character replacements in strings.
    r = Rake(min_length=min_word, max_length=max_word)
    r.extract_keywords_from_text(text) #extract keywords
    phrases = r.get_ranked_phrases() #retrieve keywords

    if num_phrases < len(phrases):
        phrases = phrases[0:num_phrases]

    return phrases

if uploaded_file is not None:
    uploaded_file.seek(0)
    file = uploaded_file.read()
    pdf = PyPDF2.PdfFileReader(io.BytesIO(file))   #all the operations related to reading a file (io to convert it to python readable code)

    for page in range(pdf.getNumPages()):   #extract keyphrases in all pages
        file_text += (pdf.getPage(page).extractText())
        phrases.extend(keyphrases(file_text, 1, 4, 10))


if len(phrases) > 0:
    q_terms = st.multiselect('Select key phrases',options=phrases,default=phrases) #display keywords

#mongo-connection
client = pymongo.MongoClient("mongodb+srv://muskaan:mukkukuhu@cluster0.xwwad.mongodb.net/JobRecommender?retryWrites=true&w=majority")

def query(country,keywords):

    result = client['JobRecommender']['Companies'].aggregate([
        {
            '$search': {
                'text': {
                    'path': [
                        'industry'
                    ],
                    'query': [
                        ' %s' % (keywords)
                    ],
                    'fuzzy': {
                        'maxEdits': 2,
                        'prefixLength': 2
                    }
                }
            }
        }, {
            '$project': {
                'Name': '$name',
                'Industry': '$industry',
                'City': '$locality',
                'Country': '$country',
                'score': {
                    '$meta': 'searchScore'
                }
            }
        }, {
            '$match': {
                'Country': '%s' % (country)
            }
        }, {
            '$limit': 10
        }
    ])

    df = pd.DataFrame(result)

    return df

if st.button('Search'):
    df = query(country,phrases)
    st.write(df)