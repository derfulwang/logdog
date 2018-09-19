# coding: utf-8

import time

i=0
while True:
    with open("test.log", 'a') as f:
        if i < 10:
            if i == 8:
                f.write("[ERROR]{0}\n".format(i))
            f.write("test{0}\n".format(i))
            i += 1
            time.sleep(1)
        else:
            break

