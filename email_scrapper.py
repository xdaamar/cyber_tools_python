from collections import deque
import re
from bs4 import BeautifulSoup
import requests
import urllib.parse
import sys

# memvalidasi dan memperbaiki URL input
def normalize_url_input(url):
    if not urllib.parse.urlsplit(url).scheme:
# tambahkan https:// secara default
        url = "https://" + url
    return url

user_url = str(input('[+] Masukan url: ')).strip()

# Validasi input awal
if not user_url:
    print("[-] URL tidak boleh kosong. Keluar.")
    sys.exit(1)

# Normalisasi URL input pengguna
user_url = normalize_url_input(user_url)

urls = deque([user_url])
scraped_urls = set()
emails = set()
count = 0

print(f"[*] Memulai scraping dari: {user_url}")

try:
    # Perulangan utama: Berjalan selama antrean 'urls' tidak kosong
    while urls:
        count += 1
        # Batasi jumlah halaman yang di-scrape untuk mencegah infinite loop atau terlalu lama
        if count > 50:
            print("[*] Batas iterasi (50 halaman) tercapai. Menghentikan scraping.")
            break

        try:
            url = urls.popleft()

            if url in scraped_urls:
                continue

            scraped_urls.add(url)
            
            # Parsing URL untuk mendapatkan base_url dan path
            parts = urllib.parse.urlsplit(url)
            base_url = f'{parts.scheme}://{parts.netloc}'
            path = url[:url.rfind('/')+1] if '/' in parts.path else url + '/'

            print(f'{count} Memproses {url}')

            # Mengirim permintaan HTTP dengan timeout
            # Menambahkan User-Agent agar terlihat seperti browser asli dan tidak mudah diblokir
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            response = requests.get(url, timeout=5, headers=headers)
            response.raise_for_status() # Memeriksa jika request mengembalikan status error (4xx atau 5xx)

        except requests.exceptions.RequestException as e:
            # Menangkap semua jenis kesalahan requests (koneksi, timeout, invalid URL, HTTP error status)
            print(f"[-] Gagal memproses {url}: {e}")
            continue
        except Exception as e:
            print(f"[-] Terjadi kesalahan tak terduga saat request URL {url}: {e}")
            continue

        # Mencari email
        new_emails = set(re.findall(r'[a-z0-9\.\-+_]+@\w+\.+[a-z\.]+', response.text, re.I))
        emails.update(new_emails)

        # Mencari tautan baru
        soup = BeautifulSoup(response.text, 'html.parser')
        for anchor in soup.find_all('a'):
            link = anchor.attrs.get('href', '')
            
            # Normalisasi tautan (menangani tautan relatif)
            if link.startswith('/'):
                link = base_url + link
            elif not link.startswith('http'):
                link = path + link
            
            # Pastikan link yang ditemukan juga dinormalisasi sebelum ditambahkan ke antrean
            link = normalize_url_input(link)

            # Tambahkan ke antrean jika belum pernah di-scrape atau belum ada di antrean
            if link not in urls and link not in scraped_urls:
                urls.append(link)

except KeyboardInterrupt:
    print('\n[-] Closing program by user request!')

print('\nProses Selesai!')
print(f'\n{len(emails)} email ditemukan \n ==============')

for mail in emails:
    print('  '+mail)
print('\n')
