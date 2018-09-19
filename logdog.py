# coding:utf-8
'''
配置文件同目录下的log_moniter.yaml
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

    def __init__(self, yaml_path):
        self.yaml_path = yaml_path
        self.conf = self.get_yaml_obj(yaml_path)
        self.logfile = open(self.conf['Filename'], 'r')
        self.skip_chars = {'','\n',None}
        while self.logfile.readline():
            pass

    def get_yaml_obj(self, yaml_path):
        with open(yaml_path, 'r', encoding='utf-8') as yml:
            conf = yaml.load(yml)
        return conf

    def on_modified(self, event):
        if os.path.basename(event.src_path) == "log_moniter.yaml": # 动态加载配置
            self.conf = self.get_yaml_obj(event.src_path)
            print(self.conf)
            return
        if os.path.normpath(self.logfile.name) != os.path.normpath(event.src_path):
            return
        while True:
            line = self.logfile.readline()
            if line in self.skip_chars:
                break
            print('-',line)
            for kw in self.conf['Keywords']:
                if line.find(kw) != -1:
                    print(line)
                    break
            else:
                print('no', line)

    def __del__(self):
        self.logfile.close()


def main():
    yaml_path = './log_moniter.yaml'
    handler = LogUpdateHandler(yaml_path)
    observer = Observer()
    observer.schedule(handler, path=os.path.split(os.path.abspath(yaml_path))[0], recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()