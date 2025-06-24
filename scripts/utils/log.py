from colorama import Fore, Style


def h1(msg):
    print(
        f"\n\n{Fore.CYAN}-------------------------------------------------------------------------")
    print(f"{Fore.CYAN}{msg}{Style.RESET_ALL}\n")


def h2(msg):
    print(f"\n{Fore.LIGHTBLUE_EX}▸ {msg}{Style.RESET_ALL}\n")


def h3(msg):
    print(f"\t{Fore.GREEN}{msg}{Style.RESET_ALL}")


def error(msg):
    print(f"{Fore.RED}{msg}{Style.RESET_ALL}")


def info(msg):
    print(msg)
