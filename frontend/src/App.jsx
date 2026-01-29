import { BrowserRouter, Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing";
import Tutorial from "./pages/Tutorial";
import ChooseSet from "./pages/ChooseSet";
import ChoosePaintings from "./pages/ChoosePaintings";
import Results from "./pages/Results";
import { AppProvider } from "./AppContext";

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/tutorial" element={<Tutorial />} />
          <Route path="/choose-set" element={<ChooseSet />} />
          <Route path="/choose-paintings" element={<ChoosePaintings />} />
          <Route path="/results" element={<Results />} />
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}