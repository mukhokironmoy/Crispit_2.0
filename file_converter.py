import markdown
from markdown_pdf import MarkdownPdf, Section
from pathlib import Path

def md_to_pdf(md_file: str | Path):
    md_path = Path(md_file)
    pdf_path = md_path.with_suffix(".pdf")

    text = md_path.read_text(encoding="utf-8")

    pdf = MarkdownPdf()
    pdf.add_section(Section(text))
    pdf.save(pdf_path)

    return pdf_path



if __name__ == '__main__':
    md_file = Path(r"telegram_out_data\test_run\notes_USA WILL NEVER BE THE SAME!! 2 Deaths that Rocked America!!.md")
    md_to_pdf(md_file)
