import { React } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Header from './components/Header';
import SessionLogin from './components/SessionLogin';
import SessionView from './components/Session';
import DebugBoardView from "./components/DebugBoardView";

function App() {
  return (
    <Router basename={process.env.PUBLIC_URL}>
      <Header />
      <div>
        <Routes>
          <Route path="/" element={<SessionLogin/>} />
          <Route path="/session" element={<SessionView/>} />
          <Route path="/debug" element={<DebugBoardView/>} />
        </Routes>
      </div>
    </Router>
  )
}

export default App;
