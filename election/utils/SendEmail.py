import smtplib
from email.mime.text import MIMEText


class EmailSender(object):
    def __init__(self, receivers, usernames, passwords, urls):
        # 发送方信息
        self.mail_host = 'smtp.163.com'  # 163邮箱服务器地址
        self.mail_user = 'htwu1995@163.com'  # 163用户名
        self.mail_pass = 'www78873443sqm'  # 密码(部分邮箱为授权码)
        self.sender = 'htwu1995@163.com'  # 邮件发送方邮箱地址
        self.receivers = receivers  # 邮件接受方邮箱地址，注意需要[]包裹，这意味着你可以写多个邮件地址群发
        self.usernames = usernames
        self.passwords = passwords
        self.urls = urls

    def send_emails(self):
        # 登录并发送邮件
        try:
            smtpObj = smtplib.SMTP()
            # 连接到服务器
            smtpObj.connect(self.mail_host, 25)
            # 登录到服务器
            smtpObj.login(self.mail_user, self.mail_pass)
            # 发送
            for i in range(len(self.receivers)):
                text = "尊敬的" + self.usernames[i] + "，您好：\n  现邀请您进行本次重要的选举投票！\n  " \
                       "本次投票地址："+self.urls+"\n  您的登录账户为：" + self.usernames[i] + "\n  您的登录密码为：" + self.passwords[i]
                message = MIMEText(text, 'plain', 'utf-8')  # 邮件内容设置
                message['Subject'] = '来自helios投票中心的投票邀请'  # 邮件主题
                message['From'] = self.sender  # 发送方信息
                message['To'] = self.receivers[i]  # 接受方信息
                smtpObj.sendmail(self.sender, self.receivers[i], message.as_string())
            # 退出
            smtpObj.quit()
            print('send success!')
        except smtplib.SMTPException as e:
            print('error', e)  # 打印错误


if __name__ == '__main__':
    receivers = ['2480850946@qq.com']
    usernames = ['htwu']
    passwords = ['123456']
    urls = 'http://localhost:3000/user/login'
    emailSender = EmailSender(receivers, usernames, passwords, urls)
    emailSender.send_emails()
