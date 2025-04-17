import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './components/Home';
import Quiz from './components/Quiz';
import QuestionManager from './components/QuestionManager';
import WikiList from './components/wiki/WikiList';
import WikiPage from './components/wiki/WikiPage';
import WikiEditor from './components/wiki/WikiEditor';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/quiz/:topic" element={<Quiz />} />
          <Route path="/manage-questions" element={<QuestionManager />} />
          
          {/* Wiki Routes */}
          <Route path="/wiki" element={<WikiList />} />
          <Route path="/wiki/category/:category" element={<WikiList />} />
          <Route path="/wiki/create" element={<WikiEditor />} />
          <Route path="/wiki/edit/:slug" element={<WikiEditor />} />
          <Route path="/wiki/:slug" element={<WikiPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;