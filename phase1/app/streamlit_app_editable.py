import streamlit as st
import json
import tempfile
import os
import sys
import pandas as pd
from utils.ocr import DocumentIntelligenceExtractor
from utils.openai_extractor import OpenAIExtractor
from utils.validation import ExtractionValidator

# Configuration de la page
st.set_page_config(
    page_title="Form Extractor ביטוח לאומי",
    page_icon="📄",
    layout="wide"
)

# Titre et description
st.title("Form Extractor ביטוח לאומי")
st.markdown("""
This application automatically extracts information from National Insurance Institute forms (ביטוח לאומי).

**Instructions:**
1. Upload a form in PDF or JPG format
2. Wait for the document to be processed
3. View and edit the extracted results if needed
""")

# Initialisation des extracteurs
@st.cache_resource
def get_extractors():
    return DocumentIntelligenceExtractor(), OpenAIExtractor(), ExtractionValidator()

doc_extractor, openai_extractor, validator = get_extractors()

# Zone de téléchargement
uploaded_file = st.file_uploader(
    "Choose a file",
    type=["pdf", "jpg", "jpeg"],
    help="Accepted formats: PDF, JPG"
)

# Fonction pour convertir un dictionnaire imbriqué en liste de paires clé-valeur plates
def flatten_dict(d, parent_key=''):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key))
        else:
            items.append((new_key, v))
    return items

# Fonction pour reconstruire un dictionnaire imbriqué à partir d'une liste de paires clé-valeur plates
def rebuild_dict(flat_items):
    result = {}
    for key, value in flat_items:
        parts = key.split('.')
        d = result
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value
    return result

if uploaded_file is not None:
    # Créer deux colonnes
    col1, col2 = st.columns([1, 2])
    
    with st.spinner("Processing..."):
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            # Étape 1: Extraction OCR
            with st.status("OCR extraction in progress...") as status:
                ocr_result = doc_extractor.extract_text(tmp_path)
                status.update(label="OCR completed ✅")
                
                with col1:
                    st.subheader("Extracted Text")
                    # Extraire uniquement le texte (sans les scores de confiance)
                    extracted_text = "\n".join([span.get("text", "") for span in ocr_result.get("text", [])])
                    st.text_area(
                        "Raw Text",
                        value=extracted_text,
                        height=400,
                        disabled=True
                    )

            # Étape 2: Extraction structurée
            with st.status("Content analysis in progress...") as status:
                # Envoyer uniquement le contenu textuel à OpenAI, pas les métadonnées OCR
                text_content = "\n".join([span.get("text", "") for span in ocr_result.get("text", [])])
                structured_result = openai_extractor.extract_structured_data(text_content)
                
                status.update(label="Analysis completed ✅")
                
                # Store the original extraction for later comparison
                if "extraction_result" not in st.session_state:
                    st.session_state["extraction_result"] = structured_result
                
                with col2:
                    st.subheader("Structured Data (Editable)")
                    
                    # Ajouter une section de débogage pour identifier la source du problème
                    with st.expander("Debug Information (Technical)"):
                        st.markdown("### OpenAI Extraction Result (Raw)")
                        st.json(structured_result)
                        
                        st.markdown("### Flattened Structure")
                        flat_items = flatten_dict(structured_result)
                        flat_dict = dict(flat_items)
                        st.json(flat_dict)
                    
                    # Créer un formulaire pour les données structurées
                    with st.form("structured_data_form", clear_on_submit=False):
                        # Dictionnaire pour des libellés plus descriptifs des champs
                        field_labels = {
                            # Personal information
                            "lastName": "Last Name",
                            "firstName": "First Name",
                            "idNumber": "ID Number",
                            "gender": "Gender",
                            
                            # Date of birth
                            "dateOfBirth.day": "Day",
                            "dateOfBirth.month": "Month",
                            "dateOfBirth.year": "Year",
                            
                            # Address
                            "address.street": "Street",
                            "address.houseNumber": "House Number",
                            "address.entrance": "Entrance",
                            "address.apartment": "Apartment",
                            "address.city": "City",
                            "address.postalCode": "Postal Code",
                            "address.poBox": "P.O. Box",
                            
                            # Contacts
                            "landlinePhone": "Landline Phone",
                            "mobilePhone": "Mobile Phone",
                            
                            # Employment
                            "jobType": "Job Type",
                            
                            # Accident
                            "dateOfInjury.day": "Day",
                            "dateOfInjury.month": "Month",
                            "dateOfInjury.year": "Year",
                            "timeOfInjury": "Time of Injury",
                            "accidentLocation": "Accident Location",
                            "accidentAddress": "Accident Address",
                            "accidentDescription": "Accident Description",
                            "injuredBodyPart": "Injured Body Part",
                            
                            # Form details
                            "signature": "Signature",
                            "formFillingDate.day": "Day",
                            "formFillingDate.month": "Month",
                            "formFillingDate.year": "Year",
                            "formReceiptDateAtClinic.day": "Day",
                            "formReceiptDateAtClinic.month": "Month",
                            "formReceiptDateAtClinic.year": "Year",
                            
                            # Medical information
                            "medicalInstitutionFields.healthFundMember": "Health Fund Member",
                            "medicalInstitutionFields.natureOfAccident": "Nature of Accident",
                            "medicalInstitutionFields.medicalDiagnoses": "Medical Diagnoses"
                        }
                        
                        # Fonction pour obtenir le libellé amélioré d'un champ
                        def get_field_label(key, field_parts):
                            # Vérifier si on a un libellé personnalisé
                            if key in field_labels:
                                base_label = field_labels[key]
                            else:
                                # Sinon, utiliser le nom du champ
                                base_label = field_parts[-1].capitalize()
                                
                            # Contextualiser les dates
                            if field_parts[-1] in ["day", "month", "year"] and len(field_parts) > 1:
                                context = field_parts[-2]
                                if context == "dateOfBirth":
                                    context_label = "Date of Birth"
                                elif context == "dateOfInjury":
                                    context_label = "Date of Injury"
                                elif context == "formFillingDate":
                                    context_label = "Form Filling Date"
                                elif context == "formReceiptDateAtClinic":
                                    context_label = "Form Receipt Date at Clinic"
                                else:
                                    context_label = context.capitalize()
                                    
                                return f"{context_label} - {base_label}"
                            
                            return base_label
                        
                        # Aplatir le dictionnaire pour faciliter l'édition
                        flat_items = flatten_dict(structured_result)
                        
                        # Titres plus descriptifs des sections
                        section_titles = {
                            "Personal Information": "🧑 Personal Information",
                            "Date of Birth": "🎂 Date of Birth",
                            "Address": "🏠 Address",
                            "Contact Information": "📱 Contact Information",
                            "Job Information": "💼 Job Information",
                            "Injury Information": "🩹 Injury Information",
                            "Form Details": "📝 Form Details",
                            "Medical Institution Information": "🏥 Medical Institution Information"
                        }
                        
                        # Organiser les champs selon la structure requise dans le README
                        sections = {
                            "Personal Information": ["lastName", "firstName", "idNumber", "gender"],
                            "Date of Birth": ["dateOfBirth.day", "dateOfBirth.month", "dateOfBirth.year"],
                            "Address": ["address.street", "address.houseNumber", "address.entrance", 
                                     "address.apartment", "address.city", "address.postalCode", "address.poBox"],
                            "Contact Information": ["landlinePhone", "mobilePhone"],
                            "Job Information": ["jobType"],
                            "Injury Information": ["dateOfInjury.day", "dateOfInjury.month", "dateOfInjury.year", 
                                              "timeOfInjury", "accidentLocation", "accidentAddress", 
                                              "accidentDescription", "injuredBodyPart"],
                            "Form Details": ["signature", 
                                           "formFillingDate.day", "formFillingDate.month", "formFillingDate.year",
                                           "formReceiptDateAtClinic.day", "formReceiptDateAtClinic.month", "formReceiptDateAtClinic.year"],
                            "Medical Institution Information": ["medicalInstitutionFields.healthFundMember", 
                                                            "medicalInstitutionFields.natureOfAccident",
                                                            "medicalInstitutionFields.medicalDiagnoses"]
                        }
                        
                        # Stocker les entrées modifiées
                        edited_items = []
                        
                        # Pour chaque section, créer un en-tête et afficher les champs
                        for section_name, section_fields in sections.items():
                            # Utiliser un titre amélioré pour la section
                            st.subheader(section_titles.get(section_name, section_name))
                            
                            # Organiser en colonnes pour une meilleure présentation
                            if section_name in ["Address", "Injury Information", "Medical Institution Information"]:
                                # Sections avec beaucoup de champs: une colonne
                                cols = [st.container()]
                                col_count = 1
                            else:
                                # Autres sections: deux colonnes
                                cols = st.columns(2)
                                col_count = 2
                            
                            col_idx = 0
                            
                            # Parcourir tous les champs à plat
                            for key, value in flat_items:
                                # Vérifier si cette clé appartient à cette section
                                if any(field in key for field in section_fields):
                                    # Obtenir les parties du champ
                                    field_parts = key.split('.')
                                    
                                    # Obtenir un libellé amélioré
                                    label = get_field_label(key, field_parts)
                                    
                                    # Créer une clé unique pour chaque input
                                    unique_key = f"input_{key.replace('.', '_')}"
                                    
                                    # Afficher le champ dans la colonne appropriée
                                    with cols[col_idx % col_count]:
                                        edited_value = st.text_input(label, value, key=unique_key)
                                        edited_items.append((key, edited_value))
                                        col_idx += 1
                            
                            # Ajouter un séparateur entre les sections
                            st.markdown("---")
                        
                        # Ajouter un bouton pour soumettre les modifications
                        submit_button = st.form_submit_button("Update Data")
                        
                        if submit_button:
                            # Reconstruire le dictionnaire à partir des éléments édités
                            updated_result = rebuild_dict(edited_items)
                            
                            # Détecter les champs modifiés manuellement
                            original_result = st.session_state.get("extraction_result", {})
                            manual_corrections = {}
                            
                            # Utiliser la même méthode pour aplatir les résultats originaux
                            flat_original = dict(flatten_dict(original_result))
                            flat_updated = dict(edited_items)
                            
                            for key, new_value in flat_updated.items():
                                if key in flat_original and flat_original[key] != new_value:
                                    manual_corrections[key] = new_value
                            
                            # Mettre à jour l'état de la session
                            structured_result = updated_result
                            st.session_state['updated_result'] = updated_result
                            
                            st.success("Data updated successfully!")
                    
                    # Bouton de téléchargement en dehors du formulaire
                    json_str = json.dumps(structured_result, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="📥 Download results (JSON)",
                        data=json_str.encode('utf-8'),
                        file_name="extraction_results.json",
                        mime="application/json"
                    )
            
            # Étape 3: Validation des données
            with st.status("Data validation in progress...") as status:
                validation_result = validator.validate_extracted_data(structured_result, ocr_result)
                status.update(label="Validation completed ✅")
                
                # Afficher les résultats de validation
                st.subheader("Data Validation")
                
                # Définir les métriques et leurs explications
                metrics_explanation = """
                **Metrics explanation:**
                - **Completeness**: Percentage of fields filled out of all possible fields (higher is better)
                - **Accuracy**: Percentage of filled fields that have valid format (higher is better)
                - **OCR Confidence**: Average confidence score of the OCR text extraction (higher is better)
                """
                st.markdown(metrics_explanation)
                
                # Afficher les métriques sous forme de jauge
                metrics_cols = st.columns(3)
                with metrics_cols[0]:
                    completeness = validation_result['completeness']['score']
                    st.metric("Completeness", f"{completeness:.2%}")
                    # Afficher une barre de progression colorée
                    st.progress(completeness)
                
                with metrics_cols[1]:
                    accuracy = validation_result['accuracy']['score']
                    st.metric("Accuracy", f"{accuracy:.2%}")
                    st.progress(accuracy)
                
                with metrics_cols[2]:
                    ocr_confidence = validation_result['confidence']['score']
                    st.metric("OCR Confidence", f"{ocr_confidence:.2%}")
                    st.progress(ocr_confidence)
                
                # Nouvelle section pour les problèmes importants
                has_issues = False
                
                st.subheader("🔍 Validation Issues")
                
                # Collecter tous les problèmes dans une liste pour les afficher ensemble
                issues_list = []
                
                # Vérifier s'il y a des champs requis manquants
                if validation_result['completeness']['missing_required']:
                    has_issues = True
                    missing_fields = validation_result['completeness']['missing_required']
                    issues_list.append({
                        "type": "warning",
                        "title": f"Missing Required Fields ({len(missing_fields)})",
                        "message": f"The following required fields are missing: {', '.join(missing_fields)}"
                    })
                
                # Vérifier s'il y a des erreurs de format
                if 'accuracy' in validation_result and 'invalid_fields' in validation_result['accuracy']:
                    invalid_fields = validation_result['accuracy']['invalid_fields']
                    if invalid_fields:
                        has_issues = True
                        for field_info in invalid_fields:
                            issues_list.append({
                                "type": "error",
                                "title": f"Invalid Format: {field_info['field']}",
                                "message": f"{field_info['reason']} (value: {field_info['value']})"
                            })
                
                # Si la confiance OCR est faible, ajouter un avertissement
                if ocr_confidence < 0.7:
                    has_issues = True
                    issues_list.append({
                        "type": "warning",
                        "title": "Low OCR Confidence",
                        "message": f"The OCR confidence score is only {ocr_confidence:.2%}, which may lead to extraction errors."
                    })
                
                # Afficher tous les problèmes
                if has_issues:
                    for issue in issues_list:
                        if issue["type"] == "error":
                            st.error(f"**{issue['title']}**: {issue['message']}")
                        elif issue["type"] == "warning":
                            st.warning(f"**{issue['title']}**: {issue['message']}")
                else:
                    st.success("✅ No validation issues found! All fields look good.")
                
                # Créer des logs lisibles à partir des résultats de validation
                logs = []
                logs.append("VALIDATION SUMMARY")
                logs.append("=" * 40)
                logs.append(f"COMPLETENESS: {validation_result['completeness']['score']:.2%}")
                logs.append(f"  - Filled fields: {validation_result['completeness']['filled_fields']}/{validation_result['completeness']['total_fields']}")
                
                if validation_result['completeness']['missing_required']:
                    logs.append(f"  - Missing required fields: {', '.join(validation_result['completeness']['missing_required'])}")
                else:
                    logs.append("  - All required fields are present")
                
                logs.append(f"ACCURACY: {validation_result['accuracy']['score']:.2%}")
                logs.append(f"  - Valid format fields: {validation_result['accuracy']['valid_format_fields']}/{validation_result['accuracy']['total_fields']}")
                
                if 'invalid_fields' in validation_result['accuracy'] and validation_result['accuracy']['invalid_fields']:
                    logs.append(f"  - Fields with invalid format: {len(validation_result['accuracy']['invalid_fields'])}")
                    for field_info in validation_result['accuracy']['invalid_fields']:
                        logs.append(f"    * {field_info['field']}: '{field_info['value']}' - {field_info['reason']}")
                
                logs.append(f"OCR CONFIDENCE: {validation_result['confidence']['score']:.2%}")
                logs.append("=" * 40)
                
                # Afficher les logs de validation
                st.subheader("📋 Validation Logs")
                
                # Onglets pour différents types de logs
                log_tabs = st.tabs(["Summary", "Complete Logs", "Field Details"])
                
                with log_tabs[0]:
                    st.text_area("Validation Summary", value="\n".join(logs), height=200)
                
                with log_tabs[1]:
                    if 'logs' in validation_result:
                        complete_logs = "\n".join(validation_result.get("logs", []))
                        st.text_area("Complete Logs", value=complete_logs, height=300)
                    else:
                        st.info("No detailed logs available from the validator.")
                
                with log_tabs[2]:
                    # Afficher des informations détaillées sur chaque champ validé
                    field_details = []
                    flat_data = structured_result
                    if isinstance(structured_result, dict):
                        # Créer une représentation plate du dictionnaire pour la lisibilité
                        flat_items = flatten_dict(structured_result)
                        flat_data = dict(flat_items)
                    
                    # Afficher un tableau des champs pour analyse rapide
                    field_data = []
                    for key, value in flat_data.items():
                        if not key.endswith('confidence') and not key.endswith('confidences'):
                            status = "✅ Valid"
                            # Vérifier si le champ est dans la liste des champs invalides
                            for invalid in validation_result['accuracy'].get('invalid_fields', []):
                                if invalid['field'] == key:
                                    status = f"❌ Invalid: {invalid['reason']}"
                                    break
                            # Vérifier si c'est un champ requis manquant
                            if not value and key in validation_result['completeness'].get('missing_required', []):
                                status = "⚠️ Missing required field"
                            
                            field_data.append({"Field": key, "Value": value, "Status": status})
                    
                    if field_data:
                        st.dataframe(pd.DataFrame(field_data), use_container_width=True)
                    else:
                        st.info("No field details available.")
            
            # Informations sur le document
            st.subheader("Document Information")
            doc_info = {
                "File name": uploaded_file.name,
                "File size": f"{len(uploaded_file.getvalue()) / 1024:.2f} KB",
                "OCR quality": f"{ocr_confidence:.2%}",
                "Pages processed": ocr_result.get("page_count", 1),
                "Text elements": len(ocr_result.get("text", [])),
                "Overall validation score": f"{(completeness + accuracy + ocr_confidence) / 3:.2%}"
            }
            
            st.json(doc_info)
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
        
        finally:
            # Nettoyer les fichiers temporaires
            try:
                os.unlink(tmp_path)
            except:
                pass

    # Remarque de bas de page
    st.markdown("---")
    st.caption("Note: This application is for demonstration purposes only.")
else:
    # Instructions lorsqu'aucun fichier n'est téléchargé
    st.info("Please upload a form to begin extraction.")
    
    # Explication des fonctionnalités
    st.markdown("""
    ## Features
    
    - **OCR Text Extraction**: Extract raw text from documents
    - **Structured Data Extraction**: Convert raw text into structured data
    - **Data Validation**: Verify completeness and accuracy of extracted data
    - **Manual Editing**: Correct any errors in the extracted data
    
    ## Supported Fields
    
    - Personal information (name, ID, gender)
    - Contact information
    - Injury and accident details
    - Medical information
    - Form metadata
    """) 