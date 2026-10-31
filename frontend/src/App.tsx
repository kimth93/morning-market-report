import { useEffect, useState } from "react";
import { loadSnapshot, type Report } from "./api/news";
import Disclaimer from "./components/Disclaimer";
import EmailSubscription from "./components/EmailSubscription";
import Footer from "./components/Footer";
import Header from "./components/Header";
import HeroSection from "./components/HeroSection";
import ResultsSection from "./components/ResultsSection";
import TrustPrinciples from "./components/TrustPrinciples";

export default function App() {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    loadSnapshot()
      .then((data) => {
        if (active) setReport(data);
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다");
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <Disclaimer />
      <main className="mx-auto w-full max-w-4xl flex-1 px-6">
        {report && <HeroSection generatedAt={report.generated_at} sourceNote={report.source_note} />}
        {!report && !error && <p role="status" className="py-10 text-label-neutral">보고서를 불러오는 중입니다</p>}
        {error && (
          <p role="alert" className="py-10 text-red-700">
            {error}
          </p>
        )}
        {report && <ResultsSection result={report} />}
        <TrustPrinciples />
        <EmailSubscription />
      </main>
      <Footer />
    </div>
  );
}
