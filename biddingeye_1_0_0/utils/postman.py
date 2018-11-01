# coding=utf-8
import ConfigParser
import datetime

import os
import re

import MySQLdb
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from cStringIO import StringIO
from platform import python_version
from smtplib import SMTP
import time

import sys

reload(sys)
sys.setdefaultencoding('utf8')

# SMTP_SSL added in 2.6, fixed in 2.6.3
#import MAILBOX as MAILBOX

release = python_version()
if release > '2.6.2':
    from smtplib import SMTP_SSL, SMTPServerDisconnected
else:
    SMTP_SSL = None


class postman():
        name = 'BiddingEye'

        def __init__(self):
                self._db_dict = {
                                 "host":"10.10.126.117",
                                 "port": 3306,
                                 "user": "saca",
                                 "passwd": "saca",
                                 "database": "bee",
                                 "charset":"utf8"
                                 }
                self._db_handle = None
                self._key_words =[]
                self._mail_users = None

                self._mail_title = ""
                self._mail_content = ""

                self._user = ""
                self._passwd = ""

                self._timelist = ""
                self._maillist = ""

                self.initDBData()
                self.initNotifyData()


        def initDBData(self):
            try:
                print self._db_dict['host'] + "|" + str(self._db_dict['port']) + "|" +  self._db_dict['user'] + \
                "|" + self._db_dict['passwd'] + "|" + self._db_dict['database'] + "|" + self._db_dict['charset']

                conn = MySQLdb.connect(host=self._db_dict["host"], port=self._db_dict["port"], user=self._db_dict["user"],
                                       passwd=self._db_dict["passwd"], db=self._db_dict["database"], charset=self._db_dict["charset"])

            except MySQLdb.Error, e:
                try:
                    sqlError = "Error %d:%s" % (e.args[0], e.args[1])
                    print sqlError
                except IndexError:
                    print "MySQL Error:%s" % str(e)
                return

            self._db_cursor = conn.cursor()

        def initNotifyData(self):
            cp = ConfigParser.SafeConfigParser()
            cp.read('../conf/setup.conf')
            self._db_handle = cp.items('db')

            cp.read('../conf/notify.conf')
            #self._key_words = cp.items('keyword')
            self._mail_users = cp.items('mailaddr')

            self._user = cp.get("userinfo", "user")
            self._passwd = cp.get("userinfo", "passwd")
            self._key_words = cp.get("keyword", "keylist1").split('|')

            print self._mail_users
            print self._user + "|" + self._passwd
            for keyword in self._key_words:
               print "keyword:"+keyword


        def checkNoticeInfo(self):

            curr_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))

            print "time:" + str(curr_time)
            select_sql = "select id, prov, date, url, title from BID_PURCHASE_NOTICE_DATA_T WHERE  " \
                  "date = date_sub(curdate(), interval 1 day) or date = curdate() and mail_time is NULL "

            print "DB UPDATE:" + str(select_sql)

            try:
                self._db_cursor.execute(select_sql)
                content_list = self._db_cursor.fetchall()
                for row  in content_list:
                    print "data:" + str(row[0]) + "|" + str(row[1]) + "|" + str(row[2]) + "|" + str(row[3] + "|" + str(row[4]))

            except MySQLdb.Error, e:
                sqlError = "Error %d:%s" % (e.args[0], e.args[1])
                print sqlError
                return

            email = self.build_mail_text(content_list)
            try:
                self.send_mail(email)
            except:
                pass

            # update_sql = "update BID_PURCHASE_NOTICE_DATA_T SET mail_time = %s WHERE  " \
            #       "id = %s " % content_list
            # content_list = self._db_cursor.execute(update_sql)


        def build_mail_text(self, content_list):
            text_body = ""
            for row in content_list:
                url = row[3]
                title = row[4]
                if self.keyword_filter(title):
                    text_body = text_body + ("<li><a href='%s' id='url_1' >%s</a></li>" % (url, title))
                    print "textbody:"+text_body

            if len(text_body) <= 0:
                return
            #组装mail content
            email = MIMEMultipart('alternative')
            #text = MIMEText(u'Hello World!\r\n', 'plain')

            text = MIMEText("Bidding系统采集到最新招标数据，参考如下:", 'html', _charset='UTF-8')
            email.attach(text)

            html_head = """
                            <html lang='en'>
                            <head><title>notice</title><meta charset="UTF-8" /></head>
                            <body>
            """

            html_tail = """
                            </body>
                            </html>
            """

            email.attach(MIMEText(html_head+text_body+html_tail, 'html', 'UTF-8'))

            who = '%s@neusoft.com' % self._user
            _from = who
            _to = ""
            for idx, addr in self._mail_users:
                print "idx:"+idx+" addr:"+addr
                _to = _to + "," + addr

            print "to:"+_to
            email['To']= ', '.join(["sun.yue@neusoft.com"])

            #email['From'] = _from
            email['From'] = "davidsun_home@163.com"
            email['Subject'] = u'[重要]中国移动招标与采购信息通知!'


            return email

        def send_mail2(self, mail_msg):
            print "发送邮件通知 .......！"
            print str(mail_msg)
            try:
                # s = SMTP('')
                # s.connect('smtp.neusoft.com')
                # s.starttls()

                print '*** Doing SMTP send via TLS...'
                s = SMTP('smtp.neusoft.com', 587)
                if release < '2.6':
                    s.ehlo()  # required in older releases
                s.starttls()
                if release < '2.5':
                    s.ehlo()  # required in older releases
                #s.login(self._user, self._passwd)
                s.login("sun.yue@neusoft.com", "LN61878@#")
                s.sendmail(mail_msg['From'], mail_msg['To'], mail_msg.as_string())
                s.quit()
                print "邮件发送成功"
            except Exception, e:
                print "失败" + str(e)

        def send_mail(self, mail_msg):
            print "发送邮件通知 .......！"
            print str(mail_msg)
            try:
                s = SMTP()
                s.connect('smtp.163.com')
                s.starttls()
                #s.login(self._user, self._passwd)
                s.login("davidsun_home@163.com", "LN5270387@#")
                s.sendmail(mail_msg['From'], mail_msg['To'], mail_msg.as_string())
                s.quit()
                print "邮件发送成功"
            except Exception, e:
                print "失败" + str(e)

        def keyword_filter(self, title):
            isSend = False
            for keyword in self._key_words:
               se = re.compile(keyword)
               if se.search(str(title)):
                   isSend = True
                   print "match key:["+keyword+"] in ("+title+")"

            return isSend




if __name__ == '__main__':
    try:
        man = postman()
        man.checkNoticeInfo()

       # parser.event_list()
    except IOError,e:
        print 'IOError:', e
