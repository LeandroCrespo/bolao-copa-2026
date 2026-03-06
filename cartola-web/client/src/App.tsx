import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import DashboardLayout from "./components/DashboardLayout";
import { lazy, Suspense } from "react";
import { Loader2 } from "lucide-react";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Escalacao = lazy(() => import("./pages/Escalacao"));
const Mercado = lazy(() => import("./pages/Mercado"));
const Simulacao = lazy(() => import("./pages/Simulacao"));
const Historico = lazy(() => import("./pages/Historico"));
const Atualizar = lazy(() => import("./pages/Atualizar"));
const StatusColeta = lazy(() => import("./pages/StatusColeta"));
const AnaliseJogador = lazy(() => import("./pages/AnaliseJogador"));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  );
}

function Router() {
  return (
    <DashboardLayout>
      <Suspense fallback={<PageLoader />}>
        <Switch>
          <Route path="/" component={Dashboard} />
          <Route path="/escalacao" component={Escalacao} />
          <Route path="/mercado" component={Mercado} />
          <Route path="/simulacao" component={Simulacao} />
          <Route path="/historico" component={Historico} />
          <Route path="/atualizar" component={Atualizar} />
          <Route path="/status-coleta" component={StatusColeta} />
          <Route path="/jogador" component={AnaliseJogador} />
          <Route path="/jogador/:id" component={AnaliseJogador} />
          <Route path="/404" component={NotFound} />
          <Route component={NotFound} />
        </Switch>
      </Suspense>
    </DashboardLayout>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="dark">
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
