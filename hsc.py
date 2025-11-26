#!/usr/bin/env python3
"""
SEO Domain Checker - Tools untuk pengecekan domain SEO marketing
Penggunaan: python seo_checker.py <file_input.txt>
"""

import sys
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import time

# Konfigurasi warna untuk output terminal
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def check_url(url: str, timeout: int = 10) -> Tuple[str, bool]:
    """
    Memeriksa apakah URL aktif atau tidak
    Returns: (url, is_active)
    """
    if url.strip().lower() == 'unavailable' or not url.strip():
        return (url, False)
    
    try:
        # Tambahkan https:// jika tidak ada protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.head(url, timeout=timeout, allow_redirects=True, headers=headers)
        
        # Jika HEAD tidak berhasil, coba GET
        if response.status_code >= 400:
            response = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers)
        
        return (url, response.status_code < 400)
    
    except Exception as e:
        return (url, False)

def parse_input_file(filename: str) -> Dict[str, List[str]]:
    """
    Membaca file input dan mengelompokkan link berdasarkan platform
    """
    platforms = {}
    current_platform = None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Deteksi platform baru (format: "Platform : count")
                if ':' in line and not line.startswith('>'):
                    platform_name = line.split(':')[0].strip()
                    current_platform = platform_name
                    platforms[current_platform] = []
                
                # Deteksi link (format: "> link" atau "> ```link```")
                elif line.startswith('>') and current_platform:
                    # Hapus '>' dan backticks
                    link = line[1:].strip().replace('```', '').strip()
                    if link:
                        platforms[current_platform].append(link)
        
        return platforms
    
    except FileNotFoundError:
        print(f"{Colors.RED}Error: File '{filename}' tidak ditemukan!{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Error membaca file: {str(e)}{Colors.RESET}")
        sys.exit(1)

def check_platform_links(platform: str, links: List[str]) -> Dict:
    """
    Memeriksa semua link untuk satu platform secara paralel
    """
    results = {
        'platform': platform,
        'total': len(links),
        'active': 0,
        'error': 0,
        'links': []
    }
    
    print(f"  Checking {platform}... ", end='', flush=True)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(check_url, link): link for link in links}
        
        for future in as_completed(future_to_url):
            url, is_active = future.result()
            
            if is_active:
                results['active'] += 1
                status = 'active'
            else:
                results['error'] += 1
                status = 'error'
            
            results['links'].append({
                'url': url,
                'status': status
            })
    
    print(f"{Colors.GREEN}✓{Colors.RESET}")
    return results

def display_results(all_results: List[Dict]):
    """
    Menampilkan hasil pengecekan dengan format yang diminta
    """
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}HASIL PENGECEKAN DOMAIN SEO{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    total_all = 0
    total_active = 0
    total_error = 0
    
    for result in all_results:
        platform = result['platform']
        total = result['total']
        active = result['active']
        error = result['error']
        
        total_all += total
        total_active += active
        total_error += error
        
        # Format output: Platform [Total] [Active] [Error]
        status_color = Colors.GREEN if error == 0 else Colors.YELLOW if active > 0 else Colors.RED
        
        print(f"{Colors.BLUE}{Colors.BOLD}{platform:<20}{Colors.RESET} ", end='')
        print(f"[{total}] ", end='')
        print(f"{Colors.GREEN}[{active}]{Colors.RESET} ", end='')
        
        if error > 0:
            print(f"{Colors.RED}[{error}]{Colors.RESET}")
        else:
            print()
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}SUMMARY{Colors.RESET}")
    print(f"Total Links     : {total_all}")
    print(f"Active Links    : {Colors.GREEN}{total_active}{Colors.RESET}")
    print(f"Error Links     : {Colors.RED}{total_error}{Colors.RESET}")
    print(f"Success Rate    : {(total_active/total_all*100):.1f}%" if total_all > 0 else "0%")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")

def display_detailed_results(all_results: List[Dict]):
    """
    Menampilkan hasil detail per link
    """
    print(f"\n{Colors.BOLD}DETAIL PENGECEKAN PER LINK{Colors.RESET}\n")
    
    for result in all_results:
        print(f"\n{Colors.BLUE}{Colors.BOLD}{result['platform']} ({result['active']}/{result['total']} active){Colors.RESET}")
        print("-" * 70)
        
        for i, link_data in enumerate(result['links'], 1):
            url = link_data['url']
            status = link_data['status']
            
            status_symbol = f"{Colors.GREEN}✓{Colors.RESET}" if status == 'active' else f"{Colors.RED}✗{Colors.RESET}"
            status_text = f"{Colors.GREEN}ACTIVE{Colors.RESET}" if status == 'active' else f"{Colors.RED}ERROR{Colors.RESET}"
            
            print(f"  {i}. {status_symbol} [{status_text}] {url}")

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}SEO DOMAIN CHECKER{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    # Cek argument
    if len(sys.argv) < 2:
        print(f"{Colors.YELLOW}Penggunaan: python seo_checker.py <file_input.txt>{Colors.RESET}")
        print(f"\nContoh file input:")
        print(f"  Youtube : 2")
        print(f"  > https://youtube.com/watch?v=...")
        print(f"  > https://youtube.com/watch?v=...")
        print(f"  Medium : 2")
        print(f"  > unavailable\n")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    print(f"📁 Membaca file: {Colors.BOLD}{filename}{Colors.RESET}")
    platforms_data = parse_input_file(filename)
    
    if not platforms_data:
        print(f"{Colors.RED}Tidak ada data platform ditemukan!{Colors.RESET}")
        sys.exit(1)
    
    print(f"✓ Ditemukan {len(platforms_data)} platform\n")
    print(f"{Colors.BOLD}Memulai pengecekan...{Colors.RESET}\n")
    
    # Proses setiap platform
    all_results = []
    for platform, links in platforms_data.items():
        result = check_platform_links(platform, links)
        all_results.append(result)
        time.sleep(0.5)  # Delay kecil untuk menghindari rate limiting
    
    # Tampilkan hasil
    display_results(all_results)
    
    # Tanya apakah ingin melihat detail
    try:
        show_detail = input(f"\n{Colors.YELLOW}Tampilkan detail per link? (y/n): {Colors.RESET}").lower()
        if show_detail == 'y':
            display_detailed_results(all_results)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Program dihentikan.{Colors.RESET}")
        sys.exit(0)
    
    print(f"\n{Colors.GREEN}✓ Pengecekan selesai!{Colors.RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Program dihentikan oleh user.{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {str(e)}{Colors.RESET}")
        sys.exit(1)
