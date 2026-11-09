import pymupdf
import os

def extract_images(pdf_path, output_dir):

    os.makedirs(output_dir, exist_ok=True)

    doc = pymupdf.open(pdf_path)
    images = []

    for page_no, page in enumerate(doc, start=1):

        for img_no, img in enumerate(page.get_images(), start=1):

            image = doc.extract_image(img[0])
            path = f"{output_dir}/page_{page_no}_image_{img_no}.{image['ext']}"

            with open(path, "wb") as f:
                f.write(image["image"])

            images.append(path)

    doc.close()
    return images


if __name__ == "__main__":
    pdf_path = r"C:/Users/Rashm/OneDrive/Desktop/flowsome-backend/test/7109a351-7893-40f5-a14d-1d08cf50904c.pdf"
    output_dir = r"C:/Users/Rashm/OneDrive/Desktop/flowsome-backend/test"
    images = extract_images(pdf_path, output_dir)
    print(images)