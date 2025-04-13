import logging
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, List

import requests
from bs4 import BeautifulSoup
from html2text import html2text, HTML2Text
from readability import Document
from requests import RequestException
from tqdm import tqdm

from fs import FileWriter

@dataclass(frozen=True)
class Configuration:
    """Configuration for the Kubernetes documentation scraper."""
    kubernetes_docs_base_url: str = "https://kubernetes.io/docs"
    kubernetes_changelog_base_url: str = "https://raw.githubusercontent.com/kubernetes/kubernetes/refs/heads/master/CHANGELOG/CHANGELOG-{major}.{minor}.md"
    output_dir: str = "./output"
    max_links_to_process: int = -1  # used for testing to limit requests
    sections: List[str] = field(default_factory=lambda: ["setup", "concepts", "tasks", "tutorials", "reference"])


@dataclass
class Scraper:
    """Scraper for Kubernetes documentation pages."""
    session: requests.Session
    file_writer: FileWriter

    def run(self, config):
        """
        Execute scraping process and collect results.
        """
        results = ScrapingResults()
        for section in config.sections:
            section_url = f"{config.kubernetes_docs_base_url}/{section.lower()}/"
            logging.info(f"Scraping section: {section} from {section_url}")

            # find links in the sidebar
            links = self.parse_sidebar_links(self.session, section_url)
            if not links:
                logging.error(f"Failed to fetch sidebar links for section: {section}")
                continue
            links_to_process = links[:config.max_links_to_process if config.max_links_to_process != -1 else len(links)]
            total_links = len(links_to_process)

            page_contents = []
            failed_links = []

            # visit each link and save the content
            for link in tqdm(links_to_process, desc=f"Processing: {section}", unit="page", colour="green"):
                # results.links_processed += 1
                resp = make_request(self.session, link)
                parsed_page = BeautifulSoup(resp, 'lxml')
                if not parsed_page:
                    failed_links.append(link)
                    continue

                page_markdown = self.select_content(parsed_page, link)
                if not page_markdown:
                    failed_links.append(link)
                    continue

                page_contents.append(page_markdown)

            header = f"# Kubernetes Documentation: {section}\n\n"
            self.file_writer.write(section, page_contents, "w", multiple_documents=True, header=header)

            logging.info(
                f"Completed scraping section: {section}. Processed {total_links} links with {len(failed_links)} failures.")

            if failed_links:
                results.failed_links.extend(failed_links)

        return results

    @staticmethod
    def parse_sidebar_links(session: requests.Session, section_url: str) -> Optional[List[str]]:
        """
        Find all links in the soup that belong to the specified section.
        """
        # fetch the index page
        response = make_request(session, section_url)
        soup = BeautifulSoup(response, 'lxml')
        if not soup:
            logging.error(f"Failed to fetch main page {section_url}")
            return None

        all_links = []
        # parse our base_url into its components
        parsed_base = urllib.parse.urlparse(section_url)
        parsed_base_path = parsed_base.path
        section_path = parsed_base_path if parsed_base_path.startswith('/') else f'/{parsed_base_path}'

        anchor_tags = soup.select('a.td-sidebar-link')
        for a in anchor_tags:
            href = a.get('href')
            if href:
                # convert a relative url to an absolute url then parse it
                absolute_url = urllib.parse.urljoin(section_url, href)
                parsed_url = urllib.parse.urlparse(absolute_url)
                # only keep the urls with same domain and section
                if (parsed_url.netloc == parsed_base.netloc and
                        parsed_url.path.startswith(section_path)):
                    all_links.append(absolute_url)
        return all_links

    @staticmethod
    def select_content(parsed_page: BeautifulSoup, link: str) -> Optional[str]:
        """
        Extract the main content from a page and convert it to markdown.
        """
        content_div = parsed_page.select_one('.td-content')
        if not content_div:
            return None

        h = HTML2Text(baseurl="https://kubernetes.io/docs")
        raw_markdown_content = h.handle(str(content_div))
        page_markdown = f"Page Source: {link}\n\n"
        page_markdown += raw_markdown_content
        page_markdown += "\n\n-------------------------------------------------------------------------------\n\n"
        return page_markdown


    def get_aws(self):
        good_practice_pdf_url = "https://docs.aws.amazon.com/pdfs/eks/latest/best-practices/eks-bpg.pdf"
        response = self.session.get(good_practice_pdf_url, stream=True)
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

    def get_kubectl(self):
        kubectl_url = "https://kubernetes.io/docs/reference/kubectl/kubectl-cmds/"
        response_text = make_request(self.session, kubectl_url)
        html = Document(response_text).summary()
        raw_markdown_content = html2text(str(html))
        page_markdown = f"Page Source: {kubectl_url}\n\n"
        page_markdown += raw_markdown_content
        header = f"# Kubernetes Documentation: Kubectl Commands (Generated)\n\n"
        self.file_writer.write("kubectl", page_markdown,
                               header=header)

    def fetch_changelog(self, config: Configuration):
        latest_kubernetes_version = make_request(self.session, "https://dl.k8s.io/release/stable.txt" )
        parts = latest_kubernetes_version.strip()[1:].split('.')
        major = int(parts[0])
        minor = int(parts[1])
        logging.info(f"Latest version: {latest_kubernetes_version} (major: {major}, minor: {minor})")
        header = f"# Kubernetes Changelog upto {latest_kubernetes_version}\n\n"
        versions_to_process = range(minor, 9 - 1, -1)
        markdown = ""
        for version in tqdm(versions_to_process, desc=f"Downloading Changelogs", unit="version",
                            colour="blue"):
            url = config.kubernetes_changelog_base_url.format(major=major, minor=version)
            response_text = make_request(self.session, url)
            markdown += response_text
        self.file_writer.write("changelog", markdown, multiple_documents=True, header=header)

    def handle_glossary(self):
        glossary_url = "https://kubernetes.io/docs/reference/glossary/?all=true"


@dataclass
class ScrapingResults:
    """Results of the scraping process."""
    failed_links: List[str] = field(default_factory=list)
    links_processed: int = 0




def print_summary(results: ScrapingResults) -> None:
    """
    Log a summary of the scraping process.
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




def make_request(session, url, timeout=30):
    """
    Makes a GET request using the provided session.
    """
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Error making request to {url}: {str(e)}"
