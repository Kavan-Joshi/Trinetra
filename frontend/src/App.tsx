import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import { getToken } from './api'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import MapView from './pages/MapView'
import AlertsPage from './pages/AlertsPage'
import EventsPage from './pages/EventsPage'
import WatchlistPage from './pages/WatchlistPage'
import CamerasPage from './pages/CamerasPage'
import DepartmentsPage from './pages/DepartmentsPage'
import GapAnalysisPage from './pages/GapAnalysisPage'
import RecordsPage from './pages/RecordsPage'
import NotificationsPage from './pages/NotificationsPage'
import LiveViewPage from './pages/LiveViewPage'
import MosaicPage from './pages/MosaicPage'
import CommunityPage from './pages/CommunityPage'

function RequireAuth({ children }: { children: JSX.Element }) {
  return getToken() ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route path="/" element={<Dashboard />} />
          <Route path="/map" element={<MapView />} />
          <Route path="/live" element={<LiveViewPage />} />
          <Route path="/grid" element={<MosaicPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
          <Route path="/cameras" element={<CamerasPage />} />
          <Route path="/gap-analysis" element={<GapAnalysisPage />} />
          <Route path="/departments" element={<DepartmentsPage />} />
          <Route path="/records" element={<RecordsPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/community" element={<CommunityPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  )
}
