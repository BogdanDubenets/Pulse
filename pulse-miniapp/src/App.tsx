import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DigestPage } from './pages/DigestPage';
import { StoryPage } from './pages/StoryPage';
import { CatalogPage } from './pages/CatalogPage';
import { CategoryPage } from './pages/CategoryPage';
import { useThemeStore } from './store/themeStore';
import { useEffect } from 'react';

// Build verification: 6500037_v3_461874849
function App() {
  const initTheme = useThemeStore(state => state.initTheme);

  useEffect(() => {
    initTheme();
  }, [initTheme]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DigestPage />} />
        <Route path="/story/:id" element={<StoryPage />} />
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="/catalog/:category" element={<CategoryPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
