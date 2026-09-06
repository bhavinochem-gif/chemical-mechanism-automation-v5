import fitz,base64,io
from PIL import Image
def process_document(data,filename,dpi=180):
    pdf=filename.lower().endswith(".pdf"); text=""; imgs=[]; pages=1
    if pdf:
        d=fitz.open(stream=data,filetype="pdf"); pages=len(d); m=fitz.Matrix(dpi/72,dpi/72)
        parts=[]
        for i,p in enumerate(d):
            parts.append(f"--- PAGE {i+1} ---\n{p.get_text('text') or ''}")
            b=p.get_pixmap(matrix=m,alpha=False).tobytes("png")
            imgs.append({"page":i+1,"mime_type":"image/png","data":base64.b64encode(b).decode()})
        text="\n".join(parts).strip(); d.close()
    else:
        Image.open(io.BytesIO(data)).verify()
        imgs=[{"page":1,"mime_type":"image/png" if filename.lower().endswith(".png") else "image/jpeg","data":base64.b64encode(data).decode()}]
    return {"filename":filename,"is_pdf":pdf,"page_count":pages,"text":text,"images":imgs}
