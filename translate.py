import os

import pandas as pd
import time
# from google.cloud import translate_v2 as translate

import html
from googletrans import Translator

translator = Translator()

def translate(text,target_language):
    # text = text.encode('latin-1', 'replace').decode('latin-1')
   
    output = translator.translate(
        text,
        dest=target_language
    )
    output = html.unescape(output.text)
    return output


if __name__ == "__main__":
    start = time.time()
    for i in range(0,1):
        print("translating...")
        print(translate("""
        With
        --------------r7w979273497927347592734972034003---------------------
        car
        --------------r7w979273497927347592734972034003---------------------
        car
         ""","hi"))

    end = time.time()
    print(end-start)