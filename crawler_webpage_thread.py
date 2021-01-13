# -*- coding: utf-8 -*
'''
弄一个爬虫：
种子页：一个首页，首页有10个链接。
1 访问首页，获取源码html
2 使用正则或者其他方式获取所有的绝对地址链接，存到一个list里面
3 遍历list，加入到队列中
4 多线程从队列中取数据，一次去一个绝对地址链接，重复上面1-3步，
  这样就可以实现爬虫的逻辑，从一个页面为起点，爬所有发现的链接页面。
'''

import re
import requests
import queue
from threading import Thread
from util import mysql

def get_url_content(url):
    request = requests.get(url,timeout=5)
    return request.text

def get_page_msg(url):
    page_content = get_url_content(url)  # 获取URL中的源码内容
    page_url_list = re.findall(r'href="(http.+?)"', page_content)  # 从源码内容中，使用正则提取出所有的URL
    page_title = re.search(r'<title>(.+?)</title>', str(page_content), re.S)  # 通过正则获取页面的标题
    page_text = ''.join(re.findall(r'<p>(.+?)</p>', page_content))  # 通过正则，或获取页面中的正文
    if page_title and page_text:
        page_title = page_title.group(1).strip()
        page_text = "".join(re.split(r"<.+?>", page_text)).strip()  # 使用正则切割，将正文中的标签去掉
        page_text = page_text.replace('"', "'")  # 将正文中的双引号替换为单引号，以防落库时SQL报错

    return page_url_list,str(page_title),str(page_text)

def get_html(queue,mysql,crawl_kw,crawl_num): #获取url页面上的所有url链接
    while not queue.empty():
        global RES_URL_LIST,CURRENT_URL_COUNT
        if len(RES_URL_LIST) >= crawl_num: #判断爬取数据的数量是否已经足够
            print(len(RES_URL_LIST))
            print("总数达到要求，提前结束")
            return
        url = queue.get()   #从队列中获取url
        CURRENT_URL_COUNT += 1
        print("队列中还有【%s】个URL，当前爬取的是第【%s】个页面，URL：【%s】" %(queue.qsize(),CURRENT_URL_COUNT,url))

        page_msg = get_page_msg(url)
        page_url_list = page_msg[0]
        page_title = page_msg[1]
        page_text = page_msg[2]

        if page_title.find(crawl_kw) != -1 or page_text.find(crawl_kw) != -1: #标题或正文中包含关键字，才往下走
            if len(page_title) > 20 and len(page_text) > 300 :
                if url not in RES_URL_LIST: #判断url是否添加过，防止数据重复落库
                    sql = 'INSERT INTO webpage(url,title,text) VALUES("%s","%s","%s")' % (url, page_title, page_text)
                    mysql.insert(sql)
                    RES_URL_LIST.append(url) #将url添加到全局变量RES_URL_LIST，用于防止数据重复落库
                    print("关键字【%s】，目前已爬取到数据【%s】条，距离目标还差【%s】条，当前落库的URL为【%s】" %(crawl_kw,len(RES_URL_LIST),crawl_num-len(RES_URL_LIST),url))

        while page_url_list:
            url = page_url_list.pop()
            if url not in RES_URL_LIST:
                queue.put(url.strip()) #将源码中的所有url放到队列中
    print("队列没有东西，退出了")


if __name__ == '__main__':
    RES_URL_LIST = []
    CURRENT_URL_COUNT = 0
    queue = queue.Queue()
    mysql = mysql.MySQL()

    home_page_url = "https://www.sohu.com/"  #要爬取数据的首页
    crawl_kw = "疫苗"     #要爬取数据的关键字
    crawl_num = 20   #要爬取数据的目标数量

    queue.put(home_page_url)  # 将首页的url放进队列中
    for i in range(200):
        pg = Thread(target=get_html,args=(queue,mysql,crawl_kw,crawl_num))
        pg.start()
        pg.join()
