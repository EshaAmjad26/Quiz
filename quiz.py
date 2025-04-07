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
        colorama.init()  # Initialize colorama for colors

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

        # Improved prompt for better response format
        self.quiz_prompt = """Generate {num_questions} multiple-choice questions about {topic} in Python at {level} level.
        Each question must follow this format:
        
        Q1. [Question text]
        A) [Option A]
        B) [Option B]
        C) [Option C]
        D) [Option D]
        Correct: [Correct option letter]
        Explanation: [Explanation of the correct answer]
        
        Do not include extra text. Only format the response strictly as mentioned.
        """

    def generate_quiz(self, topic: str, level: str, num_questions: int) -> List[Dict]:
        """Generate quiz questions using Gemini API."""
        prompt = self.quiz_prompt.format(
            topic=topic, level=level, num_questions=num_questions
        )
        response = self.model.generate_content(prompt)

        if not response.text:
            raise Exception("Failed to generate quiz questions.")

        questions = []
        raw_questions = response.text.split("Q")[
            1:
        ]  # Split by 'Q' to extract each question

        for q in raw_questions:
            try:
                parts = q.strip().split("\n")
                if len(parts) < 7:
                    print(
                        Fore.YELLOW
                        + f"⚠️ Skipping poorly formatted question: {q}"
                        + Style.RESET_ALL
                    )
                    continue

                question_text = parts[0].split(". ")[1].strip()
                options = {
                    "A": parts[1].split("A) ")[1].strip(),
                    "B": parts[2].split("B) ")[1].strip(),
                    "C": parts[3].split("C) ")[1].strip(),
                    "D": parts[4].split("D) ")[1].strip(),
                }
                correct = parts[5].split("Correct: ")[1].strip().upper()
                explanation = parts[6].split("Explanation: ")[1].strip()

                questions.append(
                    {
                        "question": question_text,
                        "options": options,
                        "correct": correct,
                        "explanation": explanation,
                    }
                )
            except Exception as e:
                print(Fore.RED + f"❌ Error parsing question: {e}" + Style.RESET_ALL)
                continue  # Skip the faulty question

        return questions

    def run_quiz(self, topic: str, level: str, num_questions: int):
        """Run an interactive quiz session with countdown timer."""
        if level.lower() not in self.difficulty_levels:
            print(
                Fore.RED
                + f"Invalid difficulty. Choose from: {', '.join(self.difficulty_levels)}"
                + Style.RESET_ALL
            )
            return

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

            for opt, text in q["options"].items():
                print(f"{opt}) {text}")

            # Timer setup
            answer = None
            timer_expired = [False]  # Use a list to modify inside thread

            def countdown_timer():
                """Function to handle countdown timer."""
                for remaining in range(time_per_question, 0, -1):
                    if not timer_expired[0]:  # Stop if user answers early
                        print(
                            Fore.YELLOW
                            + f"\rTime remaining: {remaining} seconds "
                            + Style.RESET_ALL,
                            end="",
                            flush=True,
                        )
                        time.sleep(1)
                if not timer_expired[0]:  # If still running, time expired
                    timer_expired[0] = True
                    print(
                        Fore.RED
                        + "\nTime's up! Moving to next question..."
                        + Style.RESET_ALL
                    )

            # Start countdown in a separate thread
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
                        timer_expired[0] = True  # Stop the timer
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

            if not answer:  # If user didn't answer
                answer = "TIMEOUT"

            answers.append(
                {
                    "question_num": i,
                    "user_answer": answer,
                    "correct_answer": q["correct"],
                    "explanation": q["explanation"],
                }
            )

            if answer == q["correct"]:
                score += 1

            # Ensure timer thread stops before moving to next question
            timer_thread.join()

        # Display results
        print(Fore.CYAN + "\n=== Quiz Results ===" + Style.RESET_ALL)
        print(f"Score: {score}/{num_questions}")

        # Show detailed feedback
        print(Fore.CYAN + "\n=== Detailed Feedback ===" + Style.RESET_ALL)
        for ans in answers:
            q_num = ans["question_num"]
            print(f"\nQuestion {q_num}:")
            if ans["user_answer"] == "TIMEOUT":
                print(Fore.RED + "Time expired!" + Style.RESET_ALL)
            else:
                print(f"Your answer: {ans['user_answer']}")
            print(f"Correct answer: {ans['correct_answer']}")
            print(f"Explanation: {ans['explanation']}")

        # Performance feedback
        percentage = (score / num_questions) * 100
        print(Fore.CYAN + "\n=== Performance Analysis ===" + Style.RESET_ALL)
        if percentage >= 90:
            print(
                Fore.GREEN
                + f"Excellent! You have a strong grasp of {topic}!"
                + Style.RESET_ALL
            )
        elif percentage >= 70:
            print(Fore.GREEN + "Good job! Keep improving!" + Style.RESET_ALL)
        elif percentage >= 50:
            print(
                Fore.YELLOW
                + f"You're on the right track, but need more practice in {topic}."
                + Style.RESET_ALL
            )
        else:
            print(
                Fore.RED
                + f"You might want to review {topic} concepts and try again."
                + Style.RESET_ALL
            )


# Run quiz
if __name__ == "__main__":
    quiz_agent = QuizAgent()
    print(Fore.CYAN + "=== Python Quiz Generator ===" + Style.RESET_ALL)

    level = input(Fore.CYAN + "Enter difficulty level: " + Style.RESET_ALL).lower()
    topic = input(Fore.CYAN + "Enter Python topic for quiz: " + Style.RESET_ALL)
    num_questions = int(
        input(Fore.CYAN + "Enter number of questions: " + Style.RESET_ALL)
    )

    quiz_agent.run_quiz(topic, level, num_questions)
