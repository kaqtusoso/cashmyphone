import telestoreLogo from "@/assets/telestore-logo.png";
import swappieLogo from "@/assets/swappie-logo.png";
import fixmyphoneLogo from "@/assets/fixmyphone-logo.png";
import renewedLogo from "@/assets/renewed-logo.png";
import happyphoneLogo from "@/assets/happyphone-logo.png";

const CompanyLogos = () => {
  const companies = [
    { name: "FixMyPhone", logo: fixmyphoneLogo },
    { name: "Swappie", logo: swappieLogo },
    { name: "Telestore", logo: telestoreLogo },
    { name: "HappyPhone", logo: happyphoneLogo },
  ];

  // Duplicera loggorna många gånger för 5-minuters sömlös loop
  const duplicatedCompanies = Array(20).fill(companies).flat();

  return (
    <section className="w-screen relative left-1/2 right-1/2 -ml-[50vw] -mr-[50vw] py-16 bg-muted/50 mt-12 overflow-hidden">
      {/* Inner container för att begränsa loggornas rörelse */}
      <div className="max-w-6xl mx-auto relative">
        {/* Marquee Container */}
        <div className="relative overflow-hidden w-full">
          {/* Gradient overlays för smooth fade-effekt på kanterna */}
          <div className="absolute left-0 top-0 bottom-0 w-48 bg-gradient-to-r from-muted/50 via-muted/30 to-transparent z-10 pointer-events-none" />
          <div className="absolute right-0 top-0 bottom-0 w-48 bg-gradient-to-l from-muted/50 via-muted/30 to-transparent z-10 pointer-events-none" />

          {/* Scrolling logos */}
          <div className="flex animate-marquee [animation-duration:30s] md:[animation-duration:60s]">
            {duplicatedCompanies.map((company, index) => (
              <div
                key={`${company.name}-${index}`}
                className="flex items-center justify-center flex-shrink-0 mx-8 transition-all duration-300"
              >
                <img
                  src={company.logo}
                  alt={`${company.name} logotyp`}
                  className="h-10 w-auto max-w-[120px] object-contain grayscale hover:grayscale-0 transition-all duration-300"
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default CompanyLogos;
