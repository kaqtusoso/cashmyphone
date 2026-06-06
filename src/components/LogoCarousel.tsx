import swappie from "@/assets/swappie-logo.png";
import phonehero from "@/assets/phonehero-logo.svg";
import fixmyphone from "@/assets/fixmyphone-logo.png";
import happyphone from "@/assets/happyphone-logo.png";
import telestore from "@/assets/telestore-logo.png";
import renewed from "@/assets/renewed-logo.png";
import fixiphone from "@/assets/fixiphone-logo.png";
import fixphonepro from "@/assets/fixphonepro-logo.png";

const logos = [
  { src: swappie, alt: "Swappie" },
  { src: phonehero, alt: "PhoneHero" },
  { src: fixmyphone, alt: "FixMyPhone" },
  { src: happyphone, alt: "HappyPhone" },
  { src: telestore, alt: "Telestore" },
  { src: renewed, alt: "Renewed" },
  { src: fixiphone, alt: "Fixiphone" },
  { src: fixphonepro, alt: "FixPhonePro" },
];

const repeatedLogos = Array.from({ length: 3 }, () => logos).flat();

const Track = ({ ariaHidden = false }: { ariaHidden?: boolean }) => (
  <ul
    aria-hidden={ariaHidden}
    className="flex shrink-0 items-center gap-12 pr-12"
  >
    {repeatedLogos.map((logo, index) => (
      <li
        key={`${logo.alt}-${index}`}
        className="flex shrink-0 items-center justify-center h-12 w-20 grayscale opacity-60 hover:grayscale-0 hover:opacity-100 transition-all duration-300"
      >
        <img
          src={logo.src}
          alt={logo.alt}
          width={80}
          height={48}
          loading="eager"
          decoding="sync"
          className="max-h-full w-full object-contain mix-blend-multiply dark:mix-blend-normal dark:brightness-0 dark:invert"
        />
      </li>
    ))}
  </ul>
);

const LogoCarousel = () => {
  return (
    <div className="w-full bg-muted py-8 overflow-hidden">
      <div className="flex w-max animate-scroll-logos will-change-transform">
        <Track />
        <Track ariaHidden />
      </div>
    </div>
  );
};

export default LogoCarousel;
