import io
from PIL import Image
import fitz

def extract_pages(data: bytes, filename: str):
    ext = filename.lower().rsplit('.', 1)[-1]
    if ext == 'pdf':
        doc = fitz.open(stream=data, filetype='pdf')
        pages = []
        try:
            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                pages.append({'page_number': i + 1, 'image': image})
        finally:
            doc.close()
        return pages
    image = Image.open(io.BytesIO(data)).convert('RGB')
    return [{'page_number': 1, 'image': image}]
