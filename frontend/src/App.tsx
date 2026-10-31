import { useEffect, useRef, useState } from "react";
import { loadSnapshot, type Report } from "./api/news";
import Disclaimer from "./components/Disclaimer";
import EmailSubscription from "./components/EmailSubscription";
import Footer from "./components/Footer";
import Header from "./components/Header";
import HeroSection from "./components/HeroSection";
import ResultsSection from "./components/ResultsSection";
import TrustPrinciples from "./components/TrustPrinciples";
import { nextStepIndex, PLAYBACK_STEPS } from "./state/playback";

const STEP_INTERVAL_MS = 1200;

export default function App() {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [replaying, setReplaying] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const mounted = useRef(true);

  const fetchReport = () =>
    loadSnapshot()
      .then((data) => {
        if (mounted.current) setReport(data);
      })
      .catch((err: unknown) => {
        if (mounted.current) setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다");
      });

  useEffect(() => {
    mounted.current = true;
    void fetchReport();
    return () => {
      mounted.current = false;
    };
  }, []);

  // 재생 중에는 단계 문구를 순환시키고, 끝나면 저장된 보고서를 다시 불러온다.
  useEffect(() => {
    if (!replaying) return;
    let step = 0;
    const id = setInterval(() => {
      step += 1;
      if (step >= PLAYBACK_STEPS.length) {
        clearInterval(id);
        setReplaying(false);
        setStepIndex(0);
        void fetchReport();
        return;
      }
      setStepIndex(nextStepIndex(step - 1));
    }, STEP_INTERVAL_MS);
    return () => clearInterval(id);
  }, [replaying]);

  const handleReplay = () => {
    if (replaying) return;
    setError(null);
    setStepIndex(0);
    setReplaying(true);
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <Disclaimer />
      <main className="mx-auto w-full max-w-4xl flex-1 px-6">
        {report && (
          <HeroSection
            generatedAt={report.generated_at}
            sourceNote={report.source_note}
            replaying={replaying}
            stepIndex={stepIndex}
            onReplay={handleReplay}
          />
        )}
        {!report && !error && <p role="status" className="py-10 text-label-neutral">보고서를 불러오는 중입니다</p>}
        {error && (
          <p role="alert" className="py-10 text-red-700">
            {error}
          </p>
        )}
        {report && !replaying && <ResultsSection result={report} />}
        <TrustPrinciples />
        <EmailSubscription />
      </main>
      <Footer />
    </div>
  );
}
