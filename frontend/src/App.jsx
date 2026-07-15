import { Route, Routes } from "react-router-dom";
import TopNav from "./components/TopNav.jsx";
import Footer from "./components/Footer.jsx";
import NewAnalysis from "./pages/NewAnalysis.jsx";
import Analyzing from "./pages/Analyzing.jsx";
import Report from "./pages/Report.jsx";
import History from "./pages/History.jsx";
import Rulers from "./pages/Rulers.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <TopNav />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<NewAnalysis />} />
          <Route path="/analyze/:hoSo" element={<Analyzing />} />
          <Route path="/report/:hoSo" element={<Report />} />
          <Route path="/ho-so" element={<History />} />
          <Route path="/thuoc" element={<Rulers />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
