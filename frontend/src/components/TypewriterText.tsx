import { useState, useEffect } from "react";

interface TypewriterTextProps {
  words: string[];
  className?: string;
}

const TypewriterText = ({ words, className = "" }: TypewriterTextProps) => {
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [currentText, setCurrentText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [cursorVisible, setCursorVisible] = useState(true);

  // Blinkande cursor
  useEffect(() => {
    const interval = setInterval(() => {
      setCursorVisible((prev) => !prev);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const currentWord = words[currentWordIndex];

    const typingSpeed = isDeleting ? 55 : 90;
    const pauseAfterTyped = 3000; // 3 sek
    const pauseAfterDelete = 450;

    if (!isDeleting && currentText === currentWord) {
      const timeout = setTimeout(() => setIsDeleting(true), pauseAfterTyped);
      return () => clearTimeout(timeout);
    }

    if (isDeleting && currentText === "") {
      const timeout = setTimeout(() => {
        setIsDeleting(false);
        setCurrentWordIndex((prev) => (prev + 1) % words.length);
      }, pauseAfterDelete);
      return () => clearTimeout(timeout);
    }

    const timeout = setTimeout(() => {
      setCurrentText((prev) => (isDeleting ? prev.slice(0, -1) : currentWord.slice(0, prev.length + 1)));
    }, typingSpeed);

    return () => clearTimeout(timeout);
  }, [currentText, isDeleting, currentWordIndex, words]);

  return (
    <span className={`${className} font-bold italic`} style={{ position: "relative" }}>
      {/* Underline ONLY the typed word */}
      <span
        className="underline"
        style={{
          textUnderlineOffset: "4px",
          textDecorationColor: "#00B87A", // GRÖN UNDERLINE
          textDecorationThickness: "2px",
        }}
      >
        {currentText}
      </span>

      {/* Cursor – no underline, absolute positioned */}
      <span
        style={{
          position: "absolute",
          left: "100%",
          opacity: cursorVisible ? 1 : 0,
          color: "#00B87A",
          fontWeight: "bold",
          textDecoration: "none",
          transform: "translateX(-6px)", // 👈 NYCKELN
        }}
        className="sm:translate-x-[-2px]"
      >
        │
      </span>
    </span>
  );
};

export default TypewriterText;
