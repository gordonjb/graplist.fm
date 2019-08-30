# Why?
I always wanted some stats on shows I'd attended. Like how many times I've seen promotion X or wrestler Y. setlist.fm is a good comparison point. Some people have spreadsheets. That seemed like a massive pain, so I decided to scrape Cagematch and learn some Python and data visualisation. Because that's SO much easier.

# Known Issues
I fixed the one-off gimmicks/non-database tag team issues in this branch so that's gone but there's still broken stuff I'll write in here later

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

My personal shows.yaml is in the repo, for comparison: [shows.yaml](shows.yaml)

# TODO list/Work Log
[A project diary of sorts, with notes and a TODO list, is located in the repo here](TODOLog.md).

# """"Roadmap""""
- Add a way to include shows not on Cagematch. Probably some method to load YAML from a file or directory that includes the metadata we need.
- I'm pretty confident initially that this will be a locally run thing, requiring Python etc. I'd like to get it to a place where it's something online, or at least something you just need to dump a list of shows into.
- Your request could go here!
