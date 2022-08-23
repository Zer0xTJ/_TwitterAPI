import pandas as pd
import requests
# import json
import requests

API_KEY = ''
API_SECRET_KEY = ''
BEARER_TOKEN = ''


def create_headers():
    # authenticate
    global BEARER_TOKEN
    bearer_token = BEARER_TOKEN
    """ Creates headers for requests """
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def create_url(endpoint):
    # create a url with the specific endppoint
    """ Creates a API URL for reuqests """
    url = f'https://api.twitter.com{endpoint}'
    return url


def fetch(endpoint="/2/tweets/search/recent", params={}):
    """
        Connects to API URL endpoint, and fetch data
        endpoint: endpoint API
        params: dictionary of a query url ex: {"query": "something"}
    """
    headers = create_headers()
    url = create_url(endpoint)
    response = requests.request("GET", url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def get_user(username):
    """
        Get user info as a dictionar: keys -> id, name, username
    """
    return fetch(f"/2/users/by/username/{username}").get("data", {})


def search_tweets(keywords="", from_user=None, conversation_id=None, count=10, auto_save=False):
    """
    Searrch recent tweets, account tweets, conversation tweets
    keywords: search keywords ex: (#programming, #code, python) 
    from_user: default None: if not none, this function will fetch user's tweets
    conversation_id: default None, if Not none, will fetch the replies on a specific conversation_id
    """
    # count: number | all
    fetch_endpoint = "/2/tweets/search/recent"
    user_id = None
    query = keywords + " -is:retweet"
    query = query.strip()
    if(from_user):
        user_id = get_user(from_user).get("id", None)
        if(user_id is None):
            print("User Not Found!")
            return False
        fetch_endpoint = f"/2/users/{user_id}/tweets"
    if(conversation_id):
        query += f" conversation_id:{conversation_id}"
    all_tweets = []
    oldest_id = None
    while(True):
        if(count != 'all'):
            max_results = min(count, 100)
        else:
            max_results = 100
        if(user_id is None):
            params = {"query": query, "max_results": max_results}
        else:
            params = {"max_results": max_results}
        params["tweet.fields"] = "created_at,lang,public_metrics,conversation_id"
        if(oldest_id):
            params["until_id"] = oldest_id

        tweets_x = fetch(fetch_endpoint, params)
        if(len(tweets_x.get("data", [])) > 0):
            all_tweets.extend(tweets_x['data'])
            oldest_id = tweets_x.get('meta', {}).get('oldest_id', None)
        else:
            break
        if(count != "all"):
            if(len(all_tweets) >= count):
                all_tweets = all_tweets[:count]
                break
    all_tweets = [organize_tweet(t) for t in all_tweets]
    if(auto_save):
        save_to_file(all_tweets)
    return all_tweets


def organize_tweet(tweet):
    return {
        "id": tweet.get("id", 'INVALID'),
        "text": tweet.get("text", "NONE"),
        "lang": tweet.get("lang", 'INVALID'),
        "created_at": tweet.get("created_at", 'INVALID'),
        "retweet_count": tweet.get("public_metrics", {}).get("retweet_count"),
        "reply_count": tweet.get("public_metrics", {}).get("reply_count"),
        "like_count": tweet.get("public_metrics", {}).get("like_count"),
        "quote_count": tweet.get("public_metrics", {}).get("quote_count"),
        "conversation_id": tweet.get("conversation_id", 'INVALID'),
        "replies": [],
    }


def get_replies(conv_id, replies_count):
    # GET THE REPLIES OF A SINGLE CONVERSATION ID
    # replies_count: number | all
    if(conv_id is None):
        return []
    return search_tweets(conversation_id=conv_id, count=replies_count)


def get_tweets_replies(tweets, replies_count=10):
    for t in tweets:
        print("Fetching replies of tweet: ", t['id'], '...')
        t['replies'] = get_replies(t.get('conversation_id'), replies_count)
        save_to_file(tweets)


def save_to_file(tweets):
    columns = tweets[0].keys()
    rows = [t.values() for t in tweets]
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv("data.csv", encoding="utf8", index=False)
    return df

# def main():
#     # tweets = search_tweets("python", count=200)
#     tweets = search_tweets(from_user="Twitter", count=10, auto_save=True)
#     get_tweets_replies(tweets, 50)
#     save_to_file(tweets)


# if __name__ == '__main__':
#     main()
