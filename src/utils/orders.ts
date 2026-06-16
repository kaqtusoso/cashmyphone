import { API_URL } from "@/utils/apiClient";

export interface OrderCustomer {
  first_name: string;
  last_name: string;
  personal_number: string;
  address: string;
  postal_code: string;
  city: string;
  phone: string;
  email: string;
}

export interface OrderPayment {
  method: string;
  label: string;
  clearing_number?: string;
  account_number?: string;
  iban_number?: string;
  swish_number?: string;
  paypal_email?: string;
}

export interface OrderCreatePayload {
  client_order_id?: string;
  model: string;
  storage: string;
  dealer_id: string;
  dealer_name: string;
  price_sek: number;
  bid_difference_sek?: number;
  shipping_option: string;
  shipping_label: string;
  customer: OrderCustomer;
  payment: OrderPayment;
  condition_answers?: Record<string, unknown>;
  source: "televera_web";
}

export interface IntegrationStatus {
  configured: boolean;
  ok: boolean;
  message: string;
}

export interface Order extends OrderCreatePayload {
  order_id: string;
  created_at: string;
}

export interface OrderCreateResponse {
  order: Order;
  integrations: Record<"google_sheets" | "email", IntegrationStatus>;
}

const makeOrderId = () => {
  const random = Array.from(crypto.getRandomValues(new Uint8Array(5)))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("")
    .toUpperCase();
  return `TLV-${random}`;
};

export const makeOptimisticOrder = (payload: OrderCreatePayload): Order => {
  const orderId = payload.client_order_id ?? makeOrderId();
  return {
    ...payload,
    client_order_id: orderId,
    order_id: orderId,
    created_at: new Date().toISOString(),
  };
};

export const pendingOrderIntegrations = (): Record<"google_sheets" | "email", IntegrationStatus> => ({
  google_sheets: {
    configured: true,
    ok: true,
    message: "Ordern skickas till Google Sheets i bakgrunden.",
  },
  email: {
    configured: true,
    ok: true,
    message: "Bekräftelsemail skickas i bakgrunden.",
  },
});

export const submitOrder = async (payload: OrderCreatePayload): Promise<OrderCreateResponse> => {
  const response = await fetch(`${API_URL}/api/orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Ordern kunde inte registreras (${response.status})`);
  }

  return response.json();
};

export const formatOrderPrice = (priceSek: number) => `${priceSek.toLocaleString("sv-SE")} kr`;
