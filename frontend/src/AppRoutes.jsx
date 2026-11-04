import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import Landing from './Landing';

const App = lazy(() => import('./App'));

export default function AppRoutes() {
  return <Suspense fallback={<main className="route-loading" role="status">Opening your workspace…</main>}>
    <Routes><Route path="/" element={<Landing />} /><Route path="/app" element={<App />} /></Routes>
  </Suspense>;
}
