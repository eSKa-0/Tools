#!/usr/bin/env python3
"""
Cross-Platform Threaded Zip Password Cracker
Stupid exams made me make this UGH
-v4
"""

import os
import sys
import argparse
import platform
from utils import ThreadedZipCracker, Wordlist

def print_banner():
    """Print a properly formatted banner with dynamic width"""
    import platform
    import os
    
    system = platform.system()
    python_version = platform.python_version()
    cpu_count = os.cpu_count() or 4
    
    # Calculate widths
    max_width = 58  # Total banner width
    content_width = max_width - 4  # Minus borders and padding
    
    # Format each line
    lines = [
        "THREADED ZIP PASSWORD CRACKER v2.0",
        f"Platform: {system}",
        f"Python: {python_version}",
        f"Cores: {cpu_count}",
        "",
        "Multi-threaded for faster cracking!"
    ]
    
    # Center and format each line
    formatted_lines = []
    for line in lines:
        if line == "":
            formatted_line = "║" + " " * content_width + "║"
        else:
            # Center the text
            padding = content_width - len(line)
            left_pad = padding // 2
            right_pad = padding - left_pad
            formatted_line = f"║{' ' * left_pad}{line}{' ' * right_pad}║"
        formatted_lines.append(formatted_line)
    
    # Create final banner
    top_border = "╔" + "═" * content_width + "╗"
    bottom_border = "╚" + "═" * content_width + "╝"
    
    banner = "\n".join([top_border] + formatted_lines + [bottom_border])
    print("\n" + banner + "\n")

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="Multi-threaded zip password cracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  zip_cracker.py archive.zip wordlist passwords.txt -t 8
  zip_cracker.py archive.zip bruteforce 4 -t 4 --charset alphanum
  zip_cracker.py archive.zip bruteforce 3 --charset lower -t 12 -e ./extracted

Threading:
  Use -t/--threads to specify number of threads (default: CPU count)
  More threads = faster cracking, but uses more CPU

Character sets:
  MiniASCII  - Lowercase + digits (a-z0-9) [DEFAULT]
  lower      - Lowercase letters only (a-z)
  upper      - Uppercase letters only (A-Z)
  letters    - All letters (a-zA-Z)
  alphanum   - Letters + digits (a-zA-Z0-9)
  all        - All printable ASCII
        """
    )
    
    parser.add_argument("file", help="Zip file to crack")
    
    subparsers = parser.add_subparsers(dest="mode", required=True, help="Attack mode")
    
    # Wordlist mode
    wordlist_parser = subparsers.add_parser("wordlist", help="Use wordlist attack")
    wordlist_parser.add_argument("wordlist", help="Path to wordlist file")
    
    # Brute force mode  
    brute_parser = subparsers.add_parser("bruteforce", help="Use brute force attack")
    brute_parser.add_argument("characters", type=int, help="Maximum password length")
    brute_parser.add_argument("-C", "--charset", 
                            help="Character set for brute force",
                            default="MiniASCII",
                            choices=["MiniASCII", "lower", "upper", "letters", "alphanum", "all"])
    
    # Common arguments
    parser.add_argument("-e", "--extractpath", 
                       help="Extraction path (default: current directory)",
                       default=".",
                       type=str)
    parser.add_argument("-t", "--threads", 
                       help="Number of threads (default: CPU cores)",
                       type=int,
                       default=os.cpu_count() or 4)
    parser.add_argument("-b", "--buffer", 
                       help="Buffer size for password queue (default: 1000)",
                       type=int,
                       default=1000)
    parser.add_argument("-q", "--quiet", 
                       help="Quiet mode (minimal output)",
                       action="store_true")
    
    args = parser.parse_args()
    
    # Validate file exists
    if not os.path.exists(args.file):
        print(f"[-] File not found: {args.file}")
        sys.exit(1)
    
    # Create extract directory if needed
    if args.extractpath != "." and not os.path.exists(args.extractpath):
        os.makedirs(args.extractpath, exist_ok=True)
    
    # Create cracker instance
    cracker = ThreadedZipCracker(
        zip_path=args.file,
        extract_path=args.extractpath,
        verbose=not args.quiet
    )
    
    print(f"[*] Using {args.threads} threads")
    print(f"[*] Target: {os.path.basename(args.file)}")
    
    # Start cracking based on mode
    if args.mode == "wordlist":
        if not os.path.exists(args.wordlist):
            print(f"[-] Wordlist not found: {args.wordlist}")
            sys.exit(1)
        
        result = cracker.crack_wordlist(
            wordlist_path=args.wordlist,
            threads=args.threads,
            buffer_size=args.buffer
        )
        
    elif args.mode == "bruteforce":
        # Estimate and warn
        wl = Wordlist()
        estimated = wl.estimate_combinations(args.characters, args.charset)
        
        if not args.quiet:
            print(f"[*] Max length: {args.characters}")
            print(f"[*] Charset: {args.charset}")
            print(f"[*] Estimated: {estimated:,} combinations")
        
        if estimated > 1000000 and not args.quiet:
            print("[!] WARNING: Over 1 million combinations!")
            
            if estimated > 10000000:
                response = input("[?] Continue? (y/N): ").strip().lower()
                if response != 'y':
                    print("[-] Cancelled")
                    sys.exit(0)
        
        result = cracker.crack_bruteforce(
            max_length=args.characters,
            charset=args.charset,
            threads=args.threads,
            buffer_size=args.buffer
        )
    
    else:
        print(f"[-] Unknown mode: {args.mode}")
        sys.exit(1)
    
    # Print results
    print("\n" + "="*60)
    
    if result.success:
        print(f"[✓] SUCCESS!")
        print(f"[✓] Password: {result.password}")
        print(f"[✓] Found by thread: {result.thread_id}")
        print(f"[✓] Time: {result.time_elapsed:.2f} seconds")
        print(f"[✓] Attempts: {result.attempts:,}")
        if result.time_elapsed > 0:
            print(f"[✓] Speed: {result.attempts/result.time_elapsed:.0f} attempts/sec")
        print(f"[✓] Extracted to: {os.path.abspath(args.extractpath)}")
    else:
        print(f"[✗] FAILED")
        if result.error:
            print(f"[✗] Error: {result.error}")
        if result.attempts > 0:
            print(f"[✗] Attempts: {result.attempts:,}")
            print(f"[✗] Time: {result.time_elapsed:.2f} seconds")
    
    print("="*60)
    
    sys.exit(0 if result.success else 1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[*] Interrupted by user")
        sys.exit(130 if platform.system() != "Windows" else 1)
    except Exception as e:
        print(f"\n[-] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)