import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function AppShell() {
  return (
    <div className="flex min-h-screen bg-[--color-bg]">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0" style={{ marginLeft: '232px' }}>
        <TopBar />
        <main className="flex-1 p-7 animate-fade-up">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
