const { DATABASE_URL, APP_NAME = "demo" } = process.env;

export function config() {
  return {
    database: DATABASE_URL,
    name: APP_NAME,
    stripeKey: process.env.STRIPE_SECRET_KEY,
    debug: process.env.NODE_ENV !== "production",
  };
}
