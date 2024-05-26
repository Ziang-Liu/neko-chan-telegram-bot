from httpx import URL, Proxy, Client
from httpx_socks import SyncProxyTransport

from src.utils.Logger import logger


def proxy_init(proxy: URL | str) -> Proxy:
    if isinstance(proxy, str):
        proxy = URL(proxy)

    if proxy.scheme not in ("http", "https", "socks5"):
        logger.error(f"Unknown scheme for proxy URL {proxy!r}")
        exit(1)

    if proxy.port is None:
        logger.error("No port specified.")
        exit(1)

    _test(str(proxy))

    if proxy.username or proxy.password == '':
        notice = f"{proxy.scheme}://username:password@{proxy.host}:{proxy.port}"
        logger.info(f"If you have authorization secret, use {notice} like this.")

        return Proxy(url = proxy)

    return Proxy(url = proxy, auth = (proxy.username, proxy.password))


def _test(proxy: str):
    transport = SyncProxyTransport.from_url(proxy)
    client = Client(transport = transport)

    try:
        response = client.get("https://httpbin.org/ip")

        if response.status_code != 200:
            logger.error(f"Proxy failed to respond. Status code: {response.status_code}")
            logger.error("Check your proxy URL or username/password")
            exit(1)
    except Exception as exc:
        logger.error(f"An error occurred: {exc}")
        exit(1)
    finally:
        client.close()
