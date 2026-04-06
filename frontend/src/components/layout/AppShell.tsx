import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import { SidebarProvider } from "../../contexts/SidebarContext";
export default function AppShell() {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen bg-bg">
        {/* Sidebar (left) */}
        <Sidebar />

        {/* Right Content Area */}
        <div className="flex flex-col flex-1">
          <TopBar />

          {/* Main Content */}
          <main className="flex-1 p-4 md:p-7 overflow-x-hidden">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
