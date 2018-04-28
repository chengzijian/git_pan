# coding=utf-8
import os
import sys
import time

import jenkins
import requests
import xlrd

from config import TARGET_HOST, PROJECT_NAME
from lxml import etree


def startBuildProjects():
    crawl = BuildProjects()
    crawl.run()


class BuildProjects(object):
    def __init__(self):
        self.server = jenkins.Jenkins(TARGET_HOST, timeout=5)
        self.log_list = []
        self.lines = []

    def waitfor(self, getter, interval=0.5, *args):
        while True:
            if getter(args) is None:
                return
            else:
                time.sleep(interval)

    # 输出日志信息
    def printOutputLogs(self):
        if len(self.log_list):
            for log in self.log_list:
                sys.stdout.write('#%s ' % str(log[0]))
                sys.stdout.write(log[1].encode("utf8"))
                sys.stdout.write(log[3])
                sys.stdout.write('\r')
            sys.stdout.flush()
        else:
            sys.stdout.write(u"没有日志")
            sys.stdout.flush()

    # 更新构建任务的进度并打印
    def updateAndPrintLogMsg(self, tempNumber=None):
        job_info = self.server.get_job_info(PROJECT_NAME)
        number = job_info['lastBuild']['number']  # 最后的任务
        if tempNumber == number:
            print 'done'
            return
        # 每5秒更新一次进度信息
        self.waitfor(self.conCurrentProgress, 5, number)

        self.updateLogs(number, 100)
        self.printOutputLogs()

        time.sleep(3)
        self.updateAndPrintLogMsg(number)

    # 更新日志信息
    def updateLogs(self, number, progress):
        if len(self.log_list):
            for log in self.log_list:
                if log[0] == number[0]:
                    log[3] = '(%s%%)  ' % progress

    '''
        获取指定任务的执行进度
    '''

    def conCurrentProgress(self, number):
        url = '%sjob/%s/buildHistory/ajax' % (TARGET_HOST, PROJECT_NAME)
        r = requests.post(url, headers={'n': str(number)})
        if r.ok:
            root = etree.HTML(r.text)
            td = root.xpath(".//tbody/tr/td")
            if td and len(td) == 2:
                # print td[1].attrib['style'].replace('width:', '')
                progress = td[0].attrib['style'].replace('width:', '').replace('%;', '')
                self.updateLogs(number, progress)
                self.printOutputLogs()
                return progress
        return None

    def run(self):
        path = os.path.dirname(os.path.realpath(__file__)).replace('/function', '')
        workbook = xlrd.open_workbook(path + r'/file/apps.xlsx')
        sheet_name = workbook.sheet_names()[0]
        sheet = workbook.sheet_by_name(sheet_name)
        rows = sheet.nrows
        for row in range(0, rows):
            line = sheet.row_values(row)  # 获取行内容
            if not line[0].strip() or line[0].startswith('##') or not line[1]:
                # 过滤掉无用的行
                continue

            if line not in self.lines:
                self.lines.append(line)

        if len(self.lines):
            cols = len(self.lines[0])  # 获取列数
            # 等待至少30秒的时间让Jenkins准备好
            if self.server.wait_for_normal_op(30):
                # Jenkins已经运行
                for row in range(1, len(self.lines)):
                    params = []
                    for col in range(0, cols):
                        params.append(
                            {"name": self.lines[0][col].encode("utf8"), "value": self.lines[row][col].encode("utf8")})

                    number = self.server.build_job(PROJECT_NAME, parameters={"parameter": params})
                    # 创建任务日志
                    job_info = self.server.get_job_info(PROJECT_NAME)
                    build_info = self.server.get_build_info(PROJECT_NAME, number)
                    self.log_list.append([job_info['lastBuild']['number'], build_info['description'],
                                          build_info['building'], u'排队中'])

                # 打印日志信息
                self.printOutputLogs()

                # 更新构建任务的进度并打印
                self.updateAndPrintLogMsg(0)
            else:
                print("连接 Jenkins 失败！")


if __name__ == "__main__":
    startBuildProjects()
