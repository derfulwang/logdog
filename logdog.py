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
import click

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
            logdirs = conf['Filenames']
            path_dict = {}
            logfiles = []
            for path, fnames in logdirs.items():
                if path not in path_dict:
                    path_dict[path] = []
                for fname in fnames:
                    path_dict[path].append(os.path.join(path,fname))
                logfiles.append(os.path.join(path,fname))
        
            logging.info(path_dict)
            logging.info(logfiles)
            conf['logpathes'] = path_dict
            conf['logfiles'] = logfiles
        else:
            raise Exception("No config file")

    def on_modified(self, event):
        if os.path.basename(event.src_path) == os.path.basename(self.conf_path):
            self.conf = self.get_yaml_obj(self.conf_path)

    def get_yaml_obj(self, yaml_path):
        global Conf
        try:
            with open(yaml_path, 'rb') as yml:
                Conf = yaml.load(yml)
        except Exception as e:
            logging.exception('yaml file should be correct format')
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
        for fp in self.conf['logfiles']:
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
            self.handle_callback(line, change_f)
                                  
    def handle_callback(self, line, filename):
        for callback in self.callbacks:
            callback(line, filename, self.conf)

    def __del__(self):
        for f, fp in self.logfiles.items():
            fp.close()


to_handle = LogUpdateHandler.to_handle


@to_handle
def keyword_detect(line, filename, conf):
    for kw in conf['Keywords']:
        if line.find(kw) != -1:
            print(filename, line)
            break
    else:
        print('no', filename ,line)


@click.command()
@click.option('--config', default='./logdog.yaml', help='yaml config file path')
def main(config):
    global Conf
    yaml_path = config
    assert os.path.isfile(yaml_path) == True
    conf_handler = ConfigUpdateHandler(yaml_path)
    logpathes = Conf['logpathes']

    
    handler = LogUpdateHandler(call_backs=[])
  
    observer = Observer()
    observer.schedule(
        conf_handler, path=os.path.dirname(yaml_path), recursive=False)

    for path, fnames in logpathes.items():
        observer.schedule(
            handler, path=path, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
