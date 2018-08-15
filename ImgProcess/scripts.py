import requests
from bs4 import BeautifulSoup


def get_ip():
    """获取主机公网ip"""
    response = requests.get("http://ip.chinaz.com")
    soup = BeautifulSoup(response.text, 'html.parser')
    ip = soup.find("dd", attrs={"class": "fz24"})
    if ip is not None:
        return ip.text
    return '未知'
