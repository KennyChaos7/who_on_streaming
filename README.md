# who_on_streaming
> DD监控台
- 利用b站api进行查询
- **无需登录**
- 自动忽略本地代理，无需担心挂在魔法时程序会被偷走流量
- 配置简单
  - **只需要在exe所在文件夹里，建立一个wos.ini，然后往里填写你要监控的管人uid即可**
- 支持自动3分钟定时刷新和停止
- 支持手动刷新
  - 但与自动刷新冲突，需要停止自动刷新后再进行手动刷新
- 支持上播提示功能

## 配置相关
1. 需要在exe所在文件夹里，建立一个**wos.ini**
2. 然后往里填写你要监控的管人uid即可
   - 具体配置可以参考**wos.ini**

## 源码相关
[特别感谢@bilibili-API的开源b站api](https://github.com/SocialSisterYi/bilibili-API-collect/)
- api请求相关查看wbi.py
- gui相关查看who_on_streaming.py

## 关于为什么自动刷新要3分钟
叔叔对某些接口有风控管理，所以实际上有低概率请求过多被暂时禁止访问
所以自动刷新的时间不得不设置3分钟

## 自行编译
可以参考pyinstall-cmd，dist文件夹里的exe文件就是利用这个命令生成的
