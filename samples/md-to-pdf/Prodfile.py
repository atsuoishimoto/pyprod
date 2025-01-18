# type: ignore
# ruff: noqa

pip("mistune", "pygments")
from md_to_html import md_to_html

MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME = params.get("CHROME", MAC_CHROME)  # Chrome executable

TEMPLATE = Path("template.html")  # HTML template
MODULES = glob("*.py")  # Rebuild when Python modules change

BUILD = Path(".build/")  # Output directory
PDF = Path("doc.pdf")  # Output PDF


# Rule to build PDF from HTML
@rule(PDF, pattern="%.pdf", depends=BUILD / "%.html", uses=BUILD)
def make_pdf(target, src):
    # https://developer.chrome.com/docs/chromium/headless
    run(
        quote(CHROME),
        "--headless --virtual-time-budget=10000",
        # "--no-pdf-header-footer",
        f"--print-to-pdf={target}",
        src,
    )


# Rule to build HTML from Markdown
# Rebuilds when Python modules change
@rule(BUILD / "%.html", depends=(Path("%.md"), TEMPLATE, MODULES), uses=BUILD)
def make_html(target, src, template, *_):
    body = md_to_html(open(src).read())
    html = open(template).read().format(body=body)
    open(target, "w").write(html)


# create outputs directory
@rule(BUILD)
def builds(target):
    os.makedirs(target, exist_ok=True)


@task
def clean():
    shutil.rmtree(BUILD, ignore_errors=True)
    PDF.unlink(missing_ok=True)


@task
def rebuild():
    build(clean, PDF)
