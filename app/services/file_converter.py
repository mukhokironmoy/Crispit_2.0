import markdown
from markdown_pdf import MarkdownPdf, Section
from pathlib import Path

def get_unique_pdf_path(directory: Path, base_name: str) -> Path:
    pdf_path = directory / f"{base_name}.pdf"

    counter = 1
    while pdf_path.exists():
        pdf_path = directory / f"{base_name}_{counter}.pdf"
        counter += 1

    return pdf_path

def md_to_pdf(md_file: str | Path, user_id):
    md_path = Path(md_file)

    pdf_dir = Path(f"data/buffer")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = get_unique_pdf_path(pdf_dir, str(user_id))   

    text = md_path.read_text(encoding="utf-8")

    pdf = MarkdownPdf()
    pdf.add_section(Section(text))
    pdf.save(pdf_path)

    return pdf_path

if __name__ == '__main__':
    md_file = Path(r"data\notes\notes.txt")
    md_to_pdf(md_file, 1234)
