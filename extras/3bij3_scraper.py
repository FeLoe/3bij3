#!/usr/bin/env python3
from inca import Inca
import datetime

myinca  = Inca()
outlets = ['ad', 'nrc', 'nu', 'telegraaf', 'volkskrant']
threshold = datetime.datetime.now() - datetime.timedelta(seconds = 7200)
threshold = threshold.isoformat()

for outlet in outlets:
        print("Scraping {}...".format(outlet))
        try:
            eval("myinca.rssscrapers.{}()".format(outlet))
            if outlet == 'nu':
                doctype = outlet
            else:
                doctype = outlet + " (www)"
            g = myinca.database.document_generator({"query":
                                   {"bool":
                                    {"filter":
                                     [{"term":{"doctype":doctype}},
                                      {"range":{"META.ADDED":{"gte": threshold}}}]
                                    }}})
            p = myinca.processing.driebijdrie_processer([e for e in g], field = "text", new_key = "topic", save = True)
            for result in p:
                    pass
            g = myinca.database.document_generator({"query":
                                                    {"bool":
                                                     {"filter":
                                                      [{"term":{"doctype":doctype}},
                                                       {"range":{"META.ADDED":{"gte": threshold}}}]
                                                     }}})
            q = myinca.processing.njr([e for e in g], field = "text", new_key = "text_njr", save = True)
            for result in q:
                    pass
        except Exception as ex:
            print("'\nERROR SCRAPING {}.".format(outlet))
            print(ex)
            print('\n')
