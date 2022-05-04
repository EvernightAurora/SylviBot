### 简介：仙布机器人
基于yiri-mirai框架的，一个找图机器人\
目前支持功能:
- 在pixiv、e621上按照给定tag随机查找图片，对于动态图也能完成转发/渲染
- 实时设置权限列表来阻止bot搬运到不合适图片到部分群
- 记录群内其他人的聊天记录方便查阅
- 收到好友申请时自动转发给管理员，管理员可选择接受或拒绝，当然也可以忽略
- 开启自动解析群内youtube链接，并返回视频简介
- 订阅pixiv和youtube指定作者，从而在作者有新作品时自动发到群内 

特色：
- 基于python单进程，以协程为核心异步实时爬取信息
- 内部设置同时间http请求上限，避免请求过于频繁或流量过大
- 经过抗压测试，能无误完成高频爬取图片命令
- 订阅功能以APSchedule的异步任务为核心。


### 依赖
系统要求：无要求，或者主要看yiri-mirai框架的系统要求

python版本：3.9，其他没试过
 
#### python需求库
核心框架
- yiri-mirai,  		具体配置可参考[yiri-mirai官网](https://yiri-mirai.vercel.app/tutorials/01/configuration)
  
爬虫所需库：  
-  requests
-  httpx			——异步版requests
-  beautifulsoup4
-  opencv-python	——基础图片处理

其他库
- matplotlib  
- numpy  
- tqdm
- apscheduler
- pyyaml


###  目录结构
| 文件 | 备注 |  
| :-: | :-: |  
| ```app.py``` | bot的主体文件 |  
| ```config.yaml``` | 重要： 对于bot的一些重要配置 |
| ```proxy_config.yaml``` | 重要：对于bot使用的代理的一些配置 |
| ```Proc/``` | 对于各类消息的处理代码 |  
| ```pixiv/``` | pixiv相关的一些 |
| ```utils/``` | 一些实现的通用功能 |


  

### 启动方式
第一次启动前，要先配置好```config.yaml```以及```proxy_config.yaml```配置文件
#### config.yaml内容说明
| 键 | 含义 |  
| :-: | :-: |  
| ```621/926_default_search``` | 对于e621站或e926站默认搜索的关键词 |  
| ```621/926_favcount_threshold``` | 对于e621站或e926站默认筛选的favcount阈值 |
| ```access_default_group``` | 默认可以看到非全年龄内容的群的列表，对于私聊不会有限制 |
| ```bot_qq``` | bot自己的qq，这个很重要 |
| ```root_qq``` | 管理员的qq的列表，这个很重要 |
| ```pixiv_cookie_PHPSESSID``` | 访问pixiv需要登录，因此请把pixiv.net的PHPSESSID cookie内容贴在这里，以保证可以正常访问|
| ```pixiv_default_search``` | 在pixiv搜索图片的默认搜索关键词 |

由于pixiv和youtube不一定能直接访问，因此bot会使用代理来访问这两个。代理的设置在**proxy_config.yaml**中


启动方式：
	先启动mirai，在里面登录目标qq后，（也要启动代理软件）然后运行```python app.py```启动bot  

