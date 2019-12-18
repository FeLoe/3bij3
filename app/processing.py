import re

class paragraph_processing():
    def check(self, string):
        if string.strip().count(" ")< 20:
            return True
        else:
            return False

    def right_punctuation(self, text_list):
        result = [i for i in text_list if re.match(r"^[,@\'?\.$%_:;!]\s", i)]
        for item in result:
            ind = text_list.index(item)
            punct = item[0]
            text_list[ind] = item[2:]
            text_list[ind - 1] = text_list[ind - 1] + str(punct)
            result = [i for i in text_list if re.match(r"^[,@\'?\.$%_:;!]", i)]
        for item in result:
            ind = text_list.index(item)
            punct = item[0]
            text_list[ind] = item[1:]
            text_list[ind - 1] = text_list[ind - 1] + str(punct)
        return text_list


        
    def join_text(self, list_new):
        c = True
        while c == True:
            final_list = []
            for i, item in enumerate(list_new):
                if i == len(list_new) - 1 and self.check(item) == False:
                    final_list = list_new
                    c = False
                elif i == len(list_new)-1 and self.check(item) == True:
                    final_list = list_new[:-2]
                    new_item = list_new[i - 1] + " " + item
                    final_list.append(new_item)
                    c = False
                elif self.check(item) == False:
                    final_list.append(item)
                elif self.check(item) == True:
                    if i - 1 == -1:
                        new_item = item + " " + list_new[i + 1]
                    else:
                        new_item = list_new[i - 1] + " " + item + " " + list_new[i + 1]
                        final_list = final_list[:-1]
                    final_list.append(new_item)
                    if (i + 2) == (len(list_new) - 1):
                        if self.check(list_new[i + 2]) == True:
                            final_list = final_list[:-1]
                            new_item = new_item + " " + list_new[i + 2]
                            final_list.append(new_item)
                        else:
                            final_list = final_list[:-1]
                            final_list.append(list_new[i + 2])
                        c = False
                    else:
                        for textrest in range((i + 2),len(list_new)):
                            final_list.append(list_new[textrest])
                        list_new = final_list
                        break
        final_list = [re.sub(r'\s([?.!"](?:\s|$))', r'\1', item) for item in final_list]
        final_list = self.right_punctuation(final_list)
        return final_list
