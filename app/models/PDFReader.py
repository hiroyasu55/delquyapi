from pdfminer.converter import PDFPageAggregator, TextConverter
from pdfminer.layout import LAParams, LTContainer, LTTextBox
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from io import StringIO
from pprint import pprint  # noqa: F401


def _find_textboxes_recursively(layout):
    results = []

    if isinstance(layout, LTTextBox):
        results = [layout]

    elif isinstance(layout, LTContainer):
        boxes = []
        for child in layout:
            boxes.extend(_find_textboxes_recursively(child))
        results = boxes

    # else:
    #     raise Exception('Unknown layout', layout)

    return results


def read_textboxes(filepath, pages=None, direction='horizontal'):

    laparams = LAParams(detect_vertical=True)
    resource_manager = PDFResourceManager()
    device = PDFPageAggregator(resource_manager, laparams=laparams)
    interpreter = PDFPageInterpreter(resource_manager, device)

    texts = []
    if pages:
        pages = sorted(pages, key=lambda p: p)

    with open(filepath, 'rb') as f:
        pdfpages = PDFPage.get_pages(f)
        num = 0
        for page in pdfpages:
            num += 1
            if pages:
                if num > pages[-1]:
                    break
                if num not in pages:
                    continue
            interpreter.process_page(page)
            layout = device.get_result()
            boxes = _find_textboxes_recursively(layout)
            boxes.sort(key=lambda b: (b.x1, b.y0) if direction == 'vertical' else (-b.y0, b.x1))
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
