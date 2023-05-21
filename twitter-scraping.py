import streamlit as st
import base64
from PIL import Image
import snscrape.modules.twitter as sntwitter
import numpy as np
import datetime
import json
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from wordcloud import STOPWORDS
import pandas as pd
from pymongo import MongoClient
from streamlit_option_menu import option_menu
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
#Connecting MongoDB-Database and creating a collection
connection = MongoClient("mongodb+srv://hem:hemadri123@cluster0.1aiew.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
# client = MongoClient(connection, tlsCAFile=certifi.where())

db = connection["snscrape"]
coll = db["twitter-data"]
img = Image.open("media/twitter.png")
st.set_page_config(page_title="Twitter scraping",page_icon = img,layout = "wide")

#This is used to make the streamlit web-page customized
def get_img_as_base64(file):
    with open(file,"rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()
img = get_img_as_base64("images/bg.jpg")
page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] > .main {{
background-image :url("data:image/png;base64,{img}");
background-size : cover;
}}
[data-testid="stHeader"]{{
background:rgba(0,0,0,0);
}}
</style>

"""
st.markdown(page_bg_img, unsafe_allow_html=True)
st.header("Let Us scrape some tweets!!")

#Enables user to scrape the data from twitter using "snscrape"
def ScrapingTheBird(word,From,To,maxTweets):
  tweets_list = []
  for i,tweet in enumerate(sntwitter.TwitterSearchScraper(f'{word} since:{From} until:{To}').get_items()):
      if i>maxTweets-1:
          break
      tweets_list.append([tweet.date,tweet.id,tweet.user.username,tweet.url,tweet.rawContent,tweet.replyCount,tweet.likeCount,tweet.retweetCount,tweet.lang,tweet.source ])
  tweets_df = pd.DataFrame(tweets_list, columns=['Datetime', 'Tweet Id','User Name','URL','Content','ReplyCount','LikeCount','Retweet-Count','Language','Source'])
  tweets_df.to_json("user-tweets.json")
  tweets_df.to_csv("user-tweets.csv")
  return tweets_df

#Function to visualize the most frequent word used by peoples along with the search word in wordcloud form
def word_cloud():
    stopwords = set(STOPWORDS)
    data = pd.read_csv("user-tweets.csv")
    mask = np.array(Image.open("media/tweetie.png"))
    text = " ".join(review for review in data.Content)
    wordcloud = WordCloud(background_color = "white",max_words=500,mask=mask).generate(text)
    plt.figure()
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()
    plt.savefig("media/word-cloud.png",format="png")
    return plt.show()

#Function to upload the search document in Mongodb database
def Bird_In_Database(n_word):
    with open("user-tweets.json","r") as file:
        data = json.load(file)
    dt = datetime.datetime.today()
    db.twitter_data.insert_many([{
            "Scraped Word":n_word,
            "Scraped Date":dt,
            "Scraped Data":data
            }])

#creating a navigation menu
choice = option_menu(
    menu_title = None,
    options = ["Search","Visualize","Data-Base"],
    icons =["search","camera2","boxes"],
    menu_icon="cast",
    default_index=0,
    orientation="vertical",
    styles={
        "container": { "background-color": "grey","size":"cover"},
        "icon": {"color": "red", "font-size": "30px"},
        "nav-link": {"font-size": "20px", "text-align": "center", "margin": "2px", "--hover-color": "#C8A2C8"},
        "nav-link-selected": {"background-color": "black"},}
    )

# User is allowed to search to scrape data, using search utterance, From date, to Date and Number of tweets
if choice=="Search":
    col1,col2,col3 = st.columns(3)
    word = st.text_input("Enter Word to Search")
    if word:
        From = st.date_input("From Date")
        if From:
            To = st.date_input("To Date")
            if To:
                maxTweets = st.number_input("Number of Tweets",1,100)
                if maxTweets:
                    check = st.button("Search for tweets")
                    if check:
                        st.dataframe(ScrapingTheBird(word,From,To,maxTweets).iloc[0:10])
                        col1, col2 = st.columns(2)

#Enables user to visualize the data in wordcloud form with similar tag's
if choice=="Visualize":
    col1,col2,col3= st.columns(3)
    col1 = (st.button("Tap to form wordcloud"))
    if (col1):
        word_cloud()
        col3.image(Image.open("media/word-cloud.png"))

#User can upload the search data into mongodb database which is linked to hemadri's Mongodb
if choice=="Data-Base":
    col1,col2,col3 = st.columns(3)
    list = ["Store in DB","View Data"]
    CHOICE = st.selectbox("SELECT",list)
    if CHOICE=="Store in DB":
        if "n_word" not in st.session_state:
            st.session_state["n_word"] = ""
        n_word = st.text_input("Enter the KEY-WORD",st.session_state["n_word"])
        upload = st.button("upload")
        if upload:
            Bird_In_Database(n_word)
            st.success("DATA-BASE has been UPDATED!")
            col1,col2,col3=st.columns(3)
    if CHOICE=="View Data":
        if st.button("view :goggles:"):
            df = pd.read_csv("user-tweets.csv")
            st.dataframe(df)