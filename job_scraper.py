import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse


def scrape_career_pages():
    """
    Scrape jobs from company career pages (Lever, Greenhouse, Workday, generic)
    Returns DataFrame with title, company, link, description
    """
    
    # Seed list of companies with career page URLs
    career_pages = [
    # ✅ Lever ATS - VERIFIED
    "https://jobs.lever.co/zomato",
    "https://jobs.lever.co/freshworks",  # freshtworks → freshworks
    "https://jobs.lever.co/razorpay",
    "https://jobs.lever.co/chargebee",
    
    # ✅ Greenhouse ATS - VERIFIED EU domain
    "https://boards.eu.greenhouse.io/groww",  # Fixed!
    "https://boards.greenhouse.io/swiggy",
    "https://boards.greenhouse.io/urbancompany",
    "https://boards.greenhouse.io/cred",
    
    # ✅ Working generic pages
    "https://zepto.com/careers",
    "https://www.nunobots.com/careers",  # Chennai startup
    "https://freshworks.com/careers/",   # Fixed path
    "https://www.postman.com/company/careers/",  # API company
    "https://hasura.io/careers",         # Chennai-based
    "https://www.cuelearn.com/careers",  # Chennai edtech
]
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    
    all_jobs = []
    
    for career_url in career_pages:
        try:
            print(f"🔍 Scraping: {career_url}")
            response = requests.get(career_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"  ❌ Failed: {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            company_name = extract_company_name(career_url)
            
            # Try different ATS parsers
            jobs = []
            
            # 1. Lever ATS
            jobs.extend(parse_lever_jobs(soup, career_url, company_name))
            
            # 2. Greenhouse ATS
            jobs.extend(parse_greenhouse_jobs(soup, career_url, company_name))
            
            # 3. Workday / Generic
            jobs.extend(parse_generic_jobs(soup, career_url, company_name))
            
            # 4. JobPosting Schema (JSON-LD)
            jobs.extend(parse_structured_jobs(soup, career_url, company_name))
            
            all_jobs.extend(jobs)
            print(f"  ✅ Found {len(jobs)} jobs")
            
        except Exception as e:
            print(f"  ❌ Error scraping {career_url}: {e}")
            continue
    
    # Filter and deduplicate
    df = pd.DataFrame(all_jobs)
    
    if df.empty:
        print("ℹ️ No jobs found across all career pages")
        return pd.DataFrame(columns=["title", "company", "link", "description"])
    
    # Apply your profile filters
    df = apply_job_filters(df)
    
    print(f"✅ Total {len(df)} relevant jobs from career pages")
    return df


def extract_company_name(url):
    """Extract company name from career URL"""
    domain = urlparse(url).netloc
    if "lever.co" in domain:
        return domain.split("jobs.")[1].split(".")[0].title()
    elif "greenhouse.io" in domain:
        return domain.split("boards.")[1].split(".")[0].title()
    else:
        return domain.replace("www.", "").replace(".com", "").title()


def parse_lever_jobs(soup, base_url, company):
    """Parse Lever ATS job listings"""
    jobs = []
    postings = soup.find_all("div", class_=re.compile(r"posting.*|job.*"))
    
    for post in postings[:10]:  # Limit per page
        title_elem = post.find(["h3", "h4", "h5", "a"])
        link_elem = post.find("a", href=True)
        
        if title_elem and link_elem:
            title = title_elem.get_text(strip=True)
            link = urljoin(base_url, link_elem["href"])
            
            if is_relevant_job(title):
                jobs.append({
                    "title": title,
                    "company": company,
                    "link": link,
                    "description": f"{title} - {company} (Lever ATS)"
                })
    return jobs


def parse_greenhouse_jobs(soup, base_url, company):
    """Parse Greenhouse ATS job listings"""
    jobs = []
    postings = soup.find_all("div", class_=re.compile(r"posting.*|opening.*|job.*"))
    
    for post in postings[:10]:
        title_elem = post.find(["h3", "h2", "a", "div"], class_=re.compile(r"title.*"))
        link_elem = post.find("a", href=True)
        
        if title_elem and link_elem:
            title = title_elem.get_text(strip=True)
            link = urljoin(base_url, link_elem["href"])
            
            if is_relevant_job(title):
                jobs.append({
                    "title": title,
                    "company": company,
                    "link": link,
                    "description": f"{title} - {company} (Greenhouse ATS)"
                })
    return jobs


def parse_generic_jobs(soup, base_url, company):
    """Parse generic career pages"""
    jobs = []
    # Common selectors for job listings
    selectors = [
        "div.job-listing",
        ".job-item",
        ".careers-item",
        "[class*='job'] a",
        ".position",
        ".opening"
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        for elem in elements[:10]:
            title = elem.get_text(strip=True)
            link_elem = elem.find("a", href=True) or elem
            
            if title and hasattr(link_elem, 'get') and link_elem.get('href'):
                link = urljoin(base_url, link_elem["href"])
                
                if is_relevant_job(title):
                    jobs.append({
                        "title": title,
                        "company": company,
                        "link": link,
                        "description": f"{title} - {company}"
                    })
                    break  # One job per match
    return jobs


def parse_structured_jobs(soup, base_url, company):
    """Parse JobPosting JSON-LD structured data"""
    jobs = []
    
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = script.string
            if not data or '@type' not in data:
                continue
                
            # Parse JSON-LD for JobPosting
            if 'JobPosting' in data:
                import json
                job_data = json.loads(data)
                
                if isinstance(job_data, list):
                    job_data = job_data[0]
                    
                title = job_data.get("title", "")
                description = job_data.get("description", "")
                url = job_data.get("url", job_data.get("jobLocation", {}).get("url", ""))
                
                if title and is_relevant_job(title):
                    jobs.append({
                        "title": title,
                        "company": company,
                        "link": url or base_url,
                        "description": description or title
                    })
        except:
            continue
    return jobs


def is_relevant_job(title):
    """Filter for your profile: intern, software, frontend, QA, testing"""
    title_lower = title.lower()
    
    include_keywords = [
        "intern", "internship", "software", "developer", "frontend",
        "react", "javascript", "typescript", "mern", "qa", "testing",
        "sdet", "automation", "web", "full stack", "backend"
    ]
    
    exclude_keywords = [
        "senior", "sr", "lead", "manager", "director", "principal",
        "staff", "architect", "consultant", "sales", "marketing"
    ]
    
    has_include = any(keyword in title_lower for keyword in include_keywords)
    has_exclude = any(keyword in title_lower for keyword in exclude_keywords)
    
    return has_include and not has_exclude


def apply_job_filters(df):
    """Final filtering and deduplication"""
    if df.empty:
        return df
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["title", "company", "link"])
    
    # Limit to top 50 most relevant
    return df.head(50)


# Export the function your scheduler expects
def scrape_linkedin_jobs():
    """Compatibility wrapper - use career pages instead of LinkedIn"""
    return scrape_career_pages()