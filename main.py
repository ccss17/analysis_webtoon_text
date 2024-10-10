import os
import os.path as path
import shutil
from multiprocessing import Pool, cpu_count
from glob import glob
from urllib.parse import *

from PIL import Image
from pytesseract import image_to_string
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

def download_webtoon_imgs(webtoon_page, root, title):
    headers = {
        'Host': 'image-comic.pstatic.net',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0',
        'Accept': 'image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5',
        'Accept-Language': 'en-US,en;q=0.8,ko-KR;q=0.5,ko;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Connection': 'keep-alive',
        'Referer': 'https://comic.naver.com/',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-GPC': '1',
        'Priority': 'u=5, i',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'TE': 'trailers',
    }

    parsed_url = urlparse(webtoon_page)
    parsed_query = parse_qs(parsed_url.query)
    dir_path = path.join(root, title, parsed_query['no'][0])

    resp = requests.get(webtoon_page)
    soup = BeautifulSoup(resp.text, 'html.parser')
    for img in soup.select('div.wt_viewer img'):
        img_path = path.join(dir_path, path.basename(urlparse(img['src']).path))
        if not path.exists(dir_path):
            os.makedirs(dir_path)
        if not path.exists(img_path) or os.stat(img_path).st_size == 0:
            r = requests.get(img['src'], headers=headers, stream=True)
            if r.status_code == 200:
                with open(img_path, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)        
    
    print(f'Download complete: {dir_path}')

def webtoon_pages(latest_page):
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

def download_webtoon(title, latest_page, root='imgs'):
    for webtoon_page in tqdm(webtoon_pages(latest_page)):
        download_webtoon_imgs(webtoon_page, root, title)

def download_webtoon_mp(title, latest_page, root='imgs'):
    args = [(webtoon_page, root, title) for webtoon_page in webtoon_pages(latest_page)]
    with Pool(cpu_count()) as p:
        p.starmap(download_webtoon_imgs, args)

def extract_text(img_dir):
    img_dir = img_dir.replace('\\', '/')
    txt_path = img_dir.replace('imgs', 'text') + '.txt'
    txt_dirpath = path.dirname(txt_path)
    if not path.exists(txt_dirpath):
        os.makedirs(txt_dirpath)
    if not path.exists(txt_path) or os.stat(txt_path).st_size == 0:
        with open(txt_path, 'w', encoding='utf-8') as f:
            for img_path in glob(img_dir + '/*'):
                img_path = img_path.replace('\\', '/')
                text = image_to_string(Image.open(img_path), lang='kor')
                f.write(text)
    print('Extract Text Complete: ', txt_path)

def download_extract(title, latest_page):
    download_webtoon_mp(title, latest_page)
    with Pool(cpu_count()) as p:
        p.map(extract_text, glob(f'imgs/{title}/*'))
    result_file = f'dataset/{title}.txt'
    if not path.exists(result_file) or os.stat(result_file).st_size == 0:
        with open(result_file, 'w', encoding='utf-8') as f:
            for txt in glob(f'text/{title}/*.txt'):
                with open(txt, encoding='utf-8') as inner:
                    f.write(inner.read())
    print('Output: ', result_file)

if __name__ == '__main__':
    title = '화산귀환'
    latest_page = 'https://comic.naver.com/webtoon/detail?titleId=769209&no=141&week=wed'
    # title = '에밀리의저택'
    # latest_page = 'https://comic.naver.com/webtoon/detail?titleId=824237&no=24&week=thu'
    download_extract(title, latest_page)