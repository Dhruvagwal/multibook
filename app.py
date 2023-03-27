import json
from flask import request, Flask
from flask_cors import CORS
import numpy as np
from pdf_extract_json import PDF
from translate import translate
from unflatten_pdf import unflatten 

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

app = Flask(__name__)
CORS(app)

@app.route("/convert", methods=["POST"])
def convert():
    files = request.files
    id = request.form.get("id")
    if "pdf" in files:
        pdf = files["pdf"].read()
        page_num = 0
        pdf = PDF(pdf, page_num, id)
        pdf.pdf_extract()

        html = pdf.export()
        file = json.dumps({"json": html}, cls=NumpyEncoder)
        return file, 200

    file = json.dumps({"html": None}, cls=NumpyEncoder)
    return file, 200

@app.route("/unflatten", methods=["POST"])
def unflat():
    id = request.form.get("id")
    page_num = request.form.get("idx")
    # print(id, page_num)
    if id and page_num:
        data = unflatten(id,int(page_num))
        file = json.dumps(data, cls=NumpyEncoder)
        return file, 200

    file = json.dumps({"data": None}, cls=NumpyEncoder)
    return file, 200


@app.route("/translate/<string:lang>", methods=["POST"])
def trans(lang):
    response = request.data.decode("utf-8")
    response = json.loads(response)
    try:
        text = response["text"]
        print(text)
        if text:
            trans_text = translate(text, lang)
            return {"text": trans_text}, 200
        else:
            return {"err": "Not Found"}, 404
    except:
        return {"err": "Internal Error"}, 501


@app.route("/", methods=["GET"])
def main():
    return json.dumps({"success": True}, cls=NumpyEncoder)


if __name__ == "__main__":
    app.run(debug=True)
