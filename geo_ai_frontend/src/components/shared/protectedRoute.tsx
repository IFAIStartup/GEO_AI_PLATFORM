import React, { PropsWithChildren } from "react";
import { Navigate, Outlet } from "react-router-dom";

interface Props {
  isAllowed: boolean;
}

export const ProtectedRoute: React.FC<PropsWithChildren<Props>> = ({
  isAllowed,
  children,
}) => {
  if (!isAllowed) {
    return <Navigate to="/projects" replace />;
  }

  return children ? children : <Outlet />;
};
