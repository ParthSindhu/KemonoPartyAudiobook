import requests
import json
import os
from bs4 import BeautifulSoup, NavigableString
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_all_posts(user_id=""):
    base_url = f"https://kemono.party/api/v1/patreon/user/{user_id}"
    all_posts = []
    offset = 0

    while True:
        url = f"{base_url}?o={offset}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            posts = response.json()

            if not posts:
                break

            all_posts.extend(posts)
            offset += 50
        except requests.RequestException as e:
            logging.info(f"Error fetching posts: {e}")
            break

    # Sort posts by 'id' in ascending order
    reversed_posts = all_posts[::-1]
    reversed_posts.sort(key=lambda post: int(post['id']))

    return reversed_posts

def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    # Iterate over each paragraph and other block elements
    for element in soup.find_all(['p', 'div', 'br', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        if element.name == 'br':
            element.replace_with('\n\n')
        else:
            element.append('\n\n')

    # Get text from the soup object
    text = ''.join([str(elem) if isinstance(elem, NavigableString) else elem.get_text() for elem in soup.contents])

    return text.strip()

def read_next_post(posts_filename="filtered_posts.json", books_directory="books"):
    if not os.path.exists(books_directory):
        os.makedirs(books_directory)

    with open(posts_filename, 'r', encoding='utf-8') as file:
        posts = json.load(file)
    result = None
    for post in posts:
        post_id = post['id']
        post_title = post['title'].replace('/', '_')
        filename = os.path.join(books_directory, f"{post_id}_{post_title}.txt")

        if not os.path.exists(filename):
            result = filename, clean_html(post['content'])
            break
    return result

def confirm_post_read(post_filename, post_content):
    with open(post_filename, 'w', encoding='utf-8') as output_file:
        output_file.write(post_content)

def filter_and_save_posts(posts, filter_text, filename="filtered_posts.json"):
    filtered_posts = [post for post in posts if filter_text in post.get("title", "")]
    
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(filtered_posts, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    user = ""
    filter_text = ""
    # Fetch, sort, and save posts
    all_posts = fetch_all_posts(user)
    filter_and_save_posts(all_posts, filter_text)
