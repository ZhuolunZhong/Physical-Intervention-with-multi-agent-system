import React from 'react';
import ReactDOM from 'react-dom/client';
import {
    createBrowserRouter,
    RouterProvider
} from 'react-router-dom';
import Consent from './routes/consent';
import Consent2 from './routes/consent2';
import ErrorPage from './routes/error_page';
import MainExpt from './routes/main_expt';
import Root from './routes/root';
import FinishedPage from './routes/FinishedPage';
import SurveyPage from './routes/survey';

export const App = createBrowserRouter([
  {
    path: '/',
    element: <Consent2 />,
    errorElement: <ErrorPage />,
  },
  {
    path: '/main_expt',
    element: <MainExpt />,
    errorElement: <ErrorPage />,
  },
  {
    path: '/consent',
    element: <Consent />,
    errorElement: <ErrorPage />,
  },
  {
    path: '/consent2', 
    element: <Consent2 />,
    errorElement: <ErrorPage />,
  },
  {
    path: '/finished',
    element: <FinishedPage />,
    errorElement: <ErrorPage />,
  },
  {
    path: '/survey',
    element: <SurveyPage />,
    errorElement: <ErrorPage />,
  },
]);

export default App;