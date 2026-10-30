import { useEffect, useReducer, useRef } from "react";
import { generateNews } from "./api/news";
import Disclaimer from "./components/Disclaimer";
import EmailSubscription from "./components/EmailSubscription";
import Footer from "./components/Footer";
import Header from "./components/Header";
import HeroSection from "./components/HeroSection";
import ResultsSection from "./components/ResultsSection";
import TrustPrinciples from "./components/TrustPrinciples";
import { initialState, reducer } from "./state/generation";

const STEP_INTERVAL_MS = 1500;

export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const inFlight = useRef(false);

  // 생성 중에만 단계 문구를 순환시킨다. 백엔드는 진행률을 주지 않는다.
  useEffect(() => {
    if (state.phase !== "generating") return;
    const id = setInterval(() => dispatch({ type: "stepTick" }), STEP_INTERVAL_MS);
    return () => clearInterval(id);
  }, [state.phase]);

  const handleGenerate = async () => {
    if (inFlight.current) return;
    inFlight.current = true;
    dispatch({ type: "start" });
    try {
      const result = await generateNews();
      dispatch({ type: "succeed", result });
    } catch (error) {
      dispatch({ type: "fail", message: error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다" });
    } finally {
      inFlight.current = false;
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <Disclaimer />
      <main className="mx-auto w-full max-w-4xl flex-1 px-6">
        <HeroSection state={state} onGenerate={handleGenerate} onRetry={handleGenerate} />
        {state.phase === "done" && state.result && <ResultsSection result={state.result} />}
        <TrustPrinciples />
        <EmailSubscription />
      </main>
      <Footer />
    </div>
  );
}
