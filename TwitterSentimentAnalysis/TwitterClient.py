import json
from unidecode import unidecode
import time
import re
import csv
import threading
from threading import Thread
import signal
import os

import tweepy 
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import StreamListener

import boto3

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, Event

from KinesisClient import KinesisClient

positive_sentiment = 0
negative_sentiment = 0
neutral_sentiment = 0
mixed_sentiment = 0

raw_tweet_stream = ""
processed_tweet_stream = ""

g_hashtag=''

#+----+----+----+----+----+----+
#class: StreamProducerThread
#+----+----+----+----+----+----+
class StreamProducerThread (Thread):
    #///////////////////////////
    # method:__init__
    #///////////////////////////
    def __init__(self):
        threading.Thread.__init__(self)
        self.filter_keyword = ''
 
        # The shutdown_flag is a threading.Event object that
        # indicates whether the thread should be terminated.
        self.shutdown_flag = threading.Event()

    #///////////////////////////
    # method:get_ident
    #///////////////////////////
    def getIdent (self):
        return self.ident
 
    #///////////////////////////
    # method:run
    #///////////////////////////
    def run(self):
        print('*****************************Thread #%s started **************************' % self.ident)
        while not self.shutdown_flag.is_set():
            time.sleep(0.5)
            api.start_streaming (self.filter_keyword)
        
        # ... Clean shutdown code here ...
        api.stop_streaming ()
        print('&&&&&&&&&&&&&&&&&&&&&&&&&&&Thread #%s stopped &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&' % self.ident)

    def set_stream_filter_keyword (self, hashtag):  
        self.filter_keyword = hashtag

#+----+----+----+----+----+----+
#class: TwitterStreamListener
#+----+----+----+----+----+----+
class TwitterStreamListener (StreamListener):

    #///////////////////////////
    # method:__init__
    #///////////////////////////
    def __init__ (self):
        self.kinesis_client = KinesisClient (raw_tweet_stream)
        self.filter_keyword = ""
    
    #///////////////////////////
    # method:set_hashtag
    #///////////////////////////
    def set_hashtag (self, hashtag):
        self.filter_keyword = hashtag

    #///////////////////////////
    # method:on_data
    #///////////////////////////
    def on_data(self, data):
        try:    
            all_data = json.loads (data)
            raw_tweet = all_data["text"] 

            # created_at = all_data["created_at"]
            cleaned_tweet = TwitterUtils.clean_tweet(unidecode(raw_tweet))

            # payload = json.dumps({'hashtag':self.filter_keyword, 'tweet':cleaned_tweet})
            print (cleaned_tweet)

            # add to the kinesis stream
            self.kinesis_client.pushToStream(self.filter_keyword, cleaned_tweet)

        except tweepy.TweepError as e:
            print ("Error:" + str(e))
        except Exception as e:
            print ("Error:" + str(e))
        return True
    
    #///////////////////////////
    # method:on_error
    #///////////////////////////
    def on_error (self, status_code):
        print (status_code)
        if status_code == 420:
            return False

#+----+----+----+----+----+----+
#class: TwitterClient
#+----+----+----+----+----+----+
class TwitterUtils (object):
    #///////////////////////////
    # method:__init__
    #///////////////////////////
    def __init__ (self):
        consumer_publicKey =""  #the code in production has actual values
        consumer_secretKey ="" 
        access_token = ""
        access_tokenSecret = ""
        try:
            self.auth = OAuthHandler (consumer_publicKey, consumer_secretKey)
            self.auth.set_access_token (access_token, access_tokenSecret)
            self.api = tweepy.API (self.auth)

            self.listener = TwitterStreamListener()
            self.twitterStream = Stream (self.auth, self.listener)
        except:
            print ("Error: Authentication failed")

    #///////////////////////////
    # method:start_streaming
    #///////////////////////////
    def start_streaming (self, hashtag):
        self.listener.set_hashtag(hashtag)
        try:
            #self.twitterStream.filter(track = [hashtag], async=False)
            self.twitterStream.filter(track =[hashtag], is_async=True)
        except tweepy.TweepError as e:
            print ("Error:" + str(e))
    
    #///////////////////////////
    # method:start_streaming
    #///////////////////////////
    def stop_streaming (self):
        try:
            self.twitterStream.disconnect ()
        except tweepy.TweepError as e:
            print ("Error:" + str(e))
  
    #///////////////////////////
    # method:clean_tweet
    #///////////////////////////
    @staticmethod
    def clean_tweet (tweet):
        return ' '.join(re.sub (r'(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) |(\w+:\/\/\S+)', " ", tweet).split())

#+----+----+----+----+----+----+
# ServiceExit
#+----+----+----+----+----+----+
class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.
    """
    pass
 
def service_shutdown(signum, frame):
    print('Caught signal %d' % signum)
    raise ServiceExit

def update_sentiment_values (processed_tweet):
    global positive_sentiment
    global negative_sentiment
    global neutral_sentiment
    global mixed_sentiment
    global g_hastag

    result = json.loads(processed_tweet)
    if result['hashtag'] == g_hashtag:
        print ('^^^^^^^^^^^^^^^^ update_sentiment_figures ^^^^^^^^^^^^^^^^^\n')
        print (processed_tweet)

        sentiment = (result['sentiment'])
        print (sentiment)

        if sentiment == 'POSITIVE':
            positive_sentiment += 1
        elif sentiment == 'NEGATIVE':
            negative_sentiment += 1
        elif sentiment == 'MIXED':
            mixed_sentiment += 1
        else:
            neutral_sentiment += 1
        print ('^^^^^^^^^^^^^^^^ update_sentiment_figures ^^^^^^^^^^^^^^^^^\n')

def fetch_records(kinesis_client, shard_no):
    try:
        response = kinesis_client.getRecords (shard_no, 25)
        if response['Records'] > 0:
            for res in response['Records']:
                if g_hashtag =='':
                    break
                update_sentiment_values (res['Data'])
    except:
        print ("Error: fetch_records failed")


def process_results():
    kinesis_client = KinesisClient(processed_tweet_stream)
    while True:
        print ('############################## ASYNC SUCCESSFUL ################################')
        if g_hashtag =='':
            break
        kinesis_client.get_shardIterator (0)
        fetch_records(kinesis_client, 0)
        time.sleep(1.5)
        kinesis_client.get_shardIterator (1)
        fetch_records(kinesis_client, 1)
    return

#///////////////////////////
# main 
#//////////////////////////
api = TwitterUtils ()
#streamThread = StreamProducerThread ()

#+----+----+----+----+----+----+
# Dash app
#+----+----+----+----+----+----+
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
dash_app = dash.Dash(__name__, external_stylesheets=external_stylesheets )
dash_app.layout = html.Div(children=[ html.H1(children='Twitter Sentiment Analysis'),
                                      html.Div(children='''Enter keyword:'''), 
                                      html.Div(dcc.Input(id='input_box', value='', type='text')),
                                      html.Button('Analyze', id='analyze_button'),
                                      dcc.Graph(id='live-sentiment-graph', animate=False),
                                      dcc.Interval(id='graph-update',interval=1*1000),
                                      html.Div(html.Button('Stop', id='stop_button')),
                                      html.Div(id='output-dummy'),
                                      html.Div(id='analyze-dummy'),
                                    ])

@dash_app.callback(
    Output(component_id='output-dummy', component_property='children'),
    [Input(component_id='analyze_button', component_property='n_clicks')],
    [State('input_box', 'value')],
                  )
#///////////////////////////
# method:update_output_on_submit
#///////////////////////////
def update_output_on_analyze (n_clicks, input_keyword):
    if input_keyword == "":
        return

    global g_hashtag
    g_hashtag = input_keyword
    #streamThread.set_stream_filter_keyword (input_keyword)
    #streamThread.start()
    api.start_streaming (g_hashtag)
    time.sleep(3)
    print ('############################## ASYNC SUCCESSFUL ################################')
    process_results()
    return

@dash_app.callback(
    Output(component_id='live-sentiment-graph', component_property='figure'),
    events=[Event('graph-update', 'interval')])
#///////////////////////////
# method:update_sentiment_graph
#///////////////////////////
def update_sentiment_graph ():
     return {'data': [{'x': ['POSITIVE', 'NEUTRAL', 'MIXED', 'NEGATIVE'], 'y':[positive_sentiment, neutral_sentiment, mixed_sentiment, negative_sentiment ], 'type': 'bar', 'name': 'Sentiment'},],
                        'layout' : {'title': 'Keyword: "{}"'.format(g_hashtag)}}
    
@dash_app.callback(
    Output(component_id='analyze-dummy', component_property='children'),
    [Input(component_id='stop_button', component_property='n_clicks')])
#///////////////////////////
# method:update_on_stop
#///////////////////////////
def update_analyze_stop (n_clicks):
    global positive_sentiment
    global negative_sentiment
    global neutral_sentiment
    global mixed_sentiment
    global g_hashtag


    if n_clicks == None:
        return
    print ('STOP!!!')
    try:
        api.stop_streaming ()
        
        positive_sentiment = 0
        negative_sentiment = 0
        neutral_sentiment = 0
        mixed_sentiment = 0
        g_hashtag=''
    except:
        time.sleep(0.5)

#///////////////////////////
# main 
#//////////////////////////
if __name__ == "__main__":
    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)
    dash_app.run_server(debug=False,threaded=False,processes=1,host='0.0.0.0',port=80) 
