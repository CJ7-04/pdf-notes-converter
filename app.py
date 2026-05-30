import streamlit as st
import fitz
from PIL import Image, ImageOps, ImageFilter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tempfile
import os

# Prevent PIL DecompressionBombError
Image.MAX_IMAGE_PIXELS = None

st.set_page_config(
    page_title="PDF Notes Converter",
    layout="wide"
)

st.title("📚 PDF Notes Converter")

uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"]
)

# Settings
st.sidebar.header("Settings")

dpi = st.sidebar.slider(
    "PDF Render DPI",
    100,
    300,
    200
)

threshold = st.sidebar.slider(
    "Text Darkness",
    100,
    220,
    170
)

line_spacing = st.sidebar.slider(
    "Line Spacing",
    10,
    30,
    16
)

notes_area = st.sidebar.slider(
    "Notes Area %",
    10,
    50,
    25
)

if uploaded_file:

    # Default output filename
    default_name = uploaded_file.name.replace(
        ".pdf",
        "_notes"
    )

    custom_filename = st.text_input(
        "Output PDF Name",
        value=default_name
    )

    st.success("PDF Uploaded Successfully")

    if st.button("Convert PDF"):

        with tempfile.TemporaryDirectory() as temp_dir:

            input_pdf = os.path.join(
                temp_dir,
                "input.pdf"
            )

            with open(input_pdf, "wb") as f:
                f.write(uploaded_file.read())

            output_pdf = os.path.join(
                temp_dir,
                "study_notes.pdf"
            )

            try:

                doc = fitz.open(input_pdf)

                c = canvas.Canvas(
                    output_pdf,
                    pagesize=A4
                )

                page_width, page_height = A4

                progress = st.progress(0)

                for page_num in range(len(doc)):

                    page = doc[page_num]

                    pix = page.get_pixmap(
                        dpi=dpi,
                        alpha=False
                    )

                    img_path = os.path.join(
                        temp_dir,
                        f"page_{page_num}.png"
                    )

                    pix.save(img_path)

                    try:

                        img = Image.open(img_path)

                        img = img.convert("L")

                        # Invert dark board
                        img = ImageOps.invert(img)

                        # Preserve handwriting
                        img = img.filter(
                            ImageFilter.MedianFilter(3)
                        )

                        # Darker text
                        img = img.point(
                            lambda x: 0 if x < threshold else 255,
                            mode="1"
                        )

                        img.save(img_path)

                    except Exception as e:

                        st.error(
                            f"Image processing failed on page {page_num + 1}: {e}"
                        )

                        continue

                    iw, ih = img.size

                    margin = 20

                    content_ratio = (
                        100 - notes_area
                    ) / 100

                    max_width = (
                        page_width - 2 * margin
                    )

                    max_height = (
                        page_height * content_ratio
                    )

                    scale = min(
                        max_width / iw,
                        max_height / ih
                    )

                    new_w = iw * scale
                    new_h = ih * scale

                    x = (
                        page_width - new_w
                    ) / 2

                    y = (
                        page_height - new_h - margin
                    )

                    c.drawImage(
                        img_path,
                        x,
                        y,
                        width=new_w,
                        height=new_h
                    )

                    # Notebook lines below content
                    line_y = y - 10

                    while line_y > 25:

                        c.line(
                            margin,
                            line_y,
                            page_width - margin,
                            line_y
                        )

                        line_y -= line_spacing

                    c.showPage()

                    progress.progress(
                        (page_num + 1) / len(doc)
                    )

                doc.close()

                c.save()

                with open(
                    output_pdf,
                    "rb"
                ) as f:

                    pdf_bytes = f.read()

                st.success(
                    "✅ Conversion Completed!"
                )

                if not custom_filename.endswith(".pdf"):
                    custom_filename += ".pdf"

                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=custom_filename,
                    mime="application/pdf"
                )

            except Exception as e:

                st.error(
                    f"Processing failed: {e}"
                )