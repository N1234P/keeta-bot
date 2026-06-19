import tweepy 
from credentials import bearer_token, api_key, api_key_secret, access_token, access_token_secret

client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_key_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )



    
