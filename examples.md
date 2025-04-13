# PAW Usage Examples

This document contains examples of how to use PAW for common cybersecurity tasks in Kali Linux.

## Network Reconnaissance

### Basic Network Scanning

```bash
paw "scan my local network for active hosts"
```

PAW will execute something like:
```
netdiscover -r 192.168.1.0/24
```

### Port Scanning

```bash
paw "find all open ports on 192.168.1.100"
```

PAW will execute something like:
```
nmap -sS -p- 192.168.1.100
```

### Service Enumeration

```bash
paw "identify services running on 192.168.1.100"
```

PAW will execute something like:
```
nmap -sV -A 192.168.1.100
```

## Web Application Testing

### Basic Web Scanning

```bash
paw "check if https://example.com has common web vulnerabilities"
```

PAW will execute something like:
```
nikto -h https://example.com
```

### Directory Brute-Forcing

```bash
paw "find hidden directories on https://example.com"
```

PAW will execute something like:
```
gobuster dir -u https://example.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
```

### WordPress Scanning

```bash
paw "check if this WordPress site has vulnerabilities: https://wordpress-example.com"
```

PAW will execute something like:
```
wpscan --url https://wordpress-example.com
```

## Vulnerability Assessment

### System Vulnerability Checking

```bash
paw "check this system for security vulnerabilities"
```

PAW will execute something like:
```
lynis audit system
```

### SQL Injection Testing

```bash
paw "test if http://example.com/page.php?id=1 is vulnerable to SQL injection"
```

PAW will execute something like:
```
sqlmap -u "http://example.com/page.php?id=1" --batch
```

## Password Attacks

### Password Cracking

```bash
paw "crack these MD5 hashes in the file hashes.txt"
```

PAW will execute something like:
```
john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
```

### Online Password Brute-Forcing

```bash
paw "try to brute force SSH login for user admin on 192.168.1.100"
```

PAW will execute something like:
```
hydra -l admin -P /usr/share/wordlists/rockyou.txt 192.168.1.100 ssh
```

## Wireless Testing

### Wireless Network Scanning

```bash
paw "scan for wireless networks"
```

PAW will execute something like:
```
airmon-ng start wlan0 && airodump-ng wlan0mon
```

## Advanced Usage

### Chaining Commands

```bash
paw "scan for open web servers on my network and check them for vulnerabilities"
```

PAW will execute a sequence like:
```
nmap -p80,443 192.168.1.0/24 -oG web_servers.txt
cat web_servers.txt | grep open | cut -d" " -f2 > targets.txt
for ip in $(cat targets.txt); do nikto -h $ip; done
```

### Complex Tasks

```bash
paw "perform a full reconnaissance on the domain example.com"
```

PAW will execute multiple commands to gather information about the domain, including DNS lookup, WHOIS information, subdomain enumeration, and more.

## Customizing Commands

You can always review and modify the commands suggested by PAW before execution.

```bash
paw "scan my local network but exclude my gateway"
```

PAW will suggest a command, and you can modify it before executing.

## Note on Ethical Usage

Always ensure you have proper authorization before performing security testing on any system or network you don't own. Unauthorized scanning or testing may be illegal and unethical. 