#! /usr/bin/env python3
from seleniumwire.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
import argparse
import os
from typing import Dict, List, Union
from time import sleep
import shutil
from subprocess import run

def scrollBottom(wd: Firefox):
    total_height = int(wd.execute_script("return document.body.scrollHeight;"))
    for i in range(0, total_height, 500):
        wd.execute_script("window.scrollTo(0,%i)" % i)
        sleep(0.5)


def get_links(wd: Firefox, p_type: str, limit: int = 10) -> List[Dict[str, Union[int, str]]]:
    links_url = 'https://towardsdatascience.com/latest'
    if p_type == 'trending':
        links_url = 'https://towardsdatascience.com/trending'
    wd.get(links_url)
    sleep(3)
    links = []
    num_articles = 0
    while num_articles < limit:
        articles = wd.find_elements_by_css_selector('.postArticle')
        num_articles = len(articles)
        wd.execute_script('window.scrollTo(0,document.body.scrollHeight)')
        sleep(3)

    for article in articles:
        title = article.find_element_by_css_selector('.graf--title').text.strip()
        # print(title)
        date = article.find_element_by_css_selector('time').get_attribute('datetime')
        try:
            claps = article.find_element_by_css_selector('.js-multirecommendCountButton').text
        except:
            claps = 0
        try:
            comments = article.find_element_by_css_selector('.buttonSet.u-floatRight > a[href]').text
            comments = int(comments.split(' ')[0])
        except NoSuchElementException:
            comments = 0
        link = article.find_element_by_css_selector('.postArticle-content > a').get_attribute('href')

        links.append({
            'title': title,
            'date': date,
            'claps': claps,
            'comments': comments,
            'link': link
        })

    return links[:limit]


def get_html(wd: Firefox, article: Dict[str, Union[int, str]]) -> Dict[str, str]:
    wd.get(article['link'])
    print(article['title'])
    sleep(3)

    # Scroll to the bottom to load images
    scrollBottom(wd)

    # For each image, replace with base64
    with open('convert_images.js', 'r') as script_file:
        script_src = script_file.read()

    wd.execute_script(script_src)

    sleep(5)
    # Get html of the page
    article_div = wd.find_element_by_css_selector('article')

    html = article_div.get_property('outerHTML')

    with open('cleanify.js') as script_file:
        script_src = script_file.read()
        wd.execute_script(script_src)
        sleep(3)
    html: str = wd.page_source
    html = html.replace('max-width:680px', 'max-width:90%')

    article['html'] = html


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gets Towards Data Science articles and sends them to your kindle")
    parser.add_argument('-t', choices=['trending', 'latest'])
    args = parser.parse_args()
    if not args.t:
        p_type = 'trending'
    else:
        p_type = args.t

    ff_path = 'firefox'
    gd_path = 'geckodriver'

    if 'FIREFOX_PATH' in os.environ.keys():
        ff_path = os.environ['FIREFOX_PATH']

    if 'GECKODRIVER_PATH' in os.environ.keys():
        gd_path = os.environ['GECKODRIVER_PATH']

    if os.path.exists('tmp'):
        shutil.rmtree('tmp')

    os.mkdir('tmp')

    fo = Options()
    fo.headless = True
    wd = Firefox(executable_path=gd_path, firefox_binary=ff_path, options=fo)
    wd.header_overrides = {
        'Referer': 'https://twitter.com/freedom',
    }
    links = get_links(wd, p_type)

    # TODO Filter out links already parsed and sent

    for link in links:
        get_html(wd, link)
        wd.delete_all_cookies()
        wd.execute_script('window.localStorage.clear()')
        wd.execute_script('window.sessionStorage.clear()')


    # TODO Create TOC

    # with open('template.html') as template_file:
    #     template = template_file.read()
    #
    # with open('style.css') as style_file:
    #     style = style_file.read()
    #     template = template.replace('{style}', style)

    html_files = []
    for i, link in enumerate(links):

        with open('tmp/%i.html' % i, 'w') as tmp_html:
            tmp_html.write(link['html'])

        html_files.append('tmp/%i.html' % i)

    cmd_args = [
        'wkhtmltopdf',
        '-s',
        'A5',
        '-l',
        '-g',
        '-d',
        '400',
        '--enable-smart-shrinking'
    ]

    for f in html_files:
        cmd_args.append(f)

    cmd_args.append('update.pdf')

    run(cmd_args)
    # template = template.replace('{articles}', html_accumulated)
    #
    # with open('update.html', 'w', encoding='utf8') as update_file:
    #     update_file.write(template)

    # TODO email recipients

    wd.close()

