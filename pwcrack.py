#!/usr/bin/python3
## made by v4mp1r3
import os; import threading; import zipfile; import argparse; from utils import Wordlist

wl = Wordlist()

def crack(file, wordlist):
    password = ""
    for item in wl.get():
        file.extractall()
    return password
def main():
    parser = argparse.ArgumentParser(description="Zip password cracker")
    parser.add_argument("file", help="zip file name, include file path if not in same directory", type=str)

    subparsers = parser.add_subparsers(dest="mode", required=True, help="attack mode")

    # Wordlist mode
    wordlist_parser = subparsers.add_parser("wordlist", help="use wordlist attack")
    wordlist_parser.add_argument("wordlist", help="word list file name", type=str)

    # Brute force mode  
    brute_parser = subparsers.add_parser("bruteforce", help="use brute force attack")
    brute_parser.add_argument("characters", help="max character length", type=int)
    brute_parser.add_argument("-C", "--charset", 
                            help="Select character set",
                            default="MiniASCII",
                            choices=["MiniASCII", "lower", "upper", "letters", "alphanum", "all"])

    # Common optional argument
    parser.add_argument("-e", "--extractpath", help="path for file extraction", type=str, default=".")

    args = parser.parse_args()
    
    #USAGE: python script.py archive.zip wordlist passwords.txt
    #       python script.py archive.zip bruteforce 4
    #       python script.py archive.zip bruteforce 4 --charset alphanum

    if args.wordlist:
        wl.get_from_file(args.wordlist)
    elif args.characters:
        wl.get_from_length(args.characters)
    zip = zipfile.ZipFile(args.file)
    try:
        zip.extractall(path=args.extractpath)
    except:
        password = crack(zip, wl.get())
    

if __name__ == '__main__':
    main()