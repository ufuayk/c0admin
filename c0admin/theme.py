from colorama import Fore, Style

THEMES = {
    "default": {
        "prompt": Fore.CYAN,
        "info": Fore.BLUE,
        "ok": Fore.GREEN,
        "warn": Fore.YELLOW,
        "error": Fore.RED,
        "accent": Fore.MAGENTA,
        "title": Fore.CYAN + Style.BRIGHT,
        "dim": Style.DIM,
        "answer": Fore.WHITE,
        "reset": Style.RESET_ALL,
    },
    "hacker": {
        "prompt": Fore.GREEN,
        "info": Fore.GREEN,
        "ok": Fore.GREEN,
        "warn": Fore.YELLOW,
        "error": Fore.RED,
        "accent": Fore.GREEN + Style.BRIGHT,
        "title": Fore.GREEN + Style.BRIGHT,
        "dim": Fore.GREEN,
        "answer": Fore.GREEN,
        "reset": Style.RESET_ALL,
    },
    "ocean": {
        "prompt": Fore.CYAN,
        "info": Fore.BLUE,
        "ok": Fore.GREEN,
        "warn": Fore.YELLOW,
        "error": Fore.RED,
        "accent": Fore.CYAN + Style.BRIGHT,
        "title": Fore.BLUE + Style.BRIGHT,
        "dim": Fore.BLUE,
        "answer": Fore.WHITE,
        "reset": Style.RESET_ALL,
    },
    "sunset": {
        "prompt": Fore.MAGENTA,
        "info": Fore.MAGENTA,
        "ok": Fore.GREEN,
        "warn": Fore.YELLOW,
        "error": Fore.RED,
        "accent": Fore.YELLOW + Style.BRIGHT,
        "title": Fore.MAGENTA + Style.BRIGHT,
        "dim": Fore.WHITE,
        "answer": Fore.WHITE,
        "reset": Style.RESET_ALL,
    },
    "mono": {
        "prompt": "",
        "info": "",
        "ok": "",
        "warn": "",
        "error": "",
        "accent": "",
        "title": Style.BRIGHT,
        "dim": "",
        "answer": "",
        "reset": Style.RESET_ALL,
    },
}


def get_theme(name):
    return THEMES.get(name, THEMES["default"])


def list_themes():
    return list(THEMES.keys())
