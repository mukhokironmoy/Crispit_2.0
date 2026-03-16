def split_text_for_telegram(text: str, max_length: int = 4050) -> list[str]:
    """
    Splits long text into multiple chunks that stay within Telegram's max message length.
    Splits cleanly on double newlines (paragraphs), then single newlines.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    
    # Simple split by double newline
    paragraphs = text.split('\n\n')
    current_chunk: str = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            if len(paragraph) > max_length:
                # If a single paragraph is still too long, split by newline
                lines = paragraph.split('\n')
                for line in lines:
                    if len(current_chunk) + len(line) + 1 > max_length:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                            
                        if len(line) > max_length:
                            # Hard split if a single line is too long
                            for i in range(0, len(line), max_length):
                                chunks.append(line[int(i):int(i+max_length)])
                        else:
                            current_chunk += f"{line}\n"
                    else:
                        current_chunk += f"{line}\n"
            else:
                current_chunk += f"{paragraph}\n\n"
        else:
            current_chunk += f"{paragraph}\n\n"
            
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
