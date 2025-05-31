document.getElementById("next-btn").addEventListener("click", () => {
  // You can implement quiz navigation and question loading logic here
  console.log("Next button clicked!");
});

// Example for timer countdown
let timer = 45;
const timerElement = document.getElementById("timer");

const countdown = setInterval(() => {
  if (timer > 0) {
    timer--;
    timerElement.innerText = timer;
  } else {
    clearInterval(countdown);
    alert("Time's up!");
  }
}, 1000);
let timer = 45;
const timerElement = document.getElementById("timer");
const progressRing = document.getElementById("progress-ring");
const totalTime = 45;

const updateProgressRing = (timeLeft) => {
  const radius = 22;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (timeLeft / totalTime) * circumference;
  progressRing.style.strokeDashoffset = offset;
};

const countdown = setInterval(() => {
  if (timer > 0) {
    timer--;
    timerElement.innerText = timer;
    updateProgressRing(timer);
  } else {
    clearInterval(countdown);
    alert("Time's up!");
  }
}, 1000);

// Initial ring update
updateProgressRing(timer);
