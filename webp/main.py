import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import pdfkit
from pypdf import PdfWriter
import logging
import uuid
from flask import Flask, render_template, request, jsonify, send_file

# Flask App
app = Flask(__name__)

# Global task tracking
tasks = {}

from urllib.parse import urlparse

def get_domain_name(url):
    parsed = urlparse(url)
    return parsed.netloc  # returns 'gobyexample.com'

# Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger()

def check_wkhtmltopdf():
    try:
        pdfkit.configuration()
        logger.info("wkhtmltopdf found.")
        return True
    except OSError:
        logger.error("wkhtmltopdf not found. Please install it.")
        return False

def is_html_link(url):
    parsed = urlparse(url)
    if not parsed.scheme.startswith('http'):
        return False
    non_html_ext = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.pdf',
                    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip',
                    '.rar', '.tar', '.gz', '.mp3', '.mp4', '.avi', '.mov',
                    '.wmv', '.flv', '.mkv', '.css', '.js', '.json', '.xml',
                    '.woff', '.woff2', '.ttf')
    if any(parsed.path.lower().endswith(ext) for ext in non_html_ext):
        return False
    try:
        resp = requests.head(url, allow_redirects=True, timeout=5)
        return 'text/html' in resp.headers.get('Content-Type', '')
    except:
        return False

def extract_links(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.body
    if not body:
        return []
    links = set()
    for a in body.find_all('a', href=True):
        links.add(urljoin(base_url, a['href']))
    return list(links)

def fetch_html(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException:
        return None

def filter_html_links(links):
    filtered = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(is_html_link, link): link for link in links}
        for future in as_completed(futures):
            link = futures[future]
            try:
                if future.result():
                    filtered.append(link)
            except:
                pass
    return filtered

def save_pdf_from_url(url, output_path, config):
    try:
        pdfkit.from_url(url, output_path, configuration=config)
        return output_path
    except Exception as e:
        logger.error(f"Failed to generate PDF for {url}: {e}")
        return None

def merge_pdfs(pdf_files, output_pdf):
    writer = PdfWriter()
    for pdf_file in sorted(pdf_files):
        try:
            with open(pdf_file, 'rb') as f:
                writer.append(f)
        except:
            pass
    with open(output_pdf, 'wb') as out_f:
        writer.write(out_f)

def generate_pdf(url, output_pdf_path, task_state):
    task_state['status'] = 'Checking dependencies...'
    if not check_wkhtmltopdf():
        task_state['status'] = 'Missing wkhtmltopdf'
        return

    task_state['status'] = 'Fetching main page...'
    html = fetch_html(url)
    if not html:
        task_state['status'] = 'Failed to fetch main page'
        return

    task_state['status'] = 'Extracting links...'
    links = extract_links(html, url)
    html_links = filter_html_links(links)

    all_urls = [url] + html_links
    os.makedirs('./tmp_pdf_pages', exist_ok=True)
    config = pdfkit.configuration()
    pdf_files = []

    task_state['status'] = f'Generating {len(all_urls)} PDFs...'
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {}
        for i, page_url in enumerate(all_urls):
            pdf_path = f'./tmp_pdf_pages/page_{i}.pdf'
            futures[executor.submit(save_pdf_from_url, page_url, pdf_path, config)] = pdf_path
        for future in as_completed(futures):
            result_path = future.result()
            if result_path:
                pdf_files.append(result_path)

    if not pdf_files:
        task_state['status'] = 'PDF generation failed'
        return

    task_state['status'] = 'Merging PDFs...'
    merge_pdfs(pdf_files, output_pdf_path)
    task_state['status'] = 'Done'
    task_state['done'] = True
    task_state['file'] = output_pdf_path

# ----------------- Flask Routes -----------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def start_generation():
    url = request.form['url']
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'Starting...', 'done': False, 'file': None}

    def worker():
        domain = get_domain_name(url)
        os.makedirs('tmp_pdf_pages', exist_ok=True)
        output_path = f'tmp_pdf_pages/{domain}.pdf'  # Use domain as filename
        generate_pdf(url, output_path, tasks[task_id])

    from threading import Thread
    Thread(target=worker).start()

    return render_template('status.html', task_id=task_id)

@app.route('/status/<task_id>')
def task_status(task_id):
    return jsonify(tasks.get(task_id, {}))

@app.route('/download/<task_id>')
def download(task_id):
    file_path = tasks.get(task_id, {}).get('file')
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return 'File not found', 404

if __name__ == '__main__':
    app.run(debug=True)

