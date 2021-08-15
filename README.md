项目基于爬虫实现了一个简单的[新浪新闻](https://news.sina.com.cn)客户端。

# Installation

## Conda 环境

本项目使用 Python 3.7.10 作为运行环境

```shell
conda create -n sina python=3.7.10
```

## Bitarray

第三方模块 pybloom 需要预装 Bitarray 才能使用。根据 [PyPi](https://pypi.org/project/bitarray/) 文档的指导， Windows 用户可以从 [Chris Gohlke](https://www.lfd.uci.edu/~gohlke/pythonlibs/#bitarray) 处下载 whl 文件 `bitarray-2.2.5-cp37-cp37m-win_amd64.whl` ，然后使用 pip 安装

```shell
pip install bitarray-2.2.5-cp37-cp37m-win_amd64.whl
```

## 其他依赖

为了加速下载，我们使用了清华 Pypi 镜像

```shell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

# Get Started

执行以下命令即可启动

```shell
python main.py
```

# Clean Up

每次运行结束后，会生成一些临时文件。如果不清理这些文件，下次运行的结果可能会受到影响，因此需要执行清理脚本

```shell
.\clean.ps1
```