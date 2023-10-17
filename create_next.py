#!/usr/bin/python3

import re
import glob
import json
import datetime
import os
import sys
from pprint import pprint

with open("config.json","r") as f:
    config = json.load(f)

newest = datetime.datetime(1901, 1, 1)
newest_file = ""
meeting_tomorrow = False
for minute in glob.glob(f'{config["minute_directory"]}*.md'):
    file = minute.split("/")[-1].replace(".md","")
    
    pattern = "Scheduled start: \d{4}-\d{2}-\d{2}, (2[0-3]|[01]?[0-9]):[0-5][0-9]"
    with open(minute,"r", encoding='utf-8') as f:
        x = re.search(pattern, f.read())
        if x:
            filedate = datetime.datetime.strptime(x.group(),"Scheduled start: %Y-%m-%d, %H:%M")
        else:
            filedate = datetime.datetime.strptime(file, "%Y-%m-%d")
    if filedate > newest:
        newest = filedate
        newest_file = minute

print(f"Newest file: {newest_file}")

with open(newest_file,"r") as f:
    old_minutes = f.read()

pattern = "Next meeting: \d{4}-\d{2}-\d{2}, (2[0-3]|[01]?[0-9]):[0-5][0-9]"
x = re.search(pattern, old_minutes)

if not x:
    print("No next meeting found")

else:
    next_meeting = datetime.datetime.strptime(x.group(),"Next meeting: %Y-%m-%d, %H:%M")

    # Clean up any stray template links to the next meeting that haven't been filled in
    x = re.sub("NNNN-NN-NN", next_meeting.strftime("%Y-%m-%d"), old_minutes)
    if x != old_minutes:
        with open(newest_file,"w") as f:
            f.write(x)
            old_minutes = x

    with open(config["minute_template"],"r") as f:
        template = f.read()
    
    # Add scheduled start date/time
    template = template.replace("Scheduled start: \n",f'Scheduled start: {next_meeting.strftime("%Y-%m-%d, %H:%M")}\n')

    # Add links to previous minutes
    template = template.replace("PPPP-PP-PP",newest.strftime("%Y-%m-%d"))

    # Add name of current meeting
    template = template.replace("yyyy-mm-dd",next_meeting.strftime("%Y-%m-%d"))
    
    # Change page creation time
    d = datetime.datetime.utcnow()
    s = f'{d.isoformat().split(".")[0]}.{round(d.microsecond/1000)}Z'

    template = re.sub("dateCreated: .{24}","dateCreated: "+s, template)
    template = re.sub("date: .{24}","date: "+s, template)

    if len(old_minutes.split("## Action Summary\n\n")) < 2:
        action_items = "No action items from previous meeting"
    else:
        action_items = old_minutes.split("## Action Summary\n\n")[1]
        action_items = action_items.replace("|\n","| Status | \n",1)
        action_items = action_items.replace("|\n","| ------ | \n",1)
        action_items = action_items.replace("|\n","| STATUS | \n")
        action_items = action_items.replace("| \n","|\n")
    sect = "## Review Previous Meeting's Action Items\n"
    template = template.replace(sect,f'{sect}\n{action_items}')

    # Add to minute directory
    with open(f'{config["minute_directory"]}{next_meeting.strftime("%Y-%m-%d")}.md',"w") as f:
        f.write(template)