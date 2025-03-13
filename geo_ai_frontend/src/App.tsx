import React, { useState, useEffect } from "react";
import { Routes, Route, useNavigate, useLocation } from "react-router-dom";

import { LoadingPage } from "@pages/loading";
import { LoginPage } from "@pages/login";
import { RestoreAccessPage } from "@pages/restore-access";
import { ResetPasswordPage } from "@pages/reset-password";
import { NoMatchPage } from "@pages/no-match";
import { ProjectListPage } from "@pages/project-list";
import { ProjectPage } from "@pages/project";
import { HistoryPage } from "@pages/history";
import { MLModelListPage } from "@pages/ml-model-list";
import { MLModelPage } from "@pages/ml-model";
import { CreateMLModelPage } from "@pages/ml-model-create";
import { AdminPage } from "@pages/admin";
import { ComparisonPage } from "@pages/comparison";

import { useUserStore } from "@store/user.store";
import { LoginLayout } from "@components/login/loginLayout";
import { MainLayout } from "@components/layout/mainLayout";
import { ProtectedRoute } from "@components/shared/protectedRoute";
import { TOKEN_KEY } from "@models/constants";
import { Role } from "@models/user";

export const App: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const checkAuth = useUserStore((state) => state.checkAuth);
  const user = useUserStore((state) => state.user);
  const [isLoading, setIsLoadig] = useState(true);

  useEffect(() => {
    if (localStorage.getItem(TOKEN_KEY)) {
      checkAuth()
        .then(() => {
          setIsLoadig(false);
          if (location.pathname === "/") {
            navigate("/projects", { replace: true });
          }
        })
        .catch(() => {
          setIsLoadig(false);
          if (
            !location.pathname.startsWith("/login") &&
            !location.pathname.startsWith("/restore-access")
          ) {
            navigate("/login", { replace: true });
          }
        });
    } else {
      setIsLoadig(false);
      if (
        !location.pathname.startsWith("/login") &&
        !location.pathname.startsWith("/restore-access")
      ) {
        navigate("/login", { replace: true });
      }
    }
  }, []);

  return (
    <Routes>
      <Route element={<LoginLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/restore-access">
          <Route index element={<RestoreAccessPage />} />
          <Route path=":resetKey" element={<ResetPasswordPage />} />
        </Route>
      </Route>
      <Route element={isLoading ? <LoadingPage /> : <MainLayout />}>
        <Route path="/projects">
          <Route index element={<ProjectListPage />} />
          <Route path="comparison">
            <Route index element={<ProjectListPage />} />
            <Route path=":comparisonId" element={<ComparisonPage />} />
          </Route>
          <Route path=":projectId" element={<ProjectPage />} />
        </Route>
        <Route path="/history" element={<HistoryPage />} />
        <Route
          path="/ml"
          element={
            <ProtectedRoute
              isAllowed={[Role.ML, Role.Admin].includes(
                user?.role || Role.User
              )}
            />
          }
        >
          <Route index element={<MLModelListPage />} />
          <Route path="create" element={<CreateMLModelPage />} />
          <Route path=":modelId" element={<MLModelPage />} />
        </Route>
        <Route
          path="/admin"
          element={
            <ProtectedRoute
              isAllowed={[Role.Admin].includes(user?.role || Role.User)}
            >
              <AdminPage />
            </ProtectedRoute>
          }
        />
        <Route path="/not-found" element={<NoMatchPage />} />
        <Route path="*" element={<NoMatchPage />} />
      </Route>
    </Routes>
  );
};
