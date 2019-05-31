# logdog
log moniter for fasle alarm, detect the change of log

用于监控日志中的错误报警信息，并及时作出提醒，使用watchdog来检测文件的变化

- 可以动态在yaml文件中配置需要监控的log
- 可以动态配置需要设置提醒的关键词

配置文件同目录下的logdog.yaml

一行行读取日志文件内容，然后进行处理
1. 首先读到文件末尾等待
2. 监控文件的变化情况
3. 读取新增的内容

ps:由于是日志文件的变化，只能监控追加，不能监控修改和删除, 文件的保存触发on_modified
