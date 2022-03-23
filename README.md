# control-Nao-with-NLP
基于自然语言处理控制Nao型仿人机器人
## 环境配置
开发环境：
1. Windows10
2. Webots2021
3. Pycharm2019
4. HanLP1.x
5. python3.7  

### Webots
　　由于本次实验采用python语言，故首先应在Webots中将编程语言切换为Python，方法为：在webots软件中更改python command（Tools->Preferences->Python command）参数的内容为python.exe文件所在目录。  

　　由于本实验采用pycharm集成开发平台，故需要探究Webots与pycharm结合，[官方文档](https://cyberbotics.com/doc/guide/using-your-ide)有关于这的详细描述。下面介绍本工程在解决这个问题时的步骤：  
- (1)用pycharm打开所要控制机器人的controller中python文件的目录。  
- (2)adw 点击Add Content Root（File->Setting->Project->Project Structure->Add Content Root），选择 "WEBOTS_HOME/lib/controller/python37(python38等其他版本)" 文件夹。此时工作目录刷新并产生一个新的名为python37的文件夹。  
- (3) 点击Edit Configurations（Run->Edit Configurations），点击加号，选择python，设置两个参数：  
  - (i) Script Path：将要运行的python文件的目录（含该文件）；  
  - (ii) Environments Variables："PATH=WEBOTS_HOME\lib\controller\;WEBOTS_HOME\msys64\mingw64\bin\cpp"（文档中PATH还有一条为PATH=WEBOTS_HOME\msys64\mingw64\bin\，但是添加不上，目前没发现有什么影响）。

>备注：  
>+ 第(3)(ii)步的可以解决找不到_controller.pyd模块的错误。  
>+ 详细见webots官方文档Development Environments\Using your IDE。


### HanLP
　　见[文档](https://pypi.org/project/pyhanlp/)。  
　　本人在安装HanLP时确实遇到一些问题，但因为缺乏详细记录，无法考证或复原这些问题及它们的解决办法，但应该难度不大，请读者自行解决并引以为戒。 



## 命令测试

### 单一命令测试
　　**命令**：”机器人前进。“

　　**测试视频**：[哔哩哔哩链接](https://www.bilibili.com/video/BV1TL4y1g7Zv?spm_id_from=333.999.0.0)

### 组合命令测试
　　**命令**：”机器人前进2米，然后左转60度。“

　　**测试视频**：[哔哩哔哩链接](https://www.bilibili.com/video/BV1Z44y1J7Na?spm_id_from=333.999.0.0)
　　

### 带有目标方位的命令测试
　　**命令**：“机器人前进到桌子的左边。”

　　**测试视频**：[哔哩哔哩链接](https://www.bilibili.com/video/BV1C3411L7cM?spm_id_from=333.999.0.0)