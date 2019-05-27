import requests 
import json
from bs4 import BeautifulSoup
from slackclient import SlackClient
import re

def slack_message(message, channel):
    token = 'slack_token' # https://api.slack.com/custom-integrations/legacy-tokens
    sc = SlackClient(token)
    sc.api_call('chat.postMessage', channel=channel, 
                text=message, username='ScrapeBot',
                icon_emoji=':robot_face:')

def parse_times(raw_times):
    times = [re.split('T|\+',av)[1] for av in raw_times]
    shuttle_available = any('00:00' in t for t in times)

    parsed_times = [" ".join(re.split('T|\+',av)[:2]) for av in raw_times]
    parsed_times = "\n".join(parsed_times)
    return parsed_times


# url to be scraped
scrape_url = "https://scrape.url/index.html"

# date/times available that you don't want to receive alerts for.
no_thanks = ['2019-04-25T21:30:00+1200']

def scrape(querydate):
    # request data
    data = {'_token':'token', 
		'experience':'experience', 
		'date':querydate, 
		'shuttle_pax':'0',
		'num_pools':'1'} 

    # Request
    response = requests.post(url = scrape_url, data = data) 
    html = json.loads(response.text)['data']['html']

    soup = BeautifulSoup(html, 'html.parser')
    # print(soup.prettify())

    # Collect only available entries
    avail = soup.find_all('a')
    avail_times = [ele['data-session-datetime'] for ele in avail]
    
    rejected_times = [x for x in avail_times if x in no_thanks]
    new_times  = [x for x in avail_times if x not in no_thanks]
    
    if new_times != None and len(new_times) > 0:
        parsed_times = parse_times(new_times)
        message = 'Available Times: \n%s' % parsed_times

        # Message alert channel
        slack_message(message, 'alert')
        
        # Message no-alert channel
        slack_message("Found available times!", 'healthcheck')
    else:
        parsed_times = parse_times(rejected_times)
        parsed_times = (", rejected times:\n%s" % parsed_times) if parsed_times != "" else ""
        unavail = soup.find_all('div', class_="obl-session-state-text")
        unavail_count = 0 if unavail == None else len(unavail)
        
        # Only message no-alert channel
        slack_message("No available times, %d unavail%s." % (unavail_count, parsed_times), 'healthcheck')

def handler(event,context):
    querydates = ['2019-04-27', '2019-04-30']
    for qd in querydates:
        scrape(qd)
