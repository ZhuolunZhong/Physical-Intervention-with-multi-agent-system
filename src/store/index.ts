import { createStore, applyMiddleware } from "redux";
import createSagaMiddleware from "@redux-saga/core";
import {composeWithDevTools} from 'redux-devtools-extension'
import watcherSagas from "./sagas";
import gameReducer from "./reducers";


const sagaMiddleware = createSagaMiddleware();

const store = createStore(gameReducer,
                          composeWithDevTools(applyMiddleware(sagaMiddleware)));

sagaMiddleware.run(watcherSagas);

export default store;