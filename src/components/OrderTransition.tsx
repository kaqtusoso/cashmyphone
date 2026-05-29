import { useEffect, useState } from "react";

interface Props {
  status: "loading" | "success";
  onComplete: () => void;
  model?: string;
  dealer?: string;
}

const OrderTransitionFadeLoader = ({ status, onComplete }: Props) => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (status === "success") {
      const t = setTimeout(() => {
        setVisible(false);
        onComplete();
      }, 700);
      return () => clearTimeout(t);
    }
  }, [status, onComplete]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/70 backdrop-blur-sm animate-fade-in">
      {/* ORBIT LOADER */}
      <div className="relative w-24 h-24">
        <div className="orbit-dot"></div>
      </div>

      <style>{`
        /* Orbit Animation */
        @keyframes orbit {
          0% {
            transform: rotate(0deg) translateX(38px) rotate(0deg);
          }
          100% {
            transform: rotate(360deg) translateX(38px) rotate(-360deg);
          }
        }

        .orbit-dot {
          position: absolute;
          top: 50%;
          left: 50%;
          width: 14px;
          height: 14px;
          background-color: #00B87A;
          border-radius: 50%;
          transform: translate(-50%, -50%);
          animation: orbit 1.4s linear infinite;
        }

        /* Fade-in for overlay */
        @keyframes fadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        .animate-fade-in {
          animation: fadeIn 0.25s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default OrderTransitionFadeLoader;
