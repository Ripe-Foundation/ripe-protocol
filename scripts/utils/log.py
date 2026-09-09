import os

from colorama import Fore, Style


def h1(msg):
    print(f"\n{Fore.CYAN}-------------------------------------------------------------------------")
    print(f"{Fore.CYAN}{msg}{Style.RESET_ALL}")


def h2(msg):
    print(f"\n{Fore.LIGHTBLUE_EX}▸ {msg}{Style.RESET_ALL}")


def h3(msg):
    print(f"\t{Fore.GREEN}{msg}{Style.RESET_ALL}")


def error(msg):
    print(f"{Fore.RED}{msg}{Style.RESET_ALL}")


def info(msg):
    print(msg)


def detail(msg):
    """Print noisy operator details only when explicitly requested."""
    enabled = os.environ.get("RIPE_MIGRATION_VERBOSE", "").strip().lower()
    if enabled in {"1", "true", "yes", "on"}:
        print(msg)
