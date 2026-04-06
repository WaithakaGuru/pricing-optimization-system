import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import { SidebarProvider } from "../../contexts/SidebarContext";

export default function AppShell() {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen bg-bg flex-col">
        <TopBar />
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 p-4 md:p-7 animate-fade-up overflow-x-hidden">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
