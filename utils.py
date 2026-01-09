import itertools
import string
import threading
import queue
import time
from typing import Generator, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class AttackMode(Enum):
    WORDLIST = "wordlist"
    BRUTEFORCE = "bruteforce"

@dataclass
class CrackResult:
    success: bool
    password: Optional[str] = None
    attempts: int = 0
    time_elapsed: float = 0.0
    thread_id: int = 0
    error: Optional[str] = None

class Wordlist:
    def __init__(self):
        self.generator = None
        self.total = 0
        
    def get_from_file_generator(self, filename: str) -> Generator[str, None, None]:
        """Cross-platform file reading with generator"""
        try:
            # Try UTF-8 first (Linux/macOS), fall back to latin-1 (Windows compatibility)
            try:
                with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        password = line.strip()
                        if password:
                            yield password
            except UnicodeDecodeError:
                # Fallback for Windows or odd encodings
                with open(filename, 'r', encoding='latin-1', errors='ignore') as f:
                    for line in f:
                        password = line.strip()
                        if password:
                            yield password
        except FileNotFoundError:
            raise FileNotFoundError(f"Wordlist file not found: {filename}")
        except Exception as e:
            raise Exception(f"Cannot read wordlist: {e}")
    
    def get_from_length_generator(self, length: int, charset: str = "MiniASCII") -> Generator[str, None, None]:
        """Generate passwords for brute force"""
        # Define character sets (same for all platforms)
        charsets = {
            "MiniASCII": string.ascii_lowercase + string.digits,
            "lower": string.ascii_lowercase,
            "upper": string.ascii_uppercase,
            "letters": string.ascii_letters,
            "alphanum": string.ascii_letters + string.digits,
            "all": string.ascii_letters + string.digits + string.punctuation,
        }
        
        # Get charset
        if charset in charsets:
            chars = charsets[charset]
        else:
            chars = charset  # Assume custom charset
        
        # Create generator
        def brute_generator():
            for i in range(1, length + 1):
                for combo in itertools.product(chars, repeat=i):
                    yield ''.join(combo)
        
        self.generator = brute_generator()
        return self.generator
    
    def estimate_combinations(self, length: int, charset: str = "MiniASCII") -> int:
        """Estimate total combinations"""
        charsets = {
            "MiniASCII": string.ascii_lowercase + string.digits,
            "lower": string.ascii_lowercase,
            "upper": string.ascii_uppercase,
            "letters": string.ascii_letters,
            "alphanum": string.ascii_letters + string.digits,
            "all": string.ascii_letters + string.digits + string.punctuation,
        }
        
        if charset in charsets:
            chars = charsets[charset]
        else:
            chars = charset
        
        char_count = len(chars)
        return sum(char_count ** i for i in range(1, length + 1))

class ThreadedZipCracker:
    """
    Multi-threaded zip password cracker
    Usage:
        cracker = ThreadedZipCracker(zip_path, extract_path=".")
        result = cracker.crack_wordlist("passwords.txt", threads=4)
        # or
        result = cracker.crack_bruteforce(4, charset="alphanum", threads=4)
    """
    
    def __init__(self, zip_path: str, extract_path: str = ".", verbose: bool = True):
        self.zip_path = zip_path
        self.extract_path = extract_path
        self.verbose = verbose
        self.wordlist = Wordlist()
        self._stop_event = threading.Event()
        self._found_event = threading.Event()
        self._result_queue = queue.Queue()
        self._stats_lock = threading.Lock()
        self._total_attempts = 0
        self._start_time = 0
        
    def _worker(self, thread_id: int, password_queue: queue.Queue, stats_interval: int = 1000):
        """Worker thread that tries passwords from the queue"""
        import zipfile
        
        attempts = 0
        last_report = time.time()
        
        try:
            zip_file = zipfile.ZipFile(self.zip_path)
        except Exception as e:
            self._result_queue.put(CrackResult(
                success=False,
                thread_id=thread_id,
                error=f"Cannot open zip: {e}"
            ))
            return
        
        while not self._stop_event.is_set() and not self._found_event.is_set():
            try:
                # Get password with timeout to check stop event
                password = password_queue.get(timeout=0.1)
                attempts += 1
                
                # Try password
                try:
                    zip_file.extractall(path=self.extract_path, pwd=password.encode('utf-8'))
                    
                    # SUCCESS!
                    self._found_event.set()
                    self._result_queue.put(CrackResult(
                        success=True,
                        password=password,
                        attempts=attempts,
                        thread_id=thread_id,
                        time_elapsed=time.time() - self._start_time
                    ))
                    break
                    
                except (RuntimeError, zipfile.BadZipFile):
                    # Wrong password
                    pass
                except Exception as e:
                    # Other error
                    if self.verbose:
                        print(f"[Thread {thread_id}] Error: {e}")
                
                # Update stats
                with self._stats_lock:
                    self._total_attempts += 1
                
                # Periodic reporting
                if self.verbose and time.time() - last_report > 1.0:  # Every second
                    with self._stats_lock:
                        elapsed = time.time() - self._start_time
                        rate = self._total_attempts / elapsed if elapsed > 0 else 0
                        print(f"[Thread {thread_id}] {self._total_attempts:,} total | {rate:.0f}/sec | Current: {password[:20]}...", end='\r')
                    last_report = time.time()
                    
            except queue.Empty:
                # Queue empty, check if we should continue
                continue
            except Exception as e:
                if self.verbose:
                    print(f"[Thread {thread_id}] Error: {e}")
        
        zip_file.close()
        
        if self.verbose and not self._found_event.is_set():
            print(f"[Thread {thread_id}] Finished after {attempts:,} attempts")
    
    def _password_producer(self, generator: Generator, password_queue: queue.Queue, buffer_size: int = 1000):
        """Produce passwords from generator to queue"""
        buffer = []
        
        for password in generator:
            if self._found_event.is_set() or self._stop_event.is_set():
                break
                
            buffer.append(password)
            
            # Fill buffer before putting to queue
            if len(buffer) >= buffer_size:
                for pwd in buffer:
                    if self._found_event.is_set():
                        break
                    password_queue.put(pwd)
                buffer.clear()
        
        # Put remaining passwords
        for pwd in buffer:
            if self._found_event.is_set():
                break
            password_queue.put(pwd)
    
    def crack_wordlist(self, wordlist_path: str, threads: int = 4, buffer_size: int = 1000) -> CrackResult:
        """Crack using wordlist with multiple threads"""
        print(f"[*] Starting wordlist attack with {threads} threads")
        print(f"[*] Wordlist: {wordlist_path}")
        
        # Create password generator
        try:
            password_generator = self.wordlist.get_from_file_generator(wordlist_path)
        except Exception as e:
            return CrackResult(success=False, error=str(e))
        
        return self._crack_with_generator(password_generator, threads, buffer_size, AttackMode.WORDLIST)
    
    def crack_bruteforce(self, max_length: int, charset: str = "MiniASCII", 
                         threads: int = 4, buffer_size: int = 1000) -> CrackResult:
        """Crack using brute force with multiple threads"""
        print(f"[*] Starting brute force attack with {threads} threads")
        print(f"[*] Max length: {max_length}, Charset: {charset}")
        
        # Estimate combinations
        estimated = self.wordlist.estimate_combinations(max_length, charset)
        print(f"[*] Estimated combinations: {estimated:,}")
        
        if estimated > 1000000:
            print("[!] WARNING: Over 1 million combinations!")
        
        # Create password generator
        try:
            password_generator = self.wordlist.get_from_length_generator(max_length, charset)
        except Exception as e:
            return CrackResult(success=False, error=str(e))
        
        return self._crack_with_generator(password_generator, threads, buffer_size, AttackMode.BRUTEFORCE)
    
    def _crack_with_generator(self, password_generator: Generator, threads: int, 
                             buffer_size: int, mode: AttackMode) -> CrackResult:
        """Common cracking logic with generator"""
        # Reset events and stats
        self._stop_event.clear()
        self._found_event.clear()
        self._total_attempts = 0
        self._start_time = time.time()
        
        # Create queues
        password_queue = queue.Queue(maxsize=buffer_size * 2)
        
        # Start producer thread
        producer_thread = threading.Thread(
            target=self._password_producer,
            args=(password_generator, password_queue, buffer_size),
            daemon=True
        )
        producer_thread.start()
        
        # Start worker threads
        worker_threads = []
        for i in range(threads):
            thread = threading.Thread(
                target=self._worker,
                args=(i + 1, password_queue),
                daemon=True
            )
            thread.start()
            worker_threads.append(thread)
        
        # Wait for result
        try:
            result = self._result_queue.get(timeout=3600 * 24)  # 24 hour timeout
            self._stop_event.set()
            
            # Wait for threads to finish
            producer_thread.join(timeout=1)
            for thread in worker_threads:
                thread.join(timeout=1)
            
            return result
            
        except queue.Empty:
            self._stop_event.set()
            return CrackResult(
                success=False,
                attempts=self._total_attempts,
                time_elapsed=time.time() - self._start_time,
                error="Timeout or no password found"
            )
        except KeyboardInterrupt:
            print("\n[*] Interrupted by user")
            self._stop_event.set()
            return CrackResult(
                success=False,
                attempts=self._total_attempts,
                time_elapsed=time.time() - self._start_time,
                error="Interrupted by user"
            )
    
    def stop(self):
        """Stop the cracking process"""
        self._stop_event.set()

class ProgressReporter:
    """Thread-safe progress reporting"""
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self._lock = threading.Lock()
        self._last_update = 0
        self._attempts = 0
        self._start_time = time.time()
    
    def increment(self, count: int = 1):
        with self._lock:
            self._attempts += count
            
            # Throttle updates
            current_time = time.time()
            if current_time - self._last_update >= self.update_interval:
                elapsed = current_time - self._start_time
                rate = self._attempts / elapsed if elapsed > 0 else 0
                print(f"[Progress] {self._attempts:,} attempts | {rate:.0f}/sec", end='\r')
                self._last_update = current_time
    
    def get_stats(self):
        with self._lock:
            elapsed = time.time() - self._start_time
            rate = self._attempts / elapsed if elapsed > 0 else 0
            return {
                'attempts': self._attempts,
                'elapsed': elapsed,
                'rate': rate
            }