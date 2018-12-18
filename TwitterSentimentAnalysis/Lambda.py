from __future__ import print_function
import json
import base64
import boto3
import re
import os


def lambda_handler(event, context):
    
     
     processed_tweet_stream = ''
     kinesis_client = boto3.client('kinesis', region_name='us-east-1')
     
  
     for record in event["Records"]:
        payload = str(base64.b64decode(record["kinesis"]["data"]))
        hashtag = str(record["kinesis"]["partitionKey"])
        
        payload = payload[:-1]
        payload = payload[2:]
        print (payload)
    
        sentiment = analyze_sentiment(payload)
        print (sentiment)
        
        payload_to_s3 = hashtag + ':' + payload + ':' + sentiment + ','
        payload_to_kinesis = {'hashtag':hashtag,'tweet':payload,'sentiment':sentiment}
        
        deliveryStreamName = ''
        firehoseClient = boto3.client('firehose', region_name='us-east-1')
        firehoseClient.put_record (DeliveryStreamName=deliveryStreamName, Record={'Data':payload_to_s3})
        
        kinesis_client.put_record (StreamName=processed_tweet_stream, Data=json.dumps(payload_to_kinesis), PartitionKey=hashtag)
        
  
def analyze_sentiment(tweet):
    return 'NEUTRAL'
#   client = boto3.client('comprehend')
#   sentiment='NEUTRAL'
#   try:
#       sentiment=client.detect_sentiment(Text=tweet, LanguageCode='en')['Sentiment']
#   except:
#       print("detect_sentiment FAILED")
#   return sentiment