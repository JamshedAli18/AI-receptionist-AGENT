import Hero from "@/components/hero/Hero";
import FeatureGrid from "@/components/FeatureGrid";
import HowItWorks from "@/components/HowItWorks";
import ArchitectureCallout from "@/components/ArchitectureCallout";
import DemoCTA from "@/components/DemoCTA";
import Footer from "@/components/Footer";

export default function LandingPage() {
  return (
    <>
      <Hero />
      <FeatureGrid />
      <HowItWorks />
      <ArchitectureCallout />
      <DemoCTA />
      <Footer />
    </>
  );
}
