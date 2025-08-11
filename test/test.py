import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

base_url = 'https://unicons.iconscout.com/release/v4.0.0/'

# Create folders
os.makedirs('static/unicons/css', exist_ok=True)
os.makedirs('static/unicons/fonts', exist_ok=True)

# Step 1: Download the CSS
css_url = urljoin(base_url, 'css/line.css')
css_path = 'static/unicons/css/line.css'
css_content = requests.get(css_url).text

# Step 2: Parse font URLs from the CSS
soup = BeautifulSoup(f"<style>{css_content}</style>", "html.parser")
font_urls = set()
for line in css_content.splitlines():
    if "url(" in line:
        start = line.find("url(") + 4
        end = line.find(")", start)
        font_url = line[start:end].strip('\'"')
        full_url = urljoin(base_url + 'css/', font_url)
        font_urls.add(full_url)

# Step 3: Download each font
for font_url in font_urls:
    font_name = font_url.split("/")[-1]
    font_path = os.path.join('static/unicons/fonts', font_name)
    with open(font_path, 'wb') as f:
        f.write(requests.get(font_url).content)

# Step 4: Rewrite CSS font paths
for original_url in font_urls:
    file_name = original_url.split('/')[-1]
    css_content = css_content.replace(original_url.replace(base_url + 'css/', ''), f'/static/unicons/fonts/{file_name}')

# Step 5: Save the updated CSS
with open(css_path, 'w') as f:
    f.write(css_content)
