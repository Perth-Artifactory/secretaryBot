#!/usr/bin/python3

import re
import glob
import json
import datetime
from pprint import pprint
import sys
import requests

from slack_sdk.webhook import WebhookClient

with open("config.json","r") as f:
    config = json.load(f)

slack = WebhookClient(config["webhook"])

newest = datetime.datetime(1901, 1, 1)
newest_file = ""
meeting_tomorrow = False
days_until_meeting = 0
for minute in glob.glob(f'{config["minute_directory"]}\*.md'):
    file = minute.split("\\")[-1].replace(".md","")

    pattern = "Scheduled start: \d{4}-\d{2}-\d{2}, (2[0-3]|[01]?[0-9]):[0-5][0-9]"
    with open(minute,"r", encoding='utf-8') as f:
        x = re.search(pattern, f.read())
        if x:
            filedate = datetime.datetime.strptime(x.group(),"Scheduled start: %Y-%m-%d, %H:%M")
        else:
            filedate = datetime.datetime.strptime(file,"%Y-%m-%d")
    if filedate > newest:
        newest = filedate
        newest_file = minute

with open(newest_file,"r") as f:
    next_meeting = f.read()

# Get other business titles
pattern = "\n#.*\n"
x = re.findall(pattern,next_meeting)
toc = [i.replace("\n","") for i in x]

capturing = False
other_business = []
for heading in toc:
    if heading == "## Other Business":
        capturing = True
    elif heading[:3] == "## ":
        capturing = False
    elif capturing and heading[:5] != "#### " and heading[:6] != "##### " and heading[4:] != 'OTHER BUSINESS EXAMPLE':
        other_business.append(heading[4:])
if not other_business:
    other_business = ["No other business has been added"]

url_base = config["minute_directory"].replace(config["minute_git_directory"], config["url"]).replace("\\","/")
url = f'{url_base}{newest.strftime("%Y-%m-%d")}'

deadline = newest - datetime.timedelta(hours=48)

days_until_meeting = (newest - datetime.datetime.now()).days
hours_until_meeting = round((newest - datetime.datetime.now()).seconds/3600 + days_until_meeting * 24)

other_business_string = ""
for ob in other_business:
    other_business_string += f' ‣ {ob}\n'

print(f"It is {days_until_meeting} days until the next meeting")

if days_until_meeting in [7,3]:
    blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f'Reminder, we have a meeting on <!date^{int(newest.timestamp())}'+"^{date_long_pretty} at {time}^"+f'{url}^|FALLBACK> ({days_until_meeting} days away)'
            }
        }
    ]
    blocks.append({"type": "divider"})
    blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f'You have until <!date^{int(deadline.timestamp())}'+"^{date_long_pretty} at {time}"+f'|FALLBACK> to add items to the agenda.\nOther Business added so far:\n{other_business_string}'
            }
        })
    blocks.append({"type": "divider"})
    blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f'If you cannot attend the meeting please let us know before <!date^{int(deadline.timestamp()+86400)}'+"^{date_long_pretty} at {time}"+f'|FALLBACK>'
            }
        })
    response = slack.send(
    text="A meeting notice has been sent",
    blocks=blocks)

elif -1 < hours_until_meeting < 24:
    blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f'The agenda and apologies for the meeting at <!date^{int(newest.timestamp())}'+"^{time}^"+f'{url}^|FALLBACK> has been finalised.'
            }
        }
    ]
    blocks.append({"type": "divider"})
    blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f'Other Business on the agenda:\n{other_business_string}'
            }
        })
    response = slack.send(
    text="A meeting notice has been sent",
    blocks=blocks)

if days_until_meeting == 2:
    r = requests.get(f'https://api.tidyhq.com/v1/groups/{config["committee_id"]}/contacts',params={"access_token":config["tidytoken"]})
    for contact in r.json():
        p = {"access_token":config["tidytoken"],
             "subject":"Notice of Perth Artifactory Inc Committee Meeting",
             "body":f"""The next meeting of the Management Committee is scheduled for {newest} at 8/16 Guthrie St.</br>
             The Agenda can be found <a href="{url}">here</a>.</br>
             Other business currently on the agenda: {", ".join(other_business)}""",
             "contacts":[contact["id"]]}
        r_post = requests.post("https://api.tidyhq.com/v1/emails",params=p)
