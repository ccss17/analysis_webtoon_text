import sys
import os
import os.path as path
import shutil
import multiprocessing as mp
from glob import glob
from urllib.parse import *
import traceback

from PIL import Image
import pytesseract
import requests
from bs4 import BeautifulSoup

from wt_list import *

def download_webtoon_imgs(webtoon_page, title, header_set, root='imgs'):
    parsed_url = urlparse(webtoon_page)
    parsed_query = parse_qs(parsed_url.query)
    dir_path = path.join(root, title, parsed_query['no'][0])

    resp = requests.get(webtoon_page, headers=header_set[0])
    soup = BeautifulSoup(resp.text, 'html.parser')
    for img in soup.select('div.wt_viewer img'):
        img_path = path.join(dir_path, path.basename(urlparse(img['src']).path))
        if not path.exists(dir_path):
            os.makedirs(dir_path)
        if not path.exists(img_path) or os.stat(img_path).st_size == 0:
            try:
                r = requests.get(img['src'], headers=header_set[1], stream=True)
                if r.status_code == 200:
                    with open(img_path, 'wb') as f:
                        r.raw.decode_content = True
                        shutil.copyfileobj(r.raw, f)        
            except Exception:
                traceback.print_exc(file=sys.stderr)
                print(f'arg: {title} <- {webtoon_page}', file=sys.stderr)
                print('='*80, file=sys.stderr)
    
    print(f'Download complete: {dir_path}')
    return dir_path

def webtoon_page_list(latest_page):
    parsed_url = urlparse(latest_page)
    parsed_query = parse_qs(parsed_url.query)
    latest = int(parsed_query['no'][0]) + 1
    pages = []
    for i in range(1, latest):
        parsed_query.update({'no':repr(i)})
        webtoon_page = parsed_url._replace(
            query=urlencode(
                parsed_query, doseq=True)).geturl()
        pages.append(webtoon_page)
    return pages

def extract_text(img_dir, img_root='imgs', text_root='text'):
    img_dir = img_dir.replace('\\', '/')
    txt_path = img_dir.replace(img_root, text_root) + '.txt'
    txt_dirpath = path.dirname(txt_path)
    if not path.exists(txt_dirpath):
        try:
            os.makedirs(txt_dirpath)
        except FileExistsError:
            pass
    if not path.exists(txt_path) or os.stat(txt_path).st_size == 0:
        with open(txt_path, 'w', encoding='utf-8') as f:
            for img_path in glob(img_dir + '/*'):
                img_path = img_path.replace('\\', '/')
                text = pytesseract.image_to_string(Image.open(img_path), lang='kor')
                f.write(text)
    print('Extract Text Complete: ', txt_path)

def download_extract_page(webtoon_page, title, header_set, img_root='imgs', text_root='text'):
    img_dir = download_webtoon_imgs(webtoon_page, title, header_set, img_root)
    extract_text(img_dir, img_root=img_root, text_root=text_root)

def download_extract_webtoon(title, latest_page, label, header_set, index, processes=4):
    result_file = f'dataset/{label}/{index}-{title}.txt'
    result_dirpath = path.dirname(result_file)
    if not path.exists(result_dirpath):
        os.makedirs(result_dirpath)
    if not path.exists(result_file) or os.stat(result_file).st_size == 0:
        args = [(webtoon_page, title, header_set) for webtoon_page in webtoon_page_list(latest_page)]
        with mp.Pool(processes) as p:
            p.starmap(download_extract_page, args)
        with open(result_file, 'w', encoding='utf-8') as f:
            for txt in glob(f'text/{title}/*.txt'):
                with open(txt, encoding='utf-8') as inner:
                    f.write(inner.read())
    print('Output: ', result_file)

def parse_headers(raw_headers):
    headers = {}
    for i, line in enumerate(raw_headers.split('\n')):
        if i == 0:
            continue
        k, v = line.split(': ')
        headers[k] = v
    return headers

def webtoon_title(url, headers):
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    title = soup.select('title')[0].text.split('-')[0].strip()
    for bad_character in r'<>:"/\|?*':
        title = title.replace(bad_character, '')
    return f"    ('{title}', '{url}'),"

def duplicated_webtoon():
    print(set(WEBTOON_FOR_FEMALE) & set(WEBTOON_FOR_MALE))

def parse_cookie(raw_cookie):
    cookie = {}
    for chunk in raw_cookie.split(';'):
        k, v = chunk.split('=', 1)
        cookie[k] = v
    return cookie

def test(request_page_headers, request_img_headers):
    header_set = (parse_headers(request_page_headers), 
                  parse_headers(request_img_headers))
    download_webtoon_imgs('https://comic.naver.com/webtoon/detail?titleId=822640&no=30', '소꿉친구 컴플렉스', header_set, 'test')

def run(request_page_headers, request_img_headers):
    header_set = (parse_headers(request_page_headers), 
                  parse_headers(request_img_headers))
    for i, webtoon in enumerate(WEBTOON_FOR_MALE):
        download_extract_webtoon(*webtoon, 'male', header_set, i+1, processes=4)
    for i, webtoon in enumerate(WEBTOON_FOR_FEMALE):
        download_extract_webtoon(*webtoon, 'female', header_set, i+1, processes=4)

def webtoon_title_list(request_page_headers):
    urls = '''
https://comic.naver.com/webtoon/detail?titleId=811716&no=70&week=wed
https://comic.naver.com/webtoon/detail?titleId=823076&no=27&week=thu
https://comic.naver.com/webtoon/detail?titleId=742105&no=196&week=wed
https://comic.naver.com/webtoon/detail?titleId=814599&no=57&week=wed
https://comic.naver.com/webtoon/detail?titleId=783052&no=154&week=mon
https://comic.naver.com/webtoon/detail?titleId=819929&no=42&week=tue
https://comic.naver.com/webtoon/detail?titleId=809694&no=73&week=sat
https://comic.naver.com/webtoon/detail?titleId=765158&no=166&week=wed
https://comic.naver.com/webtoon/detail?titleId=822931&no=28&week=tue
https://comic.naver.com/webtoon/detail?titleId=831168&no=5&week=tue
https://comic.naver.com/webtoon/detail?titleId=824782&no=23&week=mon
https://comic.naver.com/webtoon/detail?titleId=829830&no=7&week=wed
https://comic.naver.com/webtoon/detail?titleId=828167&no=25&week=mon
https://comic.naver.com/webtoon/detail?titleId=820104&no=83&week=thu
https://comic.naver.com/webtoon/detail?titleId=820104&no=83&week=thu
https://comic.naver.com/webtoon/detail?titleId=827863&no=16&week=fri
https://comic.naver.com/webtoon/detail?titleId=796252&no=82&week=sat
https://comic.naver.com/webtoon/detail?titleId=812164&no=68&week=thu
https://comic.naver.com/webtoon/detail?titleId=818448&no=98&week=tue
https://comic.naver.com/webtoon/detail?titleId=818888&no=46&week=wed
https://comic.naver.com/webtoon/detail?titleId=804157&no=94&week=sun
https://comic.naver.com/webtoon/detail?titleId=814817&no=56&week=tue
https://comic.naver.com/webtoon/detail?titleId=827908&no=15&week=sun
https://comic.naver.com/webtoon/detail?titleId=820169&no=39&week=sun
https://comic.naver.com/webtoon/detail?titleId=818020&no=34&week=mon
https://comic.naver.com/webtoon/detail?titleId=773797&no=169&week=fri
https://comic.naver.com/webtoon/detail?titleId=760001&no=174&week=wed
https://comic.naver.com/webtoon/detail?titleId=760001&no=174&week=wed
https://comic.naver.com/webtoon/detail?titleId=817346&no=53&week=tue
https://comic.naver.com/webtoon/detail?titleId=822239&no=32&week=fri
https://comic.naver.com/webtoon/detail?titleId=821321&no=36&week=wed
https://comic.naver.com/webtoon/detail?titleId=814289&no=55&week=fri
https://comic.naver.com/webtoon/detail?titleId=807809&no=3&week=dailyPlus
https://comic.naver.com/webtoon/detail?titleId=825415&no=20&week=thu
https://comic.naver.com/webtoon/detail?titleId=832575&no=3&week=sat
https://comic.naver.com/webtoon/detail?titleId=821095&no=36&week=mon
https://comic.naver.com/webtoon/detail?titleId=807582&no=80&week=tue
https://comic.naver.com/webtoon/detail?titleId=827752&no=3&week=dailyPlus
https://comic.naver.com/webtoon/detail?titleId=828400&no=12&week=wed
https://comic.naver.com/webtoon/detail?titleId=786082&no=125&week=sun
https://comic.naver.com/webtoon/detail?titleId=797443&no=95&week=wed
https://comic.naver.com/webtoon/detail?titleId=828103&no=12&week=mon
https://comic.naver.com/webtoon/detail?titleId=827290&no=15&week=mon
https://comic.naver.com/webtoon/detail?titleId=804333&no=185&week=tue
https://comic.naver.com/webtoon/detail?titleId=602910&no=512&week=mon
https://comic.naver.com/webtoon/detail?titleId=824780&no=3&week=dailyPlus
'''
    for url in urls.strip().split('\n'):
        print(webtoon_title(url, headers=parse_headers(request_page_headers)))

if __name__ == '__main__':
    from pprint import pprint
    # test(request_page_headers=sys.argv[1], request_img_headers=sys.argv[2])
    run(request_page_headers=sys.argv[1], request_img_headers=sys.argv[2])
    # webtoon_title_list(request_page_headers=sys.argv[1])