import React from "react";
import { createRoot } from "react-dom/client";
import { HelmetProvider } from "react-helmet-async";
import "@/index.css";
import App from "@/App";

const rootElement = document.getElementById("root");
const app = (
  <React.StrictMode>
    <HelmetProvider>
      <App />
    </HelmetProvider>
  </React.StrictMode>
);

// Always use createRoot for reliable rendering.
// Pre-rendered HTML in build/ provides SEO content for crawlers.
// React takes over the DOM on client-side load.
createRoot(rootElement).render(app);
