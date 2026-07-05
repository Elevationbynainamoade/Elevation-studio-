
import io
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

APP_TITLE = "Atelier ELEVATION"
BRAND = "ELEVATION by NAINAMOADE"
COLLECTION_DEFAULT = "PUISSANCE INTERIEURE"
OWNER_PASSWORD = "ELEVATION2026"

def clean_filename(text: str) -> str:
    text = text.upper().strip()
    text = re.sub(r"[^A-Z0-9]+", "_", text)
    return text.strip("_")

def next_number(registre: pd.DataFrame) -> str:
    if registre.empty or "Numero" not in registre.columns:
        return "INV-2026-0001"
    nums = []
    for v in registre["Numero"].dropna().astype(str):
        m = re.search(r"INV-2026-(\d+)", v)
        if m:
            nums.append(int(m.group(1)))
    return f"INV-2026-{(max(nums) + 1 if nums else 1):04d}"

def make_overlay(page_w, page_h, beneficiary, number):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_w, page_h))

    # Filigrane or discret
    c.saveState()
    c.setFillColor(Color(0.78, 0.66, 0.42, alpha=0.11))
    c.translate(page_w / 2, page_h / 2)
    c.rotate(45)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(0, 0, BRAND)
    c.setFont("Helvetica", 13)
    c.drawCentredString(0, -28, f"Exemplaire personnel - {beneficiary}")
    c.setFont("Helvetica", 11)
    c.drawCentredString(0, -48, number)
    c.restoreState()

    # Pied de page
    c.setFillColor(Color(0.70, 0.58, 0.34, alpha=0.85))
    c.setFont("Helvetica", 7.5)
    c.drawString(18, 13, f"Exemplaire personnel de {beneficiary}")
    c.drawRightString(page_w - 18, 13, number)
    c.save()

    packet.seek(0)
    return PdfReader(packet).pages[0]

def make_certificate(beneficiary, number, collection, work_title):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    w, h = A4

    # Cadre premium
    gold = Color(0.78, 0.66, 0.42)
    purple = Color(0.18, 0.10, 0.28)
    c.setStrokeColor(gold)
    c.setLineWidth(1.4)
    c.rect(18*mm, 18*mm, w - 36*mm, h - 36*mm)

    c.setFillColor(purple)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(w/2, h - 34*mm, BRAND)

    c.setFillColor(gold)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(w/2, h - 52*mm, "CERTIFICAT D'AUTHENTICITE")

    c.setFillColor(purple)
    c.setFont("Helvetica", 12)
    c.drawCentredString(w/2, h - 65*mm, f"{work_title} - Collection {collection}")
    c.drawCentredString(w/2, h - 74*mm, "Première édition - Juin 2026")

    y = h - 95*mm
    lines = [
        "Le présent document certifie que cet exemplaire a été préparé exclusivement pour :",
        "",
        beneficiary,
        "",
        f"Numéro d'exemplaire : {number}",
        "",
        "Cet exemplaire est personnalisé, numeroté et certifié conforme.",
        "Il est destiné à un usage personnel exclusivement.",
        "Toute reproduction, diffusion ou transmission à un tiers est interdite",
        "sans l'autorisation écrite de l'autrice.",
        "",
        "Tout depend de toi.",
        "",
        "NAINAMOADE",
        "Fondatrice - ELEVATION by NAINAMOADE",
    ]

    for line in lines:
        if line == beneficiary:
            c.setFillColor(gold)
            c.setFont("Helvetica-Bold", 20)
            c.drawCentredString(w/2, y, line)
            y -= 12*mm
        elif line == "Tout depend de toi.":
            c.setFillColor(gold)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(w/2, y, line)
            y -= 9*mm
        elif line == "NAINAMOADE":
            c.setFillColor(purple)
            c.setFont("Helvetica-Bold", 13)
            c.drawCentredString(w/2, y, line)
            y -= 8*mm
        else:
            c.setFillColor(purple)
            c.setFont("Helvetica", 10.5)
            c.drawCentredString(w/2, y, line)
            y -= 7*mm

    c.setFillColor(Color(0.78, 0.66, 0.42, alpha=0.10))
    c.setFont("Helvetica-Bold", 44)
    c.saveState()
    c.translate(w/2, h/2)
    c.rotate(45)
    c.drawCentredString(0, 0, number)
    c.restoreState()

    c.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]

def personalize_pdf(pdf_bytes, beneficiary, number, collection, work_title, protect=True):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    for page in reader.pages:
        page_w = float(page.mediabox.width)
        page_h = float(page.mediabox.height)
        overlay = make_overlay(page_w, page_h, beneficiary, number)
        page.merge_page(overlay)
        writer.add_page(page)

    writer.add_page(make_certificate(beneficiary, number, collection, work_title))

    if protect:
        writer.encrypt(
            user_password="",
            owner_password=OWNER_PASSWORD,
            permissions_flag=0
        )

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.getvalue()

def email_template(beneficiary, number):
    return f"""Bonjour,

Je suis heureuse de vous transmettre votre exemplaire personnel d'INVINCIBLE, le premier ouvrage de la collection PUISSANCE INTERIEURE d'ELEVATION by NAINAMOADE.

Exemplaire personnel n° {number}

Cet exemplaire a été préparé exclusivement pour {beneficiary} et fait partie de la Premiere Edition d'INVINCIBLE, publiée par ELEVATION by NAINAMOADE en juin 2026.

Votre exemplaire est personnalise, numerote et certifie. Il a ete prepare specialement pour vous dans le cadre de cette premiere edition.

Je vous souhaite une belle lecture, une profonde elevation et la revelation de toute la puissance que Dieu a placee en vous.

Tout depend de toi.

NAINAMOADE
Fondatrice
ELEVATION by NAINAMOADE

P.S. Votre exemplaire est destiné a votre usage personnel exclusif. J'aurai beaucoup de plaisir à recevoir vos impressions, vos prises de conscience ou les enseignements qui vous auront le plus marquee au cours de votre lecture.
"""

st.set_page_config(page_title=APP_TITLE, page_icon="👑", layout="wide")
st.title("👑 Atelier ELEVATION")
st.caption("Generateur d'exemplaires personnalises - ELEVATION by NAINAMOADE")

with st.sidebar:
    st.header("Registre")
    registry_file = st.file_uploader("Charger le registre CSV/Excel", type=["csv", "xlsx"], key="registry")
    if registry_file:
        if registry_file.name.endswith(".csv"):
            registre = pd.read_csv(registry_file)
        else:
            registre = pd.read_excel(registry_file)
    else:
        registre = pd.DataFrame(columns=["Numero", "Beneficiaire", "Ouvrage", "Collection", "Date", "Statut"])

    st.dataframe(registre, use_container_width=True, height=250)

next_num = next_number(registre)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Informations de l'exemplaire")
    pdf_file = st.file_uploader("PDF maitre", type=["pdf"])
    beneficiary = st.text_input("Beneficiaire", value="")
    number = st.text_input("Numero d'exemplaire", value=next_num)
    work_title = st.text_input("Ouvrage", value="INVINCIBLE")
    collection = st.text_input("Collection", value=COLLECTION_DEFAULT)
    protect = st.checkbox("Activer les restrictions PDF", value=True)

with col2:
    st.subheader("2. Generation")
    st.info("Le PDF genere contient : filigrane nominatif, pied de page, numero unique, certificat et mention de diffusion interdite.")

    if st.button("GENERER L'EXEMPLAIRE", type="primary", use_container_width=True):
        if not pdf_file:
            st.error("Ajoutez d'abord le PDF maitre.")
        elif not beneficiary.strip():
            st.error("Renseignez le nom de la beneficiaire.")
        else:
            pdf_bytes = pdf_file.read()
            final_pdf = personalize_pdf(pdf_bytes, beneficiary.strip(), number.strip(), collection.strip(), work_title.strip(), protect)
            filename = f"{clean_filename(work_title)}_{clean_filename(beneficiary)}_{number.strip()}_CERTIFIE.pdf"
            st.success("Exemplaire genere avec succes.")

            st.download_button(
                "Telecharger le PDF personnalise",
                data=final_pdf,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True
            )

            new_row = {
                "Numero": number.strip(),
                "Beneficiaire": beneficiary.strip(),
                "Ouvrage": work_title.strip(),
                "Collection": collection.strip(),
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Statut": "PDF genere"
            }
            updated = pd.concat([registre, pd.DataFrame([new_row])], ignore_index=True)

            csv = updated.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Telecharger le registre mis a jour",
                data=csv,
                file_name="Registre_INVINCIBLE.csv",
                mime="text/csv",
                use_container_width=True
            )

            st.subheader("3. Mail d'envoi")
            st.text_area("Message a copier-coller", email_template(beneficiary.strip(), number.strip()), height=320)
