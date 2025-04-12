import logging
import os
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, List

from markdownify import markdownify as md
import requests
from bs4 import BeautifulSoup
from requests import RequestException
from tqdm import tqdm


@dataclass
class Scraper:
    """Scraper for Kubernetes documentation pages."""
    session: requests.Session

    def run(self, config) -> 'ScrapingResults':
        """
        Execute scraping process and collect results.

        Args:
            config: Configuration object containing scraping parameters

        Returns:
            ScrapingResults object containing the results of the scraping process
        """
        results = ScrapingResults()
        for section in config.sections:
            section_url = f"{config.kubernetes_docs_base_url}/{section.lower()}/"
            failed_links, section_links_processed = self.scrape_section(section_url, section, config)
            if failed_links:
                results.failed_links.extend(failed_links)
            results.links_processed += section_links_processed

        return results

    def scrape_section(self, section_url: str, section_name: str, config) -> tuple[list[str], int]:
        """
        Scrape a section of the Kubernetes documentation.

        Args:
            section_url: URL of the section to scrape
            section_name: Name of the section
            config: Configuration object containing the output directory and maximum number of links to process per section.

        Returns:
            Tuple containing a list of failed links and the total number of processed links
        """
        section_output_path = os.path.join(config.output_dir, f"{section_name}.md")
        with open(section_output_path, "w", encoding="utf-8") as f:
            f.write(f"# Kubernetes Documentation: {section_name}\n\n")

        logging.info(f"Scraping section: {section_name} from {section_url}")

        soup = self.download_page(section_url)
        if not soup:
            logging.error(f"Failed to fetch main page {section_url}")
            # Avoid duplicate logging and console output
            return [], 0

        parsed_base = urllib.parse.urlparse(section_url)
        section_path = parsed_base.path

        links = self.find_links(soup, section_url, section_path)
        links_to_process = links[:config.max_links_to_process if config.max_links_to_process != -1 else len(links)]
        total_links = len(links_to_process)

        logging.info(f"Found {total_links} links to process for section: {section_name}")

        page_contents = []
        failed_links = []

        for link in tqdm(links_to_process, desc=f"Processing: {section_name}", unit="page", colour="green"):
            parsed_page = self.download_page(link)
            if not parsed_page:
                failed_links.append(link)
                continue

            page_markdown = self.extract_content(parsed_page, link)
            if not page_markdown:
                failed_links.append(link)
                continue

            page_contents.append(page_markdown)

        with open(section_output_path, "a", encoding="utf-8") as f:
            for content in page_contents:
                f.write(content)

        logging.info(
            f"Completed scraping section: {section_name}. Processed {total_links} links with {len(failed_links)} failures.")
        return failed_links, total_links

    def get_changelog(self, config):
        """
        Get the Kubernetes changelog markdown.

        Args:
            config: Configuration object containing the changelog URL
        """
        # fetch the latest major version
        response = self.session.get("https://dl.k8s.io/release/stable.txt")
        response.raise_for_status()
        parts = response.text.strip()[1:].split('.')
        latest = '.'.join(parts[:2])
        major = int(parts[0])
        minor = int(parts[1])
        logging.info(f"Latest version: {latest} (major: {major}, minor: {minor})")
        markdown = f"# Kubernetes Changelog upto {latest}\n\n"
        try:
            versions_to_process = range(minor, 9 - 1, -1)
            for version in tqdm(versions_to_process, desc=f"Downloading Changelogs", unit="version",
                                colour="blue"):
                url = config.kubernetes_changelog_base_url.format(major=major, minor=version)
                logging.info(f"Downloading {url}")
                response = self.session.get(url, timeout=30)
                markdown += response.text
                markdown += "\n\n-------------------------------------------------------------------------------\n\n"
                response.raise_for_status()
        except RequestException as e:
            logging.error(f"Failed to download {config.kubernetes_changelog_base_url}: {e}")
            print(f"Failed to download {config.kubernetes_changelog_base_url}: {e}")
            return
        except Exception as e:
            logging.error(f"Unexpected error processing {config.kubernetes_changelog_base_url}: {e}")
            print(f"Unexpected error processing {config.kubernetes_changelog_base_url}: {e}")
            return

        with open("output/changelog.md", "w", encoding="utf-8") as f:
            f.write(markdown)

    def download_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Download a web page and parse it with BeautifulSoup.

        Args:
            url: The URL to download

        Returns:
            BeautifulSoup object or None if download fails
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'lxml')
        except RequestException as e:
            logging.error(f"Failed to download {url}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error processing {url}: {e}")
            return None

    @staticmethod
    def find_links(soup: BeautifulSoup, base_url: str, section_path: str) -> List[str]:
        """
        Find all links in the soup that belong to the specified section.

        Args:
            soup: BeautifulSoup object containing the page HTML
            base_url: Base URL of the Kubernetes documentation
            section_path: Path of the section to filter links

        Returns:
            List of absolute URLs for the section
        """
        all_links = []
        # parse our base_url into its components
        parsed_base = urllib.parse.urlparse(base_url)
        section_path = section_path if section_path.startswith('/') else f'/{section_path}'

        anchor_tags = soup.select('a.td-sidebar-link')
        for a in anchor_tags:
            href = a.get('href')
            if href:
                # convert a relative url to an absolute url then parse it
                absolute_url = urllib.parse.urljoin(base_url, href)
                parsed_url = urllib.parse.urlparse(absolute_url)
                # only keep the urls with same domain and section
                if (parsed_url.netloc == parsed_base.netloc and
                        parsed_url.path.startswith(section_path)):
                    all_links.append(absolute_url)
        return all_links

    def extract_content(self, parsed_page: BeautifulSoup, link: str) -> Optional[str]:
        """
        Extract content from a page and convert it to markdown.

        Args:
            parsed_page: BeautifulSoup object containing the page HTML
            link: URL of the page

        Returns:
            Markdown content or None if extraction fails
        """
        content_div = parsed_page.select_one('.td-content')
        if not content_div:
            return None

        raw_markdown_content = md(str(content_div), heading_style="ATX")
        transformed_markdown_content = self.transform_markdown_links(raw_markdown_content)
        page_markdown = f"Page Source: {link}\n\n"
        page_markdown += transformed_markdown_content
        page_markdown += "\n\n-------------------------------------------------------------------------------\n\n"
        return page_markdown

    @staticmethod
    def transform_markdown_links(page_markdown):
        """Transform links in the markdown content to use the prefixed URL.
        A convenience for NotebookLM, as is the prefix /docs has no effect and so
        at least if we follow a reference we have a link we can open
        """
        lines = page_markdown.split('\n')
        transformed_lines = []
        for line in lines:
            # Check if the line contains a link starting with (/docs
            if '](/docs' in line:
                # Replace the link with the prefixed version
                line = line.replace('](/docs', '](https://kubernetes.io/docs')

            transformed_lines.append(line)

        return '\n'.join(transformed_lines)


    @staticmethod
    def aws_eks():
        good_practice_pdf_url = "https://docs.aws.amazon.com/pdfs/eks/latest/best-practices/eks-bpg.pdf"
        response = requests.get(good_practice_pdf_url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        with open("output/provider/aws_eks_good_practice_guide.pdf", 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)


        eks_docs_url = "https://docs.aws.amazon.com/pdfs/eks/latest/userguide/eks-ug.pdf"
        response = requests.get(eks_docs_url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        with open("output/provider/aws_eks_docs.pdf", 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("Downloaded AWS docs")




@dataclass
class ScrapingResults:
    """Results of the scraping process."""
    failed_links: List[str] = field(default_factory=list)
    links_processed: int = 0


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    filename='run.log'
)

def print_summary(results: ScrapingResults) -> None:
    """
    Log a summary of the scraping process.

    Args:
        results: ScrapingResults object containing the results of the scraping process
    """
    logging.info(f"Total pages processed: {results.links_processed}")
    logging.info(f"Failed links: {len(results.failed_links)}")

    # Log each failed link
    for link in results.failed_links:
        logging.warning(f"Failed to process: {link}")

    if results.failed_links:
        print("\n=== Summary of failed links ===")
        print(f"Total failed links: {len(results.failed_links)}")
        for link in results.failed_links:
            print(f"  - {link}")
