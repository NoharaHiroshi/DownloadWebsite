# encoding=utf-8

import requests
import ssl
import re
import os
import socket


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
        self.download_dir = os.path.join(os.path.dirname(__file__).replace('/', '\\'), self.domain)
        self.static_dir = os.path.join(self.download_dir, 'static')
        self.js_dir = os.path.join(self.static_dir, 'js')
        self.css_dir = os.path.join(self.static_dir, 'css')
        self.img_dir = os.path.join(self.static_dir, 'img')

    def main(self):
        # 初始化目录结构
        self.init_dir()
        self.download_pages()

    def init_dir(self):
        if not os.path.exists(self.download_dir):
            os.mkdir(self.download_dir)
        if not os.path.exists(self.static_dir):
            os.mkdir(self.static_dir)
        if not os.path.exists(self.css_dir):
            os.mkdir(self.css_dir)
        if not os.path.exists(self.js_dir):
            os.mkdir(self.js_dir)
        if not os.path.exists(self.img_dir):
            os.mkdir(self.img_dir)

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
    def store_file_content(cls, content, file_dir):
        print u'当前正在下载文件：%s' % file_dir
        if not os.path.exists(file_dir):
            with open(file_dir, 'w') as f:
                f.write(content)
                f.flush()

    @classmethod
    def convert_and_download_assets_src(cls, content):
        src_list = re.findall('src=.+\.\w+', content)
        href_list = re.findall('href=.+\.\w+', content)
        for src in src_list:
            _src = re.sub(r"""src="|'""", '', src)
            if len(_src):
                print _src
                f_type = _src.split('.')[-1]
                if _src[0] == '/':
                    pass

    def download_pages(self):
        if self.request_type == 'https':
            cert_dir = self.get_cert_dir()
            response = requests.get(self.web_url, cert=cert_dir)
        else:
            response = requests.get(self.web_url)
        if str(response.status_code) == '200':
            page = response.content
            WebsiteDownload.convert_and_download_assets_src(page)
            index_dir = os.path.join(self.download_dir, 'index.html')
            WebsiteDownload.store_file_content(page, index_dir)

        else:
            print u'获取页面失败'

if __name__ == '__main__':
    url = r'http://www.blockfundchain.cn'
    wd = WebsiteDownload(url)
    wd.main()