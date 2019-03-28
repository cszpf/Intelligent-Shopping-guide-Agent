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

手机领域的对话机器人入口文件，需要实现一个dialog_phone类来进行对话管理。必须实现几个供全局对话管理类调用的接口，接口详情见`./models/phone/dialog_phone.py`文件

### ./models/phone/NLU

nlu模块的文件夹，需要实现nlu_interface.py文件来提供接口


### ./models/phone/NLU/nlu_interface.py

实现基本的nlu接口，需要的接口根据不同对话系统而不同。
需要在全局范围内创建一个nlu的类并加载好模型，避免每一次调用都需要载入模型和初始化


## 调整方案
### nlu部分（俊生:手机的nlu部分）
将所有nlu的代码集中到对应的NLU文件夹中，并抽象出nlu_interface.py的接口文件

### dialog部分（志成,星宇）
将所有对话系统的文件集中到对应的文件夹中，并且实现供上层调用的接口

### tensorflow.js的前端意图识别部分（星宇）
抛弃原有的使用nodejs服务器来进行模型加载和预测的方式，改为前端在浏览器直接加载模型。