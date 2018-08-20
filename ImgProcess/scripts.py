import requests
from bs4 import BeautifulSoup
import os
import sys


def get_ip():
    """获取主机公网ip"""
    response = requests.get("http://ip.chinaz.com")
    soup = BeautifulSoup(response.text, 'html.parser')
    ip = soup.find("dd", attrs={"class": "fz24"})
    if ip is not None:
        return ip.text
    return '未知'


def text_replace():
    usage = "usage: %s search_text replace_text [infilename [outfilename]]" % os.path.basename(
        sys.argv[0])

    if len(sys.argv) < 3:
        print(usage)

    else:
        source_text = sys.argv[1]
        replace_text = sys.argv[2]
        print("There are %s args " % len(sys.argv))

        if len(sys.argv) > 4:
            source_file = open(sys.argv[3])
            destination_file = open(sys.argv[4], 'w')

            for s in source_file:
                destination_file.write(s.replace(source_text, replace_text))

            source_file.close()
            destination_file.close()


if __name__ == '__main__':
    print(os.system('shutdown /a'))
