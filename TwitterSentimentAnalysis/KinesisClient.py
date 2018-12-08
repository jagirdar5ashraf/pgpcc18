import boto3
import time
import json

#+----+----+----+----+----+----+
#class: KinesisClient
#+----+----+----+----+----+----+
class KinesisClient (object):

    accessKeyId = "" #the code in production has actual values
    awsRegion = "us-east-1"
    secretAccessKey = ""

    connection = boto3.client('kinesis', region_name=awsRegion, aws_access_key_id=accessKeyId,aws_secret_access_key=secretAccessKey)
    #///////////////////////////
    # method:__init__
    #///////////////////////////
    def __init__ (self, stream_name):
        self.my_stream_name = stream_name
        self.shard_iterator_shard1 = None
        self.shard_iterator_shard0 = None
        tries = 0
        while tries < 10:
            tries += 1
            time.sleep (0.5)
            try:
                response = self.connection.describe_stream (StreamName=self.my_stream_name)
                if response['StreamDescription']['StreamStatus'] == 'ACTIVE':
                    print (response['StreamDescription']['StreamStatus'])
                    break
            except:
                print ('error while trying to describe kinesis stream')
        else:
            print ('Stream is still not active, aborting...')

    #///////////////////////////
    # method:pushToStream- pushes records to the stream
    #///////////////////////////
    def pushToStream(self, keyword, tweetText):
        try:
            self.connection.put_record(StreamName=self.my_stream_name, Data=json.dumps(tweetText), PartitionKey=keyword)
        except Exception as e:
            print ("Error:" + str(e))

    
    #///////////////////////////
    # method:get_shardIterator
    #///////////////////////////
    def get_shardIterator(self, shard_no):
        if shard_no == 1 and self.shard_iterator_shard1 is not None:
            return self.shard_iterator_shard1
        elif shard_no == 0 and self.shard_iterator_shard0 is not None:
            return self.shard_iterator_shard0
        try:
            #self.my_shard_iterator = None
            response = self.connection.describe_stream (StreamName=self.my_stream_name)
            shard_id = response['StreamDescription']['Shards'][shard_no]['ShardId']
            shard_iterator = self.connection.get_shard_iterator(StreamName=self.my_stream_name, ShardId=shard_id, ShardIteratorType='LATEST')
            if (shard_no == 1):
                self.shard_iterator_shard1 = shard_iterator['ShardIterator']
            else:
                self.shard_iterator_shard0 = shard_iterator['ShardIterator']
            time.sleep (1)
        except Exception as e:
            print ("Error:" + str(e))

    #///////////////////////////
    # method:getRecords
    #///////////////////////////
    def getRecords(self, shard_no, limit):
        try:
            my_shard_iterator = None
            if shard_no ==1:
                my_shard_iterator = self.shard_iterator_shard1
            else:
                my_shard_iterator = self.shard_iterator_shard0

            record_response = self.connection.get_records(ShardIterator=my_shard_iterator, Limit=limit)
            if shard_no ==1:
                self.shard_iterator_shard1 = record_response['NextShardIterator']
            else:
                self.shard_iterator_shard0 = record_response['NextShardIterator']

            time.sleep(3)
            return record_response
        except Exception as e:
            print ("Error:" + str(e))