#!/usr/bin/env python3
from inca import Inca
import datetime
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode

connection = mysql.connector.connect(host = 'localhost', database = '3bij3', user = 'user', password = 'passwd')

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
            g = myinca.database.document_generator({"query":
                                                    {"bool":
                                                     {"filter":
                                                      [{"term":{"doctype":doctype}},
                                                       {"range":{"META.ADDED":{"gte": threshold}}}]
                                                     }}})
            try: 
                es_ids = []
                for result in g:
                    es_ids.append(result['_id'])
                es_ids = [(x,) for x in es_ids]
                sql_insert_query = """ INSERT INTO All_News (id) VALUES (%s) """
                cursor = connection.cursor(prepared = True)
                result = cursor.execturemany(sql_insert_query, es_ids)
                connection.commit()
                print(cursor.rowcount, "Record inserted successfully into all_news table")
            except mysql.connector.Error as error:
                    print("Failed inserting record into all_news table {}".format(error))
        except Exception as ex:
            print("'\nERROR SCRAPING {}.".format(outlet))
            print(ex)
            print('\n')
