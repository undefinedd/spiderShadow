#coding:utf8
import json,re,time,md5,random,pdb,urllib3,requests,os,datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
from termcolor import colored


def error(string):
    """
    输出红色信息
    """
    print colored("[!]"+string, "red")


def success(string):
    """
    输出绿色信息
    """
    print colored("[+]"+string, "green")


def process(string):
    """
    输出蓝色信息
    """
    print colored("[*]"+string, "blue")

def alignment(str1, space, align = 'left'):
    length = len(str1.encode('gb2312'))
    space = space - length if space >=length else 0
    if align == 'left':
        str1 = str1 + ' ' * space
    elif align == 'right':
        str1 = ' '* space +str1
    elif align == 'center':
        str1 = ' ' * (space //2) +str1 + ' '* (space - space // 2)
    return str1


class ShadowSocks(object):
    def __init__(self):
        self.debug_proxy = None#{'http':'127.0.0.1:8080','https':'127.0.0.1:8080'}
        self._getEmailTimes = 5;
        self._headers = {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0'}
        self._version = {'version':'1.0','info':''}

    def update(self):
        verify_file = 'https://raw.githubusercontent.com/undefinedd/spiderShadow/master/version'
        new_file = 'https://raw.githubusercontent.com/undefinedd/spiderShadow/master/getShadowSocks.py'
        response = requests.get(verify_file, verify=False)
        version = eval(response.content.strip())
        if version['version'] > self._version['version']:
            error('发现新版本,'+version['info'])
            response = requests.get(verify_file, verify=False)
            newFile = eval(response.content.strip())
            with open('getShadowSocksV'+version['version']+'.py', 'a') as f:
                f.write(newFile);
            success('更新完成,保存:./'+'getShadowSocks V'+version['version']+'.py')
        
    
    def start(self):
        self.update();
        self.makeParam();
        if self.readCache() and self.registerUser():
            emailObj = self.getEmail(self._email)
            if not emailObj:
                return False;
            vCode = self.parseEmail(emailObj)
            if self.verifyUser(vCode):
                login_session = self.login()
                if not login_session:
                    return
                self.createShadow(login_session);
            


    def makeParam(self):
        newMd5 = md5.new()
        newMd5.update(str(time.time()))
        self._username = newMd5.hexdigest()[-8:]
        self._password = newMd5.hexdigest()
        self._email = newMd5.hexdigest()[-16:]

    def getEmail(self, address):
        #address 是email地址
        process('开始获取邮件....')
        url = 'http://24mail.chacuo.net/enus';
        times = 0;
        session = requests.session();
        session.get(url, proxies=self.debug_proxy,headers=self._headers) #get cookies
        set_param = {'data':address,'arg':'','type':'set'};
        session.post(url, data=set_param, proxies=self.debug_proxy, headers=self._headers)
        while times <= self._getEmailTimes:
            param = {'data':address,'arg':'','type':'refresh'};
            response = session.post(url, headers=self._headers, data=param, proxies=self.debug_proxy);
            if response.status_code != 200:
                error('获取Email出错,错误状态码:'+str(response.status_code))
                return
            response_data = json.loads(response.content)
            if not len(response_data['data'][0]['list']):
                times += 1;
            else:
                emailObj = response_data['data'][0]['list'][0]
                success('获取邮件成功!')
                return emailObj
            time.sleep(3)
        error('获取Email信息失败,请重试!');
        return False

    def parseEmail(self, emailObj):
        #这里只解析标题
        if not emailObj:
            return emailObj
        subject = emailObj['SUBJECT']
        match_vCode = '.*?(\d+)'
        match_ru = re.findall(match_vCode, subject);
        if len(match_ru):
            return match_ru[0]
        else:
            return False

    def registerUser(self):
        email = '%s@chacuo.net' % self._email
        param = {'email':email, 'inviteCode':'', 'name':self._username, 'password':self._password}
        register_url = 'https://www.ss-link.com/register'
        response = requests.post(register_url, data=param, verify=False, headers=self._headers, proxies=self.debug_proxy)
        if response.status_code != 200:
            error('用户注册请求失败,失败状态码:'+str(response.status_code))
            return False
        elif 'success' in response.content:
            return True
        return False


    def verifyUser(self, vCode):
        verify_url = 'http://www.ss-link.com/validateUser/%s' % vCode
        response = requests.get(verify_url, verify=False, headers=self._headers)
        if response.status_code != 200:
            error('用户验证失败, code:'+str(response.status_code))
        elif '激活成功' in response.content:
            return True;
        else:
            return False;

    def login(self):
        login_url = 'https://www.ss-link.com/login'
        email = '%s@chacuo.net' % self._email
        param = {'email':email, 'redirect':'', 'password':self._password}
        login_session = requests.session();
        response = login_session.post(login_url, allow_redirects=False, data=param, verify=False, headers=self._headers, proxies=self.debug_proxy)
        if response.status_code != 303:
            error('用户登陆失败, code:'+(response.content))
            return False
        return login_session
    
    def createShadow(self, login_session):
        buy_url = 'https://www.ss-link.com/buy'
        response = login_session.get(buy_url, verify=False, headers=self._headers)
        soup = BeautifulSoup(response.content)
        shadow_list = []
        for item in soup.find_all('a', class_='btn btn-success btnOrder'):
            shadow_list.append(item.get('data'))
        my_shadow = shadow_list[random.randint(0,len(shadow_list)-1)]
        order_url = 'https://www.ss-link.com/order'
        param_order = {'serviceId':my_shadow, 'term':'year'}
        response = login_session.post(order_url, data=param_order, verify=False, headers=self._headers, proxies=self.debug_proxy)
        if response.status_code != 200:
            return False
        #提交订单
        pay_url = 'https://www.ss-link.com/pay'
        response = login_session.post(pay_url, verify=False, headers=self._headers)
        response_json = json.loads(response.content)
        if response_json['result'] != 1:
            #print '订单提交失败!'
            return False
        #match shadowsocks id
        info_url = 'https://www.ss-link.com/my/hostings'
        response = login_session.get(info_url, verify=False, headers=self._headers, proxies=self.debug_proxy)
        if response.status_code != 200:
            #print 'get shadow info failure! reason_code:',response.status_code
            return False
        match_id = 'ID</td.*?(\d+)'
        match_ru = re.findall(match_id, response.content, re.S)
        if len(match_ru) == 0:
            #print '获取shadowsocks ID出现错误!',response.content
            return False       
        shadow_id = match_ru[0];
        #开通服务
        create_url = 'https://www.ss-link.com/createHosting'
        response = login_session.post(create_url, data={'hostingId':shadow_id}, verify=False, headers=self._headers, proxies=self.debug_proxy)
        if response.status_code != 200:
            #print 'create shadowsocks failure! reason_code:',response.status_code
            return False
        response_json = json.loads(response.content)
        if 'port' in response_json['msg']:
            success('Shadowsocks Create Success!')
        #
        info_url = 'https://www.ss-link.com/my/hostings'
        response = login_session.get(info_url, verify=False, headers=self._headers, proxies=self.debug_proxy)
        if response.status_code != 200:
            #print 'get shadow info failure! reason_code:',response.status_code
            return False
        soup = BeautifulSoup(response.content)
        infoDict = {}
        for item in soup.find_all('tr'):
            infoDict[item.td.text] = item.text.replace(item.td.text,'').replace('\n','');
            if item.td.text == u'二维码':
                img_url = 'https://www.ss-link.com/%s' % item.img.get('src')
                response = login_session.get(img_url, verify=False, headers=self._headers)
                with open('img.png','wb') as f:
                    f.write(response.content)
                infoDict[item.td.text] = './img.png';
        #处理时间
        infoDict[u'到期时间'] = self.calcEndTime(infoDict[u'到期时间'])
        self.parseShadowInfo(infoDict)
        self.writeCache(infoDict)

    def calcEndTime(self, nowtime):
        nowtime_struct = time.strptime(nowtime,'%Y-%m-%d %H:%M:%S')
        endTime = time.struct_time([nowtime_struct[0],nowtime_struct[1],nowtime_struct[2]+1,01,0,0,0,0,0]);
        return time.strftime('%Y-%m-%d %H:%M:%S',endTime);

    def parseShadowInfo(self, infoDict):
        print '-'*50
        for key in infoDict.keys():
            print '|'+alignment(key, 15, 'left')+alignment(infoDict[key], 33, 'left')+'|'
        print '-'*50
    


    def writeCache(self, infoDict):
        with open('cache_ShadowSocks', 'w') as f:
            f.write(str(infoDict))
            
    def readCache(self):
        try:
            if os.path.isfile('cache_ShadowSocks'):
                with open('cache_ShadowSocks', 'r') as f:
                    data = f.read()
                infoDict = eval(data)
                cache_time = infoDict[u'到期时间']
                endTime = time.mktime(time.strptime(cache_time,'%Y-%m-%d %H:%M:%S'))
                #pdb.set_trace()
                if time.time() > endTime:
                    success('缓存过期,更新缓存')
                else:
                    success('缓存可用')
                    self.parseShadowInfo(infoDict)
                    return False
            else:
                process('无缓存,开始获取ShadowSocks')
        except Exception,e:
            error('读取缓存信息失败,重新获取ShadowSocks,'+str(e))
        return True
                
        
            
           
        

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
m_ShadowSocks = ShadowSocks();
m_ShadowSocks.start()