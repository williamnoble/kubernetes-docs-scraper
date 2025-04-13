import argparse
import logging
import os

import requests

from fs import FileWriter
from scraper import Scraper, Configuration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
    filename="run.log",
)


def prepare_session() -> requests.Session:
    """Create and configure a request session."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "K8sDocumentsScraper/0.1",
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return session


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Kubernetes Documentation Scraper")
    parser.add_argument(
        "--output",
        type=str,
        default="docs",
        help="Directory to store scraped documentation",
    )

    parser.add_argument(
        "--max-links",
        type=int,
        default=-1,
        help="Maximum number of links to process (-1 for unlimited)",
    )

    parser.add_argument(
        "--sections",
        type=str,
        nargs="+",
        default=["setup", "concepts", "tasks", "tutorials", "reference"],
        help="Sections to scrape (space-separated list)",
    )

    parser.add_argument(
        "--skip-links",
        type=str,
        nargs="+",
        default=[
            "https://kubernetes.io/docs/reference/glossary/",
            "https://kubernetes.io/docs/reference/kubectl/kubectl-cmds/",
        ],
        help="Links to skip (space-separated list)",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    config = Configuration(
        output_dir=args.output,
        max_links_to_process=args.max_links,
        sections=args.sections,
        skip_links=args.skip_links,
    )

    os.makedirs(f"{config.output_dir}/extras", exist_ok=True)

    session = prepare_session()
    file_writer = FileWriter(config.output_dir)
    scraper = Scraper(session=session, file_writer=file_writer, config=config)

    logging.info(f"Starting scraping with configuration: {config}")

    scraper.get_kubernetes_docs()
    scraper.get_changelog()
    scraper.get_kubectl()
    scraper.get_aws()
    scraper.get_glossary()

    print("Scraping complete.")


if __name__ == "__main__":
    main()
