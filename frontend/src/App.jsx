import React from 'react';
import { Provider } from 'react-redux';
import store from './store/store';
import InteractionForm from './components/InteractionForm';
import ChatInterface from './components/ChatInterface';
import Toast from './components/Toast';
import './App.css';

function App() {
  return (
    <Provider store={store}>
      <div className="app">
        <header className="app-header">
          <h1>HCP CRM - Log Interaction</h1>
        </header>

        <main className="app-main">
          <div className="panel left-panel">
            <InteractionForm />
          </div>

          <div className="panel right-panel">
            <ChatInterface />
          </div>
        </main>

        <Toast />
      </div>
    </Provider>
  );
}

export default App;
