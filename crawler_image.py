#--coding:utf-8--
# @Time    : 2020/12/19/019 0:05
# @Author  : panyuangao
# @File    : crawler_image.py
# @PROJECT : My_crawler

import requests
import re,os
import queue
from bs4 import BeautifulSoup
from threading import Thread

def get_download_img_url(url): #获取图片下载url
    homePage = re.search(r"(http[s]*://[a-z]+.[a-z0-9]+.com)/", url).group(1) #提取首页链接，用于拼接url
    r = requests.get(url,timeout=60)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, "html.parser") # 把网页的html内容当成一个树来解析。html.parser:表示用html解析器
    try:
        data_download_img = soup.find_all("a",attrs={'id':'img'}) #获得图片下载的a标签（图片下载页才能获取到）
        if data_download_img:
            download_img_url_relative = re.search('src="(.+?)"',str(data_download_img[0])).group(1) #获取下载相对url
            download_img_url = homePage + download_img_url_relative #将下载链接拼接成绝对url
            return download_img_url
    except Exception as e:
        print(e)

def downloadImage(url,image_dir,image_no): #将图片下载至本地
    try:
        r = requests.get(url,timeout=60) #设置超时时间
        image_type = url.split(".")[-1] #获取图片的后缀名
        image_path = image_dir + "\\" + str(image_no) + '.' + image_type #拼接图片下载至本地的绝对路径
        with open(image_path,"wb") as fp:
            fp.write(r.content) #保存图片至本地
        print("图片【%s】下载成功，保存路径:【%s】" %(url,image_path))
    except Exception as e:
        print(e)
        print("图片下载失败",url)


def get_img_page_url(url): # 获取列表页url和图片下载页面url
    homePage = re.search(r"(http[s]*://[a-z]+.[a-z0-9]+.com)/", url).group(1) #提取首页链接，用于拼接url
    r = requests.get(url,timeout=60)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, "html.parser") # 把网页的html内容当成一个树来解析。html.parser:表示用html解析器
    img_page_urls = []
    try:
        data_a = soup.find_all("a") #获取所有a标签的内容
        for a in data_a:
            url = a["href"] # 遍历获取a标签中的相对url
            # 根据url的规则，只处理列表页url和图片下载页面url
            if url.endswith(".html") and url.startswith("/tupian") or url.startswith("/index_"):
                img_page_url = homePage + url #将相对url拼成绝对url
                img_page_urls.append(img_page_url)
        return img_page_urls
    except Exception as e:
        print(e)

def task(queue): #任务函数
    global res_urls
    global image_dir
    global image_no
    while not queue.empty():
        url = queue.get()
        try:
            download_img_url = get_download_img_url(url) # 获取图片下载url
            if download_img_url and download_img_url not in res_urls:
                image_no += 1
                downloadImage(download_img_url, image_dir, image_no)  # 下载图片到本地
                res_urls.append(download_img_url)
        except Exception as e:
            print("获取图片下载url失败,页面url为：",url)
            print(e)

        try:
            img_page_urls = get_img_page_url(url)  #获取列表页url和图片下载页面url
            while img_page_urls:
                img_page_url = img_page_urls.pop()
                if img_page_url not in res_urls: #通过全局变量res_urls,防止url被重复添加
                    queue.put(img_page_url) #将获取到的图片下载页面url和列表页url，添加到队列中
                    res_urls.append(img_page_url)
        except Exception as e:
            print("获取列表所有图片详请页面url失败,列表url为：", url)
            print(e)

if __name__ == '__main__':
    queue = queue.Queue() #队列，用来存放
    res_urls = [] #存放所有url，用于去重
    image_no = 0 #图片保存本地的编号（文件名）
    image_dir = r'g:\image' #图片保存本地的目录
    if not os.path.exists(image_dir): #判断目录是否存在，不存在则创建
        os.makedirs(image_dir)

    url_image_page = 'http://pic.netbian.com/index.html' #种子页面url
    queue.put(url_image_page) #将种子页面url放入队列中

    t_lst = []
    for i in range(100): #创建100个线程，执行任务函数
        t = Thread(target=task,args=(queue,))
        t_lst.append(t)
        t.start()
    for t in t_lst: #主线程等待所有子线程结束后，主线程才结束，程序退出。
        t.join()
