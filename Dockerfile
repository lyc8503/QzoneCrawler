FROM python:3.9.7-slim-bullseye

MAINTAINER lyc8503 lyc8503@foxmail.com

# 挂载位置
VOLUME /download

# 修改时区
ENV TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive

RUN ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

# 安装依赖
RUN Deps="chromium-driver" \
    && mv /etc/apt/sources.list /etc/apt/sources.list.bak \
    && echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye main contrib non-free" > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install $Deps --no-install-recommends --no-install-suggests -y  \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /etc/apt/sources.list \
    && mv /etc/apt/sources.list.bak /etc/apt/sources.list


RUN pip3 install requests selenium pillow apscheduler tenacity opencv-python-headless numpy --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple


# 添加文件
COPY ./*.py /qzone/

WORKDIR /qzone/

ENTRYPOINT python3 -u main.py