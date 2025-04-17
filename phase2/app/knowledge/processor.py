import os
import glob
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from ..core.config import settings
from loguru import logger

class KnowledgeProcessor:
    """Classe pour traiter les fichiers HTML de la base de connaissances"""
    
    def __init__(self):
        self.knowledge_base_dir = settings.KNOWLEDGE_BASE_DIR
        logger.info(f"Initialisation du processeur de connaissances. Répertoire: {self.knowledge_base_dir}")
    
    def get_all_html_files(self) -> List[str]:
        """Récupère tous les fichiers HTML dans le répertoire de la base de connaissances"""
        html_files = glob.glob(os.path.join(self.knowledge_base_dir, "*.html"))
        logger.info(f"Trouvé {len(html_files)} fichiers HTML dans la base de connaissances")
        return html_files
    
    def extract_content_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extrait le contenu d'un fichier HTML"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraire le titre (premier h2)
            title = ''
            if soup.find('h2'):
                title = soup.find('h2').text.strip()
            
            # Extraire les paragraphes d'introduction
            intro_paragraphs = []
            for p in soup.find_all('p'):
                intro_paragraphs.append(p.text.strip())
            
            # Extraire les tables avec les données HMO
            tables = []
            for table in soup.find_all('table'):
                table_data = []
                rows = table.find_all('tr')
                
                # Extraire les en-têtes
                headers = []
                if rows and rows[0].find_all('th'):
                    for th in rows[0].find_all('th'):
                        headers.append(th.text.strip())
                
                # Extraire les données
                for row in rows[1:]:  # Ignore the header row
                    row_data = []
                    for cell in row.find_all('td'):
                        row_data.append(cell.text.strip())
                    if row_data:
                        table_data.append(row_data)
                
                tables.append({
                    'headers': headers,
                    'data': table_data
                })
            
            # Extraire les informations de contact
            contact_info = {}
            contact_section = soup.find_all('h3')
            for section in contact_section:
                if "טלפון" in section.text or "מספרי" in section.text:
                    contact_list = section.find_next('ul')
                    if contact_list:
                        contacts = []
                        for li in contact_list.find_all('li'):
                            contacts.append(li.text.strip())
                        contact_info['phones'] = contacts
            
            filename = os.path.basename(file_path)
            service_type = os.path.splitext(filename)[0]
            
            return {
                'service_type': service_type,
                'title': title,
                'introduction': intro_paragraphs,
                'tables': tables,
                'contact_info': contact_info,
                'source_file': file_path
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de contenu de {file_path}: {str(e)}")
            return {
                'service_type': os.path.basename(file_path),
                'error': str(e)
            }
    
    def process_all_knowledge_base(self) -> List[Dict[str, Any]]:
        """Traite tous les fichiers de la base de connaissances"""
        knowledge_items = []
        for html_file in self.get_all_html_files():
            item = self.extract_content_from_file(html_file)
            knowledge_items.append(item)
        
        logger.info(f"Base de connaissances traitée: {len(knowledge_items)} éléments")
        return knowledge_items
    
    def filter_by_hmo_and_tier(self, knowledge_items: List[Dict[str, Any]], 
                               hmo_name: str, insurance_tier: str) -> List[Dict[str, Any]]:
        """Filtre les informations en fonction de la HMO et du niveau d'assurance"""
        filtered_items = []
        
        for item in knowledge_items:
            # Copier l'élément pour ne pas modifier l'original
            filtered_item = item.copy()
            
            # Filtrer les tables pour ne conserver que les colonnes pertinentes
            if 'tables' in filtered_item:
                filtered_tables = []
                for table in filtered_item['tables']:
                    # Trouver l'index de la colonne correspondant à la HMO
                    hmo_index = None
                    for i, header in enumerate(table['headers']):
                        if header == hmo_name:
                            hmo_index = i
                            break
                    
                    if hmo_index is not None:
                        # Créer une nouvelle table avec uniquement les colonnes nécessaires
                        new_table = {
                            'headers': [table['headers'][0], hmo_name],  # Première colonne (nom du service) et colonne HMO
                            'data': []
                        }
                        
                        # Filtrer les données par niveau d'assurance
                        for row in table['data']:
                            hmo_data = row[hmo_index]
                            # Chercher les sections correspondant au niveau d'assurance
                            if insurance_tier in hmo_data:
                                # Extraire uniquement la partie correspondant au niveau d'assurance
                                lines = hmo_data.split('\n')
                                tier_info = ""
                                for line in lines:
                                    if insurance_tier in line:
                                        tier_info = line
                                        break
                                
                                new_table['data'].append([row[0], tier_info])
                        
                        filtered_tables.append(new_table)
                
                filtered_item['tables'] = filtered_tables
            
            filtered_items.append(filtered_item)
        
        return filtered_items

# Exemple d'utilisation
if __name__ == "__main__":
    processor = KnowledgeProcessor()
    knowledge_base = processor.process_all_knowledge_base()
    filtered_knowledge = processor.filter_by_hmo_and_tier(knowledge_base, "מכבי", "זהב")
    print(f"Items après filtrage: {len(filtered_knowledge)}") 