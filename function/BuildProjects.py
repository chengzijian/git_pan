# coding=utf-8
from config.config import PROJECT_NAME, TARGET_HOST
import os
import xlrd
import requests
import json
import jenkins
import sys
import time
import gevent
from gevent.pool import Pool

from lxml import etree

'''
这个类的作用是解析xls文件
'''


def startBuildProjects():
    crawl = BuildProjects()
    crawl.run()


class BuildProjects(object):
    proxies = set()

    def __init__(self):
        self.server = jenkins.Jenkins(TARGET_HOST)

    def run(self):
        lines = []
        workbook = xlrd.open_workbook(os.path.abspath('..') + r'/config/apps.xlsx')
        sheet_name = workbook.sheet_names()[0]
        sheet = workbook.sheet_by_name(sheet_name)
        rows = sheet.nrows
        for row in range(0, rows):
            line = sheet.row_values(row)  # 获取行内容
            if not line[0].strip() or line[0].startswith('##') or not line[1]:
                # 过滤掉无用的行
                continue

            if line not in lines:
                lines.append(line)

        if len(lines):
            cols = len(lines[0])  # 获取列数
            for row in range(1, len(lines)):
                params = []
                for col in range(0, cols):
                    params.append({"name": lines[0][col].encode("utf8"), "value": lines[row][col].encode("utf8")})
                self.server.build_job(PROJECT_NAME, parameters={"parameter": params})


'''
    获取指定任务的执行进度
'''
def conCurrentProgress(id):
    url = '%sjob/%s/buildHistory/ajax' % (TARGET_HOST, PROJECT_NAME)
    r = requests.post(url, headers={'n': str(id)})
    if r.ok:
        root = etree.HTML(r.text)
        td = root.xpath(".//tbody/tr/td")
        if td and len(td) == 2:
            # print td[1].attrib['style'].replace('width:', '')
            return td[0].attrib['style'].replace('width:', '').replace('%;', '')
    return "-1"


if __name__ == "__main__":
    # startBuildProjects()
    print conCurrentProgress(386)


    # server = jenkins.Jenkins(TARGET_HOST, timeout=5)
    # # wait for at least 30 seconds for Jenkins to be ready
    # if server.wait_for_normal_op(30):
    #     # actions once running
    #     print("actions once running")
    #
    #     # last_build_number = server.get_job_info(PROJECT_NAME)['lastCompletedBuild']['number'] #获取最后完成的任务信息
    #     # build_info = server.get_build_info(PROJECT_NAME, last_build_number)
    #     # print build_info['displayName'], build_info['description'], build_info['building'], build_info['estimatedDuration']
    #
    #
    #     # queue_info = server.get_queue_info() #获取正在排队的任务信息
    #     # id = queue_info[0].get('id') # blocked
    #     # print id
    #     # server.cancel_queue(id) # 取消排队
    #
    #     job_info = server.get_job_info(PROJECT_NAME)
    #     print job_info['lastSuccessfulBuild']['url'] # 最后成功编译的任务
    #     print job_info['lastUnsuccessfulBuild']['url'] # 最后未成功编译的任务
    #     print job_info['lastFailedBuild']['url'] # 最后编译失败的任务
    #     print job_info['lastBuild']['url'] # 最后的任务
    #     print job_info['lastStableBuild']['url'] # 最后的编译成功稳定的任务
    #     print job_info['fullDisplayName'] # 项目名
    #     print job_info['inQueue'] # 是否在排队
    #     #print job_info['builds'] # 构建列表
    #     print job_info['nextBuildNumber'] # 下一个构建号，也可能在排队
    #
    #     print job_info['queueItem'] # 排队中的任务
    #     # u'task': {
    #     #              u'url': u'http://192.168.31.95:8080/job/MeMe-Android-Develop/',
    #     #              u'_class': u'hudson.model.FreeStyleProject',
    #     #              u'name': u'MeMe-Android-Develop'
    #     #          },
    #     # u'stuck': False,
    #     # u'url': u'queue/item/327/',
    #     # u'inQueueSince': 1524822982171,
    #     # u'why': u'Build #381 is already in progress (ETA:1 \u5206 58 \u79d2)',
    #     # u'buildable': False,
    #     # u'params': u'\nParamVersionName=\u5185\u6d4b\u7248\nParamAppIcon=\u732b\u5934\u56fe\u6807\nParamAppLaunchImage=\nParamAppName=\u4e48\u4e48\u76f4\u64ad\nParamTestMode=\u5f00\nParamIsGooglePlay=\u5426\nParamXiaomiHidden=\u663e\u793a\nParamHideLauncher=\u5426',
    #     # u'_class': u'hudson.model.Queue$BlockedItem',
    #     # u'buildableStartMilliseconds': 1524822982172,
    #     # u'id': 327,
    #     # u'blocked': True
    #
    #
    #
    #     print job_info
    # else:
    #     print("Jenkins failed to be ready in sufficient time")

    # last_build_number = server.get_job_info(PROJECT_NAME)['lastCompletedBuild']['number'] #获取最后完成的任务信息
    # build_info = server.get_build_info(PROJECT_NAME, last_build_number)
    # print build_info['displayName'], build_info['description'], build_info['building'], build_info['estimatedDuration']

    # queue_info = server.get_queue_info() #获取正在排队的任务信息
    # id = queue_info[0].get('id')
    # print id
    # server.cancel_queue(id)
