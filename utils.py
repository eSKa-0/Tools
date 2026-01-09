#Made by v4mp1r3

import itertools
import string
from typing import Generator, Iterator

class Wordlist:
    def __init__(self):
        self.wordlist = []  # List for storing passwords
        self.generator = None  # Generator for memory-efficient iteration
        self.chars = 0  # Character count for brute force
        self._charset = ""  # Character set being used
        self._max_length = 0  # Max password length
        
    def create_file(self, path):
        """Save current wordlist to a file"""
        if not self.wordlist:
            print("[-] No passwords to save")
            return
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                for password in self.wordlist:
                    f.write(password + '\n')
            print(f"[+] Saved {len(self.wordlist)} passwords to {path}")
        except Exception as e:
            print(f"[-] Error creating file: {e}")
    
    def get_from_file(self, path):
        """Read passwords from file into memory"""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.wordlist = [line.strip() for line in f if line.strip()]
            print(f"[+] Loaded {len(self.wordlist)} passwords from {path}")
        except FileNotFoundError:
            print(f"[-] Error: File '{path}' not found")
            raise
        except Exception as e:
            print(f"[-] Error reading file: {e}")
            raise
    
    def get_from_file_generator(self, path) -> Generator[str, None, None]:
        """Create a generator to read passwords from file line by line (memory efficient)"""
        try:
            def file_generator():
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        password = line.strip()
                        if password:
                            yield password
            
            self.generator = file_generator()
            return self.generator
        except FileNotFoundError:
            print(f"[-] Error: File '{path}' not found")
            raise
        except Exception as e:
            print(f"[-] Error reading file: {e}")
            raise
    
    def get_from_length(self, length=4, charset="MiniASCII"):
        """
        Generate all possible combinations up to given length
        
        Args:
            length: Maximum password length (e.g., 4 = lengths 1-4)
            charset: Character set name or custom string
                    "MiniASCII" - lowercase + digits (default)
                    "lower" - lowercase letters only
                    "upper" - uppercase letters only
                    "letters" - both lower and uppercase
                    "alphanum" - letters + digits
                    "all" - letters + digits + punctuation
                    or custom string like "abc123"
        """
        # Define character sets
        charsets = {
            "MiniASCII": string.ascii_lowercase + string.digits,
            "lower": string.ascii_lowercase,
            "upper": string.ascii_uppercase,
            "letters": string.ascii_letters,
            "alphanum": string.ascii_letters + string.digits,
            "all": string.ascii_letters + string.digits + string.punctuation,
        }
        
        # Get the character set
        if charset in charsets:
            self._charset = charsets[charset]
        else:
            # Assume it's a custom character set string
            self._charset = charset
        
        self._max_length = length
        self.chars = len(self._charset)
        
        # Calculate total combinations
        total_combinations = sum(self.chars ** i for i in range(1, length + 1))
        
        print(f"[*] Using character set: {self._charset}")
        print(f"[*] Character count: {self.chars}")
        print(f"[*] Max password length: {length}")
        print(f"[*] Total combinations: {total_combinations:,}")
        
        # Generate all combinations and store in self.wordlist
        self.wordlist = []
        generated = 0
        
        for i in range(1, length + 1):
            for combo in itertools.product(self._charset, repeat=i):
                self.wordlist.append(''.join(combo))
                generated += 1
                
                # Show progress for large generations
                if generated % 100000 == 0:
                    print(f"[*] Generated {generated:,}/{total_combinations:,}...", end='\r')
        
        print(f"\n[+] Generated {len(self.wordlist):,} passwords")
    
    def get_from_length_generator(self, length=4, charset="MiniASCII") -> Generator[str, None, None]:
        """
        Create a generator for brute force combinations (memory efficient)
        
        Use this instead of get_from_length() for large password spaces
        """
        # Define character sets
        charsets = {
            "MiniASCII": string.ascii_lowercase + string.digits,
            "lower": string.ascii_lowercase,
            "upper": string.ascii_uppercase,
            "letters": string.ascii_letters,
            "alphanum": string.ascii_letters + string.digits,
            "all": string.ascii_letters + string.digits + string.punctuation,
        }
        
        # Get the character set
        if charset in charsets:
            self._charset = charsets[charset]
        else:
            # Assume it's a custom character set string
            self._charset = charset
        
        self._max_length = length
        self.chars = len(self._charset)
        
        # Calculate total combinations
        total_combinations = sum(self.chars ** i for i in range(1, length + 1))
        
        print(f"[*] Using character set: {self._charset}")
        print(f"[*] Character count: {self.chars}")
        print(f"[*] Max password length: {length}")
        print(f"[*] Total combinations: {total_combinations:,}")
        
        # Create generator function
        def brute_force_generator():
            generated = 0
            for i in range(1, length + 1):
                for combo in itertools.product(self._charset, repeat=i):
                    generated += 1
                    if generated % 100000 == 0:
                        print(f"[*] Generated {generated:,}/{total_combinations:,}...", end='\r')
                    yield ''.join(combo)
            print(f"\n[+] Generation complete")
        
        self.generator = brute_force_generator()
        return self.generator
    
    def get(self):
        """Get the wordlist as a list"""
        return self.wordlist
    
    def get_generator(self):
        """Get the current generator"""
        return self.generator
    
    def estimate_combinations(self, length=4, charset="MiniASCII"):
        """Estimate how many passwords will be generated"""
        # Define character sets
        charsets = {
            "MiniASCII": string.ascii_lowercase + string.digits,
            "lower": string.ascii_lowercase,
            "upper": string.ascii_uppercase,
            "letters": string.ascii_letters,
            "alphanum": string.ascii_letters + string.digits,
            "all": string.ascii_letters + string.digits + string.punctuation,
        }
        
        # Get the character set
        if charset in charsets:
            chars = charsets[charset]
        else:
            chars = charset
        
        char_count = len(chars)
        total = sum(char_count ** i for i in range(1, length + 1))
        return total
    
    def preview(self, count=10):
        """Show a preview of passwords"""
        if self.wordlist:
            print(f"[*] First {min(count, len(self.wordlist))} passwords:")
            for i, pwd in enumerate(self.wordlist[:count], 1):
                print(f"  {i:3}. {pwd}")
            if len(self.wordlist) > count:
                print(f"  ... and {len(self.wordlist) - count} more")
        elif self.generator:
            print("[*] Using generator mode (passwords not stored in memory)")
        else:
            print("[-] No passwords loaded or generated")

class BetterThreading:
    def __init__(s, amount=None):
        if amount != None:
            s.amount = amount
        else:
            s.amount = 6