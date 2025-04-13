#!/usr/bin/env python3

"""
Custom PAW module: Reconnaissance Suite
This module provides advanced reconnaissance capabilities for PAW.

To register this module with PAW, run:
python3 add_custom_tool.py add --name "recon-suite" --category "reconnaissance" \
    --description "Advanced reconnaissance suite for target domains" \
    --usage "recon-suite [options] {target}" \
    --examples "recon-suite -f domains.txt" "recon-suite -d example.com -o report.txt"
"""

import os
import sys
import argparse
import subprocess
import datetime
import json

def banner():
    print("""
╔═══════════════════════════════════════════════╗
║                 RECON SUITE                   ║
║        Advanced Reconnaissance for PAW        ║
╚═══════════════════════════════════════════════╝
    """)

def run_command(command):
    """Run a shell command and return the output."""
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        
        return {
            "exit_code": process.returncode,
            "stdout": stdout,
            "stderr": stderr
        }
    except Exception as e:
        return {
            "exit_code": 1,
            "stdout": "",
            "stderr": str(e)
        }

def domain_recon(domain, output_dir):
    """Perform comprehensive reconnaissance on a domain."""
    print(f"[*] Starting reconnaissance for {domain}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    domain_dir = os.path.join(output_dir, f"{domain}_{timestamp}")
    os.makedirs(domain_dir, exist_ok=True)
    
    results = {}
    
    # 1. WHOIS Lookup
    print("[*] Performing WHOIS lookup...")
    whois_result = run_command(f"whois {domain} > {domain_dir}/whois.txt")
    results["whois"] = {
        "status": "success" if whois_result["exit_code"] == 0 else "failure",
        "file": f"{domain_dir}/whois.txt"
    }
    
    # 2. DNS Enumeration
    print("[*] Performing DNS enumeration...")
    dns_result = run_command(f"host -t ANY {domain} > {domain_dir}/dns.txt")
    results["dns"] = {
        "status": "success" if dns_result["exit_code"] == 0 else "failure",
        "file": f"{domain_dir}/dns.txt"
    }
    
    # 3. Subdomain Enumeration (if available)
    print("[*] Attempting subdomain enumeration...")
    if os.path.exists("/usr/bin/sublist3r"):
        subdomain_result = run_command(f"sublist3r -d {domain} -o {domain_dir}/subdomains.txt")
        results["subdomains"] = {
            "status": "success" if subdomain_result["exit_code"] == 0 else "failure",
            "file": f"{domain_dir}/subdomains.txt"
        }
    else:
        print("[!] sublist3r not found, skipping subdomain enumeration")
        results["subdomains"] = {"status": "skipped", "reason": "Tool not available"}
    
    # 4. Web Server Headers
    print("[*] Checking web server headers...")
    headers_result = run_command(f"curl -s -I http://{domain} > {domain_dir}/headers.txt")
    results["headers"] = {
        "status": "success" if headers_result["exit_code"] == 0 else "failure",
        "file": f"{domain_dir}/headers.txt"
    }
    
    # 5. Email Harvesting (if available)
    print("[*] Attempting email harvesting...")
    if os.path.exists("/usr/bin/theHarvester"):
        email_result = run_command(f"theHarvester -d {domain} -b google -f {domain_dir}/emails.json")
        results["emails"] = {
            "status": "success" if email_result["exit_code"] == 0 else "failure",
            "file": f"{domain_dir}/emails.json"
        }
    else:
        print("[!] theHarvester not found, skipping email harvesting")
        results["emails"] = {"status": "skipped", "reason": "Tool not available"}
    
    # Save results summary
    with open(f"{domain_dir}/summary.json", "w") as f:
        json.dump(results, f, indent=4)
    
    print(f"[+] Reconnaissance complete. Results saved to {domain_dir}")
    return domain_dir

def main():
    parser = argparse.ArgumentParser(description="Advanced Reconnaissance Suite for PAW")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-d", "--domain", help="Target domain to perform reconnaissance on")
    group.add_argument("-f", "--file", help="File containing list of domains (one per line)")
    parser.add_argument("-o", "--output", default="recon_results", help="Output directory for results")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    banner()
    
    output_dir = os.path.expanduser(args.output)
    
    if args.domain:
        domain_recon(args.domain, output_dir)
    elif args.file:
        with open(args.file, "r") as f:
            domains = [line.strip() for line in f if line.strip()]
        
        print(f"[*] Found {len(domains)} domains in {args.file}")
        for i, domain in enumerate(domains, 1):
            print(f"\n[*] Processing domain {i}/{len(domains)}: {domain}")
            domain_recon(domain, output_dir)
    
    print("\n[+] All reconnaissance tasks completed!")

if __name__ == "__main__":
    main() 