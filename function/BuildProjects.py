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

    '''
        获取指定任务的执行进度
    '''

    def conCurrentProgress(self, number):
        url = '%sjob/%s/buildHistory/ajax' % (TARGET_HOST, PROJECT_NAME)
        r = requests.get(url, headers={'n': str(number[0])})
        if r.ok:
            root = etree.HTML(r.text)
            trs = root.xpath(".//table/tr")
            if len(trs):
                log_list = []
                for tr in trs:
                    build_desc = tr.xpath(".//div[@class='pane desc indent-multiline']")
                    if len(build_desc):
                        # 不为空说明，当前是构建状态
                        display_name = tr.xpath(".//div[@class='pane build-name']/a")[0].text
                        details = build_desc[0].text
                        tooltip = tr.xpath(".//a[@class='build-status-link']/img")[0].attrib['tooltip']
                        tooltip = tooltip[0: tooltip.index('>')].strip()
                        if tooltip == u'In progress':
                            td = tr.xpath(".//div[@class='pane build-details']/table/tbody/tr/td")
                            build_progress = u'（%s）' % td[0].attrib['style'].replace('width:', '').replace(';', '')
                        elif tooltip == u'Success':
                            build_progress = u'（构建完成）'
                        elif tooltip == u'Aborted':
                            build_progress = u'（取消构建）'
                        elif tooltip == u'Failed':
                            build_progress = u'（构建失败）'
                        else:
                            build_progress = u'（%s）' % tooltip
                    else:
                        try:
                            display_name = tr.xpath(".//div[@class='display-name']")[0].text
                            details = tr.xpath(".//div[@class='pane build-details indent-multiline']")[0].text.strip()
                            build_progress = u'（排队中）'
                        except:
                            pass

                    log_list.append(u'%s %s %s' % (display_name, details, build_progress))

                if len(log_list):
                    log_list.reverse()
                    os.system('clear')
                    for log in log_list:
                        sys.stdout.write(log)
                        sys.stdout.write('\n')

                    sys.stdout.write('\r')
                    sys.stdout.flush()
                    return 'Success'
        return None

    # 更新构建任务的进度并打印
    def updateAndPrintLogMsg(self, tempNumber=None):
        job_info = self.server.get_job_info(PROJECT_NAME)
        number = job_info['lastBuild']['number']  # 最后的任务
        if tempNumber == number:
            print 'done'
            return
        # 每5秒更新一次进度信息
        self.waitfor(self.conCurrentProgress, 5, number)

        time.sleep(3)
        self.updateAndPrintLogMsg(number)

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

                    self.server.build_job(PROJECT_NAME, parameters={"parameter": params})

                #### 到此为止，所有任务均已创建成功
                # 开始打印日志
                self.updateAndPrintLogMsg(0)
            else:
                print("连接 Jenkins 失败！")


if __name__ == "__main__":
    startBuildProjects()
