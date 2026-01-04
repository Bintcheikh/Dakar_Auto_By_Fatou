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
    path = DATA_DIR / "Moto.csv"
    
    if path.exists():
        df = pd.read_csv(path)
        st.markdown("Télécharger les données brutes disponibles")
        st.download_button(
            label="Télécharger Motos",
            data=df.to_csv(index=False),
            file_name=path.name,
            mime="text/csv"
        )
        st.dataframe(df.head(20))
    else:
        st.error("Aucune donnée trouvée dans le dossier Data/. Veuillez scraper d'abord.")

# ===================== DASHBOARD =====================
if Choices == "Dashboard of the data":
    path = DATA_DIR / "Moto.csv"

    if not path.exists():
        st.error("Moto.csv introuvable dans le dossier Data/")
    else:
        st.markdown("## Dashboard Motos")
        df_raw = pd.read_csv(path)
        df_raw.columns = df_raw.columns.str.strip()  # enlever espaces invisibles

        # ===== Nettoyage =====
        def clean_moto(df):
            # MARQUE / MODELE / VILLE
            def extract_marque_modele_ville(value):
                if pd.isna(value):
                    return None, None, None
                parts = str(value).split()
                marque1 = parts[0] if len(parts) > 0 else None
                modele = parts[1] if len(parts) > 2 else None
                ville = parts[-1] if len(parts) > 2 else None
                return marque1, modele, ville

            df[['Marque1', 'Modele', 'Ville']] = df['MARQUE'].apply(
                lambda x: pd.Series(extract_marque_modele_ville(x))
            )

            # ANNEE1
            df['ANNEE1'] = df['ANNEE'].astype(str).str.extract(r'(\d{4})')
            df['ANNEE1'] = pd.to_numeric(df['ANNEE1'], errors='coerce')
            df['ANNEE1'] = df.apply(
                lambda row: int(str(row['MARQUE']).split()[-2])
                if pd.isna(row['ANNEE1']) and str(row['MARQUE']).split()[-2] != '0'
                else row['ANNEE1'],
                axis=1
            )

            # KILOMETRAGE
            df['KILOMETRAGE'] = df['KILOMETRAGE'].astype(str).str.replace(r'[^\d]', '', regex=True)
            df['KILOMETRAGE'] = pd.to_numeric(df['KILOMETRAGE'], errors='coerce')

            # PRIX1
            df['PRIX1'] = df['PRIX'].astype(str).str.replace(r'[^\d]', '', regex=True)
            df['PRIX1'] = pd.to_numeric(df['PRIX1'], errors='coerce')

            # Remplacer valeurs manquantes par la médiane
            df['ANNEE1'].fillna(df['ANNEE1'].median(), inplace=True)
            df['KILOMETRAGE'].fillna(df['KILOMETRAGE'].median(), inplace=True)
            df['PRIX1'].fillna(df['PRIX1'].median(), inplace=True)

            # Supprimer lignes essentielles vides
            df = df.dropna(subset=['Marque1', 'Modele'])
            return df

        df = clean_moto(df_raw)

        # ===== KPI =====
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total annonces", len(df))
        col2.metric("Prix moyen (F CFA)", int(df['PRIX1'].mean()))
        col3.metric("Prix min (F CFA)", int(df['PRIX1'].min()))
        col4.metric("Prix max (F CFA)", int(df['PRIX1'].max()))
        col5.metric("Kilométrage moyen", int(df['KILOMETRAGE'].mean()))

        # ===== Aperçu =====
        st.subheader("Aperçu des données")
        st.dataframe(df[['Marque1', 'Modele', 'Ville', 'ANNEE1', 'PRIX1', 'KILOMETRAGE']].head(20))

        # ===== Top 5 Marques =====
        st.subheader("Top 5 marques")
        plt.figure(figsize=(6,5))
        sns.countplot(
            y="Marque1",
            data=df,
            order=df['Marque1'].value_counts().index[:5],
            palette="magma"
        )
        plt.xlabel("Nombre d'annonces")
        plt.ylabel("Marque")
        st.pyplot(plt.gcf())
        plt.close()

        # ===== Top 5 Modèles =====
        st.subheader("Top 5 modèles")
        plt.figure(figsize=(6,5))
        sns.countplot(
            y="Modele",
            data=df,
            order=df['Modele'].value_counts().index[:5],
            palette="magma"
        )
        plt.xlabel("Nombre d'annonces")
        plt.ylabel("Modèle")
        st.pyplot(plt.gcf())
        plt.close()

        # ===== Prix moyen par marque =====
        st.subheader("Prix moyen par marque")
        plt.figure(figsize=(8,5))
        df.groupby("Marque1")["PRIX1"].mean().sort_values(ascending=False).plot(kind='bar', color="teal")
        plt.xlabel("Marque")
        plt.ylabel("Prix moyen (F CFA)")
        plt.xticks(rotation=45)
        st.pyplot(plt.gcf())
        plt.close()

        # ===== Prix moyen par modèle =====
        st.subheader("Prix moyen par modèle")
        plt.figure(figsize=(8,5))
        df.groupby("Modele")["PRIX1"].mean().sort_values(ascending=False).plot(kind='bar', color="orange")
        plt.xlabel("Modèle")
        plt.ylabel("Prix moyen (F CFA)")
        plt.xticks(rotation=45)
        st.pyplot(plt.gcf())
        plt.close()

else:  # Evaluate
    st.markdown("<h3 style='text-align: center;'>Give your Feedback</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("[Kobo Evaluation Form](https://ee.kobotoolbox.org/x/sv3Wset7)")
    with col2:
        st.markdown("[Google Forms Evaluation](https://forms.gle/uFxkcoQAaU3f61LFA)")
