# coding:utf-8
'''
配置文件同目录下的logdog.yaml
配置文件和待监控文件需要在同一路径下
一行行读取日志文件内容，然后进行处理
1. 首先读到文件末尾等待
2. 监控文件的变化情况
3. 读取新增的内容

ps:由于是日志文件的变化，只能监控追加，不能监控修改和删除, 文件的保存触发on_modified
'''

from __future__ import unicode_literals
from __future__ import print_function

import sys
import os
import time
import logging

import yaml

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(
    filename=os.path.join(sys.path[0],"logdog.log"),
    level=logging.DEBUG,
    format="%(asctime)s %(filename)s[line:%(lineno)d] [%(levelname)s]\
        %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

Conf = {}  # global config

class ConfigUpdateHandler(FileSystemEventHandler):

    def __init__(self, conf_path):
        self.conf_path = conf_path
        self.conf= self.get_yaml_obj(conf_path)

    def check_config(self, conf):
        if conf:
            logfiles = conf['Filenames']
            logdir = {os.path.dirname(f) for f in logfiles}
            logging.info(logdir)
            assert len(logdir) == 1
            conf['logpath'] = logdir.pop()
        else:
            raise Exception("No config file")

    def on_modified(self, event):
        if os.path.basename(event.src_path) == os.path.basename(self.conf_path):
            self.conf = self.get_yaml_obj(self.conf_path)

    def get_yaml_obj(self, yaml_path):
        global Conf
        with open(yaml_path, 'rb') as yml:
            Conf = yaml.load(yml)
        print(Conf)
        self.check_config(Conf)
        #logging.info(Conf)
        return Conf

class LogUpdateHandler(FileSystemEventHandler):

    __handle_funcs = []

    @classmethod
    def to_handle(cls, func):
        cls.__handle_funcs.append(func)

    def __init__(self, call_backs):
        global Conf
        self.conf = Conf
        self.logfiles = {}
        for fp in self.conf['Filenames']:
            try:
                logf = open(fp, 'r')
            except IOError:
                logging.exception('open {0} failed'.format(fp))
                continue
            logf.seek(0,2)
            self.logfiles[os.path.normpath(fp)] = logf

        self.skip_chars = {'','\n',None}
        self.callbacks = call_backs + self.__handle_funcs
        #while self.logfile.readline():
        #    pass

    def on_modified(self, event):
        change_f = os.path.normpath(event.src_path)
        if change_f not in self.logfiles:
            return
        while True:
            curfile = self.logfiles[change_f]
            line = curfile.readline()
            if line in self.skip_chars:
                break
            self.handle_callback(line)
                                  
    def handle_callback(self, line):
        for callback in self.callbacks:
            callback(line, self.conf)

    def __del__(self):
        for f, fp in self.logfiles.items():
            fp.close()


to_handle = LogUpdateHandler.to_handle


@to_handle
def keyword_detect(line, conf):
    for kw in conf['Keywords']:
        if line.find(kw) != -1:
            print(line)
            break
    else:
        print('no', line)



def main():
    global Conf
    yaml_path = './logdog.yaml'
    conf_handler = ConfigUpdateHandler(yaml_path)
    logpath = Conf['logpath']

    
    handler = LogUpdateHandler(call_backs=[])
  
    observer = Observer()
    observer.schedule(
        conf_handler, path=os.path.dirname(yaml_path), recursive=False)
    observer.schedule(
        handler, path=logpath, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
