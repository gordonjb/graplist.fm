# Why?
I always wanted some stats on shows I'd attended. Like how many times I've seen promotion X or wrestler Y. setlist.fm is a good comparison point. Some people have spreadsheets. That seemed like a massive pain, so I decided to scrape Cagematch and learn some Python and data visualisation. Because that's SO much easier.

# Known Issues
Currently, we just pull out workers on a show from the All Workers list. Unfortunately, this includes named Tag Teams. This is fine when that team is in the database, because we can just recognize the tag team link and exclude it. However if the Tag Team doesn't exist in the database, we can't differentiate it from wrestlers who don't exist in the database, as they are both just strings with no meta data. We could possibly do some weird regex parsing on the results to detect what is a tag team, which we might want to replace the all workers parse with anyway if we wanted to do some more complex analysis

# Shows list
I've used YAML to store the list of shows. While it's more of a pain in the arse to have to format each show you add slightly than just pasting in a list, it does allow you to include comments to indicate which show the link refers to so it's easier for you to understand.

To add shows to the list that will be considered, add a new line containing the text `- ` followed by the URL of the show page from Cagematch. The `- ` syntax creates a list in YAML. You can also use comments to identify links in any way you choose. Comments are created by typing `#`. All text that follows on that line will be ignored when the file is loaded in.

```yaml
- https://www.cagematch.net/?id=1&nr=211116 #PROGRESS Bokkle
- https://www.cagematch.net/?id=1&nr=226485
- https://www.cagematch.net/?id=1&nr=202871 #SHEVOLUTION 2
# AJPW Dream Power Series 2019 - Tag 5
- https://www.cagematch.net/?id=1&nr=226489
# This link will be ignored, for example: https://www.cagematch.net/?id=1&nr=226480
```

# TODO
- Add a way to include shows not on Cagematch. Probably some method to load YAML from a file or directory that includes the metadata we need
- Your request could go here!
