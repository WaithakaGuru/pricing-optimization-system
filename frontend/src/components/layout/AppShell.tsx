import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

export default function AppShell() {
  return (
    <div className="flex min-h-screen bg-bg flex-col md:flex-row">
      <Sidebar />
      <div className="flex flex-col flex-1">
        <TopBar />
        <main className="flex-1 p-4 md:p-7 animate-fade-up overflow-x-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
