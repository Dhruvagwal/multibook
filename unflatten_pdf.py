import fitz
from pdf_extract_json import PDF
import fb
import urllib.request


def get_svg(page, coord):
    graphics = page.get_drawings()
    # print(graphics)
    vector_doc = fitz.open()
    vector_doc.insert_page(-1, width=coord['width'], height=coord['height'])
    vector_page = vector_doc[0]

    for path in graphics:
        shape = vector_page.new_shape()
        for item in path["items"]:
            if item[0] == "l":  # line
                shape.draw_line(item[1], item[2])
            elif item[0] == "re":  # rectangle
                # print(item[1])
                shape.draw_rect(item[1].normalize())  # <==
            elif item[0] == "qu":  # <== quad
                shape.draw_quad(item[1])
            elif item[0] == "c":  # curve
                shape.draw_bezier(item[1], item[2], item[3], item[4])
            else:
                raise ValueError("unhandled drawing", item)

        shape.finish(
            fill=path["fill"],  # fill color
            color=path["color"],  # line color
            dashes=path["dashes"],  # line dashing
            even_odd=path.get("even_odd", True),  # control color of overlaps
            # whether to connect last and first point
            closePath=path["closePath"],
            lineJoin=path["lineJoin"],  # how line joins should look like
            lineCap=max(path["lineCap"]),  # how line ends should look like
            width=path["width"],  # line width
            stroke_opacity=path.get(
                "stroke_opacity", 1
            ),  # key may not always be present
            fill_opacity=path.get("fill_opacity", 1),  # key may not be present
        )
        shape.commit()

    svg = vector_page.get_svg_image(matrix=fitz.Identity)
    svg = svg.replace("pt", "px")
    return svg


def get_image(doc, page, data):
    blocks = data["blocks"]
    images = []
    image_rect = []
    image_pix = []
    image_mat = []

    for block in blocks:
        if(block["type"] == 1):
            idx = PDF.compare_bbox(PDF, block["bbox"])
            if not idx:
                rect = block["bbox"]
                b64 = block["image"]
                pix = fitz.Pixmap(b64)
                if not pix.is_unicolor and pix.alpha != 1:
                    images.append({
                        "pix-image": pix,
                        "rect": rect,
                        "mat": block["transform"]
                    })

    for image in page.get_images():
        pix = PDF.recoverpix(PDF, doc, image)
        rects = page.get_image_rects(image, True)
        for rect, mat in rects:
            if rect not in image_rect:
                image_rect.append(rect)
                image_pix.append(pix)
                image_mat.append(mat)

    for rect, pix, mat in zip(image_rect, image_pix, image_mat):
        idx = PDF.compare_bbox(PDF, rect)
        if idx:
            images.append({
                "pix-image": pix,
                "rect": rect,
                "mat": mat
            })

    return images


def unflatten(id, idx):
    data = fb.read(f"/assets/{id}/file.pdf")
    pdf = urllib.request.urlopen(data)
    doc = fitz.open(stream=pdf.read(), filetype="pdf")
    page = doc[idx]
    result_list = []
    data = page.get_text("dict")

    PDF.data_bbox = page.get_bboxlog()

    images = get_image(doc, page, data)
    for image in images:
        img = image["pix-image"].tobytes()
        rect = image["rect"]
        # print(image["mat"],rect)
        url = fb.store(f"/assets/{id}/images/%s.png" % PDF.gen_id(), img)
        result_list.append({
            "type": "image",
            "src": url,
            "left": rect[0],
            "top": rect[1],
            "right": rect[2],
            "bottom": rect[3],
            "crossOrigin": "anonymous",
            "scaleX":1,
            "scaleY":1
            # "globalCompositeOperation": 'source-atop'
        })

    svg = get_svg(page, data)
    svg_url = fb.store(f"/assets/{id}/images/%s.svg" % PDF.gen_id(), bytes(svg,"utf-8"))

    return {"images": result_list,"svg": svg_url}


if __name__ == '__main__':
    f = open("./sample.html", "w", encoding="utf-8")
    f.write(unflatten(4253, 0))
    f.close()
