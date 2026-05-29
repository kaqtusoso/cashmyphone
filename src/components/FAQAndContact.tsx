import FAQ from "./FAQ";
import ContactForm from "./ContactForm";

const FAQAndContact = () => {
  return (
    <section id="faq-contact" className="py-20 px-4 bg-[#F1F8F4] scroll-mt-20">
      <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-12 items-start">
        <div>
          <ContactForm />
        </div>
        <div className="md:sticky md:top-24">
          <FAQ />
        </div>
      </div>
    </section>
  );
};

export default FAQAndContact;
