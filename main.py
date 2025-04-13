import logging
import os
from dataclasses import dataclass, field
from typing import List

import requests


from fs import FileWriter
from scraper import Scraper, print_summary, Configuration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    filename='run.log'
)

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
    # Build Configuration and output directory
    config = Configuration(
        sections=["tutorials"],
        max_links_to_process=2
    )

    os.makedirs(config.output_dir, exist_ok=True)
    os.makedirs(f"{config.output_dir}/provider", exist_ok=True)

    session = prepare_session()
    file_writer = FileWriter(config.output_dir)
    scraper = Scraper(session=session, file_writer=file_writer)

    # logging.info(f"Starting scraping with configuration: {config}")
    results = scraper.run(config)
    print_summary(results)

    scraper.fetch_changelog(config)
    # scraper.aws_eks()
    #
    scraper.get_kubectl()
    print("Scraping complete.")


if __name__ == '__main__':
    main()
