# -*- coding: UTF-8 -*-
import os
import sys
import time

import jenkins
import requests
import xlrd

from lxml import etree

# Jenkins 服务地址
TARGET_HOST = "http://192.168.31.95:8080/"

# Develop
PROJECT_NAMES = ["MeMe-Android-Develop", "MeMe-Android-Release", "MeMe-Android-Tinker"]


class BuildProjects(object):
    def __init__(self):
        self.server = jenkins.Jenkins(TARGET_HOST, timeout=5)
        self.log_list = []
        self.lines = []
        self.select = int(sys.argv[1])

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
        url = '%sjob/%s/buildHistory/ajax' % (TARGET_HOST, PROJECT_NAMES[self.select])
        r = requests.get(url, headers={'n': str(number[0])})
        if r.ok:
            root = etree.HTML(r.text)
            trs = root.xpath(".//table/tr")
            if len(trs):
                log_list = []
                for tr in trs:
                    build_desc = tr.xpath(".//div[@class='pane desc indent-multiline']")
                    display_name = ''
                    details = ''
                    build_progress = ''
                    if len(build_desc):
                        # 不为空说明，当前是构建状态
                        display_name = tr.xpath(".//div[@class='pane build-name']/a")[0].text
                        details = build_desc[0].text
                        tooltip = tr.xpath(".//a[@class='build-status-link']/img")[0].attrib['tooltip']
                        tooltip = tooltip[0: tooltip.index('>')].strip()
                        if tooltip == u'In progress':
                            td = tr.xpath(".//div[@class='pane build-details']/table/tbody/tr/td")
                            build_progress = u'（Building %s）' % td[0].attrib['style'].replace('width:', '').replace(';', '')
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

                # 当所有任务都被取消的话，不再进行轮询
                count = 0
                for log in log_list:
                    if 'Building' in log:
                        count = count + 1
                if count <= 0:
                    print('全部构建完成')
                    return None

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
        job_info = self.server.get_job_info(PROJECT_NAMES[self.select])
        number = job_info['lastBuild']['number']  # 最后的任务
        if tempNumber == number:
            print('程序关闭')
            return
        # 每5秒更新一次进度信息
        self.waitfor(self.conCurrentProgress, 5, number)

        time.sleep(3)
        self.updateAndPrintLogMsg(number)

    def run(self):
        path = os.path.dirname(os.path.realpath(__file__)).replace('/function', '')
        workbook = xlrd.open_workbook(path + r'/file/apps.xlsx')

        sheet_name = workbook.sheet_names()[self.select]
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
            for row in range(1, len(self.lines)):
                params = []
                version = ''
                appicon = ''
                appname = ''
                xiaomi = ''
                for col in range(0, cols):
                    if self.lines[0][col] == 'ParamTag':
                        version = "%s_" % self.lines[row][col]
                    if self.lines[0][col] == 'ParamAppIcon':
                        appicon = self.lines[row][col]
                    if self.lines[0][col] == 'ParamAppName':
                        appname = self.lines[row][col]
                    if self.lines[0][col] == 'ParamXiaomiHidden':
                        xiaomi = '小米登陆：%s' % self.lines[row][col]
                    params.append({"name": self.lines[0][col], "value": self.lines[row][col]})

                name = '%s%s_%s_%s' % (version, appicon, appname, xiaomi)
                url = '%sjob/%s/build?delay=0sec' % (TARGET_HOST, PROJECT_NAMES[self.select])
                data = {'json': '{"parameter": %s, "statusCode": "303", "redirectTo": "."}' % str(params).replace('\'',
                                                                                                                  '"')}  # 定义参数
                #print(name, data)
                res = requests.post(url, data=data)
                if res.ok:
                    print('构建 %s 成功' % name)
                else:
                    print('构建 %s 失败' % name)

            #### 到此为止，所有任务均已创建成功
            # 开始打印日志
            time.sleep(3)
            self.updateAndPrintLogMsg(0)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['0', '1', '2']:
        crawl = BuildProjects()
        crawl.run()
    else:
        print('需要参数（0 构建Develop，1 构建Release，2 构建tinker）')