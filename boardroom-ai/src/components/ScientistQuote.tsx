import { useEffect, useState } from "react";

const QUOTES = [
  {
    text: "Dream, dream, dream. Dreams transform into thoughts and thoughts result in action.",
    author: "Dr A. P. J. Abdul Kalam",
  },
  {
    text: "We must be second to none in the application of advanced technologies to the real problems of man and society.",
    author: "Dr Vikram Sarabhai",
  },
  {
    text: "The essence of science is independent thinking, hard work, and not equipment.",
    author: "Sir C. V. Raman",
  },
] as const;

export function ScientistQuote({ className = "" }: { className?: string }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const previous = Number(sessionStorage.getItem("boardroom.quoteIndex") ?? "-1");
    const next = Number.isFinite(previous) ? (previous + 1) % QUOTES.length : 0;
    sessionStorage.setItem("boardroom.quoteIndex", String(next));
    setIndex(next);
  }, []);

  const quote = QUOTES[index] ?? QUOTES[0];
  return (
    <figure className={className}>
      <blockquote>“{quote.text}”</blockquote>
      <figcaption className="mt-3 text-[13px] font-medium uppercase tracking-[0.12em] opacity-75">
        — {quote.author}
      </figcaption>
    </figure>
  );
}