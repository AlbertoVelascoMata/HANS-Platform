import { React } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Header from './components/Header';
import SessionLogin from './components/SessionLogin';
import Session from './components/Session';

function App() {
  return (
    <Router basename={process.env.PUBLIC_URL}>
      <Header />
      <div>
        <Routes>
          <Route path="/" element={<SessionLogin/>} />
          <Route path="/session" element={<Session/>} />
        </Routes>
      </div>
    </Router>
  )
}

export default App;
