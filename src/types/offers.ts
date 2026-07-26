export interface CompanyOffer {
  företag: string;
  modell: string;
  lagring: string;
  skick: string;
  pris: number;
  prisMax?: number;
  uppskattatIntervall?: boolean;
  url: string;
  leverans: string;
  utbetalningstid: string;
  uppdaterad: string;
  notPurchased?: boolean;
  trustpilotScore?: string;
  trustpilotReviews?: string;
  trustpilotUrl?: string;
  paymentMethods?: string[];
}
