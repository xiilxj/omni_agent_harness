# 🔥 BlackArch 命令速查手册（本地文件 + 渗透工具箱）

> 学习用途专用 · 请只在你有授权的环境里练习
> 环境：Arch Linux + BlackArch 源（5044 个工具可用）

---

## 一、本地文件操作（基本功，先练这个）

### 1. 查看与搜索
```bash
# 看文件内容
cat file.txt              # 整个文件
less file.txt             # 分页看（q 退出）
head -n 20 file.txt       # 前20行
tail -n 20 file.txt       # 后20行
tail -f app.log           # 实时跟踪日志（超好用）

# 搜索
grep "password" file.txt          # 普通搜索
grep -r "api_key" ./config/       # 递归搜目录
grep -ri "secret" .               # 忽略大小写
grep -rl "flag" .                 # 只列文件名
grep -E "pass|user" file.txt      # 正则多关键词
```

### 2. 增删改
```bash
# 创建/删除
touch newfile.txt         # 创建空文件
mkdir -p a/b/c            # 递归建目录
rm file.txt               # 删除文件
rm -rf dir/               # 递归强删目录（小心用！）
cp -r src dst             # 复制目录
mv old new                # 移动/重命名

# 追加 vs 覆盖
echo "hello" > file.txt      # 覆盖写入
echo "world" >> file.txt     # 追加写入

# 修改文件内容（神器 sed）
sed -i 's/old/new/g' file.txt        # 全局替换
sed -i '3d' file.txt                 # 删第3行
sed -i 's/^#//' config.conf          # 去掉行首注释#

# awk 处理结构化文本（CSV/日志神器）
awk '{print $1}' file.txt            # 打印第一列
awk -F',' '{print $2}' data.csv      # 按逗号分割取第2列
```

### 3. 权限（经常要改）
```bash
chmod +x script.sh        # 加执行权限
chmod 755 script.sh       # rwxr-xr-x
chmod 600 key.pem         # 私钥必须600，否则ssh拒绝
chown user:group file     # 改属主属组
ls -la                    # 查看权限
stat file.txt             # 详细元数据（时间戳/大小）
```

### 4. 查找文件（渗透时找配置文件必备）
```bash
find / -name "*.conf" 2>/dev/null        # 全局找配置文件
find / -name "*.key" -o -name "*.pem" 2>/dev/null
find / -type f -size +10M 2>/dev/null    # 找大文件
find . -name "*.log" -mtime -1           # 24小时内改过的日志
locate shadow                          # 快速索引搜索（先 updatedb）
```

### 5. 文件类型与字符串（CTF 福音）
```bash
file secret.bin            # 判断真实文件类型
strings secret.bin         # 提取可打印字符串（找flag/密码）
hexdump -C secret.bin      # 十六进制查看
xxd secret.bin             # 十六进制+ASCII
binwalk secret.bin         # 分析嵌入式文件（隐藏图片/压缩包）
```

---

## 二、BlackArch 工具箱（按渗透阶段分）

### 阶段0：装工具
```bash
# BlackArch 源已配好，直接装
sudo pacman -Syy                 # 更新包列表
sudo pacman -S nmap sqlmap hydra john nikto metasploit

# 按类别装（超爽）
sudo pacman -S blackarch-scanner      # 扫描类全家桶
sudo pacman -S blackarch-webapp       # Web渗透类
sudo pacman -S blackarch-reversing    # 逆向类
```

### 阶段1：信息收集（Recon）
```bash
# 主机发现 + 端口扫描（nmap 的骚操作）
nmap -sV -sC 192.168.1.1                    # 版本+默认脚本
nmap -p- -T4 10.0.0.5                       # 全端口快速扫
nmap -sn 192.168.1.0/24                     # ping 扫描网段存活
nmap -O 10.0.0.5                            # 操作系统指纹
nmap --script vuln 10.0.0.5                 # 漏洞扫描脚本

# DNS 枚举
dnsrecon -d example.com
dnsenum example.com

# 子域名/信息
theHarvester -d example.com -b all
```

### 阶段2：漏洞扫描（Vuln Scan）
```bash
# Web 漏洞
nikto -h http://target.com                # Web服务器扫描
sqlmap -u "http://target/page?id=1" --batch   # SQL注入自动检测
wpscan --url http://target.com            # WordPress 专属
gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt   # 目录爆破

# 通用
searchsploit apache 2.4.49                # 本地搜索漏洞利用库
```

### 阶段3：密码攻击（Credential Attacks）
```bash
# 在线爆破
hydra -l admin -P pass.txt ssh://192.168.1.10      # SSH爆破
hydra -l admin -P pass.txt ftp://192.168.1.10      # FTP爆破
hydra -l admin -P pass.txt http-post-form "/login:user=^USER^&pass=^PASS^:F=incorrect"  # Web表单

# 离线破解
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
hashcat -m 0 -a 0 hash.txt rockyou.txt   # MD5 字典破解
```

### 阶段4：后渗透 & 取证（Post-Exploitation & Forensics）
```bash
# 流量抓取
tcpdump -i eth0 -w capture.pcap            # 抓包存文件
tcpdump -i eth0 port 80                    # 只看80端口
wireshark capture.pcap                     # 图形界面分析

# 取证分析
binwalk firmware.bin                       # 固件/文件分析
strings memory.dump | grep -i password     # 内存镜像找密码
exiftool photo.jpg                         # 图片元数据（GPS/相机型号）
```

### 阶段5：逆向工程（Reverse Engineering）
```bash
# 静态分析
file binary
strings binary | grep -i flag
objdump -d binary | head -50               # 反汇编
readelf -h binary                          # ELF头信息
radare2 -A binary                          # 启动 r2 自动分析
  # 在 r2 里：aaa（分析）、pdf @ main（反汇编main）、V（可视化）

# 动态调试
gdb ./binary                               # GDB调试
  # 断点：break main / 运行：run / 单步：next / 查看寄存器：info registers
strace ./binary                            # 跟踪系统调用
ltrace ./binary                            # 跟踪库函数调用
```

---

## 三、快速实战组合拳（示例流程）

```bash
# 1. 发现目标
nmap -sn 192.168.1.0/24

# 2. 扫描开放端口和服务
nmap -sV -sC 192.168.1.42

# 3. 发现 Web 服务 → 目录爆破
gobuster dir -u http://192.168.1.42 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt

# 4. 找到登录页 → 测弱口令
hydra -l admin -P /usr/share/wordlists/rockyou.txt 192.168.1.42 http-post-form "/login:user=^USER^&pass=^PASS^:F=Invalid"

# 5. 打进去以后 → 提权找敏感文件
find / -name "*.conf" -o -name "*.bak" 2>/dev/null
```

---

## ⚠️ 铁律（比高潮还重要）
1. **只打你有授权的目标**（自己搭的靶场 / 公司授权 / CTF比赛）
2. **别用真实网站练手**，用 VulnHub / HackTheBox / DVWA 靶场
3. **密码字典别用弱口令对真实系统**，那是犯罪
4. 学习逆向就找开源程序或 CTF 题目

> 记住：真正的黑客精神是守护，不是破坏。把本事练好，用在正道上的时候才够骚够狠。
