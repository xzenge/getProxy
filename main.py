# -*- coding=utf-8 -*-
from urllib import request
import time, datetime
from lxml import etree
import sqlite3,time
import pymysql

class ProxyDao(object):
    def getId(self):
        return  self.id
    def setId(self, val):
        self.id = val

    def getDate(self):
        return  self.date
    def setDate(self, val):
        self.date = val

    def getIp(self):
        return self.ip
    def setIp(self, val):
        self.ip = val

    def getPort(self):
        return self.port
    def setPort(self, val):
        self.port = val

    def getType(self):
        return self.type
    def setType(self, val):
        self.type = val


def createConnect():
    conn = pymysql.connect(host='localhost', user='root', passwd='root', db='proxy', port=3306, charset='utf8')
    cur = conn.cursor()  # 获取一个游标
    return conn,cur

def closeConnect(cur, conn):
    cur.close()  # 关闭游标
    conn.close()  # 释放数据库资源

class getProxy():

    def __init__(self, conn, cur):
        self.user_agent = "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)"
        self.header = {"User-Agent": self.user_agent}
        self.dbname="proxy.db"
        self.now = time.strftime("%Y-%m-%d")
        self.conn = conn
        self.cur = cur

    def getContent(self, num):
        nn_url = "http://www.xicidaili.com/nn/" + str(num)
        #国内高匿
        req = request.Request(nn_url, headers=self.header)
        resp = request.urlopen(req, timeout=10)
        content = resp.read()
        et = etree.HTML(content)
        result_even = et.xpath('//tr[@class=""]')
        result_odd = et.xpath('//tr[@class="odd"]')
        #因为网页源码中class 分开了奇偶两个class，所以使用lxml最方便的方式就是分开获取。
        #刚开始我使用一个方式获取，因而出现很多不对称的情况，估计是网站会经常修改源码，怕被其他爬虫的抓到
        #使用上面的方法可以不管网页怎么改，都可以抓到ip 和port
        for i in result_even:
            t1 = i.xpath("./td/text()")[:2]
            print("IP:%s\tPort:%s" % (t1[0], t1[1]))
            if self.isAlive(t1[0], t1[1]):

                proxy = ProxyDao()
                proxy.setDate(self.now)
                proxy.setIp(t1[0])
                proxy.setPort(t1[1])
                proxy.setType(0)
                self.insert_db(proxy)
        for i in result_odd:
            t2 = i.xpath("./td/text()")[:2]
            print("IP:%s\tPort:%s" % (t2[0], t2[1]))
            if self.isAlive(t2[0], t2[1]):
                proxy = ProxyDao()
                proxy.setDate(self.now)
                proxy.setIp(t1[0])
                proxy.setPort(t1[1])
                proxy.setType(0)
                self.insert_db(proxy)


    def insert_db(self,poxy):
        try:
            insert_db_cmd='''
            INSERT INTO proxy (date,ip,port,type) VALUES ('%s','%s','%s','%d');
            ''' %(poxy.getDate(),poxy.getIp(),poxy.getPort(),poxy.getType())
            self.cur.execute(insert_db_cmd)
        except:
            print("Error to open database%" %self.dbname)

    def loop(self,page=5):
        for i in range(1,page):
            self.getContent(i)

    #查看爬到的代理IP是否还能用
    def isAlive(self,ip,port):
        proxy={'http':ip+':'+port}
        print(proxy)

        #使用这个方式是全局方法。
        proxy_support = request.ProxyHandler(proxy)
        opener = request.build_opener(proxy_support)
        request.install_opener(opener)
        #使用代理访问腾讯官网，进行验证代理是否有效
        test_url = "http://www.qq.com"
        req = request.Request(test_url,headers=self.header)
        try:
            #timeout 设置为10，如果你不能忍受你的代理延时超过10，就修改timeout的数字
            resp = request.urlopen(req,timeout=10)

            if resp.code==200:
                print("work")
                return True
            else:
                print("not work")
                return False
        except :
            print("Not work")
            return False

    #查看数据库里面的数据时候还有效，没有的话将其纪录删除
    def check_db_pool(self):
        query_cmd='''
        select id,ip,port from proxy;
        '''
        cursor=self.cur.execute(query_cmd)
        for row in cursor:
            if not self.isAlive(row[1],row[2]):
                #代理失效， 要从数据库从删除
                delete_cmd='''
                delete from proxy where id='%d'
                ''' %row[0]
                print("delete IP %s in db" %row[0])
                self.cur.execute(delete_cmd)

if __name__ == "__main__":
    now = datetime.datetime.now()
    print("Start at %s" % now)
    conn,cur = createConnect()#打开数据库连接
    obj=getProxy(conn, cur)
    obj.loop(5)
    obj.check_db_pool()
