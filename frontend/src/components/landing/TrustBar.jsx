import { motion } from "framer-motion";

const logos = [
  { name: "FashionHub", color: "#2563eb" },
  { name: "StyleStore", color: "#4f46e5" },
  { name: "TrendyWear", color: "#7c3aed" },
  { name: "UrbanMatch", color: "#2563eb" },
  { name: "FusionWear", color: "#4f46e5" },
];

export default function TrustBar() {
  return (
    <section data-testid="trust-bar" className="py-12 bg-gray-50 border-y border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <p className="text-center text-sm text-gray-500 uppercase tracking-wide mb-8 font-medium">
          Trusted by fashion retailers worldwide
        </p>
        <div className="flex flex-wrap justify-center items-center gap-8 md:gap-14">
          {logos.map((logo, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: idx * 0.1 }}
              className="flex items-center gap-2 opacity-40 grayscale hover:opacity-100 hover:grayscale-0 transition-all duration-300 cursor-default"
            >
              <div className="w-7 h-7 rounded-md flex items-center justify-center text-white text-xs font-bold" style={{ backgroundColor: logo.color }}>
                {logo.name[0]}
              </div>
              <span className="text-lg font-semibold text-gray-600">{logo.name}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
