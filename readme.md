# DongTai-openapi

[![django-project](https://img.shields.io/badge/django%20versions-3.0.3-blue)](https://www.djangoproject.com/)
[![DongTai-project](https://img.shields.io/badge/DongTai%20versions-beta-green)](https://huoxianclub.github.io/LingZhi/)
[![DongTai--openapi](https://img.shields.io/badge/DongTai--openapi-v1.0.0-lightgrey)](https://huoxianclub.github.io/LingZhi/#/doc/tutorial/quickstart)
[![DongTai-OpenAPI-Build](https://github.com/HXSecurity/DongTai-openapi/actions/workflows/build-openapi.yml/badge.svg)](https://github.com/HXSecurity/DongTai-openapi/actions/workflows/build-openapi.yml)

> 负责与agent相关的api服务，包括：接收agent注册信息、接收心跳信息、接收错误日志信息、接收组件信息、接收漏洞信息、接收权限变更信息、发送引擎控制命令、发送hook点策略、下载检测引擎；

## 项目介绍
“火线～洞态IAST”是一款专为甲方安全人员、甲乙代码审计工程师和0 Day漏洞挖掘人员量身打造的辅助工具，可用于集成devops环境进行漏洞检测、作为代码审计的辅助工具和自动化挖掘0 Day。

“火线～洞态IAST”具有五大模块，分别是`DongTai-webapi`、`DongTai-openapi`、`DongTai-engine`、`DongTai-web`、`agent`，其中：
- `DongTai-webapi`用于与`DongTai-web`交互，负责用户相关的API请求；
- `DongTai-openapi`用于与`agent`交互，处理agent上报的数据，向agent下发策略，控制agent的运行等
- `DongTai-engine`用于对`DongTai-openapi`接收到的数据进行分析、处理，计算存在的漏洞和可用的污点调用链等
- `DongTai-web`为“火线～洞态IAST”的前端项目，负责页面展示
- `agent`为各语言的数据采集端，从安装探针的项目中采集相对应的数据，发送至`DongTai-openapi`服务


### 应用场景
“火线～洞态IAST”可应用于：`devsecops`阶段做自动化漏洞检测、开源软件/组件挖掘通用漏洞、上线前安全测试等场景，主要目的是降低现有漏洞检测的工作量，释放安全从业人员的生产力来做更专业的事情。

### 部署方案

**源码部署**

1.配置安装`DongTai-webapi`服务

2.修改配置文件

复制配置文件`conf/config.ini.example`为`conf/config.ini`并需改其中的配置；其中：

- `engine`对应的url为`DongTai-engine`的服务地址
- `apiserver`对应的url为`DongTai-openapi`的服务地址
- 数据库配置为`DongTai-webapi`服务所使用的数据库

3.运行服务 

- 运行`python manage.py runserver`启动服务

**容器部署**

1.确保已通过[DongTai-webapi](https://github.com/huoxianclub/DongTai-webapi#%E9%83%A8%E7%BD%B2%E6%96%B9%E6%A1%88)创建并部署数据库

2.修改配置文件

复制配置文件`conf/config.ini.example`为`conf/config.ini`并需改其中的配置；其中：
- `engine`对应的url为`DongTai-engine`的服务地址
- `apiserver`对应的url为`DongTai-openapi`的服务地址

3.构建镜像
```
$ docker build -t huoxian/dongtai-openapi:latest .
```

4.启动容器
```
$ docker run -d -p 8002:8000 --restart=always --name dongtai-openapi huoxian/dongtai-openapi:latest
```


### 文档
- [官方文档](https://huoxianclub.github.io/LingZhi/#/)
- [快速体验](http://aws.iast.huoxian.cn:8000/login)
