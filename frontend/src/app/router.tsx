import { Navigate, createBrowserRouter } from "react-router-dom";

import { AppLayout } from "./AppLayout";
import { MainPage } from "../pages/MainPage";
import { CreateTypePage } from "../pages/CreateTypePage";
import { TypeDetailsPage } from "../pages/TypeDetailsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <MainPage />,
      },
      {
        path: "types/new",
        element: <CreateTypePage />,
      },
      {
        path: "types/:typeId",
        element: <TypeDetailsPage />,
      },
      {
        path: "*",
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);
