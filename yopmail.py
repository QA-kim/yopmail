import unittest
import time

from bs4 import BeautifulSoup
import requests

import datetime
import re
import sys

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'
}


class Yopmail(object):
    def __init__(self, userid):
        self.jar = requests.cookies.RequestsCookieJar()
        self.ses = requests.Session()
        self.localtime = None
        self.userid = userid

    def request(self, url, params=None):
        if not self.localtime is None:
            # after first time we use it, we start to update it everytime
            self.add_localtime()
        r = self.ses.get(url, params=params, cookies=self.jar, headers=headers)
        # print(f"url: {url}, params: {params}\nstatus_code: {r.status_code}")
        # for cookie in r.cookies:
        #     print(f"cookie: {cookie}")
        return r

    def r1(self):
        self.request('http://www.yopmail.com')

    def extract_yp(self, req):
        bs = BeautifulSoup(req.text, 'html.parser')
        #search for:
        #   <input type="hidden" name="yp" id="yp" value="OAwt2BGN5AGD4AQp2ZmDmZt" />
        input_el = bs.find('input', {'name':'yp','id':'yp'})
        self.yp = input_el['value']
        # print('yp is:', self.yp)

    def r2(self):
        self.extract_yp(
            self.request('http://www.yopmail.com/en/'))

    def add_localtime(self):
        now = datetime.datetime.now().time()
        self.localtime = '%d:%d'%(now.hour, now.minute)
        self.jar.set('localtime', self.localtime,
                     domain='yopmail.com', path='/')

    def r3(self):
        self.username = self.userid
        self.add_localtime()
        #yp = self.jar.get("yp", domain="yopmail.com")
        data = {'yp':self.yp, 'login': self.username}
        rq = self.ses.post('http://www.yopmail.com/en/', data, cookies=self.jar, headers=headers)
        # print(rq.status_code)
        # for cookie in rq.cookies:
        #     print(cookie)

    YJ_RE = re.compile("value\+\'\&yj\=([0-9a-zA-Z]*)\&v\=\'", re.MULTILINE)
    def extract_yj(self, req):
        #serach for:
        #   value+'&yj=QBQVkAQVmZmZ4BQR0ZwNkAN&v='
        match = self.YJ_RE.search(req.text)
        self.yj = match.groups()[0]

    def r7(self):
        self.extract_yj(
            self.request("http://www.yopmail.com/style/3.1/webmail.js"))

    def extract_inbox(self, req):
        """<div  class=\"m\" onclick=\"g(6,0);\" id=\"m6\">
                <div   class=\"um\"><a class=\"lm\" href=\"mail.php?b=pelado&id=me_ZGpjZGVkZGpmZmZ2ZQNjAmZ2AwtjBN==\">
                <span class=\"lmfd\">
                <span class=\"lmh\">14:33</span>"""
        # print(f"req.text: {req.text}")
        bs = BeautifulSoup(req.text, 'html.parser')
        results = {}
        for idx in range(10):
            div_mX = bs.find('div', {'class': 'm', 'id': 'm%d'%idx})
            if div_mX is None:
                continue
            a = div_mX.find('a', {'class':'lm'})

            href = a['href'].rsplit('&id=',1)[1]
            results[idx] = href

        # print(f"in extract_inbox, results: {results}")
        self.mailids=results

    def r8(self, mail_idx=None, page=1):
        if mail_idx is None:
            mailid = ''
        else:
            mailid = self.mailids[mail_idx]
        params = {
            'login':self.username,
            'p':str(page), # page
            'd':'',  # mailid? to delete?
            'ctrl':mailid, #mailid or ''
            'scrl':'', #always?
            'spam':True,#false
            'yf':'005',
            'yp':self.yp,
            'yj':self.yj,
            'v':"3.1",
            'r_c':'', # ""
            'id':"", # idaff / sometimes "none" / nextmailid='last' / mailid = id('m%d'%mail_nr)
        }
        self.extract_inbox(
            self.request("http://www.yopmail.com/en/inbox.php", params=params))

    def fetch(self, mail_idx):
        if mail_idx is None:
            mailid = ''
        else:
            mailid = self.mailids[mail_idx]
        params = {'b':self.username,
                  'id':mailid}  # mailid 'me_ZGpjZGV1ZwRkZwD0ZQNjAmx0AmpkAj=='
        return self.request('http://www.yopmail.com/en/m.php', params=params)

    def __iter__(self):
        return iter(self.mailids.keys())

    def login(self):
        self.r1()
        self.r2()
        self.r3()
        self.r7()
        self.r8()
        return self


class TestSomething(unittest.TestCase):
    def test_yj_re(self):
        value = 'QBQVkAQVmZmZ4BQR0ZwNkAN'
        sample = "value+'&yj=QBQVkAQVmZmZ4BQR0ZwNkAN&v='"
        self.assertIsNotNone(Yopmail.YJ_RE.match(sample))
        self.assertEqual(Yopmail.YJ_RE.match(sample).groups()[0], value)

def main(username):
    em = Yopmail(username)
    em.login()
    for _id in em:
        print(f"reading mail id#{_id}")
        resp = em.fetch(_id)
        with open(username+'_'+str(_id)+".html", "w", encoding="utf8") as f:
            try:
                f.write(resp.text)
                print(f"mail id#{_id} saved!!!")
            except UnicodeEncodeError as e:
                print(f"UnicodeEncodeError occured, mail id#{_id} not saved!")
        print()
        time.sleep(1)


if __name__=="__main__":
    try:
        main(sys.argv[1])
    except:
        print("Usage: python yopmail.py email_user")
        print("where email_user is the name of email without the '@yopmail.com'")
        print()
        raise
