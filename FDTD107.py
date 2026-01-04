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
    loc_path = DATA_DIR / "Location.csv"
    if loc_path.exists():
        df_loc = pd.read_csv(loc_path)
        st.markdown("### Télécharger les données Locations")
        st.download_button(
            label="Télécharger Location",
            data=df_loc.to_csv(index=False),
            file_name=loc_path.name,
            mime="text/csv"
        )
        st.dataframe(df_loc.head(20))
    else:
        st.warning("Aucune donnée Locations trouvée dans Data/. Veuillez scraper d'abord.")
    # --- Véhicules ---
    veh_path = DATA_DIR / "Vehicule.csv"
    if veh_path.exists():
        df_veh = pd.read_csv(veh_path)
        st.markdown("### Télécharger les données Véhicules")
        st.download_button(
            label="Télécharger Véhicules",
            data=df_veh.to_csv(index=False),
            file_name=veh_path.name,
            mime="text/csv"
        )
        st.dataframe(df_veh.head(20))
    else:
        st.warning("Aucune donnée Véhicules trouvée dans Data/. Veuillez scraper d'abord.")
    
# ===================== DASHBOARD =====================
if Choices == "Dashboard of the data":
    tabs = st.tabs(["Motos", "Location", "Véhicule"])

    # ==================================================
    # ================= DASHBOARD MOTOS ================
    # ==================================================
    with tabs[0]:
        moto_path = DATA_DIR / "Moto.csv"

        if moto_path.exists():
            st.markdown("### Dashboard Motos")

            df_raw = pd.read_csv(moto_path)
            df_raw.columns = df_raw.columns.str.strip()

            # ===== NETTOYAGE MOTOS AVEC OUTLIERS =====
            def clean_moto(df):
                df = df.copy()

                # ---- MARQUE / MODELE / VILLE ----
                def extract_infos(value):
                    if pd.isna(value):
                        return None, None, None
                    parts = str(value).split()
                    marque = parts[0] if len(parts) >= 1 else None
                    modele = parts[1] if len(parts) >= 2 else None
                    ville = parts[-1] if len(parts) >= 3 else None
                    return marque, modele, ville

                df[['Marque1', 'Modele', 'Ville']] = df['MARQUE'].apply(
                    lambda x: pd.Series(extract_infos(x))
                )

                # ---- ANNEE ----
                df['ANNEE1'] = pd.to_numeric(df['ANNEE'], errors='coerce')

                # ---- KILOMETRAGE ----
                df['KILOMETRAGE'] = pd.to_numeric(df['KILOMETRAGE'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce')

                # ---- PRIX ----
                df['PRIX1'] = pd.to_numeric(df['PRIX'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce')

                # ---- GESTION DES OUTLIERS ----
                # Prix et Kilométrage : suppression valeurs extrêmes (> 3 écarts-types)
                df = df[(df['PRIX1'] <= df['PRIX1'].mean() + 3*df['PRIX1'].std()) &
                        (df['PRIX1'] >= df['PRIX1'].mean() - 3*df['PRIX1'].std())]

                df = df[(df['KILOMETRAGE'] <= df['KILOMETRAGE'].mean() + 3*df['KILOMETRAGE'].std()) &
                        (df['KILOMETRAGE'] >= df['KILOMETRAGE'].mean() - 3*df['KILOMETRAGE'].std())]

                # Remplacer valeurs manquantes par médiane
                df['PRIX1'].fillna(df['PRIX1'].median(), inplace=True)
                df['KILOMETRAGE'].fillna(df['KILOMETRAGE'].median(), inplace=True)

                # ---- SUPPRESSION LIGNES VIDES ESSENTIELLES ----
                df = df.dropna(subset=['Marque1', 'Modele', 'PRIX1'])

                # ---- SUPPRESSION DOUBLONS ----
                df = df.drop_duplicates(subset=['Marque1', 'Modele', 'ANNEE1', 'PRIX1'])

                return df

            df_moto = clean_moto(df_raw)

            # ===== KPI =====
            col1, col2, col3 = st.columns(3)
            col1.metric("Total annonces", len(df_moto))
            col2.metric("Prix moyen (F CFA)", int(df_moto['PRIX1'].mean()))
            col3.metric("Prix maximum (F CFA)", int(df_moto['PRIX1'].max()))

            # ===== APERÇU =====
            st.subheader("Aperçu des motos")
            st.dataframe(df_moto[['Marque1', 'Modele', 'Ville', 'ANNEE1', 'PRIX1', 'KILOMETRAGE']].head(20))

            # ===== TOP 5 MARQUES =====
            st.subheader("Top 5 marques de motos")
            plt.figure(figsize=(6, 5))
            sns.countplot(
                y="Marque1",
                data=df_moto,
                order=df_moto['Marque1'].value_counts().index[:5],
                palette="magma"
            )
            st.pyplot(plt.gcf())
            plt.close()

            # ===== TOP 5 MODELES =====
            st.subheader("Top 5 modèles de motos")
            plt.figure(figsize=(6, 5))
            sns.countplot(
                y="Modele",
                data=df_moto,
                order=df_moto['Modele'].value_counts().index[:5],
                palette="viridis"
            )
            st.pyplot(plt.gcf())
            plt.close()

        else:
            st.warning("Fichier Moto.csv introuvable dans Data/")

    # ==================================================
    # =============== DASHBOARD LOCATION ===============
    # ==================================================
    with tabs[1]:
        loc_path = DATA_DIR / "Location.csv"

        if loc_path.exists():
            st.markdown("### Dashboard Location")

            df_raw = pd.read_csv(loc_path)
            df_raw.columns = df_raw.columns.str.strip()

            # ===== NETTOYAGE LOCATION AVEC OUTLIERS =====
            def clean_location(df):
                df = df.copy()

                # ---- MARQUE / MODELE ----
                def extract_infos(value):
                    if pd.isna(value):
                        return None, None
                    parts = str(value).split()
                    marque = parts[0] if len(parts) >= 1 else None
                    modele = parts[1] if len(parts) >= 2 else None
                    return marque, modele

                df[['Marque1', 'Modele']] = df['MARQUE'].apply(lambda x: pd.Series(extract_infos(x)))

                # ---- ANNEE ----
                df['ANNEE1'] = pd.to_numeric(df['ANNEE'], errors='coerce')

                # ---- PRIX ----
                df['PRIX1'] = pd.to_numeric(df['PRIX'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce')

                # ---- SUPPRESSION DES VALEURS IMPOSSIBLES / EXTREMES ----
                min_prix = 10000      # valeur minimale réaliste pour la location
                max_prix = 250000    # valeur maximale réaliste pour la location

                # Filtrer par min/max et par 3 écarts-types
                mean = df['PRIX1'].mean()
                std = df['PRIX1'].std()
                df = df[(df['PRIX1'] >= min_prix) & (df['PRIX1'] <= max_prix)]
                df = df[(df['PRIX1'] <= mean + 3*std) & (df['PRIX1'] >= mean - 3*std)]

                # ---- SUPPRESSION DES NAN ----
                df['PRIX1'].fillna(df['PRIX1'].median(), inplace=True)

                # ---- SUPPRESSION LIGNES VIDES ESSENTIELLES ----
                df = df.dropna(subset=['Marque1', 'Modele', 'PRIX1'])

                # ---- SUPPRESSION DOUBLONS ----
                df = df.drop_duplicates(subset=['Marque1', 'Modele', 'ANNEE1', 'PRIX1'])

                # ---- VILLE ----
                if 'ADRESSE' in df.columns:
                    df['Ville'] = df['ADRESSE']
                else:
                    df['Ville'] = None

                return df


            df_loc = clean_location(df_raw)

            # ===== KPI =====
            col1, col2, col3 , col4  = st.columns(4)
            col1.metric("Total annonces", len(df_loc))
            col2.metric("Prix minimum de location (F CFA)", int(df_loc['PRIX1'].min()))
            col3.metric("Prix moyen de location (F CFA)", int(df_loc['PRIX1'].mean()))
            col4.metric("Prix maximum de location (F CFA)", int(df_loc['PRIX1'].max()))

            # ===== APERÇU =====
            st.subheader("Aperçu des locations")
            st.dataframe(df_loc[['Marque1', 'Modele', 'Ville', 'ANNEE1', 'PRIX1']].head(20))

            # ===== TOP 5 MARQUES =====
            st.subheader("Top 5 marques en location")
            plt.figure(figsize=(6, 5))
            sns.countplot(
                y="Marque1",
                data=df_loc,
                order=df_loc['Marque1'].value_counts().index[:5],
                palette="coolwarm"
            )
            st.pyplot(plt.gcf())
            plt.close()

            # ===== TOP 5 MODELES =====
            st.subheader("Top 5 modèles en location")
            plt.figure(figsize=(6, 5))
            sns.countplot(
                y="Modele",
                data=df_loc,
                order=df_loc['Modele'].value_counts().index[:5],
                palette="viridis"
            )
            st.pyplot(plt.gcf())
            plt.close()

        else:
            st.warning("Fichier Location.csv introuvable dans Data/")
    # ================= DASHBOARD VEHICULE =====================
    with tabs[2]:
        veh_path = DATA_DIR / "Vehicule.csv"

        if veh_path.exists():
            st.markdown("### Dashboard Véhicules")

            df_raw = pd.read_csv(veh_path)
            df_raw.columns = df_raw.columns.str.strip()

            # ===== NETTOYAGE VEHICULE AVEC OUTLIERS =====
            def clean_vehicule(df):
                df = df.copy()

                # ---- MARQUE / MODELE / VILLE ----
                def extract_infos(value):
                    if pd.isna(value):
                        return None, None, None
                    parts = str(value).split()
                    marque = parts[0] if len(parts) >= 1 else None
                    modele = parts[1] if len(parts) >= 2 else None
                    ville = parts[-1] if len(parts) >= 3 else None
                    return marque, modele, ville

                df[['Marque1', 'Modele', 'Ville']] = df['MARQUE'].apply(
                    lambda x: pd.Series(extract_infos(x))
                )

                # ---- ANNEE ----
                df['ANNEE1'] = pd.to_numeric(df['ANNEE'], errors='coerce')

                # ---- KILOMETRAGE ----
                if 'KILOMETRAGE' in df.columns:
                    df['KILOMETRAGE'] = pd.to_numeric(
                        df['KILOMETRAGE'].astype(str).str.replace(r'[^\d]', '', regex=True),
                        errors='coerce'
                    )
                else:
                    df['KILOMETRAGE'] = None

                # ---- PRIX ----
                df['PRIX1'] = pd.to_numeric(
                    df['PRIX'].astype(str).str.replace(r'[^\d]', '', regex=True),
                    errors='coerce'
                )

                # ---- SUPPRESSION VALEURS IMPOSSIBLES ----
                df = df[(df['PRIX1'] > 0)]
                if 'KILOMETRAGE' in df.columns:
                    df = df[df['KILOMETRAGE'] > 0]

                # ---- GESTION DES OUTLIERS ----
                df = df[(df['PRIX1'] <= df['PRIX1'].mean() + 3*df['PRIX1'].std()) &
                        (df['PRIX1'] >= df['PRIX1'].mean() - 3*df['PRIX1'].std())]

                if 'KILOMETRAGE' in df.columns:
                    df = df[(df['KILOMETRAGE'] <= df['KILOMETRAGE'].mean() + 3*df['KILOMETRAGE'].std()) &
                            (df['KILOMETRAGE'] >= df['KILOMETRAGE'].mean() - 3*df['KILOMETRAGE'].std())]

                # Remplacer valeurs manquantes par médiane
                df['PRIX1'].fillna(df['PRIX1'].median(), inplace=True)
                if 'KILOMETRAGE' in df.columns:
                    df['KILOMETRAGE'].fillna(df['KILOMETRAGE'].median(), inplace=True)

                # ---- SUPPRESSION LIGNES VIDES ESSENTIELLES ----
                df = df.dropna(subset=['Marque1', 'Modele', 'PRIX1'])

                # ---- SUPPRESSION DOUBLONS ----
                df = df.drop_duplicates(subset=['Marque1', 'Modele', 'ANNEE1', 'PRIX1'])

                return df

            df_veh = clean_vehicule(df_raw)

            # ===== KPI =====
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total annonces", len(df_veh))
            col2.metric("Prix minimum (F CFA)", int(df_veh['PRIX1'].min()))
            col3.metric("Prix moyen (F CFA)", int(df_veh['PRIX1'].mean()))
            col4.metric("Prix maximum (F CFA)", int(df_veh['PRIX1'].max()))

            # ===== APERÇU =====
            st.subheader("Aperçu des véhicules")
            cols_to_show = ['Marque1', 'Modele', 'Ville', 'ANNEE1', 'PRIX1']
            if 'KILOMETRAGE' in df_veh.columns:
                cols_to_show.append('KILOMETRAGE')
            st.dataframe(df_veh[cols_to_show].head(20))

            # ===== TOP 5 MARQUES =====
            st.subheader("Top 5 marques")
            plt.figure(figsize=(6,5))
            sns.countplot(
                y="Marque1",
                data=df_veh,
                order=df_veh['Marque1'].value_counts().index[:5],
                palette="coolwarm"
            )
            st.pyplot(plt.gcf())
            plt.close()

            # ===== TOP 5 MODELES =====
            st.subheader("Top 5 modèles")
            plt.figure(figsize=(6,5))
            sns.countplot(
                y="Modele",
                data=df_veh,
                order=df_veh['Modele'].value_counts().index[:5],
                palette="viridis"
            )
            st.pyplot(plt.gcf())
            plt.close()

        else:
            st.warning("Fichier Vehicule.csv introuvable dans Data/")
if Choices == "Evaluate the App":
#if   # Evaluate
    st.markdown("<h3 style='text-align: center;'>Give your Feedback</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("[Kobo Evaluation Form](https://ee.kobotoolbox.org/x/sv3Wset7)")
    with col2:
        st.markdown("[Google Forms Evaluation](https://forms.gle/uFxkcoQAaU3f61LFA)")
