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
    config = Configuration(
        sections=["tutorials"],
        max_links_to_process=2
    )

    os.makedirs(config.output_dir, exist_ok=True)
    os.makedirs(f"{config.output_dir}/provider", exist_ok=True)

    session = prepare_session()
    file_writer = FileWriter(config.output_dir)
    scraper = Scraper(session=session, file_writer=file_writer, config=config)

    logging.info(f"Starting scraping with configuration: {config}")

    scraper.get_kubernetes_docs()
    scraper.get_changelog()
    scraper.get_kubectl()
    scraper.get_aws()

    print("Scraping complete.")


if __name__ == '__main__':
    main()
