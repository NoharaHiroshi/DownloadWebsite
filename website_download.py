# encoding=utf-8

import requests
import ssl
import re
import os
import socket
import traceback


class WebsiteDownload:
    def __init__(self, web_url):
        self.info = web_url.split('://')
        self.web_url = web_url
        if len(self.info) == 2:
            self.domain = self.info[1].split('/')[0]
            self.request_type = self.info[0]
            if self.request_type == 'https':
                self.port = 443
            else:
                self.port = 80
        else:
            print u'当前请求URL不符合规则，请输入完整URL，例如：https://www.baidu.com'
            return
        self.ip = socket.gethostbyname(self.domain)
        # 设置静态资源路径
        self.download_dir = os.path.join(os.path.dirname(__file__).replace('/', '\\'), self.domain)
        # 设置可下载文件的后缀名
        self.download_type_list = ['js', 'css', 'scss', 'png', 'jpg', 'jpeg', 'gif', 'ico']

    def main(self):
        # 初始化目录结构
        if not os.path.exists(self.download_dir):
            os.mkdir(self.download_dir)
        self.download_pages()

    def get_cert_dir(self):
        cert_dir = os.path.join(self.download_dir, 'cert.pem')
        if os.path.exists(cert_dir):
            return cert_dir
        else:
            cert = ssl.get_server_certificate(addr=(self.ip, self.port))
            with open(cert_dir, 'ab') as f:
                f.write(cert)
                f.flush()
            return cert_dir

    @classmethod
    def store_file_content(cls, download_file_src, file_dir, times=0):
        """
        :param download_file_src: 静态资源url
        :param file_dir: 下载目录dir
        :param times: 重试下载次数
        :return:
        """
        try:
            response = requests.get(download_file_src)
            if str(response.status_code) == '200':
                content = response.content
                if not os.path.exists(file_dir):
                    print u'当前正在下载文件：%s' % file_dir
                    with open(file_dir, 'ab') as f:
                        f.write(content)
                        f.flush()
            else:
                times += 1
                print u'重新尝试下载，重试次数：%s' % times
                if times == 10:
                    print u'下载文件：%s， 失败' % file_dir
                    return
                cls.store_file_content(download_file_src, file_dir, times)
        except Exception as e:
            print traceback.format_exc(e)

    def create_assets_path_dir(self, url):
        """
        :param url: 静态文件的url
        :return: 返回本地目录的路径
        """
        if url[0] == '/':
            path_list = url.split('/')
            path_list_len = len(path_list)
            for i in range(1, path_list_len-1):
                tmp_path = '/'.join(path_list[1:i+1])
                _path = os.path.join(self.download_dir, tmp_path)
                if not os.path.exists(_path):
                    os.mkdir(_path)
            return os.path.join(self.download_dir, url[1:])

    def convert_and_download_assets_src(self, content):
        """
        查找当前页面代码中的静态文件并下载，并变更静态文件的路径
        :param content: 当前页面代码
        :return: 变更静态文件链接后的页面代码
        """
        # 获取url类型
        for url_type in ['src', 'href']:
            url_list = re.findall('%s=.+\.\w+' % url_type, content)
            tmp_url_list = list()
            for src in url_list:
                _src = re.sub(r"""%s="|'""" % url_type, '', src)
                if len(_src):
                    if url_type == 'href':
                        if _src[0] == '#':
                            continue
                    if _src not in tmp_url_list:
                        tmp_url_list.append(_src)
                    else:
                        continue
                    # 文件后缀名
                    f_type = _src.split('.')[-1]
                    if f_type not in self.download_type_list:
                        continue
                    # 获取静态资源url
                    if _src[0] == '/':
                        download_file_src = self.request_type + '://' + self.domain + _src
                    else:
                        download_file_src = _src
                    # 更改静态资源相对路径
                    download_file_dir = self.create_assets_path_dir(_src)
                    # 下载静态资源
                    WebsiteDownload.store_file_content(download_file_src, download_file_dir)
                    content = content.replace(_src, '.%s' % _src)
        return content

    # 主页入口
    def download_pages(self):
        response = requests.get(self.web_url)
        if str(response.status_code) == '200':
            content = response.content
            content = self.convert_and_download_assets_src(content)
            index_dir = os.path.join(self.download_dir, 'index.html')
            if not os.path.exists(index_dir):
                with open(index_dir, 'ab') as f:
                    f.write(content)
                    f.flush()
        else:
            print u'获取页面失败'

if __name__ == '__main__':
    url = r'http://www.blockfundchain.cn'
    wd = WebsiteDownload(url)
    wd.main()