#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @FileName：     query_ssl_expired.py
# @Software:      
# @Author:         Leven Xiang
# @Mail:           xiangle0109@outlook.com
# @Date：          2021/4/27 9:04


from datetime import datetime
from urllib3.contrib import pyopenssl as reqs
import json
import requests

def get_expire_time(url):
    cert = reqs.OpenSSL.crypto.load_certificate(reqs.OpenSSL.crypto.FILETYPE_PEM, reqs.ssl.get_server_certificate((url, 443)))
    # 获取证书到期时间
    notafter = datetime.strptime(cert.get_notAfter().decode()[0:-1], '%Y%m%d%H%M%S')  # 获取到的时间戳格式是ans.1的，需要转换
    # print(notafter)
    # 用证书到期时间减去当前时间
    remain_days = notafter - datetime.now()
    # 获取剩余天数
    return remain_days.days



class WeChat(object):
    def __init__(self, corpid, agentid, corpsecret):
        self.url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
        # 企业ID
        self.corpid = corpid
        # 应用AgentID
        self.agentid = agentid
        # 应用Secret
        self.corpsecret = corpsecret

    @property
    def __auth(self):
        params = {'corpid': self.corpid, 'corpsecret': self.corpsecret}
        try:
            rs = requests.get(self.url, params=params)
            return rs.json()['access_token']
        except Exception as auth_error:
            return 'get access_token error: {}'.format(auth_error)

    @property
    def __get_token(self):
        token = self.__auth
        return token.strip()

    def __message(self, touser, toparty, subject, content):
        data = json.dumps({
            'touser': touser,
            'toparty': toparty,
            'msgtype': 'text',
            'agentid': self.agentid,
            'text': {
                'content': '{}\n{}'.format(subject, content)},
            'safe': '0'
        }, ensure_ascii=False).encode('utf-8')
        return data

    def send(self, touser, toparty, subject, content):
        """
        :param touser:  用户名，多用户名用|分隔
        :param toparty: 部门，指定部门ID,或为空
        :param subject: 标题
        :param content: 消息内容
        :return:
        """
        try:
            url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + self.__get_token
            send = requests.post(url, data=self.__message(touser, toparty, subject, content))
            return json.loads(send.text)
        except Exception as send_error:
            return 'send error: {}'.format(send_error)


if __name__ == '__main__':
    wx = WeChat(corpid='112312312', agentid='12312312312312', corpsecret='32kdhxcvjkp23uijhdfsda')
    expired_days = 30
    # 微信消息接收人，多个用户用|分隔
    send_user = r'XiangLe'
    msg_list = []
    #需要被检查的域名url列表
    with open('/opt/bin/domains.txt', 'r') as urls:
        for url in urls.read().splitlines():
            ssl_expire = get_expire_time(url)
            if ssl_expire < expired_days:
                msg_list.append('域名[{}]证书还有{}天过期，请注意续签' .format(url, ssl_expire))
    urls.close()

    if len(msg_list) > 0:
        msg = '\n'.join(msg_list)
        wx.send(send_user,'','【证书即将过期】', msg)
    else:
        wx.send(send_user, '', '【SSL证书过期时间检查】', 'SSL证书有效期正常')
