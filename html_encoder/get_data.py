from typing import Optional
import requests

def get_data(link: str) -> Optional[requests.Response]:
    try:
        session = requests.Session()
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11;"
            " Linux x86_64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/44.0.2403.157"
            " Safari/537.36"
        )
        return session.get(link, timeout=2)
    except requests.exceptions.Timeout as e:
        print(e)
    except Exception as e:
        print(link, e)
