from pdfminer.converter import PDFPageAggregator, TextConverter
from pdfminer.layout import LAParams, LTContainer, LTTextBox
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from io import StringIO


def find_textboxes_recursively(layout):
    if isinstance(layout, LTTextBox):
        return [layout]

    elif isinstance(layout, LTContainer):
        boxes = []
        for child in layout:
            boxes.extend(find_textboxes_recursively(child))
        return boxes

    return []


def read_textboxes(filepath):

    laparams = LAParams(detect_vertical=True)
    resource_manager = PDFResourceManager()
    device = PDFPageAggregator(resource_manager, laparams=laparams)
    interpreter = PDFPageInterpreter(resource_manager, device)

    texts = []
    with open(filepath, 'rb') as f:
        for page in PDFPage.get_pages(f):
            interpreter.process_page(page)
            layout = device.get_result()
            boxes = find_textboxes_recursively(layout)
            boxes.sort(key=lambda b: (-b.y1, b.x0))
            for box in boxes:
                texts.append(box.get_text().strip())

    return texts


def read_text(filepath):

    laparams = LAParams()
    manager = PDFResourceManager()
    device = PDFPageAggregator(manager, laparams=laparams)
    interpreter = PDFPageInterpreter(manager, device)

    text = None

    with StringIO() as output:
        with open(filepath, 'rb') as f:
            with TextConverter(manager, output, codec='utf-8', laparams=laparams) as converter:
                interpreter = PDFPageInterpreter(manager, converter)
                for page in PDFPage.get_pages(f):
                    interpreter.process_page(page)

        text = output.getvalue()

    return text
