# Kubernetes Documentation Scraper

A small personal project that scrapes the official Kubernetes Documentation.
Additionally, scrapes the main documentation from certain cloud providers 
e.g. AWS EKS good practice and user guide.

I wrote this as I wanted the Kubernetes Docs for use with Google NotebookLM.
That said, I'm not much of a Python programmer so PRs welcome :)

## What this scrapes
- Kubernetes Documentation from https://kubernetes.io/docs/home/
- AWS EKS User Guide https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html
- AWS EKS Good Practice Guide https://docs.aws.amazon.com/eks/latest/best-practices/introduction.html

## Requirements
- Python 3.13 or higher
- Dependencies:
  - beautifulsoup4
  - markdownify
  - requests
  - tqdm
- [uv](https://github.com/astral-sh/uv) (Python package manager and runner)
- [Just](https://github.com/casey/just) (Optional, Command Runner)

## Installation and Usage

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd kubernetes-docs-scraper
   ```

2. Install dependencies using uv:
   ```bash
   uv pip install lxml
   ```

3. Run via uv
    ```bash
    uv run -m main
   ```

    Alternatively, Run via Just
    ```bash
    just run
    ```

## Output
The scraper generates predominantly markdown files in the `output` directory:
- `setup.md`: Setup guides
- `concepts.md`: Conceptual information about Kubernetes
- `tasks.md`: Task-based documentation
- `tutorials.md`: Tutorials for accomplishing larger goals
- `reference.md`: Reference documentation
- `changelog.md`: Kubernetes changelogs
- `provider/aws_eks_docs.pdf`: AWS EKS User Guide
- `provider/aws_eks_good_practice_guide.pdf`: AWS EKS Good Practice

## GitHub Releases
This project uses GitHub Actions to automatically run the scraper and create a release with the latest documentation. Each release includes a tar.gz file containing all the scraped documentation.

You can find the latest release on the [Releases page](../../releases) of this repository. This allows you to download the documentation without having to run the scraper yourself.

The workflow runs:
- On every push to the main branch
- Manually when triggered from the Actions tab

## Bugs
- There's currently two files which fail to parse properly when creating `reference.md`.
