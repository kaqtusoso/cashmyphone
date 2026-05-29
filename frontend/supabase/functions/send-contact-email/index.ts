import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { Resend } from "https://esm.sh/resend@2.0.0";

const resend = new Resend(Deno.env.get("RESEND_API_KEY"));
const contactEmail = Deno.env.get("CONTACT_EMAIL");

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

interface ContactEmailRequest {
  message: string;
  email: string;
}

// Simple in-memory rate limiting (resets on cold start)
const rateLimitMap = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT_MAX = 5;
const RATE_LIMIT_WINDOW_MS = 3600000; // 1 hour

const checkRateLimit = (ip: string): boolean => {
  const now = Date.now();
  const entry = rateLimitMap.get(ip);
  
  if (!entry || now > entry.resetTime) {
    rateLimitMap.set(ip, { count: 1, resetTime: now + RATE_LIMIT_WINDOW_MS });
    return true;
  }
  
  if (entry.count >= RATE_LIMIT_MAX) {
    return false;
  }
  
  entry.count++;
  return true;
};

const handler = async (req: Request): Promise<Response> => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Rate limiting
    const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || 
               req.headers.get("x-real-ip") || 
               "unknown";
    
    if (!checkRateLimit(ip)) {
      console.log(`Rate limit exceeded for IP: ${ip.substring(0, 10)}...`);
      return new Response(
        JSON.stringify({ error: "Rate limit exceeded. Please try again later." }),
        {
          status: 429,
          headers: { 
            "Content-Type": "application/json", 
            "Retry-After": "3600",
            ...corsHeaders 
          },
        }
      );
    }

    const { message, email }: ContactEmailRequest = await req.json();

    console.log("Received contact form submission:", { messageLength: message?.length || 0 });

    if (!message || !email) {
      return new Response(
        JSON.stringify({ error: "Message and email are required" }),
        {
          status: 400,
          headers: { "Content-Type": "application/json", ...corsHeaders },
        }
      );
    }

    // Validate email format server-side
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return new Response(
        JSON.stringify({ error: "Invalid email format" }),
        {
          status: 400,
          headers: { "Content-Type": "application/json", ...corsHeaders },
        }
      );
    }

    // Limit message length
    if (message.length > 5000) {
      return new Response(
        JSON.stringify({ error: "Message too long (max 5000 characters)" }),
        {
          status: 400,
          headers: { "Content-Type": "application/json", ...corsHeaders },
        }
      );
    }

    // HTML escape function to prevent XSS
    const escapeHtml = (unsafe: string): string => {
      return unsafe
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    };

    const safeEmail = escapeHtml(email);
    const safeMessage = escapeHtml(message);

    const emailResponse = await resend.emails.send({
      from: "CashMyPhone <onboarding@resend.dev>",
      to: [contactEmail || "brjanssonp@gmail.com"],
      subject: `Nytt meddelande från CashMyPhone - ${safeEmail}`,
      html: `
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #16a34a; margin-bottom: 20px;">Nytt meddelande från kontaktformuläret</h2>
          
          <div style="background-color: #f5fff7; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
            <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">Avsändarens e-post:</p>
            <p style="margin: 0; font-size: 16px;"><a href="mailto:${safeEmail}" style="color: #16a34a;">${safeEmail}</a></p>
          </div>
          
          <div style="background-color: #f5fff7; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
            <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">Meddelande:</p>
            <p style="margin: 0; font-size: 16px; white-space: pre-wrap;">${safeMessage}</p>
          </div>
          
          <p style="color: #999; font-size: 12px; margin-top: 30px;">
            Skickat: ${new Date().toLocaleString("sv-SE", { timeZone: "Europe/Stockholm" })}
          </p>
        </div>
      `,
    });

    console.log("Email sent successfully:", emailResponse);

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  } catch (error: unknown) {
    console.error("Error in send-contact-email function:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return new Response(
      JSON.stringify({ error: message }),
      {
        status: 500,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      }
    );
  }
};

serve(handler);
