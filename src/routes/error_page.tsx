import {useRouteError, isRouteErrorResponse} from 'react-router-dom';

export default function ErrorPage() {
    const error = useRouteError();
    console.error(error);

    return (
        <div id='error_page'>
            <h1>Uh oh!</h1>
            <p>Sorry, an unexpected error has occurred.</p>
            <p>
                Please send the error and details of what led to it austerweil@wisc.edu.
            </p>
            <p>
                <i> {isRouteErrorResponse(error) ? (error.statusText) : 'not a route error'
                }</i>
            </p>
        </div>
    );
}