## 电商导购助手
一个web端的电商导购助手，能够通过对话来帮助用户选购手机、电脑。后端运行环境为`Node.js`+`Python`,使用的机器学习模型由`Tensorflow.js`与`Python`训练而来。

### 主要文件
 - *./server.py*
 
    后端对话管理服务器入口文件

 - *./dialogManager.py*
 
    后端顶层对话管理模块

 - *./phoneparam.sql*

    数据库手机产品信息表

 - *./app/backend/NLU/*

    NLU模块，包括意图识别、关系抽取

 - *./app/backend/NLU/NLU_service.py*
 
    NLU服务器入口

 - *./templates/*
 
    前端页面文件
