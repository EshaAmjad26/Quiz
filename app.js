async function fetchQuiz() {
  const response = await fetch("http://127.0.0.1:8000/get-quiz");
  const data = await response.json();
  displayQuiz(data.quiz);
}

document.getElementById("generate-btn").addEventListener("click", function () {
  // Get selected topic
  const topicSelect = document.getElementById("topic");
  const topic = topicSelect.options[topicSelect.selectedIndex].text;

  // Get selected number of questions (only the number part)
  const numQuestionsSelect = document.getElementById("num-questions");
  const questionText =
    numQuestionsSelect.options[numQuestionsSelect.selectedIndex].text;
  const question_number = parseInt(questionText); // Extract number from "10 Questions"

  // Get selected difficulty level
  const levelBtns = document.querySelectorAll(".difficulty-btn");
  let level = "";
  levelBtns.forEach((btn) => {
    if (btn.classList.contains("selected")) {
      level = btn.getAttribute("data-level");
    }
  });

  // Show values in console (or use them in your logic)
  console.log("Topic:", topic);
  console.log("Number of Questions:", question_number);
  console.log("Difficulty Level:", level);

  // You can now use these variables for your quiz generation logic
});
document.getElementById("generate-btn").addEventListener("click", () => {
  const topic = document.getElementById("topic").value;
  const question_number = document.getElementById("num-questions").value;
  const level = document.getElementById("level").value;

  fetch("http://localhost:8000/generate-quiz", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      topic: topic,
      question_number: question_number,
      level: level,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Quiz data:", data);
      // You can display the quiz on the page here
    })
    .catch((error) => {
      console.error("Error generating quiz:", error);
    });
});

// Optional: Highlight selected difficulty button
const difficultyButtons = document.querySelectorAll(".difficulty-btn");
difficultyButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    difficultyButtons.forEach((b) => b.classList.remove("selected"));
    btn.classList.add("selected");
  });
});
