import os
import threading
import time
from typing import Dict, List

import colorama
import google.generativeai as genai
from colorama import Fore, Style
from dotenv import load_dotenv


class QuizAgent:
    def __init__(self):
        colorama.init()  # Initialize colorama for colored text

        # Load environment variables
        load_dotenv()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")

        # Configure Gemini API
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

        # Quiz settings
        self.difficulty_levels = ["beginner", "intermediate", "advanced"]
        self.time_limits = {"beginner": 30, "intermediate": 45, "advanced": 60}

        # Different prompts based on difficulty level
        self.quiz_prompts = {
            "beginner": """Generate {num_questions} multiple-choice questions about {topic} in Python at {level} level.
            Each question must strictly follow this format:
            
            Q1. [Conceptual Question text]
            A) [Option A]
            B) [Option B]
            C) [Option C]
            D) [Option D]
            Correct: [Correct option letter]
            Explanation: [Detailed explanation]
            
            Ensure exactly {num_questions} conceptual questions are generated with correct formatting. Do not include code snippets.
            """,
            "intermediate": """Generate {num_questions} multiple-choice questions about {topic} in Python at {level} level.
            Each question must strictly follow this format:
            
            Q1. [Question text]
            ```python
            [Code snippet]
            ```
            A) [Option A]
            B) [Option B]
            C) [Option C]
            D) [Option D]
            Correct: [Correct option letter]
            Explanation: [Detailed explanation]
            
            Ensure exactly {num_questions} questions are generated with correct formatting.
            """,
            "advanced": """Generate {num_questions} multiple-choice questions about {topic} in Python at {level} level.
            Each question must strictly follow this format:
            
            Q1. [Question text]
            ```python
            [Code snippet]
            ```
            A) [Option A]
            B) [Option B]
            C) [Option C]
            D) [Option D]
            Correct: [Correct option letter]
            Explanation: [Detailed explanation]
            
            Ensure exactly {num_questions} questions are generated with correct formatting.
            """
        }

    def generate_quiz(self, topic: str, level: str, num_questions: int) -> List[Dict]:
        """Generate quiz questions using Gemini API."""
        prompt = self.quiz_prompts[level].format(topic=topic, level=level, num_questions=num_questions)
        response = self.model.generate_content(prompt)

        if not response.text:
            raise Exception("Failed to generate quiz questions.")

        questions = []
        raw_questions = response.text.split("Q")[1:]  # Extract each question

        for q in raw_questions:
            try:
                lines = q.strip().split("\n")
                question_text = ""
                code_snippet = ""
                options = {}
                correct = ""
                explanation = ""

                # Step 1: Extract question text
                if ". " in lines[0]:
                    question_text = lines[0].split(". ", 1)[1].strip()
                else:
                    continue

                # Step 2: Extract code if present
                if level in ["intermediate", "advanced"]:
                    code_lines = []
                    in_code = False
                    options_start_index = 1

                    for idx, line in enumerate(lines[1:], start=1):
                        if line.strip().startswith("```python"):
                            in_code = True
                            continue
                        elif line.strip() == "```" and in_code:
                            in_code = False
                            options_start_index = idx + 1
                            break
                        elif in_code:
                            code_lines.append(line)

                    code_snippet = "\n".join(code_lines)
                else:
                    options_start_index = 1  # For beginner level (no code)

                # Step 3: Parse options, correct answer, and explanation
                try:
                    options = {
                        "A": lines[options_start_index].split("A) ")[1].strip(),
                        "B": lines[options_start_index + 1].split("B) ")[1].strip(),
                        "C": lines[options_start_index + 2].split("C) ")[1].strip(),
                        "D": lines[options_start_index + 3].split("D) ")[1].strip(),
                    }
                    correct = lines[options_start_index + 4].split("Correct: ")[1].strip().upper()
                    explanation = lines[options_start_index + 5].split("Explanation: ")[1].strip()
                except Exception as inner_e:
                    print(Fore.YELLOW + f"⚠️ Skipping poorly formatted question block: {inner_e}" + Style.RESET_ALL)
                    continue

                questions.append(
                    {
                        "question": question_text,
                        "code": code_snippet,
                        "options": options,
                        "correct": correct,
                        "explanation": explanation,
                    }
                )
            except Exception as e:
                print(Fore.RED + f"❌ Error parsing question: {e}" + Style.RESET_ALL)
                continue

        if len(questions) < num_questions:
            print(Fore.YELLOW + f"⚠️ Only {len(questions)} questions generated, retrying..." + Style.RESET_ALL)
            return self.generate_quiz(topic, level, num_questions)

        return questions

    def run_quiz(self, topic: str, level: str, num_questions: int):
        """Run an interactive quiz session with a countdown timer."""
        print(
            Fore.CYAN
            + f"\nGenerating a {level} level quiz on {topic}..."
            + Style.RESET_ALL
        )
        questions = self.generate_quiz(topic, level, num_questions)

        if not questions:
            print(Fore.RED + "Failed to generate quiz questions." + Style.RESET_ALL)
            return

        score = 0
        answers = []
        time_per_question = self.time_limits[level.lower()]

        for i, q in enumerate(questions, 1):
            print(Fore.GREEN + f"\nQuestion {i}/{num_questions}:" + Style.RESET_ALL)
            print(q["question"])

            if q["code"]:
                print(Fore.YELLOW + q["code"] + Style.RESET_ALL)

            for opt, text in q["options"].items():
                print(f"{opt}) {text}")

            answer = None
            timer_expired = [False]

            def countdown_timer():
                """Function to handle countdown timer."""
                for remaining in range(time_per_question, 0, -1):
                    if not timer_expired[0]:  
                        print(
                            Fore.YELLOW
                            + f"\rTime remaining: {remaining} seconds "
                            + Style.RESET_ALL,
                            end="",
                            flush=True,
                        )
                        time.sleep(1)
                if not timer_expired[0]:  
                    timer_expired[0] = True
                    print(
                        Fore.RED
                        + "\nTime's up! Moving to next question..."
                        + Style.RESET_ALL
                    )

            timer_thread = threading.Thread(target=countdown_timer)
            timer_thread.start()

            try:
                while not timer_expired[0]:
                    answer = (
                        input(f"\n{Fore.CYAN}Your answer (A/B/C/D):{Style.RESET_ALL} ")
                        .upper()
                        .strip()
                    )
                    if answer in ["A", "B", "C", "D"]:
                        timer_expired[0] = True  
                        break
                    else:
                        print(
                            Fore.RED
                            + "Invalid choice. Please enter A, B, C, or D."
                            + Style.RESET_ALL
                        )
            except KeyboardInterrupt:
                print("\nQuiz terminated by user.")
                return

            if not answer:
                answer = "TIMEOUT"

            answers.append({"question_num": i, "user_answer": answer, "correct_answer": q["correct"], "explanation": q["explanation"]})

            if answer == q["correct"]:
                score += 1

            timer_thread.join()  

        print(Fore.CYAN + "\n=== Quiz Results ===" + Style.RESET_ALL)
        print(f"Score: {score}/{num_questions}")
        
        print(Fore.CYAN + "\n=== Detailed Feedback ===" + Style.RESET_ALL)
        for ans in answers:
            print(f"\nQuestion {ans['question_num']}:")
            print(f"Your answer: {ans['user_answer']}")
            print(f"Correct answer: {ans['correct_answer']}")
            print(f"Explanation: {ans['explanation']}")

if __name__ == "__main__":
    quiz_agent = QuizAgent()
    topic = input("Enter Python topic for quiz: ")
    level = input("Enter difficulty level: ").lower()
    num_questions = int(input("Enter number of questions: "))
    quiz_agent.run_quiz(topic, level, num_questions)
