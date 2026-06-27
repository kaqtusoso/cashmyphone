export type PaymentMethod = "swish" | "bank" | "paypal";

export interface CommerceCheckoutForm {
  swishNumber: string;
  clearingNumber: string;
  accountNumber: string;
  paypalEmail: string;
  firstName: string;
  lastName: string;
  personalNumber: string;
  email: string;
  phone: string;
  address: string;
  postalCode: string;
  city: string;
}

export type CheckoutField = keyof CommerceCheckoutForm;
export type CheckoutErrors = Partial<Record<CheckoutField, string>>;

export const emptyCheckoutForm: CommerceCheckoutForm = {
  swishNumber: "",
  clearingNumber: "",
  accountNumber: "",
  paypalEmail: "",
  firstName: "",
  lastName: "",
  personalNumber: "",
  email: "",
  phone: "",
  address: "",
  postalCode: "",
  city: "",
};

const digits = (value: string) => value.replace(/\D/g, "");
const isBlank = (value: string) => value.trim().length === 0;

export const validatePaymentDetails = (payment: PaymentMethod | null, form: CommerceCheckoutForm): CheckoutErrors => {
  const errors: CheckoutErrors = {};

  if (payment === "swish" && digits(form.swishNumber).length < 10) {
    errors.swishNumber = "Ange ett giltigt Swish-nummer.";
  }

  if (payment === "bank") {
    if (digits(form.clearingNumber).length < 4) errors.clearingNumber = "Ange clearingnummer.";
    if (digits(form.accountNumber).length < 5) errors.accountNumber = "Ange kontonummer.";
  }

  if (payment === "paypal" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.paypalEmail.trim())) {
    errors.paypalEmail = "Ange e-postadressen till ditt PayPal-konto.";
  }

  return errors;
};

export const validateCustomerDetails = (form: CommerceCheckoutForm, requirePersonalNumber = true): CheckoutErrors => {
  const errors: CheckoutErrors = {};

  if (isBlank(form.firstName)) errors.firstName = "Förnamn krävs.";
  if (isBlank(form.lastName)) errors.lastName = "Efternamn krävs.";
  if (requirePersonalNumber && !/^\d{8}-?\d{4}$/.test(form.personalNumber.trim())) {
    errors.personalNumber = "Ange personnummer som ÅÅÅÅMMDD-XXXX.";
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
    errors.email = "Ange en giltig e-postadress.";
  }
  if (digits(form.phone).length < 10) errors.phone = "Ange ett giltigt telefonnummer.";
  if (isBlank(form.address)) errors.address = "Gatuadress krävs.";
  if (digits(form.postalCode).length < 5) errors.postalCode = "Ange postnummer.";
  if (isBlank(form.city)) errors.city = "Ort krävs.";

  return errors;
};

export const hasErrors = (errors: CheckoutErrors) => Object.keys(errors).length > 0;

export const formatPhone = (value: string) => {
  const valueDigits = digits(value).slice(0, 10);
  if (valueDigits.length <= 3) return valueDigits;
  if (valueDigits.length <= 6) return `${valueDigits.slice(0, 3)}-${valueDigits.slice(3)}`;
  if (valueDigits.length <= 8) return `${valueDigits.slice(0, 3)}-${valueDigits.slice(3, 6)} ${valueDigits.slice(6)}`;
  return `${valueDigits.slice(0, 3)}-${valueDigits.slice(3, 6)} ${valueDigits.slice(6, 8)} ${valueDigits.slice(8)}`;
};

export const formatPersonalNumber = (value: string) => {
  const valueDigits = digits(value).slice(0, 12);
  if (valueDigits.length <= 8) return valueDigits;
  return `${valueDigits.slice(0, 8)}-${valueDigits.slice(8)}`;
};
