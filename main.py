from dataclasses import dataclass, field
import logging
import os
from typing import List

import requests

from scraper import Scraper, ScrapingResults, print_summary


@dataclass(frozen=True)
class Configuration:
    """Configuration for the Kubernetes documentation scraper."""
    kubernetes_docs_base_url: str = "https://kubernetes.io/docs"
    kubernetes_changelog_base_url: str = "https://raw.githubusercontent.com/kubernetes/kubernetes/refs/heads/master/CHANGELOG/CHANGELOG-{major}.{minor}.md"
    output_dir: str = "./output"
    max_links_to_process: int = -1  # used for testing to limit requests
    # Available sections: ["setup", "concepts", "tasks", "tutorials", "reference"]
    # sections: List[str] = field(default_factory=lambda: ["tutorials"])
    sections: List[str] = field(default_factory=lambda: ["setup", "concepts", "tasks", "tutorials", "reference"])

def prepare_session() -> requests.Session:
    """Create and configure a request session."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'K8sDocumentsScraper/0.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Accept-Language': 'en-US,en;q=0.9'
    })
    return session


def main() -> None:
    """
    Main function to run the Kubernetes documentation scraper.
    """
    # Build Configuration and output directory
    config = Configuration()

    os.makedirs(config.output_dir, exist_ok=True)
    os.makedirs(f"{config.output_dir}/provider", exist_ok=True)

    # Create a session
    session = prepare_session()

    # Create a Scraper instance
    scraper = Scraper(session=session)

    logging.info(f"Starting scraping with configuration: {config}")
    results = scraper.run(config)
    print_summary(results)

    # scraper.get_changelog(config)
    scraper.aws_eks()

    print("Scraping complete.")


if __name__ == '__main__':
    main()
