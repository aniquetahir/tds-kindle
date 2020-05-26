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
from datetime import datetime
from khut import send_mail
import json

CLAP_THRESHOLD = 0

tag_map = {
    'ml': 'machine-learning',
    'ai': 'artificial-intelligence',
    'ds': 'data-science'
}


def scrollBottom(wd: Firefox):
    total_height = int(wd.execute_script("return document.body.scrollHeight;"))
    for i in range(0, total_height, 500):
        wd.execute_script("window.scrollTo(0,%i)" % i)
        sleep(0.5)


def get_links(wd: Firefox, p_type: str, tag: str = None, limit: int = 10) -> List[Dict[str, Union[int, str]]]:
    links_url = 'https://towardsdatascience.com/latest'

    if tag:
        links_url = "https://towardsdatascience.com/tagged/%s" % tag_map[tag]

    print("Parsing Index Page: %s" % links_url)

    if p_type == 'trending':
        links_url = 'https://towardsdatascience.com/trending'
    wd.get(links_url)
    sleep(3)
    links = []
    num_articles = 0
    articles_parsed = 0
    while num_articles < limit:
        articles = wd.find_elements_by_css_selector('.postArticle')
        num_articles = len(articles)
        wd.execute_script('window.scrollTo(0,document.body.scrollHeight)')
        sleep(3)

    while True:
        for article in articles:
            title = article.find_element_by_css_selector('.graf--title').text.strip()
            # print(title)
            date = article.find_element_by_css_selector('time').get_attribute('datetime')
            try:
                claps = int(article.find_element_by_css_selector('.js-multirecommendCountButton').text)
            except:
                claps = 0
            try:
                comments = article.find_element_by_css_selector('.buttonSet.u-floatRight > a[href]').text
                comments = int(comments.split(' ')[0])
            except NoSuchElementException:
                comments = 0
            link = article.find_element_by_css_selector('.postArticle-content > a').get_attribute('href')

            if claps < CLAP_THRESHOLD:
                continue

            links.append({
                'title': title,
                'date': date,
                'claps': claps,
                'comments': comments,
                'link': link
            })

        if len(links) >= limit:
            break
        else:
            print("Getting More articles to match threshold...")
            articles_parsed += len(articles)
            wd.execute_script('window.scrollTo(0,document.body.scrollHeight)')
            sleep(5)
            articles = wd.find_elements_by_css_selector('.postArticle')[articles_parsed:]

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
    parser.add_argument('-type', choices=['trending', 'latest'])
    parser.add_argument('-c', required=True, type=int, help="The clap threshold")
    parser.add_argument('-tag', choices=['ml', 'ds', 'ai'],
                        help="Select a tag: ml(Machine Learning), ds(Data Science), or ai(Artificial Intelligence)")

    args = parser.parse_args()
    if not args.type:
        p_type = 'latest'
    else:
        p_type = args.type

    CLAP_THRESHOLD = int(args.c)

    config_filename = "config.json"
    config = None
    if os.path.exists("config.local.json"):
        config_filename = "config.local.json"

    with open(config_filename) as config_file:
        config = json.load(config_file)

    ff_path = config['FIREFOX_PATH']
    gd_path = config['GECKODRIVER_PATH']

    if os.path.exists('tmp'):
        shutil.rmtree('tmp')

    os.mkdir('tmp')

    fo = Options()
    fo.headless = True
    wd = Firefox(executable_path=gd_path, firefox_binary=ff_path, options=fo)
    wd.header_overrides = {
        'Referer': 'https://twitter.com/freedom',
    }
    links = get_links(wd, p_type, args.tag)

    # TODO Filter out links already parsed and sent

    for link in links:
        get_html(wd, link)
        wd.delete_all_cookies()
        wd.execute_script('window.localStorage.clear()')
        wd.execute_script('window.sessionStorage.clear()')

    # TODO Create TOC

    html_files = []
    for i, link in enumerate(links):

        with open('tmp/%i.html' % i, 'w') as tmp_html:
            tmp_html.write(link['html'])

        html_files.append('tmp/%i.html' % i)

    cmd_args = [
        'html2pdf/main.js'
    ]

    for f in html_files:
        cmd_args.append('file://%s' % os.path.abspath(f))

    category = ""
    if args.type:
        category = args.type + "_"

    output_filename = 'update_%s%s.pdf' % (category, datetime.now().strftime("%d_%b_%y"))

    cmd_args.append(output_filename)

    run(cmd_args)
    # template = template.replace('{articles}', html_accumulated)
    #
    # with open('update.html', 'w', encoding='utf8') as update_file:
    #     update_file.write(template)

    # TODO email recipients
    send_mail(config['email_from'], config['email_to'],
              config['email_subject'], config['smtp_server'],
              config['smtp_port'], config['smtp_username'],
              config['smtp_password'],
              [{
                  'path': os.path.abspath(output_filename),
                  'type': 'application',
                  'subtype': 'pdf'
              }])

    wd.close()

