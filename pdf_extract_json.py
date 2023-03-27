import fitz
import os, binascii
import numpy as np
import sys
from collections import Counter
import re
import fb
import unicodedata, sys


class PDF:
    def __init__(self, pdf: str, page_num, id) -> None:
        self.global_style: list = []
        self.xref_visited: list = []
        self.avail_fonts: list = []
        self.result_list = []

        self.font_path: str = "fonts/"
        self.other_font_path: str = "other_font/"
        self.id: str = id
        self.base_url: str = (
            "https://firebasestorage.googleapis.com/v0/b/onelangworld.appspot.com/o/"
        )

        self.page_num: int = page_num
        self.pdf = pdf

    # ------------------------------------------------------------------------------------------------

    def create_rec(self, quads) -> None:

        """
        temparary function to draw boxes
        annotated around text

        input:
        quad(quadilateral) - type = tuple

        output:
        none
        but draw rectangle around text

        """
        shape = self.page.new_shape()
        beta = -360.0 / 4  # our angle, drawn clockwise
        center = fitz.Point(0, 0)  # center of circle
        ul = fitz.Point(quads.ul)  # start here (1st edge)
        ur = fitz.Point(quads.ur)  # start here (1st edge)
        ll = fitz.Point(quads.ll)  # start here (1st edge)
        lr = fitz.Point(quads.lr)  # start here (1st edge)
        points = [ll, lr, ur, ul]  # store polygon edges

        shape.draw_cont = ""  # do not draw the circle sectors
        shape.draw_polyline(points)  # draw the polygon
        shape.finish(color=(0, 0, 1), closePath=True)
        shape.commit()

    # ------------------------------------------------------------------------------------------------

    def compare_bbox(self, tup):
        indx = 0
        for i in self.data_bbox:
            indx += 1
            if i[1] == tup:
                return indx
        return False

    # ------------------------------------------------------------------------------------------------

    def rep(self, lines: dict) -> dict:

        """
        function to calculate maximum frequency of
        size
        flag
        color
        font

        input type -- dict
        input line

        return type -- dict
        return --{""size"":max_size, ""flags"":max_flag,""color"":max_color, ""font"":max_font}

        """

        size_list = []
        color_list = []
        flag_list = []
        font_list = []

        freq_flag = {}
        freq_size = {}
        freq_color = {}
        freq_font = {}

        # base={"text":[{flag:itt},{}]}

        for line in lines:
            lst = line["spans"]
            for dic in lst:
                size_list.append(dic["size"])
                flag_list.append(dic["flags"])
                color_list.append(dic["color"])
                font_list.append(dic["font"])

            for item in size_list:
                if item in freq_size:
                    freq_size[item] += 1
                else:
                    freq_size[item] = 1

            for item in flag_list:
                if item in freq_flag:
                    freq_flag[item] += 1
                else:
                    freq_flag[item] = 1

            for item in font_list:
                if item in freq_font:
                    freq_font[item] += 1
                else:
                    freq_font[item] = 1

            for item in color_list:
                if item in freq_color:
                    freq_color[item] += 1
                else:
                    freq_color[item] = 1

        # returning max frequency
        max_size = max(zip(freq_size.values(), freq_size.keys()))[1]
        max_flag = max(zip(freq_flag.values(), freq_flag.keys()))[1]
        max_color = max(zip(freq_color.values(), freq_color.keys()))[1]
        max_font = max(zip(freq_font.values(), freq_font.keys()))[1]

        x = {"size": max_size, "flags": max_flag, "color": max_color, "font": max_font}

        return x

    # ------------------------------------------------------------------------------------------------

    def style_decomposer(self, data, position: bool = True) -> str:

        """
        function to give styling to annotated elements
        it includes:

        font size
        font style
        font color

        input data:
        data -            type = list
        position -        type = bool

        output /return:
        stle string
        string format = f"color:{color}",f"font-size:{data[""size""]}",f"font-family:{data[""font""]}"

        """
        flags = data["flags"]
        font_size = data["size"]
        coord = data["bbox"]
        h = coord[3] - coord[1]
        w = coord[2] - coord[0]

        angle = 0
        if "text" in data.keys():
            angle = self.extract_angle(data)

        # color hexcode
        color = "#" + hex(data["color"])[2:]
        if data["color"] == 0:
            color = "#000"

        style = {
            "fill":color,
            "width":w,
            "height":h,
            "fontSize":font_size,
            "fontFamily":data["font"],
        }

        if angle != 0 and angle != None:
            style["angle"]=angle

        if flags & 2**0:
            style["verticalAlign"]="super"
        if flags & 2**4:
            style["fontWeight"]="bold"

        if position:
            style["left"]=coord[0]
            style["top"]=coord[1]
        return style

    # --------------------------------------- block format --------------------------------------

    # memorize already processed font xrefs here

    """
    format of blocks

    block = {
        number --> line number,
        type,
        bbox --> tuple,
        lines:[
            {spans:[
                {text:"",flags:0, size, bbox, origin:(),color}]},
            }]
    }

    """

    # ------------------------------------------------------------------------------------------------

    def get_line_text(self, line: dict) -> str:

        """
        function to get the data/info in a line

        input:
        line  - type = dictionary

        output:
        line_text - type = string
        """

        line_text = ""
        for span in line["spans"]:
            line_text += span["text"]
        return line_text

    # ------------------------------------------------------------------------------------------------

    def distance_calc(self, p1: int, p2: int) -> int:
        """
        function to calcuate distance between 2 coordinates

        input:
        p1 - point1 - type = int
        p2 - point2 - type = int

        output:
        dictance b/w p1 & p2 - type = int

        """
        return np.sqrt(np.square(p1[0] - p2[0]) + np.square(p1[1] - p2[1]))

    # ------------------------------------------------------------------------------------------------

    def extract_bg(self, coord: tuple) -> bool:
        """
        functiont to detect and save svg and background images present in the page

        input:
        coord - type = tuple


        output:
        return - bool
        save svg and background image present in the page

        """       
        block_rect = []
        text = []
        block = self.page.get_text("blocks")
        for i in block:
            if i[6] == 0: #text blocks only
                l = (i[0],i[1],i[2],i[3])
                block_rect.append(l)
                text.append(i[4].replace("\n",""))
                # removing text from page.
                try:
                    self.page.add_redact_annot(l)
                    self.page.apply_redactions()
                except:
                    pass       

        pix = self.page.get_pixmap()
        if not pix.is_unicolor :
            bytesarray = pix.tobytes()
            return fb.store(f"/assets/{self.id}/images/%s.png"%self.gen_id(),bytesarray)
        return False
            

        # except:
        # return []

    # ---------------------------------------------------------------------------------------------------------------------------

    def gen_html(self, coord: tuple) -> None:
        """
        function to add bg to html file

        input:
        coord - type = tuples

        return:
        html - type = None


        """
        data = self.extract_bg(coord)
        if data :
            self.result_list.append({
                "type":"image",
                "src":data,
                "width":coord[0],
                "height":coord[1],
                "crossOrigin":"anonymous",
            })
            # html.add_bg_image(data)

    # ---------------------------------------------------------------------------------------------------------------------

    def ext_fonts(self, doc, ofp: str, fp: str) -> None:

        """
        function to add font styling

        input:
        doc - document type = file object
        ofp - other_font_path - type = string
        fp - file path -type = string

        output:
        none

        """
        fl = (
            self.page.get_fonts()
        )  # Extract Font which are used in the pdf file per page
        for f in fl:
            xref = f[0]  # xref of font
            if xref in self.xref_visited:
                continue
            self.xref_visited.append(xref)
            # extract font buffer
            basename, ext, _, buffer = doc.extract_font(xref)

            # Rename the basename and remove all the word before +
            try:
                basename = basename[basename.index("+") + 1 :]
            except:
                pass

            # basename with extension
            fontname = "%s.%s" % (basename, ext)
            font_ttf_name = f"{basename}.ttf"

            # All the fonts which are available in font_path directory
            font_list = os.listdir(fp)  # fontpath

            # To check pdf font is availabl in the font_path directory
            isTrue = font_ttf_name in font_list
            if isTrue:
                url = f"{self.base_url}fonts%2F{font_ttf_name}?alt=media"
                self.avail_fonts.append(font_ttf_name)

            elif ext == "n/a" or ext == None:
                return

            else:  # is the font extractable?

                if ext != "ttf":  # is the font extractable?
                    # print(fontname, ext)
                    other_font_list = os.listdir(ofp)  # other fontpath
                    isOtherFont = fontname in other_font_list
                    if not isOtherFont:
                        save_path = os.path.join(ofp, fontname)  # ofp = other_font_path

                        url = f"{self.base_url}other_font%2F{fontname}?alt=media"
                        fb.store(save_path, buffer)

                        font = open(save_path, "wb")
                        font.write(buffer)
                        font.close()

                    # Then change cff to ttf manually and font will store at other_font_path directory

                elif ext == "ttf":
                    save_path = os.path.join(fp, font_ttf_name)  # fp = font_path

                    # Store in Firebase Storage
                    try:
                        url = fb.store(save_path, buffer)
                        self.html.create_font_family(basename, url)
                    except:
                        pass

                    self.avail_fonts.append(font_ttf_name)
                    font = open(save_path, "wb")
                    font.write(buffer)
                    font.close()

    # ------------------------------------------------------------------------------------------------------------------------------------------------
    def extract_angle(self, span: dict) -> list:
        if span["size"] / (span["bbox"][3] - span["bbox"][1]) >= 0.8:
            return
        """
        function to calculate angle of wvery word in pdf

        input:
        span - type = dict

        output:
        list of angle with maximum frequency for evwry line
        typr = lsit
        """

        ul, ur, ll, lr, x_0, y_0, x_1, y_1 = 0, 0, 0, 0, 0, 0, 0, 0
        angle_list = []
        angle = 0

        clean_text = self.clean_text(span["text"])
        words = clean_text.split(" ")

        for word in words:
            if word != "" and word != " ":
                Quad = self.page.search_for(word, quads=True)  # detecting quad
                if Quad != None and len(Quad) != 0:
                    Quad = Quad[0]
                    ul, ur, ll, lr = (
                        Quad[0],
                        Quad[1],
                        Quad[2],
                        Quad[3],
                    )  # ul- upper left,ur - upper right,ll - lower left,lr - lower right

                Rect = self.page.search_for(word)  # detecting rectangle covering quad
                if len(Rect) != 0 and len(Quad) != 0:
                    Rect = Rect[0]

                    x_0, y_0, x_1, y_1 = (
                        Rect[0],
                        Rect[1],
                        Rect[2],
                        Rect[3],
                    )  # four coord of a rect.

                if ul and ll and lr and ur != None:  # check wither quad is not null

                    # checking oreantaion of quad wrt rect by comparing ul, ur, ll, lr with x_0, x_1, y_0, y_1.
                    if (
                        ul[0] == x_0 and ul[1] == y_0
                    ):  # if quad overlaps rect means that angle is 0 degree
                        angle = 0
                        # print(angle,word)
                        angle_list.append(angle)
                        # return angle

                    elif (
                        ll[0] == x_0 and ll[1] == y_0
                    ):  # if quad is perpendicular to rect menas anglr in this case is 90 deg
                        angle = 90
                        # print(angle,word)
                        angle_list.append(angle)
                        # return angle

                    elif lr[0] == x_0 and lr[1] == y_0:  # condition for word at 180 deg
                        angle = 180
                        # print(angle,word)
                        angle_list.append(angle)
                        # return angle

                    elif (
                        ur[0] == x_0 and lr[0] == y_0
                    ):  # condtion for word at 270 deg - compare coords of rect and quad
                        angle = 270
                        # print(angle,word)
                        angle_list.append(angle)
                        # return angle

                    else:
                        # now checking wither the word is at angle somewhere between (0 -90),(90-180),(180-720)and (270-0)
                        # p = Perpendicular
                        # b = base
                        # angle = tan^-1(p/b)

                        if (
                            ul[0] == x_0 and ur[1] == y_0
                        ):  # condtion for anticloclwise rotation bw 0 to 90

                            p = self.distance_calc(ll, (x_0, y_1))
                            b = self.distance_calc(ul, (x_0, y_1))

                            angle = np.round(np.arctan(p / b) * 180 / np.pi * 10) / 10
                            # print(angle,word)
                            angle_list.append(angle)
                            # return angle

                        elif (
                            ll[0] == x_0 and ul[1] == y_0
                        ):  # condtoin for clockwise rotattion
                            p = self.distance_calc(lr, (x_1, y_1))
                            b = self.distance_calc(ur, (x_1, y_1))

                            angle = np.round(np.arctan(p / b) * 180 / np.pi * 10) / 10
                            angle = -angle
                            # print(angle,word)
                            angle_list.append(angle)
                            # return angle

                        elif (
                            lr[0] == x_0 and ll[1] == y_0
                        ):  # condtion for anti-clockwise for angle 90+
                            p = self.distance_calc(ur, (x_0, y_1))
                            b = self.distance_calc(lr, (x_0, y_1))

                            angle = np.round(np.arctan(p / b) * 180 / np.pi * 10) / 10
                            angle = angle + 180
                            # print(angle,word)
                            angle_list.append(angle)
                            # return angle

                        elif (
                            ur[0] == x_0 and lr[1] == y_0
                        ):  # condtion for clockwise rotation for angle 90+
                            p = self.distance_calc(ul, (x_1, y_1))
                            b = self.distance_calc(ll, (x_1, y_1))

                            angle = np.round(np.arctan(p / b) * 180 / np.pi * 10) / 10
                            angle = angle + 180
                            angle = -angle
                            # print(angle,word)

                            angle_list.append(angle)
                            # return angle
        ##        print(angle_list)

        if len(angle_list) == 0:
            return 0

        else:
            c = Counter(angle_list)
            m_c = c.most_common(1)  # calculating most frequent element in the list.
            m_c = m_c[0][0]
            return -m_c

    # --------------------------------------------------------static method--------------------------------------------------------

    @staticmethod
    def gen_id():
        return binascii.b2a_hex(os.urandom(5)).decode("utf-8")

    @staticmethod
    def destructure(span):
        return (span["flags"], span["size"], span["color"], span["font"])

    @staticmethod
    def clean_text(text):
        # Remove all the span tag and styling
        REGEX_SPAN = "</?span[^>]*>"
        try:
            re_text = re.sub(REGEX_SPAN, "", text).group()
        except AttributeError:
            re_text = re.sub(REGEX_SPAN, "", text)

        return re_text

    @staticmethod
    def remove_control_chars(s):
        return "".join(c for c in s if not unicodedata.category(c).startswith("C"))


    def recoverpix(self, doc, image):
        x = image[0]  # xref of PDF image
        s = image[1]
        # xref of its /SMask
        # print(image)

        if s == 0:  # no smask: use direct image output
            return fitz.Pixmap(doc.extract_image(x)["image"])

        def getimage(pix):
            if pix.colorspace.name in (fitz.csGRAY.name, fitz.csRGB.name):
                return pix
            else:
                return fitz.Pixmap(fitz.csRGB, pix)

        # we need to reconstruct the alpha channel with the smask
        pix1 = fitz.Pixmap(doc, x)
        pix2 = fitz.Pixmap(doc, s)  # create pixmap of the /SMask entry
        pix = fitz.Pixmap(pix1, 1)  # copy of pix1, with an alpha channel added
        ba = bytearray(pix2.samples)
        for i in range(len(ba)):
            if ba[i] > 0:
                ba[i] = 255
        pix.set_alpha(ba)
        pix1 = pix2 = None  # free temp pixmaps

        # we may need to adjust something for CMYK pixmaps here:
        return getimage(pix)

    # --------------------------------------------------------------------------------------------------------------------------------------------

    def pdf_extract(self) -> None:
        """
        function for :-
        1 - data extractions
        2 - computing lines via calculating their y coord of center
        3 - blockwise line classification
        4 - putting every element together

        input:
        none

        return:
        none

        """
        if type(self.pdf) is bytes:
            doc = fitz.open(stream=self.pdf, filetype="pdf")
        else:
            doc = fitz.open(self.pdf)
        # doc.scrub()
        # Loop across all over the pdf

        loop_range = [int(self.page_num)] if type(self.page_num) == int else range(len(doc)) 
        for page_num in loop_range:

            self.page_num = page_num

            self.page = doc[page_num]
            page = self.page

            ######### data_bbox
            self.data_bbox = page.get_bboxlog()

            self.data = page.get_text("dict")  # return Dictionary
            data = self.data

            coord = (data["width"], data["height"])
            print(coord)
            blocks = data["blocks"]

            # html class to generate html file
            self.html = self.gen_html(coord)

            # Check whether the folder path exsist.
            for path in [self.font_path, self.other_font_path]:
                if not os.path.isdir(path):
                    os.makedirs(path)

            # Extract Font which are used in the pdf file per page
            # Save font to appropriate path
            self.ext_fonts(doc, self.other_font_path, self.font_path)

            for _, block in enumerate(blocks):
                block_type = block["type"]

                # type 0 means text
                if block_type == 0:
                    # print(self.compare_bbox(block[""bbox""]))
                    block_text = ""
                    lines = block["lines"]
                    first_line_bbox = lines[0]["bbox"]

                    prev_x_c, prev_y_c = (
                        first_line_bbox[0] + first_line_bbox[2]
                    ) / 2, (first_line_bbox[1] + first_line_bbox[3]) / 2

                    global_css = self.rep(lines)

                    init_line_num = 0

                    for line_num in range(len(lines)):
                        line = lines[line_num]
                        line_text = ""

                        is_next_line = True if len(lines) > line_num + 1 else False
                        X_C, Y_C = (line["bbox"][0] + line["bbox"][2]) / 2, (
                            line["bbox"][1] + line["bbox"][3]
                        ) / 2

                        non_css_text = ""

                        first_span = line["spans"][0]
                        i_styles = {}
                        if len(line["spans"]) != 1:
                            for span in line["spans"]:
                                text = span["text"]

                                non_css_text += text

                                if text != "" and text != " ":
                                    style = self.style_decomposer(span, False)
                                    # Add Internal Styling
                                    start = len(line_text)-1
                                    end = len(line_text) + len(text)
                                    line_text += text + " "
                                    i_style = {
                                        str(i):{
                                            **style
                                        }
                                        for i in range(start, end)
                                    }
                                    i_styles.update(i_style)


                        elif first_span["text"] != " " and first_span["text"] != "":

                            text = first_span["text"]
                            non_css_text += text

                            if self.destructure(global_css) == self.destructure(
                                first_span
                            ):
                                line_text += text + " "

                            else:
                                style = self.style_decomposer(first_span, False)
                                # Add Internal Styling
                                start = len(line_text)-1
                                end = len(line_text) + len(text)
                                line_text += text + " "
                                i_style = {
                                    str(i):{
                                        **style
                                    }
                                    for i in range(start, end)
                                }
                                i_styles.update(i_style)

                        style = self.style_decomposer(first_span)
                        if (
                            Y_C - (1 / 55) * Y_C <= prev_y_c <= Y_C + (1 / 55) * Y_C
                            and X_C != prev_x_c
                        ):
                            self.result_list.append({
                                "type":"textbox",
                                "text":line_text,
                                "styles":{"0":i_styles},
                                **style
                            })

                            line_text = ""
                            i_styles = {}

                        elif is_next_line:
                            N_X_C, N_Y_C = (
                                lines[line_num + 1]["bbox"][0]
                                + lines[line_num + 1]["bbox"][2]
                            ) / 2, (
                                lines[line_num + 1]["bbox"][1]
                                + lines[line_num + 1]["bbox"][3]
                            ) / 2
                            if (
                                N_Y_C - (1 / 55) * N_Y_C
                                <= Y_C
                                <= N_Y_C + (1 / 55) * N_Y_C
                            ) and X_C != N_X_C:


                                self.result_list.append({
                                    "type":"textbox",
                                    "text":line_text,
                                    "styles":{"0":i_styles},
                                    **style,
                                })
                                line_text = ""
                                i_styles = {}

                        prev_y_c = Y_C

                        if line_text != "" and line_text != " ":
                            block_text += line_text + " "

                    block_bbox = block["bbox"]
                    first_span_bbox = lines[init_line_num]["spans"][0]["bbox"]
                    global_css["bbox"] = first_span_bbox
                    global_css["text"] = block_text
                    style = self.style_decomposer(global_css)
                    style["width"] = block_bbox[2]-block_bbox[0]+10
                    self.result_list.append({
                        "type":"textbox",
                        "text":block_text,
                        "styles":{"0":i_styles},
                        **style,
                    })
                    
    def export(self):
        return self.result_list


if __name__ == "__main__":
    # Module Should Be Removed During Deployment
    from tqdm import tqdm
    import timeit

    if len(sys.argv) < 2:
        print("pdf path")
        sys.exit(1)

    pdf = sys.argv[1]
    page_num = None if len(sys.argv) < 4 else sys.argv[2]
    id = sys.argv[3]


    # Start Run time To calculate Time Complexity
    start = timeit.default_timer()

    pdf = PDF(pdf, int(page_num), id)
    pdf.pdf_extract()
    print(pdf.export())

    stop = timeit.default_timer()
    print("Time: ", stop - start)
