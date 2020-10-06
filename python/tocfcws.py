 # importing modules
import os
import json
import pathlib
import tweepy
import datefinder
from datetime import datetime, timedelta
from requests import get
import helper

root = pathlib.Path(__file__).parent.parent.resolve()
tweet_on = os.getenv('tweet')
minute_offset = 65

auth = tweepy.OAuthHandler(os.getenv('c_key'), os.getenv('c_secret'))
auth.set_access_token(os.getenv('a_token'), os.getenv('a_secret'))
api = tweepy.API(auth)

def compare_time(timestamp):
    working_date = datetime.strftime(datetime.utcnow() - timedelta(minutes=5),"%Y-%m-%d %H:%M:%S") # 5 minutes ago
    print(working_date, timestamp)
    diff = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") - datetime.strptime(working_date, "%Y-%m-%d %H:%M:%S")
    minutes = int(round(int(diff.seconds) / 60, 0))
    print("working Time =", minutes)
    return minutes


class article:
        def __init__(self, title, url, timestamp):
                self.title = title
                self.url = url.replace('prod-content-cdn','www').replace('content/chelseafc/','').replace('.html','')
                self.timestamp = timestamp
        def __repr__(self):
            return repr((self.title, self.url, self.timestamp))


def get_news(num):
    endpoint = ( "https://prod-content-cdn.chelseafc.com/content/chelseafc/en.newsfeed.v3.0.9.2020.0.all.web.none.order_date_desc.json")
    response = get(endpoint, timeout=10)
    articles = list()
    if response.status_code >= 400:
        raise RuntimeError(f'Request failed: { response.text }')
    data = response.json()['newsFeed'][:num]
    for i in range(0, num):
        link = data[i]['link']['url']
        title = data[i]['link']['title']
        time = data[i]['publishDate']
        try:
            published_matches = list(datefinder.find_dates(time))
            if len(published_matches) > 0:
                published_str_dt = published_matches[0].strftime("%Y-%m-%d %H:%M:%S")
            else:
                published_str_dt = ""
        except KeyError:
            print("error with publishing " + title)
            published_str_dt = ""
        articles.append(article(title, link, published_str_dt))
    return articles

# output
if __name__ == "__main__":
    index_page = root / "index.html"
    index_contents = index_page.open().read()
    string_output = ''
    for article in get_news(5):
        output_builder = f"{article.title} :- {article.url}"
        string_output += f'<li><a href="{article.url}">{article.title}</a><small>{article.timestamp}</small></li>\n'
        if(compare_time(article.timestamp) < 5):
            print(output_builder)
            if(tweet_on):
                api.update_status(status = f"★: {output_builder}")
    final_output = helper.replace_chunk(index_contents, "news_marker", f"<ul>\n{string_output}</ul>")
    index_page.open("w").write(final_output)

