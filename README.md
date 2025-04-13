# Kubernetes Documentation Scraper

A small personal project that scrapes the official Kubernetes Documentation.
Additionally, scrapes the main documentation from certain cloud providers 
e.g. AWS EKS good practice and user guide.

I wrote this as I wanted the Kubernetes Docs for use with Google NotebookLM.
NotebookLM allows you to supply a URL, but it doesn't traverse to my knowledge.
Hence, this repo. That said, I'm not much of a Python programmer so PRs welcome :)

Official docs are in `/docs`, docs from other providers are in `/docs/extras`. There's
quite a few other supplementary docs I'd like to include e.g. I'm a big fan of
https://iximiuz.com/.

## What this scrapes
- Kubernetes Documentation from https://kubernetes.io/docs/home/
- Kubernetes Changelog from https://github.com/kubernetes/kubernetes/tree/master/CHANGELOG
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
   uv pip install lxml[html_clean]
   ```

3. Run via uv
    ```bash
    uv run -m main
   ```

    Alternatively, Run via Just
    ```bash
    just run
    ```

## GitHub Releases
This project uses GitHub Actions to automatically run the scraper and create a release with the latest documentation. 
Each release contains two zip files, one contains official docs and the other supplementary resources.

You can find the latest release on the [Releases page](../../releases) of this repository. 
This allows you to download the documentation without having to run the scraper yourself.

