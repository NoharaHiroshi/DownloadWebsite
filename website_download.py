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
        # 设置项目路径
        self.download_dir = os.path.join(os.path.dirname(__file__).replace('/', '\\'), self.domain)
        # 设置可下载文件的后缀名
        self.download_type_list = ['js', 'css', 'scss', 'png', 'jpg', 'jpeg', 'gif', 'ico']
        # 当前页面URL
        self.current_page_url = web_url if web_url[-2:] != '#/' else web_url[:-2]

    def main(self):
        # 初始化目录结构
        if not os.path.exists(self.download_dir):
            os.mkdir(self.download_dir)
        self.download_pages(self.web_url)

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
        path_list_len = 0
        path_list = list()
        if url[0] == '/':
            path_list = url.split('/')
            path_list_len = len(path_list)
        if url[:4] == 'http':
            path_list = url.split('/')
            # 站内静态文件
            if path_list[2] == self.domain:
                url = url.replace('%s://%s' % (self.request_type, self.domain), '')
                path_list = url.split('/')
                path_list_len = len(path_list)
            else:
                url = '/' + '/'.join(path_list[3:])
                path_list = url.split('/')
                path_list_len = len(path_list)
        for i in range(1, path_list_len-1):
            tmp_path = '/'.join(path_list[1:i+1])
            _path = os.path.join(self.download_dir, tmp_path)
            if not os.path.exists(_path):
                os.mkdir(_path)
        return os.path.join(self.download_dir, url[1:])


    def handle_css_image(self, download_file_dir):
        """
        处理静态文件，查找其中的图片资源
        :param download_file_dir: css文件路径
        :return: None
        """
        # 判断css文件所处的位置作为根目录
        cur_dir = os.path.dirname(download_file_dir)
        with open(download_file_dir, 'r') as f:
            css_content = '\n'.join(f.readlines())
            # 不知道为什么分组不可用
            css_url_list = re.findall(r'\(.+\.jpeg|\(.+\.png|\(.+\.jpg|\(.+\.gif', css_content)
            css_url_list = [item.replace('(', '') for item in css_url_list]
            for css_url in css_url_list:
                last_layer_dir_flag = css_url.split('..')
                left_dir = last_layer_dir_flag[-1][1:]
                last_layer_count = len(last_layer_dir_flag) - 1
                _cur_dir = cur_dir
                while last_layer_count > 0:
                    _cur_dir = os.path.dirname(_cur_dir)
                    last_layer_count -= 1
                img_dir = os.path.join(_cur_dir, left_dir)
                img_uri = img_dir.split(self.download_dir)[-1].replace('\\', '/')
                img_url = self.request_type + '://' + self.domain + img_uri
                WebsiteDownload.store_file_content(img_url, img_dir)

    def convert_and_download_assets_src(self, content):
        """
        查找当前页面代码中的静态文件并下载，并变更静态文件的路径
        :param content: 当前页面代码
        :return: 变更静态文件链接后的页面代码
        """
        for url_type in ['src', 'href']:
            file_type_reg = '(%s)' % '|'.join(['.+?\.%s' % t for t in self.download_type_list])
            url_list = re.findall('%s=%s' % (url_type, file_type_reg), content)
            tmp_url_list = list()
            for url in url_list:
                _url = re.sub(r"""%s="|'""" % url_type, '', url)
                if len(_url):
                    if url_type == 'href':
                        if _url[0] == '#':
                            continue
                    # 防止下载重复静态资源
                    if _url not in tmp_url_list:
                        tmp_url_list.append(_url)
                    else:
                        continue
                    # 筛选静态资源后缀
                    f_type = _url.split('.')[-1]
                    if f_type not in self.download_type_list:
                        continue

                    # 获取静态资源url
                    if _url[0] == '/':
                        download_file_src = self.request_type + '://' + self.domain + _url
                        if _url[1] == '/':
                            download_file_src = self.request_type + ':' + _url
                    elif _url[0] == '.':
                        download_file_src = self.current_page_url + _url[2:]
                    else:
                        download_file_src = _url
                    # 更改静态资源相对路径
                    download_file_dir = self.create_assets_path_dir(download_file_src)
                    # 下载静态资源
                    WebsiteDownload.store_file_content(download_file_src, download_file_dir)
                    # 替换静态资源路径
                    content = content.replace(_url, '.%s' % _url)
                    # css样式文件中可能存在着静态文件，比如图片
                    if f_type in ['css', 'scss']:
                        self.handle_css_image(download_file_dir)
        return content

    # 下载页面
    def download_pages(self, web_url, times=0):
        """
        下载页面代码并存储在本地，同时处理构成页面所需的静态资源（下载和按照本地路径重新构造静态资源的相对位置）
        :param web_url: 页面url
        :param times: 重试次数
        :return: None
        """
        try:
            response = requests.get(web_url)
            if str(response.status_code) == '200':
                content = response.content
                content = self.convert_and_download_assets_src(content)
                index_dir = os.path.join(self.download_dir, 'index.html')
                if not os.path.exists(index_dir):
                    with open(index_dir, 'ab') as f:
                        f.write(content)
                        f.flush()
                print u'获取页面%s 完成' % web_url
            else:
                times += 1
                print u'获取页面%s 失败，尝试第%s次重新获取' % (web_url, times)
                if times == 10:
                    print u'获取页面%s 获取失败' % web_url
                    return
                self.download_pages(web_url, times)
        except Exception as e:
            print u'获取页面%s 错误' % web_url
            print traceback.format_exc(e)

if __name__ == '__main__':
    url = r'http://developer.blockfundchain.net/bfchome/#/'
    wd = WebsiteDownload(url)
    wd.main()