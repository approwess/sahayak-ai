import json
import os
from typing import List, Dict, Optional
from pathlib import Path

class ResourceFinder:
    def __init__(self, json_file_path: str = None):
        """Initialize ResourceFinder with JSON file path"""
        if json_file_path is None:
            # Default path relative to the service file
            json_file_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 'data', 'textbook_links.json'
            )
        
        self.json_file_path = json_file_path
        self.resources_data = self._load_json_file()
    
    def _load_json_file(self) -> Dict:
        """Load and parse the JSON file"""
        try:
            if not os.path.exists(self.json_file_path):
                print(f"❌ JSON file not found at: {self.json_file_path}")
                return {"resources": []}
            
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                print(f"✅ Successfully loaded {len(data.get('resources', []))} resources")
                return data
                
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON file: {e}")
            return {"resources": []}
        except Exception as e:
            print(f"❌ Error loading JSON file: {e}")
            return {"resources": []}
    
    def find_links_by_criteria(self, grades: str, medium: str = None, subject: str = None, topic: str = None) -> List[Dict]:
        """Find educational links based on grade(s), medium, and topic"""

        # Parse grades string into list
        grade_list = self._parse_grades(grades)
        
        matching_resources = []
        
        for resource in self.resources_data.get('resources', []):
            medium_match = True
            if medium:
                resource_medium = resource.get('medium', '').lower()
                medium_match = medium.lower() in resource_medium or resource_medium in medium.lower()
            subject_match = True
            if subject:
                resource_subject = resource.get('subject', '').lower()
                subject_match = subject.lower() in resource_subject or resource_subject in subject.lower()
            # Check if resource matches any of the specified grades
            if str(resource.get('grade')) in grade_list and medium_match and subject_match:
                # Check medium match (case-insensitive)
                # medium_match = True
                # if medium:
                #     resource_medium = resource.get('medium', '').lower()
                #     medium_match = medium.lower() in resource_medium or resource_medium in medium.lower()
                
                # Check topic match (case-insensitive, partial match)
                # topic_match = True
                # if topic:
                #     resource_topic = resource.get('topic', '').lower()
                #     topic_match = topic.lower() in resource_topic or resource_topic in topic.lower()
                
                # If all criteria match, add to results
                print(medium_match)
                if medium_match:
                    matching_resources.append({
                        'grade': resource.get('grade'),
                        'medium': resource.get('medium'),
                        'topic': resource.get('topic'),
                        'subject': resource.get('subject'),
                        'link': resource.get('link', [])
                    })
        
        return matching_resources
    
    def _parse_grades(self, grades_str: str) -> List[str]:
        """Parse grades string into list of individual grades"""
        if not grades_str:
            return ['1']  # Default grade
        
        # Handle various formats: "1,2,3", "1, 2, 3", "1-3", etc.
        grades_str = grades_str.strip()
        
        # Split by comma and clean up
        if ',' in grades_str:
            grade_list = [g.strip() for g in grades_str.split(',') if g.strip()]
        # Handle range format like "1-3"
        elif '-' in grades_str and len(grades_str.split('-')) == 2:
            start, end = grades_str.split('-')
            try:
                start_num = int(start.strip())
                end_num = int(end.strip())
                grade_list = [str(i) for i in range(start_num, end_num + 1)]
            except ValueError:
                grade_list = [grades_str]
        else:
            # Single grade
            grade_list = [grades_str]
        
        return grade_list
    
    def get_all_resources(self) -> Dict:
        """Get all resources from the JSON file"""
        return self.resources_data
    
    def search_resources(self, search_term: str) -> List[Dict]:
        """Search resources by any field containing the search term"""
        search_term = search_term.lower()
        matching_resources = []
        
        for resource in self.resources_data.get('resources', []):
            # Search in grade, medium, topic, subject, and link titles
            searchable_fields = [
                resource.get('grade', ''),
                resource.get('medium', ''),
                resource.get('topic', ''),
                resource.get('subject', '')
            ]
            
            # Add link titles to searchable fields
            for link in resource.get('links', []):
                searchable_fields.append(link.get('title', ''))
                searchable_fields.append(link.get('description', ''))
            
            # Check if search term matches any field
            if any(search_term in field.lower() for field in searchable_fields):
                matching_resources.append(resource)
        
        return matching_resources