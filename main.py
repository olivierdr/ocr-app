import streamlit as st
import os
import json
import pandas as pd
from utils import (
    ocr_voucher_data,
    ocr_voucher_security_check_rework,
    check_if_groundtruth_exist,
    check_if_ocr_data_exist,
    comment_section,
)
from PIL import Image
from selected_vouchers import vouchers_selection
from time import strftime, localtime
import logging
import csv
from params import *

st.title("Lydia OCR App")
col1, col2 = st.columns(2)

col1.header("Uploaded Documents")
col2.header(":arrows_counterclockwise:")


file = open(os.path.join(PATH_JSON, NAME_JSON))
js_file = json.load(file)

voucher_in_imgfolder = os.listdir(PATH_IMAGES)
item_to_remove = [".DS_Store", ".gitignore"]
vouchers_list = [e for e in voucher_in_imgfolder if e not in item_to_remove]

if USE_VOUCHER_SELECTION:
    vouchers_selection = [str(x) for x in vouchers_selection]
    vouchers_list = list(set(vouchers_list).intersection(vouchers_selection))
    vouchers_list.sort()


if "voucher_idx" not in st.session_state:
    st.session_state["voucher_idx"] = 0

with st.sidebar:
    voucher_input = st.selectbox(
        "Voucher ID available", vouchers_list, index=st.session_state["voucher_idx"]
    )
    st.session_state["voucher_idx"] = vouchers_list.index(voucher_input)
    if st.button("Next"):
        st.session_state["voucher_idx"] += 1
        voucher_input = vouchers_list[st.session_state["voucher_idx"]]


path_img_voucher = os.path.join(PATH_IMAGES, str(voucher_input))

col1, col2 = st.columns(2)

try:
    imgs = [f for f in os.listdir(path_img_voucher) if (f.endswith(".jpg") or f.endswith(".jpeg"))]

    if len(imgs) == 1:
        image = Image.open(os.path.join(path_img_voucher, imgs[0]))
        col1.image(image, caption=imgs[0])
    else:
        image_recto = Image.open(os.path.join(path_img_voucher, imgs[0]))
        image_verso = Image.open(os.path.join(path_img_voucher, imgs[1]))

        col1.image(image_recto, caption=imgs[0])
        col2.image(image_verso, caption=imgs[1])

except FileNotFoundError:
    st.warning(
        f"Could not print the voucher image because could not find the directory of the voucher image: {path_img_voucher}",
        icon="⚠️",
    )


try:
    js_voucher = js_file[voucher_input]
except ValueError:
    st.warning("This voucher is not in the IHOCR results json file", icon="⚠️")

try:
    ocr_data = ocr_voucher_data(js_voucher)
    ocr_security = ocr_voucher_security_check_rework(js_voucher)
    df_data = pd.DataFrame.from_dict(ocr_data, orient="index", columns=["value", "confidence"])
    df_data.sort_index(inplace=True)
    df_data.style.highlight_min(subset="confidence", axis=0)

    df_security = pd.DataFrame.from_dict(
        ocr_security,
        orient="index",
        columns=["confidence"],
    )
    df_security.reset_index(names="value", inplace=True)
    df_security.drop(df_security.loc[df_security.value == "expiration_date", :].index, inplace=True)
    df_security.sort_index(inplace=True)
    df_security.style.highlight_min(subset="confidence", axis=0)

    st.subheader("OCR - Data")
    df_data["valid ?"] = False
    edited_df_data = st.data_editor(df_data)

    st.subheader("OCR - Security Checks")
    st.dataframe(df_security.style.highlight_min(subset="confidence", axis=0))
except KeyError:
    st.warning(
        f"""Voucher {voucher_input} has a document type equal to: {js_voucher['document_type']}. So this voucher does not have data or security Check to look on""",
        icon="⚠️",
    )


comment = comment_section(js_voucher)

# Save Data if checkbox
checkbox = st.button("Click here to validate your review")
if checkbox:
    datetime_ = strftime("%Y-%m-%d %H:%M:%S", localtime())
    dict_ = {
        "voucher_id": voucher_input,
        "type": js_file[voucher_input]["type"],
        "groundtruth": js_file[voucher_input]["groundtruth"]
        if check_if_groundtruth_exist(js_voucher)
        else "Unavailable",
        "ocr_decision": js_file[voucher_input]["decision"],
        "ocr_data_valide": edited_df_data["valid ?"].all()
        if check_if_ocr_data_exist(js_voucher)
        else False,
        "data_right": list(edited_df_data[edited_df_data["valid ?"] == True].index.values)
        if check_if_ocr_data_exist(js_voucher)
        else False,
        "data_error": list(edited_df_data[edited_df_data["valid ?"] == False].index.values)
        if check_if_ocr_data_exist(js_voucher)
        else False,
        "datetime": datetime_,
        "comments": comment,
    }

    df_review = pd.DataFrame.from_dict(dict_, orient="index").T

    try:
        df = pd.read_csv(os.path.join(PATH_ANNOTATION, NAME_ANNOTATION), sep=",")
    except FileNotFoundError:
        with open(os.path.join(PATH_ANNOTATION, NAME_ANNOTATION), "w", newline="") as file:
            writer = csv.writer(file)
            field = [
                "voucher_id",
                "type",
                "groundtruth",
                "ocr_decision",
                "ocr_data_valide",
                "data_right",
                "data_error",
                "datetime",
                "comments",
            ]
            writer.writerow(field)
        logging.warning(
            f"""File {NAME_ANNOTATION} not found. A New File {NAME_ANNOTATION} has just been created."""
        )
        df = pd.read_csv(os.path.join(PATH_ANNOTATION, NAME_ANNOTATION), sep=",")

    df_new = pd.concat([df, df_review], axis=0)
    df_new = df_new.reset_index(drop=True)
    df_new.to_csv(os.path.join(PATH_ANNOTATION, NAME_ANNOTATION), sep=",", index=False)

    st.success("Data uploaded successfully in GCP!", icon="✅")
    st.dataframe(df_review)
