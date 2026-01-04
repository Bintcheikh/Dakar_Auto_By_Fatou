import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup as bs
from requests import get
from pathlib import Path
import logging
import os

# Chemins robustes (GitHub / Streamlit Cloud)
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"

logging.basicConfig(level=logging.WARNING)
sns.set_style("whitegrid")  # Style seaborn

# ================= TITRE =================
st.markdown("<h1 style='text-align: center;'>MY FIRST APP</h1>", unsafe_allow_html=True)
st.markdown("Application de web scraping Véhicules -  Motos - Locations")

# ================= FONCTIONS =================
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

def load(dataframe, title, key1, key2):
    st.write(f"Dimensions : {dataframe.shape}")
    st.dataframe(dataframe)
    st.download_button(
        "Télécharger CSV",
        convert_df(dataframe),
        f"{title}.csv",
        "text/csv",
        key=key2
    )

def get_proprietaire(container):
    txt = container.get_text(" ", strip=True)
    if "Par " in txt:
        return txt.split("Par ")[1].split("Appeler")[0].strip().title()
    return "Inconnu"

def get_adresse(container, type_):
    if type_ in ["vehicle","moto", "location"]:
        adresse_tag = container.find("div", class_="col-12 entry-zone-address")
        if adresse_tag:
            return adresse_tag.text.strip()

def scrape_listing(url, type_):
    soup = bs(get(url).text, "html.parser")

    if type_ == "vehicle":
        containers = soup.find_all("div", class_="listings-cards__list-item mb-md-3 mb-3")
    else:
        containers = soup.find_all("div", class_="listing-card__content p-2")

    data = []
    for c in containers:
        try:
            title = c.find("h2").text.split()
            marque = title[0]
            annee = int(title[-1])
            prix = int(c.find("h3").text.replace(" F CFA", "").replace("\u202f", ""))
            proprietaire = get_proprietaire(c)
            adresse = get_adresse(c, type_)

            if type_ == "vehicle":
                infos = c.find_all("li")
                kilometrage = int(infos[1].text.replace(" km", "").replace("\u202f", ""))
                boite = infos[2].text
                carburant = infos[3].text
                data.append({
                    "marque": marque,
                    "annee": annee,
                    "prix": prix,
                    "adresse": adresse,
                    "kilometrage": kilometrage,
                    "boite": boite,
                    "carburant": carburant,
                    "proprietaire": proprietaire
                })

            elif type_ == "moto":
                infos = c.find_all("li")
                kilometrage = int(infos[1].text.replace(" km", "").replace("\u202f", ""))
                data.append({
                    "marque": marque,
                    "annee": annee,
                    "prix": prix,
                    "adresse": adresse,
                    "kilometrage": kilometrage,
                    "proprietaire": proprietaire
                })

            else:  # location
                proprietaire_tag = c.find("span", class_="owner")
                proprietaire = proprietaire_tag.text.strip() if proprietaire_tag else "Inconnu"
                data.append({
                    "marque": marque,
                    "annee": annee,
                    "prix": prix,
                    "adresse": adresse,
                    "proprietaire": proprietaire
                })

        except Exception as e:
            logging.warning(f"Erreur scraping : {e}")

    return pd.DataFrame(data)

# ================= SIDEBAR =================
st.sidebar.header("Paramètres")
Pages = st.sidebar.selectbox("Nombre de pages à scraper", list(np.arange(1, 51)))
Choices = st.sidebar.selectbox("Options", [
    "Scrape data using BeautifulSoup",
    "Download scraped data",
    "Dashboard of the data",
    "Evaluate the App"
])

# ================= LOGIQUE =================
if Choices == "Scrape data using BeautifulSoup":

    st.subheader("Choisissez les données à scraper")

    col1, col2, col3 = st.columns(3)
    with col1:
        scrape_vehicles = st.checkbox("Véhicules")
    with col2:
        scrape_motos = st.checkbox("Motos")
    with col3:
        scrape_locations = st.checkbox("Locations")

    if not (scrape_vehicles or scrape_motos or scrape_locations):
        st.info("Veuillez sélectionner au moins une catégorie.")
        st.stop()

    if st.button("▶ Lancer le scraping"):

        progress = st.progress(0.0)
        Vehicles_df = pd.DataFrame()
        Motocycles_df = pd.DataFrame()
        Locations_df = pd.DataFrame()

        for p in range(1, Pages + 1):

            if scrape_vehicles:
                Vehicles_df = pd.concat([Vehicles_df,
                    scrape_listing(f"https://dakar-auto.com/senegal/voitures-4?page={p}", "vehicle")],
                    ignore_index=True
                )

            if scrape_motos:
                Motocycles_df = pd.concat([Motocycles_df,
                    scrape_listing(f"https://dakar-auto.com/senegal/motos-and-scooters-3?page={p}", "moto")],
                    ignore_index=True
                )

            if scrape_locations:
                Locations_df = pd.concat([Locations_df,
                    scrape_listing(f"https://dakar-auto.com/senegal/location-de-voitures-19?page={p}", "location")],
                    ignore_index=True
                )

            progress.progress(p / Pages)

        if scrape_vehicles:
            Vehicles_df.to_csv("Vehicles_data.csv", index=False)
            load(Vehicles_df, "Vehicles_data", "1", "101")

        if scrape_motos:
            Motocycles_df.to_csv("Motocycles_data.csv", index=False)
            load(Motocycles_df, "Motocycles_data", "2", "102")

        if scrape_locations:
            Locations_df.to_csv("Locations_data.csv", index=False)
            load(Locations_df, "Locations_data", "3", "103")
# ===================== CONFIG =====================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"

sns.set_style("whitegrid")        

# ===================== DOWNLOAD =====================
if Choices == "Download scraped data":
    # --- Motos ---
    moto_path = DATA_DIR / "Moto.csv"
    if moto_path.exists():
        df_moto = pd.read_csv(moto_path)
        st.markdown("### Télécharger les données Motos")
        st.download_button(
            label="Télécharger Motos",
            data=df_moto.to_csv(index=False),
            file_name=moto_path.name,
            mime="text/csv"
        )
        st.dataframe(df_moto.head(20))
    else:
        st.warning("Aucune donnée Moto trouvée dans Data/. Veuillez scraper d'abord.")

    # --- Locations ---
    loc_path = DATA_DIR / "Locations.csv"
    if loc_path.exists():
        df_loc = pd.read_csv(loc_path)
        st.markdown("### Télécharger les données Locations")
        st.download_button(
            label="Télécharger Locations",
            data=df_loc.to_csv(index=False),
            file_name=loc_path.name,
            mime="text/csv"
        )
        st.dataframe(df_loc.head(20))
    else:
        st.warning("Aucune donnée Locations trouvée dans Data/. Veuillez scraper d'abord.")

# ===================== DASHBOARD =====================
if Choices == "Dashboard of the data":
    tabs = st.tabs(["Motos", "Locations"])

    # ================= DASHBOARD MOTOS =================
    with tabs[0]:
        moto_path = DATA_DIR / "Moto.csv"
        if moto_path.exists():
            st.markdown("### Dashboard Motos")
            df_moto = pd.read_csv(moto_path)
            df_moto.columns = df_moto.columns.str.strip()

            # Nettoyage simple
            df_moto['ANNEE'] = pd.to_numeric(df_moto['ANNEE'], errors='coerce')
            df_moto['KILOMETRAGE'] = pd.to_numeric(df_moto['KILOMETRAGE'], errors='coerce')
            df_moto['PRIX'] = pd.to_numeric(df_moto['PRIX'], errors='coerce')

            # KPI
            col1, col2, col3 = st.columns(3)
            col1.metric("Total annonces", len(df_moto))
            col2.metric("Prix moyen (F CFA)", int(df_moto['PRIX'].mean()))
            col3.metric("Kilométrage moyen", int(df_moto['KILOMETRAGE'].mean()))

            # Aperçu
            st.subheader("Aperçu des motos")
            st.dataframe(df_moto.head(20))

            # Top 5 marques
            st.subheader("Top 5 marques de motos")
            plt.figure(figsize=(6,5))
            sns.countplot(
                y="MARQUE",
                data=df_moto,
                order=df_moto['MARQUE'].value_counts().index[:5],
                palette="magma"
            )
            plt.xlabel("Nombre d'annonces")
            plt.ylabel("Marque")
            st.pyplot(plt.gcf())
            plt.close()

        else:
            st.warning("Fichier Moto.csv introuvable dans Data/")

    # ================= DASHBOARD LOCATIONS =================
    with tabs[1]:
        loc_path = DATA_DIR / "Locations.csv"
        if loc_path.exists():
            st.markdown("### Dashboard Locations")
            df_loc = pd.read_csv(loc_path)
            df_loc.columns = df_loc.columns.str.strip()

            # Nettoyage
            df_loc['ANNEE'] = pd.to_numeric(df_loc['ANNEE'], errors='coerce')
            df_loc['PRIX'] = pd.to_numeric(df_loc['PRIX'], errors='coerce')

            # KPI
            col1, col2 = st.columns(2)
            col1.metric("Total annonces", len(df_loc))
            col2.metric("Prix moyen (F CFA)", int(df_loc['PRIX'].mean()))

            # Aperçu
            st.subheader("Aperçu des locations")
            st.dataframe(df_loc.head(20))

            # Top 5 Marques
            st.subheader("Top 5 marques en location")
            plt.figure(figsize=(6,5))
            sns.countplot(
                y="MARQUE",
                data=df_loc,
                order=df_loc['MARQUE'].value_counts().index[:5],
                palette="coolwarm"
            )
            plt.xlabel("Nombre d'annonces")
            plt.ylabel("Marque")
            st.pyplot(plt.gcf())
            plt.close()

            # Top 5 Modèles
            st.subheader("Top 5 modèles en location")
            plt.figure(figsize=(6,5))
            sns.countplot(
                y="MODELE",
                data=df_loc,
                order=df_loc['MODELE'].value_counts().index[:5],
                palette="viridis"
            )
            plt.xlabel("Nombre d'annonces")
            plt.ylabel("Modèle")
            st.pyplot(plt.gcf())
            plt.close()

        else:
            st.warning("Fichier Locations.csv introuvable dans Data/")
                  
else:  # Evaluate
    st.markdown("<h3 style='text-align: center;'>Give your Feedback</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("[Kobo Evaluation Form](https://ee.kobotoolbox.org/x/sv3Wset7)")
    with col2:
        st.markdown("[Google Forms Evaluation](https://forms.gle/uFxkcoQAaU3f61LFA)")
