# -*- coding: UTF-8 -*-
from urllib.parse import urlsplit

import requests
from lxml import etree

import queue
import threading
from os.path import basename

'''
 下载apk至本地
'''
# Jenkins 服务地址
TARGET_HOST = "http://192.168.31.95:8080/"

# Develop
PROJECT_NAMES = ["MeMe-Android-Develop", "MeMe-Android-Release", "MeMe-Android-Tinker"]

# apk存放路径
DOWNLOAD_FOLDER = "download/"


def url2name(url):
    return basename(urlsplit(url)[2])


class download(threading.Thread):
    def __init__(self, que):
        threading.Thread.__init__(self)
        self.que = que

    def run(self):
        while True:
            if not self.que.empty():
                print('-----%s------' % (self.name))
                # os.system('wget ' + self.que.get())

                url = self.que.get()
                chrome = 'Mozilla/5.0 (X11; Linux i86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
                headers = {'User-Agent': chrome}
                filename = url.split('/')[-1].strip()
                print(filename, "开始下载")
                r = requests.get(url.strip(), headers=headers, stream=True)
                filename = DOWNLOAD_FOLDER + filename
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            f.flush()
                print(filename, "下载完成")
            else:
                break


def startDown(param, select, num):
    if not isinstance(param, list):
        param = param.split(' ')
    que = queue.Queue()
    for l in param:
        url = '%sjob/%s/%s/artifact/bakApk/' % (TARGET_HOST, PROJECT_NAMES[select], l.strip())
        r = requests.get(url)
        if r.ok:
            root = etree.HTML(r.text)
            trs = root.xpath(".//div[@class='dirTree']/table/tr")
            if len(trs):
                filename = trs[0].xpath(".//td/a")[0].attrib['href']
                que.put(url + filename)
        else:
            print('#%s 号文件不存在' % l.strip())

    for i in range(num):
        d = download(que)
        d.start()


if __name__ == "__main__":
    # 参数1 要下载的apk build编号
    # 参数2 对应的project编号
    # 参数3 开启的线程数
    startDown(['691', '692', '693', '695'], 2, 10)
