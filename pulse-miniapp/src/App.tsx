import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DigestPage } from './pages/DigestPage';
import { StoryPage } from './pages/StoryPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DigestPage />} />
        <Route path="/story/:id" element={<StoryPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
