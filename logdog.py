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

import yaml

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class LogUpdateHandler(FileSystemEventHandler):

    __handle_funcs = []

    def __init__(self, yaml_path, call_backs):
        self.yaml_path = yaml_path
        self.conf = self.get_yaml_obj(yaml_path)
        print(self.conf)
        self.logfile = open(self.conf['Filename'], 'r')
        self.skip_chars = {'','\n',None}

        self.callbacks = call_backs + self.__handle_funcs
        while self.logfile.readline():
            pass
        #self.logfile.seek(0,2)

    def get_yaml_obj(self, yaml_path):
        with open(yaml_path, 'rb') as yml:
            conf = yaml.load(yml)
        return conf

    def on_modified(self, event):
        if os.path.basename(event.src_path) == os.path.basename(self.yaml_path): # 动态加载配置
            self.conf = self.get_yaml_obj(event.src_path)
            print(self.conf)
            return
        if os.path.normpath(self.logfile.name) != os.path.normpath(event.src_path):
            return
        while True:
            line = self.logfile.readline()
            if line in self.skip_chars:
                break
            self.handle_callback(line)
                                  
    def handle_callback(self, line):
        for callback in self.callbacks:
            callback(line, self.conf)

    @classmethod
    def to_handle(cls, func):
        cls.__handle_funcs.append(func)

    def __del__(self):
        self.logfile.close()


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
    yaml_path = './logdog.yaml'
    handler = LogUpdateHandler(yaml_path, call_backs=[])
    observer = Observer()
    observer.schedule(
        handler, path=os.path.split(os.path.abspath(yaml_path))[0], recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
