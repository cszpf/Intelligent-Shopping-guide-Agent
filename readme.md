## 文件结构
### ./server.py

启动对话服务器的文件

### ./dialog_manager.py

全局对话管理文件

### ./static

flask的静态资源文件夹,包括js css等

### ./templates

flask的前端页面文件夹

### ./models

存放不同的对话系统的文件夹，分为computer,phone,camera三个子文件夹，每个文件夹的结构类似

### ./models/phone/dialog_phone.py

手机领域的对话机器人入口文件

### ./models/phone/data/

手机领域的静态资源文件

### ./models/NLU

nlu模块的文件夹


### ./models/NLU/nlu_interface.py

实现基本的nlu接口，需要的接口根据不同对话系统而不同。

### ./sql
数据库文件
