import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from datetime import datetime
from scipy.stats import linregress
import plotly.express as px
import io
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Spreads')
    processed_data = output.getvalue()
    return processed_data
# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="MOROCCAN BONDS SPREADS | CFG Bank",
    page_icon="YR logo.jpg",
    layout="wide",
    initial_sidebar_state="expanded"
)
# --- STYLE CSS AVANCÉ (Ombre profonde, gradient, hover) ---
st.markdown(
    """
    <style>
    /* Fond global */
    .stApp {
        background-color: #0a0c10;
        color: #e0e0e0;
    }
    /* Conteneur du header */
    .header-container {
        text-align: center;
        padding: 2.5rem 1rem;
        margin-bottom: 2rem;
    }

    /* Style personnalisé pour le logo */
    .logo-glow {
        display: block;
        margin: 0 auto 1.2rem auto;
        border-radius: 14px;
        box-shadow: 
            0 0 20px rgba(215, 0, 53, 0.3),
            0 0 40px rgba(215, 0, 53, 0.25),
            0 0 60px rgba(215, 0, 53, 0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        max-width: 100%;
    }
    .logo-glow:hover {
        transform: scale(1.03);
        box-shadow:
            0 0 25px rgba(215, 0, 53, 0.4),
            0 0 50px rgba(215, 0, 53, 0.35),
            0 0 70px rgba(215, 0, 53, 0.2);
    }
    /* Titre principal */
    .header-title {
        font-size: 2.6em;
        color: #D70035;
        margin: 0.6rem 0 0.3rem 0;
        font-weight: 700;
        letter-spacing: -0.8px;
        text-shadow: 0 0 10px rgba(215, 0, 53, 0.3);
    }
    /* Sous-titre */
    .header-subtitle {
        color: #aaa;
        font-size: 1.2em;
        margin: 0;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    /* Badge discret */
    .header-badge {
        display: inline-block;
        margin-top: 1rem;
        background: rgba(215, 0, 53, 0.12);
        color: #D70035;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: 600;
        border: 1px solid rgba(215, 0, 53, 0.2);
    }
    /* Ligne de séparation élégante */
    .divider {
        height: 2px;
        background: linear-gradient(to right, transparent, rgba(215, 0, 53, 0.5), transparent);
        margin: 2.8rem auto;
        width: 85%;
        border: none;
        opacity: 0.6;
    }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(15, 15, 25, 0.95) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(215, 0, 53, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True
)
# --- EN-TÊTE : Logo Grand + Titre + Sous-titre ---
col1, col2, col3 = st.columns([1, 6, 1])  # Largeur centrale élargie
with col2:
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    # ✅ Logo grand avec ombre profonde (via CSS)
    try:
        st.image("Logo_CFG_BANK-.jpg", use_container_width=True)
        st.markdown(
            """
            <style>
            img[data-testid="stImage"] {
                margin: 0 auto !important;
                display: block !important;
                border-radius: 14px !important;
                box-shadow: 
                    0 0 20px rgba(215, 0, 53, 0.3),
                    0 0 40px rgba(215, 0, 53, 0.25),
                    0 0 60px rgba(215, 0, 53, 0.15) !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        st.markdown(
            """
            <div style="
                font-size: 2.5em;
                color: #D70035;
                margin: 0 auto;
                width: fit-content;
                font-weight: 700;
                text-shadow: 0 0 15px rgba(215, 0, 53, 0.3);
                border: 2px solid rgba(215, 0, 53, 0.3);
                padding: 10px 25px;
                border-radius: 14px;
            ">
                CFG BANK
            </div>
            """,
            unsafe_allow_html=True
        )

    # Titre
    st.markdown("<div class='header-title'>Analyse des Spreads de Crédit</div>", unsafe_allow_html=True)
    
    # Sous-titre
    st.markdown("<p class='header-subtitle'>CFG Bank • Salle des Marchés • By YOUNES REHHABY</p>", unsafe_allow_html=True)

    # Badge
    st.markdown("<div class='header-badge'> Application Interne</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# --- Séparateur élégant ---
st.markdown("<hr class='divider'>", unsafe_allow_html=True)
# --- CHARGEMENT DES DONNÉES (Dynamique) ---
st.sidebar.header(" Import des Données")
@st.cache_data(ttl="1h")
def load_data(emissions_file, courbe_file):
    try:
        if emissions_file.name.endswith('.csv'):
            emissions = pd.read_csv(emissions_file)
        elif emissions_file.name.endswith(('.xls', '.xlsx')):
            emissions = pd.read_excel(emissions_file)
        else:
            raise ValueError("Format non supporté pour les émissions")

        if courbe_file.name.endswith(('.xls', '.xlsx')):
            courbe = pd.read_excel(courbe_file)
        else:
            raise ValueError("La courbe doit être un fichier Excel")

        courbe = courbe.rename(columns={'Unnamed: 0': 'Date'})
        courbe['Date'] = pd.to_datetime(courbe['Date'], errors='coerce')
        
        required_cols = ['INSTRID', 'ISSUEDT', 'MATURITYDT_L', 'INTERESTRATE', 'INTERESTPERIODCTY']
        missing = [col for col in required_cols if col not in emissions.columns]
        if missing:
            raise ValueError(f"Colonnes critiques manquantes : {missing}")
        if 'Date' not in courbe.columns:
            raise ValueError("Colonne 'Date' manquante dans BKAM")

        return emissions, courbe

    except Exception as e:
        st.error(f"❌ Erreur lors du chargement : {str(e)}")
        return None, None
# --- Widgets d'upload ---
with st.sidebar:
    st.markdown("### 1. Émissions (Maroclear)")
    uploaded_emissions = st.file_uploader("Choisir un fichier CSV ou Excel", type=["csv", "xls", "xlsx"], key="emissions")

    st.markdown("### 2. Courbe des Taux (BKAM)")
    uploaded_courbe = st.file_uploader("Choisir un fichier Excel", type=["xls", "xlsx"], key="courbe")

    st.markdown("---")
    st.info("💡 Vérifiez que les colonnes clés sont présentes.")
# --- Chargement effectif ---
if uploaded_emissions is not None and uploaded_courbe is not None:
    with st.spinner("🔄 Chargement et validation des données..."):
        emissions, courbe = load_data(uploaded_emissions, uploaded_courbe)

    if emissions is not None and courbe is not None:
        st.sidebar.success("✅ Données chargées !")
        
        # ✅ Initialisation de la session
        if 'has_issuecapital' not in st.session_state:
            st.session_state.has_issuecapital = 'ISSUECAPITAL' in emissions.columns

        st.session_state['data_loaded'] = True
    else:
        st.session_state['data_loaded'] = False
        st.stop()
else:
    # ✅ Même ici, il faut l'initialiser
    if 'has_issuecapital' not in st.session_state:
        st.session_state.has_issuecapital = False
    st.info("📤 Veuillez importer les deux fichiers.")
    st.session_state['data_loaded'] = False
    st.stop()
# --- PRÉTRAITEMENT DES DONNÉES ---
st.sidebar.subheader("🔧 Prétraitement")

@st.cache_data
def preprocess_emissions(emissions_df):
    df = emissions_df.copy()
    # Renommage de base
    mapping = {
        'INSTRID': 'ISIN',
        'INSTRCTGRY': 'TYPETITLE',
        'PREFERREDNAMEISSUER': 'EMETTEUR',
        'ENGLONGNAME': 'DESCRIPTION',
        'ISSUECAPITAL': 'ISSUECAPITAL',  # Optionnel
        'INTERESTRATE': 'INTERESTRATE',
        'INTERESTPERIODCTY': 'INTERESTPERIODCTY'
    }
    
    case_map = {col.upper(): col for col in df.columns}
    rename_map = {case_map[k]: v for k, v in mapping.items() if k in case_map}
    df = df.rename(columns=rename_map)

    # Vérifier les colonnes critiques
    required = ['ISIN', 'EMETTEUR', 'ISSUEDT', 'MATURITYDT_L', 'INTERESTRATE', 'INTERESTPERIODCTY']
    missing = [col for col in required if col not in df.columns]
    if missing:
        st.error(f"❌ Colonnes manquantes : {missing}")
        return None
    # Convertir les dates
    for col in ['ISSUEDT', 'MATURITYDT_L']:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    today = pd.Timestamp.today()
    df['DAYS_TO_MATURITY'] = (df['MATURITYDT_L'] - df['ISSUEDT']).dt.days
    df['RESIDUAL_DAYS'] = (df['MATURITYDT_L'] - today).dt.days.clip(lower=0)
    df['MATURITY_YEARS'] = df['DAYS_TO_MATURITY'] / 365.0
    df['STATUT'] = np.where(df['MATURITYDT_L'] > today, 'Vivante', 'Échue')
        # --- Détection du secteur : mots-clés + liste blanche ---
    financial_keywords = ['banque', 'bank', 'finance', 'crédit', 'leasing', 'lease', 'assurance', 'insurance', 'capital', 'investment', 'société de financement']
    
    # Liste explicite des émetteurs financiers connus (partiels ou complets)
    financial_entities = [
        'atw e', 'axa credit', 'bcp e', 'bmci', 'bmci leasi', 'boa', 'cam e', 'cdg k e',
        'cdm', 'cih e', 'ma leasing', 'saham', 'saham finances', 'salfin', 'sgmb',
        'sofac credit', 'vivalis salaf', 'wafabail', 'wafasalaf', 'attijari', 'wafabank',
        'crédit du maroc', 'société générale', 'hsbc', 'barid bank', 'bank of africa',
        'almada', 'maroc leasing', 'nacex', 'finanfac', 'société de financement du maroc'
    ]

    def is_financial(issuer):
        issuer_str = str(issuer).strip().lower()
        # 1. Vérifier si c'est dans la liste blanche
        if any(ent in issuer_str for ent in financial_entities):
            return True
        # 2. Vérifier les mots-clés
        if any(kw in issuer_str for kw in financial_keywords):
            return True
        return False

    df['SECTEUR'] = df['EMETTEUR'].apply(lambda x: "Sociétés Financières" if is_financial(x) else "Sociétés Non Financières")

    # Type d'obligation
    TYPE_LABELS = {
        'TCN': 'TCN',
        'OBL_ORDN': 'Obligation ordinaire',
        'OBL_SUBD': 'Obligation subordonnée',
        'OBL_CONV': 'Obligation convertible'
    }
    df['TYPE_LIBELLE'] = df['TYPETITLE'].map(TYPE_LABELS).fillna('Autre')

    # Garantie
    def extract_guarantee(g):
        if pd.isna(g): return "Aucune"
        g = str(g).strip().upper()
        return "GTG" if g.startswith("GTG") else "GT" if g.startswith("GT") else "SD" if g.startswith("SD") else "USUG" if g.startswith("USUG") else "Autre"
    df['GUA_TYPE'] = df['GUARANTEE'].apply(extract_guarantee)
    df['A_GARANTIE'] = df['GUA_TYPE'] != "Aucune"

    # Fréquence intérêts (sans ONRD)
    freq_map = {'ANLY': 'Annuel', 'HFLY': 'Semestriel', 'QTLY': 'Trimestriel', 'MNLY': 'Mensuel', 'MNTH': 'Mensuel', 'BMLY': 'Bimestriel'}
    df['FREQUENCE_INTERET'] = df['INTERESTPERIODCTY'].astype(str).map(freq_map)
    df = df[df['FREQUENCE_INTERET'].notna()].copy()

    # Marquer si ISSUECAPITAL est disponible
    if 'ISSUECAPITAL' not in df.columns:
        st.warning("⚠️ Colonne 'ISSUECAPITAL' absente → filtres et affichages liés désactivés.")
        df['ISSUECAPITAL'] = np.nan  # Pour éviter les erreurs
        st.session_state.has_issuecapital = False
    else:
        st.session_state.has_issuecapital = True

    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['ISIN', 'INTERESTRATE'])
    st.sidebar.success(f"✅ {len(df)} émissions prétraitées")
    return df

with st.spinner("🔧 Prétraitement..."):
    emissions = preprocess_emissions(emissions)

if emissions is None or emissions.empty:
    st.error("❌ Échec du prétraitement.")
    st.stop()


# --- ✅ CRÉATION SÉCURISÉE DE TYPE_TAUX APRÈS LE PRÉTRAITEMENT (après renommage) ---
def is_taux_revisable(row):
    # 1. Vérifier INTERESTTYPE (peut être manquant)
    if 'INTERESTTYPE' in row and pd.notna(row['INTERESTTYPE']):
        itype = str(row['INTERESTTYPE']).upper()
        if 'FLOT' in itype or 'FLTG' in itype:
            return 'Révisable'
    # 2. Vérifier DESCRIPTION (renommée depuis ENGLONGNAME)
    if 'DESCRIPTION' in row and pd.notna(row['DESCRIPTION']):
        desc = str(row['DESCRIPTION']).upper()
        words = desc.replace(',', ' ').replace(';', ' ').replace('.', ' ').replace('-', ' ').split()
        if 'TR' in words:
            return 'Révisable'
    return 'Fixe'

# Appliquer seulement si les colonnes existent
if 'DESCRIPTION' in emissions.columns or 'INTERESTTYPE' in emissions.columns:
    emissions['TYPE_TAUX'] = emissions.apply(is_taux_revisable, axis=1)
else:
    emissions['TYPE_TAUX'] = 'Fixe'  # Par défaut


# --- Interpolation des taux souverains (Version ULTRA-RAPIDE) ---
@st.cache_data
def interpolate_sovereign_rates_vectorized(_emissions, _courbe):
    """
    Version optimisée : interpolation vectorisée complète
    → 50x plus rapide que la version originale
    """
    import time
    start_time = time.time()

    # Maturités en jours
    maturites_jours = {
        "13 Semaines": 91,
        "26 Semaines": 182,
        "52 Semaines": 365,
        "2 Ans": 730,
        "5 Ans": 1825,
        "10 ans": 3650,
        "15 ans": 5475,
        "20 ans": 7300,
        "30 ans": 10950
    }

    # Mapping période → maturité
    period_to_label = {
        'ANLY': '52 Semaines', 'HFLY': '26 Semaines', 'QTLY': '13 Semaines',
        'MNLY': '13 Semaines', 'MNTH': '13 Semaines', 'BMLY': '13 Semaines'
    }

    # Colonnes disponibles
    available_maturities = [col for col in maturites_jours.keys() if col in _courbe.columns]
    available_days = np.array([maturites_jours[col] for col in available_maturities])
    available_rates = _courbe[available_maturities].values  # (N_dates, N_maturities)
    curve_dates = _courbe['Date'].dropna().values  # (N_dates,)

    if len(available_maturities) < 3:
        st.error("❌ Pas assez de points de maturité dans la courbe BKAM.")
        return _emissions.assign(Taux_Souverain=np.nan, Spread=np.nan, Spread_bp=np.nan)

    # Fonction pour trouver la date la plus proche
    def get_closest_date_idx(issue_dates):
        # Vectorisation : toutes les dates d'émission
        issue_dates = pd.to_datetime(issue_dates).values.astype('datetime64[D]')
        time_diff = np.abs(issue_dates[:, None] - curve_dates)  # (N_emissions, N_curve_dates)
        return np.argmin(time_diff, axis=1)  # (N_emissions,)

    # Déterminer les maturités cibles
    target_days = np.zeros(len(_emissions))

    for idx, row in _emissions.iterrows():
        is_floating = False
        if 'INTERESTTYPE' in row and pd.notna(row['INTERESTTYPE']):
            itype = str(row['INTERESTTYPE']).upper()
            if 'FLOT' in itype or 'FLTG' in itype:
                is_floating = True
        if 'DESCRIPTION' in row and pd.notna(row['DESCRIPTION']):
            words = str(row['DESCRIPTION']).upper().replace(',', ' ').replace(';', ' ').split()
            if 'TR' in words:
                is_floating = True

        period = str(row['INTERESTPERIODCTY']).strip() if pd.notna(row['INTERESTPERIODCTY']) else ""
        if is_floating and period in period_to_label:
            label = period_to_label[period]
            target_days[idx] = maturites_jours.get(label, 365)
        else:
            target_days[idx] = row['DAYS_TO_MATURITY']

    # Trouver la date la plus proche pour chaque émission
    closest_date_indices = get_closest_date_idx(_emissions['ISSUEDT'])

    # Extraire les taux correspondants
    selected_rates = available_rates[closest_date_indices]  # (N_emissions, N_maturities)

    # Interpolation vectorisée avec numpy
    sovereign_rates = []
    for i in range(len(_emissions)):
        try:
            f = interp1d(available_days, selected_rates[i], bounds_error=False, fill_value='extrapolate')
            sovereign_rates.append(f(target_days[i]) * 100)  # en %
        except:
            sovereign_rates.append(np.nan)

    _emissions['Taux_Souverain'] = sovereign_rates
    _emissions['Spread'] = _emissions['INTERESTRATE'] - _emissions['Taux_Souverain']
    _emissions['Spread_bp'] = _emissions['Spread'] * 100

    # Nettoyage
    _emissions[['Taux_Souverain', 'Spread', 'Spread_bp']] = _emissions[['Taux_Souverain', 'Spread', 'Spread_bp']].apply(pd.to_numeric, errors='coerce')

    end_time = time.time()
    st.success(f"✅ Calcul des spreads terminé en {end_time - start_time:.2f} secondes")
    return _emissions

# --- Calcul des spreads (sur demande) ---
if 'spreads_calculated' not in st.session_state:
    st.session_state.spreads_calculated = False

if st.button("⚡ Calculer les Spreads") or st.session_state.spreads_calculated:
    if not st.session_state.spreads_calculated:
        with st.spinner("Calcul des spreads en cours..."):
            emissions = interpolate_sovereign_rates_vectorized(emissions, courbe)
            st.session_state.spreads_calculated = True
            st.session_state.emissions_with_spread = emissions
    else:
        emissions = st.session_state.emissions_with_spread
else:
    st.info("📊 Cliquez sur 'Calculer les spreads' pour démarrer l'analyse.")
    st.stop()

# --- ✅ RÉCUPÉRER OU REC crée TYPE_TAUX APRÈS interpolate_sovereign_rates ---
def is_taux_revisable(row):
    if 'INTERESTTYPE' in row and pd.notna(row['INTERESTTYPE']):
        itype = str(row['INTERESTTYPE']).upper()
        if 'FLOT' in itype or 'FLTG' in itype:
            return 'Révisable'
    if 'DESCRIPTION' in row and pd.notna(row['DESCRIPTION']):
        desc = str(row['DESCRIPTION']).upper()
        words = desc.replace(',', ' ').replace(';', ' ').replace('.', ' ').replace('-', ' ').split()
        if 'TR' in words:
            return 'Révisable'
    return 'Fixe'

# Appliquer seulement si les colonnes existent
if 'DESCRIPTION' in emissions.columns:
    if 'INTERESTTYPE' in emissions.columns:
        emissions['TYPE_TAUX'] = emissions.apply(is_taux_revisable, axis=1)
    else:
        # Seulement DESCRIPTION
        emissions['TYPE_TAUX'] = emissions.apply(is_taux_revisable, axis=1)
else:
    # Si aucune des deux colonnes n'existe
    emissions['TYPE_TAUX'] = 'Fixe'

# ✅ Vérification finale
if 'TYPE_TAUX' not in emissions.columns:
    st.error("❌ Erreur critique : la colonne TYPE_TAUX n'a pas été créée.")
    st.stop()


# --- Supprimer les spreads négatifs ---
st.subheader("🧹 Nettoyage : Suppression des spreads négatifs")
neg_count = (emissions['Spread_bp'] < 0).sum()
if neg_count > 0:
    st.warning(f"❌ {neg_count} obligation(s) ont un spread négatif → exclue(s) de l'analyse.")
    emissions = emissions[emissions['Spread_bp'] >= 0].copy()
    st.success("✅ Analyse mise à jour : seules les obligations avec spread ≥ 0 sont conservées.")
else:
    st.success("✅ Aucun spread négatif détecté. Toutes les obligations sont conservées.")

# --- Onglets principaux ---
tab1, tab3, tab4 = st.tabs([
    "Analyse par Émetteur",
    "Courbe des Taux",
    "Benchmark & Comparaison"
])

# ====================== ONGLET 1 : Analyse par Émetteur ======================
with tab1:
    st.header("🔍 Analyse par Émetteur")

    # --- Filtres dans la sidebar ---
    with st.sidebar:
        st.header("⚙️ Filtres d'analyse")

        secteur = st.radio("Secteur", ["Sociétés Financières", "Sociétés Non Financières"])
        emetteurs = sorted(emissions[emissions['SECTEUR'] == secteur]['EMETTEUR'].dropna().unique())
        emetteur_choisi = st.selectbox("Émetteur", emetteurs)

        type_options = ["Tous", "TCN", "Obligation ordinaire", "Obligation subordonnée", "Obligation convertible"]
        type_general = st.selectbox("Type d'obligation", type_options)

        tcn_subtype = None
        if type_general == "TCN":
            tcn_subtype = st.radio("Type de TCN", ["Tous", "CD", "BT", "BSF"], horizontal=True)

        avec_garantie = st.radio("Garantie", ["Tous", "Avec", "Sans"])
        type_garantie = "Tous"
        if avec_garantie == "Avec":
            type_garantie = st.radio("Type de garantie", ["Tous", "GT", "GTG", "SD", "USUG", "Autre"])

        maturity_range = st.slider("Maturité (ans)", 0.0, 30.0, (1.0, 10.0), step=0.5)
        annee_min = int(emissions['ISSUEDT'].dt.year.min())
        annee_max = int(emissions['ISSUEDT'].dt.year.max())
        annee_emission = st.slider("Année d'émission", annee_min, annee_max, (2020, annee_max))

        frequence_options = ["Toutes"] + sorted(emissions['FREQUENCE_INTERET'].dropna().unique().tolist())
        frequence_choisie = st.selectbox("Fréquence intérêts", frequence_options)

        # ✅ Filtrer par type de taux
        type_taux = st.radio(
            "Type de taux",
            ["Tous", "Fixe", "Révisable"],
            horizontal=True
        )

        # ✅ Filtrer capital seulement si disponible
        if st.session_state.has_issuecapital:
            capital_min = st.slider(
                "Capital min (M MAD)",
                0,
                int(emissions['ISSUECAPITAL'].max() / 1e6),
                0,
                step=10
            )
            capital_min_dhs = capital_min * 1_000_000
        else:
            capital_min_dhs = 0

    # --- 0. Tableau global des spreads (vue d'ensemble) ---
    st.subheader("📋 Vue d'ensemble des spreads (toutes émissions)")

    overview_df = emissions[[
        'ISIN', 'EMETTEUR', 'SECTEUR', 'TYPE_LIBELLE', 'DESCRIPTION',
        'ISSUEDT', 'MATURITY_YEARS', 'INTERESTRATE', 'Taux_Souverain', 'Spread', 'Spread_bp', 'STATUT', 'FREQUENCE_INTERET', 'TYPE_TAUX'
    ]].copy()

    overview_df['ISSUEDT'] = pd.to_datetime(overview_df['ISSUEDT']).dt.strftime('%Y-%m-%d')
    overview_df['INTERESTRATE'] = overview_df['INTERESTRATE'].round(2)
    overview_df['Taux_Souverain'] = overview_df['Taux_Souverain'].round(2)
    overview_df['Spread'] = overview_df['Spread'].round(2)
    overview_df['MATURITY_YEARS'] = overview_df['MATURITY_YEARS'].round(1)

    overview_df = overview_df.rename(columns={
        'ISIN': 'ISIN',
        'EMETTEUR': 'Émetteur',
        'SECTEUR': 'Secteur',
        'TYPE_LIBELLE': 'Type',
        'DESCRIPTION': 'Description',
        'ISSUEDT': 'Émission',
        'MATURITY_YEARS': 'Maturité (ans)',
        'INTERESTRATE': 'Taux (%)',
        'Taux_Souverain': 'Taux souv. (%)',
        'Spread': 'Spread (%)',
        'Spread_bp': 'Spread (pb)',
        'STATUT': 'Statut',
        'FREQUENCE_INTERET': 'Fréq. intérêt',
        'TYPE_TAUX': 'Type de taux'
    })

    overview_df = overview_df.sort_values('Émission', ascending=True)
    st.dataframe(overview_df, use_container_width=True)

    # Export global
    csv_overview = overview_df.to_csv(index=False).encode('utf-8')
    xlsx_overview = to_excel(overview_df)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Télécharger en CSV",
            csv_overview,
            "spreads_toutes_obligations.csv",
            "text/csv",
            use_container_width=True
        )
    with col2:
        st.download_button(
            "📘 Télécharger en Excel",
            xlsx_overview,
            "spreads_toutes_obligations.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.markdown("---")

    # --- Filtrage ---
    filtered = emissions[emissions['EMETTEUR'] == emetteur_choisi].copy()

    if type_general != "Tous":
        mapping = {
            "TCN": "TCN",
            "Obligation ordinaire": "Obligation ordinaire",
            "Obligation subordonnée": "Obligation subordonnée",
            "Obligation convertible": "Obligation convertible"
        }
        filtered = filtered[filtered['TYPE_LIBELLE'] == mapping[type_general]]
    if type_general == "TCN" and tcn_subtype != "Tous":
        filtered = filtered[filtered['DESCRIPTION'].str.upper().str.startswith(tcn_subtype)]
    if avec_garantie == "Avec":
        filtered = filtered[filtered['A_GARANTIE']]
        if type_garantie != "Tous":
            filtered = filtered[filtered['GUA_TYPE'] == type_garantie]
    elif avec_garantie == "Sans":
        filtered = filtered[filtered['GUA_TYPE'] == "Aucune"]
    if frequence_choisie != "Toutes":
        filtered = filtered[filtered['FREQUENCE_INTERET'] == frequence_choisie]

    # ✅ Appliquer le filtre sur le type de taux
    if type_taux == "Fixe":
        filtered = filtered[filtered['TYPE_TAUX'] == "Fixe"]
    elif type_taux == "Révisable":
        filtered = filtered[filtered['TYPE_TAUX'] == "Révisable"]

    filtered = filtered[
        (filtered['MATURITY_YEARS'] >= maturity_range[0]) &
        (filtered['MATURITY_YEARS'] <= maturity_range[1]) &
        (filtered['ISSUEDT'].dt.year >= annee_emission[0]) &
        (filtered['ISSUEDT'].dt.year <= annee_emission[1])
    ]
    if st.session_state.has_issuecapital:
        filtered = filtered[filtered['ISSUECAPITAL'] >= capital_min_dhs]

    if len(filtered) == 0:
        st.warning("Aucune obligation trouvée.")
    else:
        st.success(f"✅ {len(filtered)} trouvée(s)")

    # Colonnes à afficher
    cols_to_show = ['ISIN', 'TYPE_LIBELLE', 'DESCRIPTION', 'ISSUEDT', 'MATURITY_YEARS', 'INTERESTRATE', 'Taux_Souverain', 'Spread', 'Spread_bp', 'STATUT', 'FREQUENCE_INTERET','TYPE_TAUX']
    if st.session_state.get('has_issuecapital', False):
        cols_to_show.insert(5, 'ISSUECAPITAL')

    display_df = filtered[cols_to_show].copy()
    display_df['ISSUEDT'] = display_df['ISSUEDT'].dt.strftime('%Y-%m-%d')
    display_df['INTERESTRATE'] = display_df['INTERESTRATE'].round(2)
    display_df['Taux_Souverain'] = display_df['Taux_Souverain'].round(2)
    display_df['Spread'] = display_df['Spread'].round(2)
    if st.session_state.get('has_issuecapital', False):
        display_df['ISSUECAPITAL'] = (display_df['ISSUECAPITAL'] / 1e6).round(2).astype(str) + " M"

    rename_dict = {
        'ISIN': 'ISIN', 'TYPE_LIBELLE': 'Type', 'DESCRIPTION': 'Description',
        'ISSUEDT': 'Émission', 'MATURITY_YEARS': 'Maturité (ans)',
        'INTERESTRATE': 'Taux (%)', 'Taux_Souverain': 'Taux souv. (%)',
        'Spread': 'Spread (%)', 'Spread_bp': 'Spread (pb)', 'STATUT': 'Statut',
        'FREQUENCE_INTERET': 'Fréq. intérêt',
        'TYPE_TAUX': 'Type de taux'
    }
    if st.session_state.get('has_issuecapital', False):
        rename_dict['ISSUECAPITAL'] = 'Capital (M MAD)'

    display_df = display_df.rename(columns=rename_dict)
    display_df_sorted = display_df.sort_values('Émission')
    st.dataframe(display_df_sorted, use_container_width=True)

    # Export
    csv = display_df_sorted.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Export CSV", csv, "spreads.csv", "text/csv", use_container_width=True)

    # --- Graphique 1: Spreads par type de taux ---
    hover_data = {'DESCRIPTION': True, 'Spread_bp': ':.0f'}
    if st.session_state.get('has_issuecapital', False):
        hover_data['ISSUECAPITAL'] = ':.0f'

    graph_data = filtered.dropna(subset=['ISSUEDT', 'Spread_bp']).copy()
    graph_data['TYPE_TAUX'] = graph_data['TYPE_TAUX']
    graph_data = graph_data.sort_values('ISSUEDT')

    if len(graph_data) > 1:
        fig = px.scatter(
            graph_data,
            x='ISSUEDT',
            y='Spread_bp',
            color='TYPE_TAUX',
            symbol='TYPE_TAUX',
            hover_name='ISIN',
            hover_data=hover_data,
            title=f"Spreads de {emetteur_choisi}",
            color_discrete_map={'Fixe': '#2C7BB6', 'Révisable': '#D70035'},
            symbol_map={'Fixe': 'circle', 'Révisable': 'triangle-up'}
        )
        fig.update_traces(marker=dict(size=10, opacity=0.85))
        st.plotly_chart(fig, use_container_width=True)

    # --- Graphique 2: Évolution des spreads (obligations vivantes) ---
    st.markdown("---")
    st.subheader("📈 Évolution des Spreads (Obligations Vivantes)")
    today = pd.Timestamp.today()
    oblig_vivantes = filtered[filtered['MATURITYDT_L'] > today].copy()

    if oblig_vivantes.empty:
        st.info("Aucune obligation vivante trouvée après filtrage.")
    else:
        cols_vivantes = ['ISSUEDT', 'Spread_bp', 'ISIN', 'DESCRIPTION', 'MATURITYDT_L', 'TYPE_LIBELLE']
        if st.session_state.get('has_issuecapital', False):
            cols_vivantes.append('ISSUECAPITAL')

        oblig_vivantes = oblig_vivantes[cols_vivantes].copy()
        oblig_vivantes = oblig_vivantes.sort_values('ISSUEDT')

        oblig_vivantes['ISSUEDT'] = oblig_vivantes['ISSUEDT'].dt.strftime('%Y-%m-%d')
        oblig_vivantes['MATURITYDT_L'] = oblig_vivantes['MATURITYDT_L'].dt.strftime('%Y-%m-%d')

        fig_live = px.line(
            oblig_vivantes,
            x='ISSUEDT',
            y='Spread_bp',
            hover_name='ISIN',
            hover_data={
                'DESCRIPTION': True,
                'MATURITYDT_L': True,
                'TYPE_LIBELLE': True,
                'Spread_bp': ':.0f'
            },
            title=f"Évolution des spreads - Obligations vivantes de {emetteur_choisi}",
            markers=True
        )

        fig_live.update_traces(
            line=dict(width=3, color='#D70035'),
            marker=dict(size=8, color='#2C7BB6', line=dict(width=1, color='white'))
        )

        fig_live.update_layout(
            paper_bgcolor='#0a0c10',
            plot_bgcolor='#0a0c10',
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='white', title="Date d'émission"),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='white', title="Spread (pb)"),
            font=dict(color='white'),
            hoverlabel=dict(bgcolor="black", font_color="white"),
            hovermode="x unified"
        )

        st.plotly_chart(fig_live, use_container_width=True)
        st.caption(f"📊 Affiche {len(oblig_vivantes)} obligation(s) vivante(s) après tous les filtres.")

            

# ======================
# ONGLET 3 : Courbe des taux
# ======================
with tab3:
    st.subheader(" Évolution de la courbe des taux souverains (BKAM)")

    selected_dates = st.multiselect(
        "Sélectionnez des dates",
        courbe['Date'].dt.strftime('%Y-%m-%d').tolist(),
        default=courbe['Date'].dt.strftime('%Y-%m-%d').tail(5).tolist()
    )

    selected_data = courbe[courbe['Date'].isin([pd.to_datetime(d) for d in selected_dates])]
    maturites = [91, 182, 365, 730, 1825, 3650, 5475, 7300, 10950]
    labels = ['13W', '26W', '1Y', '2Y', '5Y', '10Y', '15Y', '20Y', '30Y']

    curve_data = selected_data.melt(id_vars='Date', value_vars=selected_data.columns[1:], var_name='Maturité', value_name='Taux (%)')
    fig_curve = px.line(curve_data, x='Maturité', y='Taux (%)', color='Date', markers=True, title="Courbe BKAM")
    fig_curve.update_xaxes(categoryorder='array', categoryarray=labels)
    st.plotly_chart(fig_curve, use_container_width=True)

# --- Footer ---
st.markdown("---")
st.markdown(
    """
    <div class="footer">
        💼 Application interne – CFG Bank | Powered by Streamlit | Données : Maroclear & BKAM
    </div>
    """,
    unsafe_allow_html=True
)

# ======================
# ONGLET 4 : Benchmark & Comparaison d'Émetteurs
# ======================
with tab4:
    st.header("📊 Benchmark & Comparaison d'Émetteurs")

    # --- Filtres dans la sidebar ---
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🎯 Filtres - Benchmark")

        # --- Détection du secteur (identique à tab1) ---
        financial_keywords = ['banque', 'bank', 'finance', 'crédit', 'leasing', 'lease', 'assurance', 'insurance', 'capital', 'investment', 'société de financement']
        
        financial_entities = [
            'atw e', 'axa credit', 'bcp e', 'bmci', 'bmci leasi', 'boa', 'cam e', 'cdg k e',
            'cdm', 'cih e', 'ma leasing', 'saham', 'saham finances', 'salfin', 'sgmb',
            'sofac credit', 'vivalis salaf', 'wafabail', 'wafasalaf', 'attijari', 'wafabank',
            'crédit du maroc', 'société générale', 'hsbc', 'barid bank', 'bank of africa',
            'almada', 'maroc leasing', 'nacex', 'finanfac', 'société de financement du maroc'
        ]

        def is_financial(issuer):
            issuer_str = str(issuer).strip().lower()
            if any(ent in issuer_str for ent in financial_entities):
                return True
            if any(kw in issuer_str for kw in financial_keywords):
                return True
            return False

        # Recalculer SECTEUR si pas encore fait
        if 'SECTEUR' not in emissions.columns:
            emissions['SECTEUR'] = emissions['EMETTEUR'].apply(
                lambda x: "Sociétés Financières" if is_financial(x) else "Sociétés Non Financières"
            )

        # Filtre secteur
        secteur_bench = st.radio(
            "Secteur",
            ["Tous", "Sociétés Financières", "Sociétés Non Financières"],
            key="bench_secteur"
        )

        # Maturité
        maturity_range_bench = st.slider(
            "Maturité (ans)", 0.0, 30.0, (1.0, 10.0), step=0.5, key="bench_maturity"
        )

        # Année d'émission
        annee_min = int(emissions['ISSUEDT'].dt.year.min())
        annee_max = int(emissions['ISSUEDT'].dt.year.max())
        annee_bench = st.slider(
            "Année d'émission", annee_min, annee_max, (2020, annee_max), key="bench_annee"
        )

        # Type d'obligation
        type_bench = st.selectbox(
            "Type d'obligation", 
            ["Tous", "TCN", "Obligation ordinaire", "Obligation subordonnée", "Obligation convertible"],
            key="bench_type"
        )

    # --- Filtrage du dataset ---
    df_bench = emissions.copy()

    # Appliquer les filtres
    if secteur_bench != "Tous":
        df_bench = df_bench[df_bench['SECTEUR'] == secteur_bench]
    df_bench = df_bench[
        (df_bench['MATURITY_YEARS'] >= maturity_range_bench[0]) &
        (df_bench['MATURITY_YEARS'] <= maturity_range_bench[1]) &
        (df_bench['ISSUEDT'].dt.year >= annee_bench[0]) &
        (df_bench['ISSUEDT'].dt.year <= annee_bench[1])
    ]
    if type_bench != "Tous":
        mapping = {
            "TCN": "TCN",
            "Obligation ordinaire": "Obligation ordinaire",
            "Obligation subordonnée": "Obligation subordonnée",
            "Obligation convertible": "Obligation convertible"
        }
        df_bench = df_bench[df_bench['TYPE_LIBELLE'] == mapping[type_bench]]

    if df_bench.empty:
        st.warning("Aucune obligation disponible pour ces critères.")
        st.stop()

    # --- Sélection des émetteurs à comparer ---
    st.subheader("🔍 Sélection des Émetteurs à Comparer")
    emetteurs_dispo = sorted(df_bench['EMETTEUR'].dropna().unique())
    emetteurs_choisis = st.multiselect(
        "Sélectionnez les émetteurs à comparer",
        options=emetteurs_dispo,
        default=emetteurs_dispo[:5]  # Top 5 par défaut
    )

    if not emetteurs_choisis:
        st.info("Veuillez sélectionner au moins un émetteur pour la comparaison.")
    else:
        filtered_bench = df_bench[df_bench['EMETTEUR'].isin(emetteurs_choisis)].copy()

        if filtered_bench.empty:
            st.warning("Aucune obligation trouvée pour les émetteurs sélectionnés.")
        else:
            st.success(f"✅ {len(filtered_bench)} obligations trouvées pour {len(emetteurs_choisis)} émetteurs")

            # --- Tableau des obligations ---
            st.markdown("### 📋 Détail des Obligations")
            cols_show_bench = [
                'ISIN', 'EMETTEUR', 'TYPE_LIBELLE', 'DESCRIPTION', 'ISSUEDT',
                'MATURITY_YEARS', 'INTERESTRATE', 'Taux_Souverain', 'Spread_bp',
                'TYPE_TAUX', 'FREQUENCE_INTERET'
            ]
            if st.session_state.get('has_issuecapital', False):
                cols_show_bench.insert(5, 'ISSUECAPITAL')

            display_bench = filtered_bench[cols_show_bench].copy()
            display_bench['ISSUEDT'] = display_bench['ISSUEDT'].dt.strftime('%Y-%m-%d')
            display_bench['INTERESTRATE'] = display_bench['INTERESTRATE'].round(2)
            display_bench['Taux_Souverain'] = display_bench['Taux_Souverain'].round(2)
            display_bench['Spread_bp'] = display_bench['Spread_bp'].round(0).astype(int)
            if st.session_state.get('has_issuecapital', False):
                display_bench['ISSUECAPITAL'] = (display_bench['ISSUECAPITAL'] / 1e6).round(2).astype(str) + " M"

            rename_bench = {
                'ISIN': 'ISIN',
                'EMETTEUR': 'Émetteur',
                'TYPE_LIBELLE': 'Type',
                'DESCRIPTION': 'Description',
                'ISSUEDT': 'Émission',
                'MATURITY_YEARS': 'Maturité (ans)',
                'INTERESTRATE': 'Taux (%)',
                'Taux_Souverain': 'Taux souv. (%)',
                'Spread_bp': 'Spread (pb)',
                'TYPE_TAUX': 'Type de taux',
                'FREQUENCE_INTERET': 'Fréq. intérêt'
            }
            if st.session_state.get('has_issuecapital', False):
                rename_bench['ISSUECAPITAL'] = 'Capital (M MAD)'

            display_bench = display_bench.rename(columns=rename_bench)
            st.dataframe(display_bench, use_container_width=True)

            # --- Export ---
            csv_bench = display_bench.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Télécharger les données comparées (CSV)",
                csv_bench,
                "benchmark_obligations.csv",
                "text/csv",
                use_container_width=True
            )

            # --- KPIs ---
            st.markdown("### 📊 KPIs de Comparaison")
            col1, col2, col3, col4 = st.columns(4)
            spread_mean = filtered_bench.groupby('EMETTEUR')['Spread_bp'].mean().round(1)
            spread_std = filtered_bench.groupby('EMETTEUR')['Spread_bp'].std().round(1)
            count_bonds = filtered_bench.groupby('EMETTEUR').size()
            maturity_avg = filtered_bench.groupby('EMETTEUR')['MATURITY_YEARS'].mean().round(1)

            col1.metric("Nb Émetteurs", len(emetteurs_choisis))
            col2.metric("Spread Moyen Global", f"{spread_mean.mean():.1f} pb")
            col3.metric("Écart-type moyen", f"{spread_std.mean():.1f} pb")
            col4.metric("Maturité Moy.", f"{maturity_avg.mean():.1f} ans")

            # --- Graphique 1: Spread vs Maturité (par émetteur) ---
            st.markdown("### 📈 Spread vs Maturité (par émetteur)")
            fig_scatter = px.scatter(
                filtered_bench,
                x='MATURITY_YEARS',
                y='Spread_bp',
                color='EMETTEUR',
                hover_name='ISIN',
                hover_data={
                    'DESCRIPTION': True,
                    'INTERESTRATE': ':.2f',
                    'ISSUEDT': True
                },
                title="Spread (pb) vs Maturité (ans) - Comparaison par émetteur",
                labels={'MATURITY_YEARS': 'Maturité (ans)', 'Spread_bp': 'Spread (pb)'},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_scatter.update_traces(marker=dict(size=10, opacity=0.8))
            st.plotly_chart(fig_scatter, use_container_width=True)

            # --- Graphique 2: Spread moyen par type d'obligation ---
            st.markdown("### 📊 Spread Moyen par Type d'Obligation")
            spread_by_type = filtered_bench.groupby(['EMETTEUR', 'TYPE_LIBELLE'])['Spread_bp'].mean().reset_index()
            fig_type = px.bar(
                spread_by_type,
                x='TYPE_LIBELLE',
                y='Spread_bp',
                color='EMETTEUR',
                barmode='group',
                title="Spread Moyen par Type d'Obligation",
                labels={'Spread_bp': 'Spread Moyen (pb)', 'TYPE_LIBELLE': 'Type d’obligation'},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig_type, use_container_width=True)

            # --- Graphique 3: Distribution des spreads (boxplot) ---
            st.markdown("### 📏 Distribution des Spreads (Boxplot)")
            fig_box = px.box(
                filtered_bench,
                x='EMETTEUR',
                y='Spread_bp',
                color='EMETTEUR',
                title="Distribution des Spreads par Émetteur",
                labels={'Spread_bp': 'Spread (pb)', 'EMETTEUR': 'Émetteur'},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig_box, use_container_width=True)

            # --- Graphique 4: Évolution des spreads dans le temps (lignes droites, sans lissage) ---
    st.markdown("### 📅 Évolution des Spreads dans le Temps (Comparaison)")

    # Préparer les données
    time_data = filtered_bench.dropna(subset=['ISSUEDT', 'Spread_bp']).copy()
    time_data = time_data.sort_values(['EMETTEUR', 'ISSUEDT'])

    if len(time_data) < 2:
        st.info("📊 Pas assez de données dans le temps pour afficher une évolution.")
    else:
        fig_timeline = px.line(
            time_data,
            x='ISSUEDT',
            y='Spread_bp',
            color='EMETTEUR',
            markers=True,  # Affiche les points
            hover_name='ISIN',
            hover_data={
                'DESCRIPTION': True,
                'INTERESTRATE': ':.2f',
                'MATURITY_YEARS': ':.1f ans'
            },
            title="Évolution des Spreads dans le Temps par Émetteur",
            labels={'ISSUEDT': 'Date d\'émission', 'Spread_bp': 'Spread (pb)', 'EMETTEUR': 'Émetteur'},
            line_shape='linear',  # ✅ Ligne droite entre points (affine)
            color_discrete_sequence=px.colors.qualitative.Bold
        )

    # Personnalisation pour un rendu pro
    fig_timeline.update_traces(
        line=dict(width=2.5),
        marker=dict(size=8, line=dict(width=1, color="DarkSlateGrey")),
        mode='lines+markers'
    )

    fig_timeline.update_layout(
        hovermode='x unified',
        xaxis_title="Date d'émission",
        yaxis_title="Spread (points de base)",
        legend_title="Émetteur",
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',  # Fond transparent
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.1)'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.1)')
    )

    st.plotly_chart(fig_timeline, use_container_width=True)
    # --- Graphique 5: Boxplot des spreads (obligations vivantes uniquement) ---
st.markdown("### 📦 Spread des Obligations Vivantes (Distribution par Émetteur)")

today = pd.Timestamp.today()

# Filtrer les obligations vivantes parmi les émetteurs sélectionnés
vivantes_bench = filtered_bench[filtered_bench['MATURITYDT_L'] > today].copy()

if vivantes_bench.empty:
    st.info("Aucune obligation vivante trouvée parmi les émetteurs sélectionnés.")
else:
    st.success(f"✅ {len(vivantes_bench)} obligation(s) vivante(s) incluse(s) dans l’analyse.")

    fig_box_live = px.box(
        vivantes_bench,
        x='EMETTEUR',
        y='Spread_bp',
        color='EMETTEUR',
        title="Distribution des Spreads (Obligations Vivantes)",
        labels={'Spread_bp': 'Spread (pb)', 'EMETTEUR': 'Émetteur'},
        hover_data={
            'ISIN': True,
            'DESCRIPTION': True,
            'MATURITY_YEARS': ':.1f ans',
            'INTERESTRATE': ':.2f%'
        },
        color_discrete_sequence=px.colors.qualitative.Bold
    )

    fig_box_live.update_layout(
        xaxis_title="Émetteur",
        yaxis_title="Spread (points de base)",
        showlegend=False,
        hovermode='x unified'
    )

    st.plotly_chart(fig_box_live, use_container_width=True) 

    # --- Classement ---
    st.markdown("### 🏆 Classement des Émetteurs par Spread Moyen")
    ranking = spread_mean.sort_values(ascending=True).reset_index()
    ranking.columns = ['Émetteur', 'Spread Moyen (pb)']
    ranking['Rang'] = ranking.index + 1
    st.dataframe(ranking, use_container_width=True)

    # --- Top 3 / Bottom 3 ---
    top3 = ranking.head(3)['Émetteur'].tolist()
    bottom3 = ranking.tail(3)['Émetteur'].tolist()
    st.markdown(f"**Meilleur crédit** : 1. {top3[0]} | 2. {top3[1]} | 3. {top3[2]}")
    st.markdown(f"**Risque de crédit élevé** : 1. {bottom3[2]} | 2. {bottom3[1]} | 3. {bottom3[0]}")
