from langchain_google_genai import ChatGoogleGenerativeAI
import os
import json
import random
from typing import List, Dict, Optional

class GradeSpecificAssessmentGenerator:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=os.getenv('GOOGLE_API_KEY')
        )
    
    # ==================== STD 1-2 FUNCTIONS ====================
    
    def generate_simple_words_std1_2(self, num_words: int = 7, language: str = "Hindi") -> Optional[List[str]]:
        """Generates simple 2-3 letter words for Std 1-2 recognition."""
        prompt = f"""Generate a list of {num_words} very simple, common {language} words (2-3 letters).
        These words should be easy for a Standard 1-2 rural Indian child to recognize and read.
        Do NOT include any complex characters or conjuncts (e.g., श, त्र, ज्ञ). Focus on basic, everyday vocabulary.
        Present them as a comma-separated list without numbering or extra text.
        Example: जल, घर, फल, नल, बस, आम
        """
        try:
            response = self.model.invoke(prompt)
            words_str = response.content.strip()
            return [w.strip() for w in words_str.split(',') if w.strip()]
        except Exception as e:
            print(f"Error generating simple words: {e}")
            return None

    def generate_picture_suggestions_for_sounds_std1_2(self, num_pics: int = 5, language: str = "Hindi") -> Optional[List[Dict]]:
        """Generates picture suggestions for initial sound recognition for Std 1-2."""
        prompt = f"""Suggest {num_pics} common objects that a Standard 1-2 rural Indian child would recognize.
        These objects should have clear, distinct initial sounds in {language}.
        For each object, provide the {language} word and the initial sound.
        Format each item as "Object: [Object Name], Sound: [Initial Sound]". Use simple words only.

        Example:
        Object: आम, Sound: आ
        Object: बकरी, Sound: ब
        """
        try:
            response = self.model.invoke(prompt)
            suggestions = []
            for line in response.content.strip().split('\n'):
                if "Object:" in line and "Sound:" in line:
                    try:
                        obj_name = line.split("Object:")[1].split(",")[0].strip()
                        initial_sound = line.split("Sound:")[1].strip()
                        suggestions.append({"object": obj_name, "sound": initial_sound})
                    except IndexError:
                        pass
            return suggestions
        except Exception as e:
            print(f"Error generating picture suggestions: {e}")
            return None

    def generate_simple_story_and_questions_std1_2(self, grade_level: int = 1, language: str = "Hindi", topic: str = "animals") -> Optional[Dict]:
        """Generates a simple story and 2 direct comprehension questions for Std 1-2."""
        prompt = f"""Generate a very simple story in {language} for a Standard {grade_level} rural Indian child.
        The story should be about '{topic}', 3-4 sentences long, using basic, common vocabulary.
        Ensure the plot is straightforward and easy to follow.
        After the story, provide exactly 2 direct comprehension questions based on the story.

        Format:
        Story:
        [Your simple story text]

        Questions:
        1. [Question 1]
        2. [Question 2]
        """
        try:
            response = self.model.invoke(prompt)
            text = response.content.strip()
            parts = text.split("Questions:")
            story = parts[0].replace("Story:", "").strip()
            questions = [q.strip() for q in parts[1].split('\n') if q.strip()] if len(parts) > 1 else []
            return {"story": story, "questions": questions}
        except Exception as e:
            print(f"Error generating story and questions: {e}")
            return None

    def generate_single_digit_word_problems_std1_2(self, num_problems: int = 2, language: str = "Hindi", operation_type: str = "addition") -> Optional[List[Dict]]:
        """Generates simple single-digit word problems for Std 1-2."""
        prompts = {
            "addition": f"""Generate {num_problems} very simple single-digit addition word problems in {language} for a Standard 1-2 rural Indian child.
                       Use common objects or scenarios from village life (e.g., fruits, animals, children playing, flowers).
                       Include the numerical answer for each problem.
                       Format:
                       Problem: [Problem text]
                       Answer: [Numerical answer]

                       Problem: [Problem text]
                       Answer: [Numerical answer]
                    """,
            "subtraction": f"""Generate {num_problems} very simple single-digit subtraction word problems in {language} for a Standard 1-2 rural Indian child.
                            Use common objects or scenarios from village life.
                            Include the numerical answer for each problem.
                            Format:
                            Problem: [Problem text]
                            Answer: [Numerical answer]

                            Problem: [Problem text]
                            Answer: [Numerical answer]
                         """
        }

        prompt = prompts.get(operation_type, prompts["addition"])
        try:
            response = self.model.invoke(prompt)
            problems_text = response.content.strip().split('\n\n')
            problems = []
            for problem_block in problems_text:
                lines = problem_block.split('\n')
                if len(lines) >= 2 and lines[0].startswith("Problem:") and lines[1].startswith("Answer:"):
                    problem_text = lines[0].replace("Problem:", "").strip()
                    answer_text = lines[1].replace("Answer:", "").strip()
                    problems.append({"problem": problem_text, "answer": answer_text})
            return problems
        except Exception as e:
            print(f"Error generating word problems: {e}")
            return None

    # ==================== STD 3-5 FUNCTIONS ====================

    def generate_paragraph_for_reading_std3_5(self, grade_level: int = 3, language: str = "Hindi", topic: str = None) -> Optional[str]:
        """Generates a paragraph for reading comprehension for Std 3-5."""
        topics = ["गाँव का मेला", "मेरा स्कूल", "एक किसान की कहानी", "नदी के किनारे", "जंगल के जानवर", "एक नया दोस्त"]
        chosen_topic = topic if topic else random.choice(topics)

        prompt = f"""Generate a simple paragraph in {language} for a Standard {grade_level} child.
        The paragraph should be about "{chosen_topic}", 5-7 sentences long, with slightly more complex vocabulary than Standard 1-2, but still easy to understand for a rural Indian child.
        Avoid very long sentences or highly abstract concepts.
        The paragraph should be coherent and flow naturally.
        """
        try:
            response = self.model.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"Error generating paragraph: {e}")
            return None

    def generate_story_with_inference_questions_std3_5(self, grade_level: int = 3, language: str = "Hindi", complexity: str = "medium") -> Optional[Dict]:
        """Generates a story with inference questions for Std 3-5."""
        prompt = f"""Generate a short story in {language} suitable for a Standard {grade_level} child.
        The story should be 6-8 sentences long, feature relatable characters or scenarios, and have a clear plot.
        Use vocabulary slightly more advanced than basic, but still within a {grade_level} child's grasp in rural India.

        After the story, provide exactly 3 comprehension questions.
        1. A direct recall question.
        2. A question requiring simple inference (e.g., character's feeling, reason for an action).
        3. A question about a moral or a main idea.

        Format:
        Story:
        [Your short story text]

        Questions:
        1. [Direct recall question]
        2. [Inference question]
        3. [Moral/Main idea question]
        """
        try:
            response = self.model.invoke(prompt)
            text = response.content.strip()
            parts = text.split("Questions:")
            story = parts[0].replace("Story:", "").strip()
            questions = [q.strip() for q in parts[1].split('\n') if q.strip()] if len(parts) > 1 else []
            
            # Generate expected answers
            expected_answers = []
            for i, question in enumerate(questions[:3]):
                if i == 0:  # Direct recall
                    answer_prompt = f"Given this story: '{story}' and question '{question}', what is a likely direct answer? Provide only the answer in {language}."
                elif i == 1:  # Inference
                    answer_prompt = f"Given this story: '{story}' and question '{question}', what is a likely answer that requires simple inference? Provide only the answer in {language}."
                else:  # Moral/main idea
                    answer_prompt = f"Given this story: '{story}' and question '{question}', what is a likely answer for the moral or main idea? Provide only the answer in {language}."
                
                try:
                    temp_response = self.model.invoke(answer_prompt)
                    expected_answers.append(temp_response.content.strip())
                except:
                    expected_answers.append("Answer not generated")

            return {"story": story, "questions": questions, "expected_answers": expected_answers}
        except Exception as e:
            print(f"Error generating story and questions: {e}")
            return None

    def generate_two_digit_math_problems_std3_5(self, num_problems: int = 3, language: str = "English", operation_type: str = "addition_with_carry") -> Optional[List[Dict]]:
        """Generates 2-digit math problems for Std 3-5."""
        prompts = {
            "addition_with_carry": f"""Generate {num_problems} two-digit addition problems in {language} for a Standard 3-5 child.
                                     Each problem MUST involve carrying over.
                                     Format each problem as 'Problem: [num1] + [num2], Answer: [result]'.
                                     Example: Problem: 37 + 45, Answer: 82
                                  """,
            "subtraction_with_borrow": f"""Generate {num_problems} two-digit subtraction problems in {language} for a Standard 3-5 child.
                                      Each problem MUST involve borrowing. Ensure the first number is larger than the second.
                                      Format each problem as 'Problem: [num1] - [num2], Answer: [result]'.
                                      Example: Problem: 72 - 38, Answer: 34
                                   """
        }
        
        prompt = prompts.get(operation_type)
        if not prompt:
            return None

        try:
            response = self.model.invoke(prompt)
            problems_text = response.content.strip().split('\n')
            problems = []
            for line in problems_text:
                if "Problem:" in line and "Answer:" in line:
                    try:
                        parts = line.split("Problem:")[1].split(", Answer:")
                        problem_str = parts[0].strip()
                        answer_str = parts[1].strip()
                        problems.append({"problem": problem_str, "answer": answer_str})
                    except IndexError:
                        pass
            return problems
        except Exception as e:
            print(f"Error generating 2-digit math problems: {e}")
            return None

    def generate_multiplication_division_problems_std3_5(self, num_problems: int = 2, language: str = "English", operation_type: str = "multiplication") -> Optional[List[Dict]]:
        """Generates multiplication/division problems for Std 3-5."""
        prompts = {
            "multiplication": f"""Generate {num_problems} simple multiplication problems (e.g., single-digit by two-digit, or two-digit by single-digit) in {language} for a Standard 3-5 child.
                              Format each problem as 'Problem: [num1] x [num2], Answer: [result]'.
                              Example: Problem: 15 x 3, Answer: 45
                           """,
            "division": f"""Generate {num_problems} simple division problems (e.g., two-digit by single-digit, with or without remainder) in {language} for a Standard 3-5 child.
                        Format each problem as 'Problem: [num1] ÷ [num2], Answer: [result with/without remainder]'.
                        Example: Problem: 48 ÷ 4, Answer: 12
                        Example: Problem: 50 ÷ 7, Answer: 7 शेष 1 (7 Remainder 1)
                      """
        }
        
        prompt = prompts.get(operation_type)
        if not prompt:
            return None

        try:
            response = self.model.invoke(prompt)
            problems_text = response.content.strip().split('\n')
            problems = []
            for line in problems_text:
                if "Problem:" in line and "Answer:" in line:
                    try:
                        parts = line.split("Problem:")[1].split(", Answer:")
                        problem_str = parts[0].strip()
                        answer_str = parts[1].strip()
                        problems.append({"problem": problem_str, "answer": answer_str})
                    except IndexError:
                        pass
            return problems
        except Exception as e:
            print(f"Error generating multiplication/division problems: {e}")
            return None

    def generate_simple_english_sentences_std3_5(self, num_sentences: int = 3) -> Optional[List[str]]:
        """Generates simple English sentences for Std 3-5."""
        prompt = f"""Generate {num_sentences} very simple English sentences for a Standard 3-5 rural Indian child.
        These sentences should use common words and simple grammar, similar to what a child at this level might learn.
        Each sentence should be on a new line.
        Example:
        This is a big house.
        The cat runs fast.
        She has a red ball.
        """
        try:
            response = self.model.invoke(prompt)
            return [s.strip() for s in response.content.strip().split('\n') if s.strip()]
        except Exception as e:
            print(f"Error generating English sentences: {e}")
            return None