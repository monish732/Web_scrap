import scrapy
from scrapy.http import FormRequest
import os
import sys

# Ensure current directory is in the path to import dynamic_parser
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dynamic_parser import parse_patient_narrative

class PatientSpider(scrapy.Spider):
    name = 'patient_spider'
    
    # Enable cookie support to maintain login sessions
    custom_settings = {
        'COOKIES_ENABLED': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'LOG_LEVEL': 'INFO'
    }

    def __init__(self, start_url=None, username=None, password=None, 
                 provider="Heuristics", api_key="", model_name="", ollama_url="",
                 *args, **kwargs):
        super(PatientSpider, self).__init__(*args, **kwargs)
        self.start_url = start_url
        self.start_urls = [start_url] if start_url else []
        self.username = username
        self.password = password
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        self.ollama_url = ollama_url

    async def start(self):
        print("!!! MY START CALLED !!!", flush=True)
        if not self.start_url:
            self.logger.error("start_url parameter is missing!")
            return
        self.logger.info(f"Starting crawl. Accessing login page: {self.start_url}")
        yield scrapy.Request(url=self.start_url, callback=self.parse_login_page)

    def parse_login_page(self, response):
        print("!!! MY PARSE_LOGIN_PAGE CALLED !!!", flush=True)
        self.logger.info("Attempting form authentication...")
        # from_response automatically searches for forms and populates values.
        # If no form is found, we fall back to manual form submission.
        form_data = {
            'username': self.username,
            'password': self.password
        }
        
        # In some websites, the form might not have name attributes or form elements are nested.
        # FormRequest.from_response handles standard form tags.
        try:
            yield FormRequest.from_response(
                response,
                formdata=form_data,
                callback=self.after_login
            )
        except ValueError:
            self.logger.warning("No HTML form found on login page, trying direct POST request.")
            # Fallback to direct POST request using the login action URL or same page URL
            # Standard login forms POST to the same page or action path
            yield FormRequest(
                url=response.url,
                formdata=form_data,
                callback=self.after_login
            )

    def after_login(self, response):
        # Check if login was successful
        # If the page still contains password inputs, we likely failed
        has_password_input = response.css('input[type="password"]')
        if has_password_input or "error" in response.url or "login" in response.url.lower() and response.status == 200:
            self.logger.error("Authentication failed. Please check login URL, username, and password.")
            return

        self.logger.info(f"Successfully authenticated! Landed page: {response.url}")
        
        # Crawl patient profiles
        # Extract patient links (e.g. hrefs containing '/patient/')
        links = response.css('a::attr(href)').getall()
        patient_links = []
        for l in links:
            full_url = response.urljoin(l)
            if '/patient/' in full_url:
                patient_links.append(full_url)
                
        # Remove duplicates
        patient_links = list(set(patient_links))
        
        self.logger.info(f"Discovered {len(patient_links)} patient records to crawl.")
        
        if not patient_links:
            self.logger.warning("No patient records found. Page content might be empty or selectors incorrect.")
            
        for link in patient_links:
            yield response.follow(link, self.parse_patient)

    def parse_patient(self, response):
        self.logger.info(f"Crawl patient profile: {response.url}")
        
        # Extract narrative text
        # Attempt to read from the narrative box
        raw_text = response.css('.narrative-box::text').get()
        if not raw_text:
            # Fallback: extract all visible text from body
            raw_text = " ".join(response.css('body ::text').getall())
            
        # Clean white spaces
        raw_text = " ".join(raw_text.split())
        
        # Parse using dynamic parser
        parsed_data = parse_patient_narrative(
            raw_text,
            provider=self.provider,
            api_key=self.api_key,
            model_name=self.model_name,
            ollama_url=self.ollama_url
        )
        
        # Add metadata field
        parsed_data["Source URL"] = response.url
        
        yield parsed_data
