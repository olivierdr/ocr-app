from PIL import Image
import os
import numbers
import streamlit as st


def image_show(path_image, filename, columns, caption=None):
    full_name = os.path.join(path_image, filename)

    image = Image.open(full_name)
    columns.write(f"Filename - {full_name}")
    columns.image(image, caption)


def ocr_voucher_data(js):
    keys = js["data"].keys()

    dict_ = {}
    for key in keys:
        if ("value" in js["data"][key].keys()) and (
            "confidence" in js["data"][key].keys()
        ):
            dict_[key] = [js["data"][key]["value"], js["data"][key]["confidence"]]

    return dict_


def ocr_voucher_security_check(js):
    keys = js["security_checks"].keys()

    dict_ = {}
    for key in keys:
        if ("name" in js["security_checks"][key].keys()) and (
            "output" in js["security_checks"][key].keys()
        ):
            if isinstance(js["security_checks"][key]["output"], numbers.Number):
                dict_[key] = [
                    js["security_checks"][key]["name"],
                    js["security_checks"][key]["output"],
                ]

    return dict_


def ocr_voucher_security_check_rework(js):
    """Rework"""
    dict_ = {}
    keys = js["security_checks"].keys()
    for key in keys:
        if js["security_checks"][key] is None:
            dict_[key] = 0
        else:
            dict_[key] = js["security_checks"][key]["output"]

    return dict_


def check_if_ocr_data_exist(js_voucher):
    if "data" in js_voucher.keys():
        return True
    else:
        return False


def check_if_groundtruth_exist(js_voucher):
    if "groundtruth" in js_voucher.keys():
        return True
    else:
        return False


def comment_section(js_voucher):
    if check_if_ocr_data_exist(js_voucher):
        comment = st.text_input(
            ":point_right: OCR Comments Section: OCR errors? Please specify them in few words."
        )
        return comment
    else:
        comment = st.text_input(
            ":point_right: Comments will be generate auto, except you right on this box"
        )
        if comment == "":
            return js_voucher["document_type"]
        else:
            return comment
