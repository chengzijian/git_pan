# coding:utf-8

from multiprocessing import Process

from function.BuildProjects import startBuildProjects

if __name__ == "__main__":
    p0 = Process(target=startBuildProjects)
    p0.start()
    p0.join()
