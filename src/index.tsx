import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import Cookies from 'universal-cookie';
import { RouterProvider } from 'react-router-dom';


const cookies = new Cookies();
cookies.set('SameSite', 'Strict');

// const root = ReactDOM.createRoot(
//   document.getElementById('root') as HTMLElement
// );

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <RouterProvider router={App} />
)


// root.render(
//     <App />
// );
