from langchain_google_genai import ChatGoogleGenerativeAI
import os
import json
from typing import Dict, List, Optional
from app.services.grade_specific_assessment import GradeSpecificAssessmentGenerator

class CombinedAssessmentGenerator:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=os.getenv('GOOGLE_API_KEY')
        )
        self.grade_generator = GradeSpecificAssessmentGenerator()
    
    def create_assessment_questionnaire_std1_2(self, language: str = "Hindi", student_name: str = "", class_section: str = "") -> Optional[Dict]:
        """Creates a complete assessment questionnaire for Std 1-2"""
        try:
            questionnaire = {
                "assessment_info": {
                    "title": f"Standard 1-2 Assessment - {language}",
                    #"student_name": student_name,
                    "class_section": class_section,
                    "date": "",
                    #"teacher_name": "",
                    "total_sections": 4,
                    "instructions": f"This assessment contains multiple sections. Please complete all sections carefully. Use {language} for responses where indicated."
                },
                "sections": []
            }
            
            # Section 1: Word Recognition
            simple_words = self.grade_generator.generate_simple_words_std1_2(5, language)
            if simple_words:
                questionnaire["sections"].append({
                    "section_number": 1,
                    "section_title": "Word Recognition / शब्द पहचान",
                    "section_type": "word_recognition",
                    "instructions": f"Read the following words aloud / निम्नलिखित शब्दों को पढ़ें:",
                    "items": [{"word": word, "read_correctly": "", "pronunciation_score": ""} for word in simple_words],
                    "scoring": {
                        "max_score": len(simple_words) * 2,
                        "criteria": "2 points for correct reading and pronunciation, 1 point for correct reading only"
                    }
                })
            
            # Section 2: Initial Sound Recognition
            picture_sounds = self.grade_generator.generate_picture_suggestions_for_sounds_std1_2(4, language)
            if picture_sounds:
                questionnaire["sections"].append({
                    "section_number": 2,
                    "section_title": "Initial Sound Recognition / प्रारंभिक ध्वनि पहचान",
                    "section_type": "sound_recognition",
                    "instructions": "Identify the first sound of each object / प्रत्येक वस्तु की पहली आवाज़ पहचानें:",
                    "items": [
                        {
                            "object": item["object"],
                            "correct_sound": item["sound"],
                            "student_response": "",
                            "is_correct": ""
                        } for item in picture_sounds
                    ],
                    "scoring": {
                        "max_score": len(picture_sounds),
                        "criteria": "1 point for each correct initial sound identification"
                    }
                })
            
            # Section 3: Reading Comprehension
            story_data = self.grade_generator.generate_simple_story_and_questions_std1_2(1, language, "daily life")
            if story_data:
                questionnaire["sections"].append({
                    "section_number": 3,
                    "section_title": "Reading Comprehension / पढ़ने की समझ",
                    "section_type": "reading_comprehension",
                    "instructions": "Read the story and answer the questions / कहानी पढ़ें और प्रश्नों के उत्तर दें:",
                    "story": story_data["story"],
                    "questions": [
                        {
                            "question_number": i+1,
                            "question": q,
                            "student_answer": "",
                            "teacher_evaluation": "",
                            "score": ""
                        } for i, q in enumerate(story_data["questions"])
                    ],
                    "scoring": {
                        "max_score": len(story_data["questions"]) * 2,
                        "criteria": "2 points for complete answer, 1 point for partial answer"
                    }
                })
            
            # Section 4: Mathematics
            math_problems = self.grade_generator.generate_single_digit_word_problems_std1_2(3, language, "addition")
            if math_problems:
                questionnaire["sections"].append({
                    "section_number": 4,
                    "section_title": "Mathematics / गणित",
                    "section_type": "mathematics",
                    "instructions": "Solve the following word problems / निम्नलिखित शब्द समस्याओं को हल करें:",
                    "problems": [
                        {
                            "problem_number": i+1,
                            "problem_text": prob["problem"],
                            "correct_answer": prob["answer"],
                            "student_answer": "",
                            "working_shown": "",
                            "is_correct": "",
                            "score": ""
                        } for i, prob in enumerate(math_problems)
                    ],
                    "scoring": {
                        "max_score": len(math_problems) * 3,
                        "criteria": "3 points for correct answer with working, 2 points for correct answer only, 1 point for correct method"
                    }
                })
            
            # Overall scoring summary
            total_max_score = sum(section.get("scoring", {}).get("max_score", 0) for section in questionnaire["sections"])
            questionnaire["scoring_summary"] = {
                "total_max_score": total_max_score,
                "student_total_score": "",
                "percentage": "",
                "grade": "",
                "teacher_comments": "",
                "areas_of_strength": [],
                "areas_for_improvement": [],
                "recommendations": []
            }
            
            return questionnaire
            
        except Exception as e:
            print(f"Error creating Std 1-2 questionnaire: {e}")
            return None
    
    def create_assessment_questionnaire_std3_5(self, grade_level: int = 3, language: str = "Hindi", student_name: str = "", class_section: str = "") -> Optional[Dict]:
        """Creates a complete assessment questionnaire for Std 3-5"""
        try:
            questionnaire = {
                "assessment_info": {
                    "title": f"Standard {grade_level} Assessment - {language}",
                    "student_name": student_name,
                    "class_section": class_section,
                    "grade_level": grade_level,
                    "date": "",
                    "teacher_name": "",
                    "total_sections": 5,
                    "instructions": f"This assessment contains multiple sections testing different skills. Complete all sections carefully."
                },
                "sections": []
            }
            
            # Section 1: Reading Comprehension - Paragraph
            paragraph = self.grade_generator.generate_paragraph_for_reading_std3_5(grade_level, language)
            if paragraph:
                questionnaire["sections"].append({
                    "section_number": 1,
                    "section_title": "Reading Comprehension - Paragraph / पैराग्राफ पढ़ने की समझ",
                    "section_type": "paragraph_reading",
                    "instructions": "Read the paragraph carefully and be prepared to discuss it / पैराग्राफ को ध्यान से पढ़ें:",
                    "paragraph": paragraph,
                    "evaluation_criteria": {
                        "fluency": "",
                        "pronunciation": "",
                        "comprehension": "",
                        "expression": ""
                    },
                    "scoring": {
                        "max_score": 8,
                        "criteria": "2 points each for fluency, pronunciation, comprehension, and expression"
                    }
                })
            
            # Section 2: Story with Inference Questions
            story_data = self.grade_generator.generate_story_with_inference_questions_std3_5(grade_level, language)
            if story_data:
                questionnaire["sections"].append({
                    "section_number": 2,
                    "section_title": "Story Comprehension & Inference / कहानी की समझ और निष्कर्ष",
                    "section_type": "inference_comprehension",
                    "instructions": "Read the story and answer all questions thoughtfully / कहानी पढ़ें और सभी प्रश्नों के उत्तर सोचकर दें:",
                    "story": story_data["story"],
                    "questions": [
                        {
                            "question_number": i+1,
                            "question": q,
                            "question_type": ["Direct Recall", "Inference", "Main Idea/Moral"][i] if i < 3 else "Comprehension",
                            "expected_answer": story_data.get("expected_answers", [""] * len(story_data["questions"]))[i] if i < len(story_data.get("expected_answers", [])) else "",
                            "student_answer": "",
                            "teacher_evaluation": "",
                            "score": ""
                        } for i, q in enumerate(story_data["questions"])
                    ],
                    "scoring": {
                        "max_score": len(story_data["questions"]) * 3,
                        "criteria": "3 points for excellent answer, 2 points for good answer, 1 point for basic answer"
                    }
                })
            
            # Section 3: Two-Digit Mathematics
            two_digit_problems = self.grade_generator.generate_two_digit_math_problems_std3_5(2, "English", "addition_with_carry")
            if two_digit_problems:
                questionnaire["sections"].append({
                    "section_number": 3,
                    "section_title": "Two-Digit Mathematics / दो अंकों का गणित",
                    "section_type": "two_digit_math",
                    "instructions": "Solve the following problems showing your work / निम्नलिखित समस्याओं को हल करें और अपना काम दिखाएं:",
                    "problems": [
                        {
                            "problem_number": i+1,
                            "problem_text": prob["problem"],
                            "correct_answer": prob["answer"],
                            "student_answer": "",
                            "working_space": "",
                            "method_used": "",
                            "is_correct": "",
                            "score": ""
                        } for i, prob in enumerate(two_digit_problems)
                    ],
                    "scoring": {
                        "max_score": len(two_digit_problems) * 4,
                        "criteria": "4 points for correct answer with clear working, 3 points for correct answer, 2 points for correct method, 1 point for partial understanding"
                    }
                })
            
            # Section 4: Multiplication/Division
            mult_div_problems = self.grade_generator.generate_multiplication_division_problems_std3_5(2, "English", "multiplication")
            if mult_div_problems:
                questionnaire["sections"].append({
                    "section_number": 4,
                    "section_title": "Multiplication & Division / गुणा और भाग",
                    "section_type": "multiplication_division",
                    "instructions": "Solve these multiplication/division problems / इन गुणा/भाग की समस्याओं को हल करें:",
                    "problems": [
                        {
                            "problem_number": i+1,
                            "problem_text": prob["problem"],
                            "correct_answer": prob["answer"],
                            "student_answer": "",
                            "working_space": "",
                            "strategy_used": "",
                            "is_correct": "",
                            "score": ""
                        } for i, prob in enumerate(mult_div_problems)
                    ],
                    "scoring": {
                        "max_score": len(mult_div_problems) * 4,
                        "criteria": "4 points for correct answer with strategy, 3 points for correct answer, 2 points for correct approach, 1 point for effort"
                    }
                })
            
            # Section 5: English Language
            english_sentences = self.grade_generator.generate_simple_english_sentences_std3_5(3)
            if english_sentences:
                questionnaire["sections"].append({
                    "section_number": 5,
                    "section_title": "English Language / अंग्रेजी भाषा",
                    "section_type": "english_language",
                    "instructions": "Read the English sentences aloud and explain their meaning in Hindi / अंग्रेजी वाक्यों को जोर से पढ़ें और हिंदी में अर्थ बताएं:",
                    "sentences": [
                        {
                            "sentence_number": i+1,
                            "sentence": sent,
                            "reading_fluency": "",
                            "pronunciation": "",
                            "meaning_explanation": "",
                            "score": ""
                        } for i, sent in enumerate(english_sentences)
                    ],
                    "scoring": {
                        "max_score": len(english_sentences) * 3,
                        "criteria": "3 points for fluent reading with correct meaning, 2 points for good reading, 1 point for basic reading"
                    }
                })
            
            # Overall scoring summary
            total_max_score = sum(section.get("scoring", {}).get("max_score", 0) for section in questionnaire["sections"])
            questionnaire["scoring_summary"] = {
                "total_max_score": total_max_score,
                "student_total_score": "",
                "percentage": "",
                "grade": "",
                "performance_level": "",
                "teacher_comments": "",
                "subject_wise_performance": {
                    "language_arts": "",
                    "mathematics": "",
                    "english": ""
                },
                "areas_of_strength": [],
                "areas_for_improvement": [],
                "recommendations": [],
                "next_steps": []
            }
            
            return questionnaire
            
        except Exception as e:
            print(f"Error creating Std 3-5 questionnaire: {e}")
            return None