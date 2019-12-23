'''String processing functionality to process article text to be displayed'''
class paragraph_processing():
    def check(self, string):
        if string.strip().count(" ") < 4:
            return True
        else:
            return False

    def join_text(self, list_new):
        keep_running = True
        while keep_running:
            final_list = []
            for i, item in enumerate(list_new):
                if i == len(list_new) - 1 and not self.check(item):
                    final_list = list_new
                    keep_running = False
                elif i == len(list_new)-1 and self.check(item):
                    final_list = list_new[:-2]
                    new_item = list_new[i - 1] + " " + item
                    final_list.append(new_item)
                    keep_running = False
                elif not self.check(item):
                    final_list.append(item)
                elif self.check(item):
                    if i - 1 == -1:
                        new_item = item + " " + list_new[i + 1]
                    else:
                        new_item = list_new[i - 1] + " " + item + " " + list_new[i + 1]
                        final_list = final_list[:-1]
                    final_list.append(new_item)
                    if (i + 2) == (len(list_new) - 1):
                        if self.check(list_new[i + 2]):
                            final_list = final_list[:-1]
                            new_item = new_item + " " + list_new[i + 2]
                            final_list.append(new_item)
                        else:
                            final_list.append(list_new[i + 2])
                        keep_running = False
                    else:
                        for textrest in range((i + 2),len(list_new)):
                            final_list.append(list_new[textrest])
                        list_new = final_list
                        break
        return final_list
